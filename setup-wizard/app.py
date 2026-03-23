#!/usr/bin/env python3
"""
OpenClaw PaaS - Setup Wizard (Docker Compose / Podman Edition)
Zero-touch provisioning: AI engine configuration + Cloudflare tunnel routing.
Adapted from K8s version for Podman Docker Compose deployment.

POST /setup  -> starts background provisioning
GET  /setup/status -> polls progress
"""

import json
import logging
import os
import socket
import sys
import threading
import time

import docker
import requests as http_requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("setup-wizard")

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------
GATEWAY_HOST = os.environ.get("GATEWAY_HOST", "openclaw-gateway")
GATEWAY_PORT = int(os.environ.get("GATEWAY_PORT", "18789"))

CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "")
CF_TUNNEL_ID = os.environ.get("CF_TUNNEL_ID", "")
CF_TUNNEL_DOMAIN = os.environ.get("CF_TUNNEL_DOMAIN", "woowtech-openclaw.woowtech.io")

WIZARD_PORT = int(os.environ.get("WIZARD_PORT", "18790"))

# Path to host .env file (mounted as volume for persistence)
HOST_ENV_FILE = os.environ.get("HOST_ENV_FILE", "/host-env/.env")

# ---------------------------------------------------------------------------
# State management (thread-safe)
# ---------------------------------------------------------------------------
setup_state = {
    "running": False, "step": 0, "step_label": "",
    "done": False, "success": False, "error": "", "message": "",
}
setup_lock = threading.Lock()

# AI provider mappings (same as K8s version)
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
AI_AUTH_KEY = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google",
    "minimax": "minimax",
    "deepseek": "deepseek",
    "qwen": "qwen",
    "openrouter": "openrouter",
}


def set_state(**kwargs):
    with setup_lock:
        setup_state.update(kwargs)
    if "step_label" in kwargs:
        log.info(f"[Step {setup_state['step']}] {kwargs['step_label']}")


def get_docker_client():
    """Get Docker/Podman client via socket."""
    return docker.DockerClient(base_url="unix:///var/run/docker.sock")


def _update_env_file(key, value):
    """Update or add a key=value pair in the host .env file.

    This ensures API keys configured via the setup wizard persist
    across container restarts (podman compose down/up).
    """
    env_path = HOST_ENV_FILE
    if not os.path.exists(os.path.dirname(env_path)):
        log.warning(f"Host .env directory not mounted at {os.path.dirname(env_path)}, skipping env persistence")
        return

    try:
        lines = []
        found = False
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith(f"{key}=") or stripped.startswith(f"{key} ="):
                    lines[i] = f"{key}={value}\n"
                    found = True
                    break
        if not found:
            lines.append(f"{key}={value}\n")
        with open(env_path, "w") as f:
            f.writelines(lines)
        log.info(f"Persisted {key} to host .env file")
    except Exception as e:
        log.warning(f"Failed to update host .env file: {e}")


# ---------------------------------------------------------------------------
# Step functions
# ---------------------------------------------------------------------------

def wait_for_gateway(timeout=180, interval=3):
    """TCP check on gateway readiness."""
    start = time.time()
    deadline = start + timeout
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        elapsed = int(time.time() - start)
        set_state(step_label=f"Waiting for system readiness... ({elapsed}s)")
        try:
            sock = socket.create_connection((GATEWAY_HOST, GATEWAY_PORT), timeout=3)
            sock.close()
            log.info(f"Gateway ready (attempt #{attempt}, {elapsed}s)")
            return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            log.info(f"Gateway not reachable (attempt #{attempt}, {elapsed}s)")
        time.sleep(interval)
    return False


def configure_gateway(ai_provider, ai_api_key, ai_model):
    """Configure AI model via podman exec through Docker socket API."""
    try:
        client = get_docker_client()
        container = client.containers.get("openclaw-gateway")
    except Exception as e:
        log.warning(f"Cannot connect to gateway container: {e}")
        return

    def exec_cmd(cmd):
        try:
            exit_code, output = container.exec_run(
                ["/bin/sh", "-c", cmd],
                demux=True,
            )
            stdout = output[0].decode().strip() if output[0] else ""
            stderr = output[1].decode().strip() if output[1] else ""
            result = stdout or stderr
            log.info(f"Exec [{cmd[:60]}]: exit={exit_code} {result[:100]}")
            return result
        except Exception as e:
            log.warning(f"Exec failed [{cmd[:40]}]: {e}")
            return ""

    # Write auth-profiles.json with API key (v1 format, merge with existing)
    if ai_provider and ai_api_key:
        auth_key = AI_AUTH_KEY.get(ai_provider)
        if auth_key:
            exec_cmd("mkdir -p /home/node/.openclaw/agents/main/agent")
            # Read existing auth-profiles to merge (don't overwrite other providers)
            existing_raw = exec_cmd(
                "cat /home/node/.openclaw/agents/main/agent/auth-profiles.json 2>/dev/null || echo '{}'"
            )
            try:
                existing = json.loads(existing_raw) if existing_raw.strip() else {}
            except (json.JSONDecodeError, ValueError):
                existing = {}
            # Ensure v1 format
            if existing.get("version") != 1:
                existing = {"version": 1, "profiles": {}}
            if "profiles" not in existing:
                existing["profiles"] = {}
            # Merge new profile
            existing["profiles"][auth_key] = {
                "type": "api_key",
                "key": ai_api_key,
                "provider": auth_key,
            }
            auth_json = json.dumps(existing)
            exec_cmd(
                f"echo '{auth_json}' > /home/node/.openclaw/agents/main/agent/auth-profiles.json"
            )
            log.info(f"Merged auth-profiles.json for {auth_key}")

        # Persist API key to host .env file (survives compose down/up)
        env_var_name = AI_ENV_MAP.get(ai_provider, "")
        if env_var_name and ai_api_key:
            _update_env_file(env_var_name, ai_api_key)

        # Set model with provider prefix
        raw_model = ai_model or AI_MODEL_MAP.get(ai_provider, "")
        if raw_model and "/" not in raw_model:
            raw_model = f"{ai_provider}/{raw_model}"
        if raw_model:
            exec_cmd(f'openclaw config set agents.defaults.model "{raw_model}"')

    # Auto-approve pending device pairing requests
    time.sleep(2)
    exec_cmd(
        'openclaw devices list 2>/dev/null | '
        'grep -oP "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" '
        '| while read req; do openclaw devices approve "$req" 2>/dev/null; done'
    )


