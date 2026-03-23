#!/usr/bin/env python3
"""
OpenClaw PaaS - Setup Wizard
Zero-touch provisioning: core credentials, AI engine, chat platform.
Async: POST /setup returns immediately, background thread provisions,
frontend polls GET /setup/status.
"""

import base64
import json
import logging
import os
import threading
import time

import requests as http_requests
from flask import Flask, render_template, request, jsonify
from kubernetes import client, config

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("setup-wizard")

NAMESPACE = os.environ.get("NAMESPACE", "openclaw-tenant-1")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "")
CF_TUNNEL_ID = os.environ.get("CF_TUNNEL_ID", "")
DOMAIN = os.environ.get("DOMAIN", "cindytech1-openclaw.woowtech.io")

_k8s_core = None
_k8s_apps = None

setup_state = {
    "running": False, "step": 0, "step_label": "",
    "done": False, "success": False, "error": "", "message": "",
}
setup_lock = threading.Lock()

# AI provider → env var name mapping
AI_ENV_MAP = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GEMINI_API_KEY",
    "minimax": "MINIMAX_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "qwen": "QWEN_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "ollama": "OLLAMA_HOST",
}

# AI provider → model prefix
AI_MODEL_MAP = {
    "openai": "openai/gpt-4o",
    "anthropic": "anthropic/claude-sonnet-4-20250514",
    "google": "google/gemini-2.0-flash",
    "minimax": "minimax/MiniMax-M2.5",
    "deepseek": "deepseek/deepseek-chat",
    "qwen": "qwen/qwen-max",
    "openrouter": "openrouter/auto",
    "ollama": "ollama/llama3",
}

# AI provider → auth-profiles.json key
AI_AUTH_KEY = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google",
    "minimax": "minimax",
    "deepseek": "deepseek",
    "qwen": "qwen",
    "openrouter": "openrouter",
}

# Chat platform → env var / channel name
CHAT_ENV_MAP = {
    "telegram": ("TELEGRAM_BOT_TOKEN", "telegram"),
    "discord": ("DISCORD_BOT_TOKEN", "discord"),
    "slack": ("SLACK_BOT_TOKEN", "slack"),
    "whatsapp": ("WHATSAPP_ENABLED", "whatsapp"),
}


def set_state(**kwargs):
    with setup_lock:
        setup_state.update(kwargs)
    if "step_label" in kwargs:
        log.info(f"[Step {setup_state['step']}] {kwargs['step_label']}")


def get_k8s_clients():
    global _k8s_core, _k8s_apps
    if _k8s_core is None:
        config.load_incluster_config()
        _k8s_core = client.CoreV1Api()
        _k8s_apps = client.AppsV1Api()
    return _k8s_core, _k8s_apps


def create_secret(secret_data):
    """Create or patch openclaw-secrets with all provided key-value pairs."""
    core, _ = get_k8s_clients()
    encoded = {k: base64.b64encode(v.encode()).decode() for k, v in secret_data.items() if v}
    secret = client.V1Secret(
        metadata=client.V1ObjectMeta(name="openclaw-secrets", namespace=NAMESPACE),
        type="Opaque",
        data=encoded,
    )
    try:
        core.read_namespaced_secret("openclaw-secrets", NAMESPACE)
        core.patch_namespaced_secret("openclaw-secrets", NAMESPACE, secret)
    except client.exceptions.ApiException as e:
        if e.status == 404:
            core.create_namespaced_secret(NAMESPACE, secret)
        else:
            raise


def scale_deployment(name, replicas):
    _, apps = get_k8s_clients()
    apps.patch_namespaced_deployment_scale(name, NAMESPACE, {"spec": {"replicas": replicas}})
    log.info(f"Scaled '{name}' to {replicas}")


def wait_for_gateway(timeout=180, interval=3):
    import socket
    start = time.time()
    deadline = start + timeout
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        elapsed = int(time.time() - start)
        set_state(step_label=f"Waiting for system readiness... ({elapsed}s)")
        try:
            sock = socket.create_connection(("openclaw-gateway-svc", 18789), timeout=3)
            sock.close()
            log.info(f"Gateway ready (attempt #{attempt}, {elapsed}s)")
            return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            log.info(f"Gateway not reachable (attempt #{attempt}, {elapsed}s)")
        time.sleep(interval)
    return False


def configure_gateway(ai_provider, ai_api_key, ai_model):
    """Configure AI model, auth-profiles, chat channel, and auto-approve devices."""
    core, _ = get_k8s_clients()

    pods = core.list_namespaced_pod(NAMESPACE, label_selector="app=openclaw-gateway")
    if not pods.items:
        log.warning("No gateway pod found for configuration")
        return

    pod_name = pods.items[0].metadata.name
    from kubernetes.stream import stream

    def exec_cmd(cmd):
        try:
            result = stream(
                core.connect_get_namespaced_pod_exec,
                pod_name, NAMESPACE,
                command=["/bin/sh", "-c", cmd],
                stderr=True, stdout=True, stdin=False, tty=False,
            )
            log.info(f"Exec [{cmd[:60]}]: {result.strip()[:100]}")
            return result
        except Exception as e:
            log.warning(f"Exec failed [{cmd[:40]}]: {e}")
            return ""

    # Write auth-profiles.json with API key (v1 format, critical for AI to work)
    if ai_provider and ai_api_key:
        auth_key = AI_AUTH_KEY.get(ai_provider)
        if auth_key:
            auth_json = json.dumps({
                "version": 1,
                "profiles": {
                    auth_key: {
                        "type": "api_key",
                        "key": ai_api_key,
                        "provider": auth_key,
                    }
                }
            })
            exec_cmd(
                f'mkdir -p /home/node/.openclaw/agents/main/agent && '
                f'echo \'{auth_json}\' > /home/node/.openclaw/agents/main/agent/auth-profiles.json'
            )
            log.info(f"Wrote auth-profiles.json for {auth_key}")

        # Set model with provider prefix
        raw_model = ai_model or AI_MODEL_MAP.get(ai_provider, "")
        if raw_model and "/" not in raw_model:
            raw_model = f"{ai_provider}/{raw_model}"
        if raw_model:
            exec_cmd(f'openclaw config set agents.defaults.model "{raw_model}"')

    # Auto-approve any pending device pairing requests
    import time as _time
    _time.sleep(2)
    exec_cmd(
        'openclaw devices list 2>/dev/null | grep -oP "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" '
        '| while read req; do openclaw devices approve "$req" 2>/dev/null; done'
    )


def switch_cloudflare_route():
    url = (
        f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}"
        f"/cfd_tunnel/{CF_TUNNEL_ID}/configurations"
    )
    payload = {
        "config": {
            "ingress": [
                {"hostname": DOMAIN, "service": "http://openclaw-gateway-svc:18789"},
                {"service": "http_status:404"},
            ]
        }
    }
    resp = http_requests.put(
        url,
        headers={"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"},
        json=payload, timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"Cloudflare API error: {data.get('errors')}")
    return data


def run_setup(params):
    """Background thread: full provisioning pipeline."""
    gateway_token = params["gateway_token"]
    db_password = params["db_password"]
    ai_provider = params.get("ai_provider", "")
    ai_api_key = params.get("ai_api_key", "")
    ai_model = params.get("ai_model", "")
    try:
        # Step 1: Create K8s Secret with all credentials
        set_state(step=1, step_label="Creating encryption keys...")
        secret_data = {
            "OPENCLAW_GATEWAY_TOKEN": gateway_token,
            "POSTGRES_PASSWORD": db_password,
        }
        if ai_provider and ai_api_key:
            env_name = AI_ENV_MAP.get(ai_provider, "")
            if env_name:
                secret_data[env_name] = ai_api_key
        create_secret(secret_data)

        # Step 2: Scale up database
        set_state(step=2, step_label="Starting database engine...")
        scale_deployment("openclaw-db", 1)

        # Step 3: Scale up gateway
        set_state(step=3, step_label="Launching AI gateway...")
        scale_deployment("openclaw-gateway", 1)

        # Step 4: Wait for gateway
        set_state(step=4, step_label="Waiting for system readiness...")
        if not wait_for_gateway(timeout=180, interval=3):
            set_state(
                done=True, success=False, running=False,
                error="OpenClaw Gateway did not start within 180 seconds.",
            )
            return

        # Step 5: Configure AI engine & chat channels
        set_state(step=5, step_label="Configuring AI & channels...")
        try:
            configure_gateway(ai_provider, ai_api_key, ai_model)
        except Exception as e:
            log.warning(f"Gateway configuration partially failed: {e}")

        # Step 6: Switch Cloudflare route
        set_state(step=6, step_label="Switching network routes...")
        try:
            switch_cloudflare_route()
        except Exception as e:
            set_state(
                done=True, success=False, running=False,
                error=f"Cloudflare route switch failed: {e}",
            )
            return

        # Step 7: Done
        set_state(
            step=7, step_label="Deployment complete!",
            done=True, success=True, running=False,
            message=f"https://{DOMAIN}/#token={gateway_token}",
        )

        # Self-destruct
        time.sleep(5)
        try:
            scale_deployment("setup-wizard", 0)
            log.info("Setup wizard self-destructed.")
        except Exception as e:
            log.error(f"Self-destruct failed: {e}")

    except Exception as e:
        log.exception("Setup pipeline failed.")
        set_state(done=True, success=False, running=False, error=f"Unexpected error: {e}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/setup", methods=["POST"])
def setup():
    gateway_token = request.form.get("gateway_token", "").strip()
    db_password = request.form.get("db_password", "").strip()

    if not gateway_token or not db_password:
        return jsonify({"success": False, "error": "Gateway token and database password are required."}), 400

    if not CF_API_TOKEN or not CF_ACCOUNT_ID or not CF_TUNNEL_ID:
        return jsonify({"success": False, "error": "Missing Cloudflare configuration."}), 500

    with setup_lock:
        if setup_state["running"]:
            return jsonify({"success": False, "error": "Setup is already in progress."}), 409
        setup_state.update(running=True, step=0, done=False, success=False, error="", message="")

    params = {
        "gateway_token": gateway_token,
        "db_password": db_password,
        "ai_provider": request.form.get("ai_provider", "").strip(),
        "ai_api_key": request.form.get("ai_api_key", "").strip(),
        "ai_model": request.form.get("ai_model", "").strip(),
    }

    t = threading.Thread(target=run_setup, args=(params,), daemon=True)
    t.start()
    return jsonify({"success": True, "message": "Setup started."})


@app.route("/setup/status")
def setup_status():
    with setup_lock:
        return jsonify(dict(setup_state))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=18790, debug=False)