def switch_cloudflare_route():
    """Update Cloudflare tunnel ingress to point to the gateway (3 retries)."""
    if not CF_API_TOKEN or not CF_ACCOUNT_ID or not CF_TUNNEL_ID:
        log.warning("Cloudflare credentials not configured, skipping route switch")
        return

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}"
        f"/cfd_tunnel/{CF_TUNNEL_ID}/configurations"
    )
    payload = {
        "config": {
            "ingress": [
                {"hostname": CF_TUNNEL_DOMAIN, "service": f"http://localhost:{GATEWAY_PORT}"},
                {"service": "http_status:404"},
            ]
        }
    }
    last_err = None
    for attempt in range(1, 4):
        try:
            resp = http_requests.put(
                url,
                headers={"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"},
                json=payload, timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success"):
                raise RuntimeError(f"Cloudflare API error: {data.get('errors')}")
            log.info(f"Cloudflare route switched to gateway (attempt {attempt})")
            return data
        except Exception as e:
            last_err = e
            log.warning(f"Cloudflare route attempt {attempt}/3 failed: {e}")
            if attempt < 3:
                time.sleep(3)
    raise RuntimeError(f"Cloudflare route switch failed after 3 attempts: {last_err}")


# ---------------------------------------------------------------------------
# Main provisioning pipeline
# ---------------------------------------------------------------------------

def run_setup(params):
    """Background thread: full provisioning pipeline for Docker Compose."""
    gateway_token = params["gateway_token"]
    ai_provider = params.get("ai_provider", "")
    ai_api_key = params.get("ai_api_key", "")
    ai_model = params.get("ai_model", "")

    try:
        # Step 1: Validate credentials
        set_state(step=1, step_label="Validating credentials...")
        if not gateway_token:
            raise ValueError("Gateway token is required")
        log.info("Credentials validated")

        # Step 2: Verify database connectivity
        set_state(step=2, step_label="Checking database engine...")
        # In Docker Compose, DB is already running via depends_on
        log.info("Database is managed by Docker Compose (already running)")

        # Step 3: Verify gateway is launched
        set_state(step=3, step_label="Checking AI gateway...")
        # In Docker Compose, gateway is already running via depends_on
        log.info("Gateway is managed by Docker Compose (already running)")

        # Step 4: Wait for gateway readiness
        set_state(step=4, step_label="Waiting for system readiness...")
        if not wait_for_gateway(timeout=180, interval=3):
            set_state(
                done=True, success=False, running=False,
                error="OpenClaw Gateway did not start within 180 seconds.",
            )
            return

        # Step 5: Configure AI engine
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
            log.warning(f"Cloudflare route switch skipped or failed: {e}")

        # Step 7: Done
        gateway_url = f"https://{CF_TUNNEL_DOMAIN}/#token={gateway_token}"
        set_state(
            step=7, step_label="Deployment complete!",
            done=True, success=True, running=False,
            message=gateway_url,
        )
        log.info(f"Setup complete! Gateway URL: {gateway_url}")

        # Exit wizard after a short delay (restart: "no" prevents restart)
        time.sleep(10)
        log.info("Setup wizard exiting.")
        os._exit(0)

    except Exception as e:
        log.exception("Setup pipeline failed.")
        set_state(done=True, success=False, running=False, error=f"Unexpected error: {e}")


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/setup", methods=["POST"])
def setup():
    gateway_token = request.form.get("gateway_token", "").strip()
    db_password = request.form.get("db_password", "").strip()

    if not gateway_token or not db_password:
        return jsonify({"success": False, "error": "Gateway token and database password are required."}), 400

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
    app.run(host="0.0.0.0", port=WIZARD_PORT, debug=False)
