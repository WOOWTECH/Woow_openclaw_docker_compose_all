#!/usr/bin/env python3
"""
OpenClaw Console — Unified setup wizard + management UI.
Extends the original setup wizard with management API endpoints.
"""

import base64
import json
import logging
import os
import subprocess
import threading
import time

import requests as http_requests
from flask import Flask, render_template, request, jsonify
from kubernetes import client, config

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("openclaw-console")

NAMESPACE = os.environ.get("NAMESPACE", "openclaw-tenant-1")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "")
CF_TUNNEL_ID = os.environ.get("CF_TUNNEL_ID", "")
DOMAIN = os.environ.get("DOMAIN", "cindytech1-openclaw.woowtech.io")

_k8s_core = None
_k8s_apps = None

# --- Setup wizard state ---
setup_state = {
    "running": False, "step": 0, "step_label": "",
    "done": False, "success": False, "error": "", "message": "",
}
setup_lock = threading.Lock()

# --- Health history state ---
health_history = []  # list of {time, health, pod}, max 100 entries
health_history_lock = threading.Lock()
HEALTH_HISTORY_MAX = 100


def health_check_loop():
    """Background thread: check gateway health every 60 seconds."""
    time.sleep(15)  # wait for Flask to start
    while True:
        try:
            pod = get_gateway_pod()
            entry = {
                "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "pod": pod or "",
                "health": "0",
            }
            if pod:
                result = subprocess.run(
                    ["kubectl", "exec", pod, "-n", NAMESPACE, "-c", "openclaw-gateway",
                     "--", "sh", "-c",
                     "curl -s -o /dev/null -w '%{http_code}' http://localhost:18789/health 2>/dev/null || echo 0"],
                    capture_output=True, text=True, timeout=10,
                )
                entry["health"] = result.stdout.strip() or "0"
            with health_history_lock:
                health_history.append(entry)
                if len(health_history) > HEALTH_HISTORY_MAX:
                    health_history.pop(0)
        except Exception as e:
            log.warning(f"Health check error: {e}")
        time.sleep(60)


# Start health check thread
threading.Thread(target=health_check_loop, daemon=True).start()


AI_ENV_MAP = {
    "openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY",
    "google": "GEMINI_API_KEY", "minimax": "MINIMAX_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY", "qwen": "QWEN_API_KEY",
    "openrouter": "OPENROUTER_API_KEY", "ollama": "OLLAMA_HOST",
}

AI_MODEL_MAP = {
    "openai": "openai/gpt-4o", "anthropic": "anthropic/claude-sonnet-4-20250514",
    "google": "google/gemini-2.0-flash", "minimax": "minimax/MiniMax-M2.5",
    "deepseek": "deepseek/deepseek-chat", "qwen": "qwen/qwen-max",
    "openrouter": "openrouter/auto", "ollama": "ollama/llama3",
}

AI_AUTH_KEY = {
    "openai": "openai", "anthropic": "anthropic", "google": "google",
    "minimax": "minimax", "deepseek": "deepseek", "qwen": "qwen",
    "openrouter": "openrouter",
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


# =========================================================
# K8s helpers
# =========================================================

def get_gateway_pod():
    """Return the first running openclaw-gateway pod name, or None."""
    core, _ = get_k8s_clients()
    pods = core.list_namespaced_pod(
        NAMESPACE, label_selector="app=openclaw-gateway",
        field_selector="status.phase=Running",
    )
    if pods.items:
        return pods.items[0].metadata.name
    return None


def kexec(cmd):
    """Non-interactive exec into the gateway pod. Returns stdout string."""
    pod = get_gateway_pod()
    if not pod:
        return ""
    try:
        result = subprocess.run(
            ["kubectl", "exec", pod, "-n", NAMESPACE, "-c", "openclaw-gateway",
             "--", "sh", "-c", cmd],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0 and result.stderr:
            log.warning(f"kexec non-zero exit [{cmd[:60]}]: {result.stderr[:200]}")
        return result.stdout
    except Exception as e:
        log.warning(f"kexec failed [{cmd[:60]}]: {e}")
        return ""


def kexec_write(file_path, content):
    """Write content to a file inside the gateway pod using stdin pipe to avoid shell quoting issues."""
    pod = get_gateway_pod()
    if not pod:
        return False
    try:
        result = subprocess.run(
            ["kubectl", "exec", pod, "-n", NAMESPACE, "-c", "openclaw-gateway",
             "-i", "--", "sh", "-c", f"cat > '{file_path}'"],
            input=content, capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            log.warning(f"kexec_write failed [{file_path}]: {result.stderr[:200]}")
            return False
        return True
    except Exception as e:
        log.warning(f"kexec_write exception [{file_path}]: {e}")
        return False


def create_secret(secret_data):
    core, _ = get_k8s_clients()
    encoded = {k: base64.b64encode(v.encode()).decode() for k, v in secret_data.items() if v}
    secret = client.V1Secret(
        metadata=client.V1ObjectMeta(name="openclaw-secrets", namespace=NAMESPACE),
        type="Opaque", data=encoded,
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


def wait_for_gateway(timeout=180, interval=3):
    import socket
    start = time.time()
    while time.time() - start < timeout:
        elapsed = int(time.time() - start)
        set_state(step_label=f"Waiting for system readiness... ({elapsed}s)")
        try:
            sock = socket.create_connection(("openclaw-gateway-svc", 18789), timeout=3)
            sock.close()
            return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            pass
        time.sleep(interval)
    return False


# =========================================================
# Management API endpoints
# =========================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/detect")
def api_detect():
    """Auto-detect: is gateway running?"""
    pod = get_gateway_pod()
    return jsonify({"running": pod is not None, "pod": pod or ""})


@app.route("/api/status")
def api_status():
    """Service status: pod, health, model, disk, processes."""
    pod = get_gateway_pod()
    if not pod:
        return jsonify({"running": False})

    # Health check
    health = kexec("curl -s -o /dev/null -w '%{http_code}' http://localhost:18789/health 2>/dev/null || echo 0")

    # Current model
    config_raw = kexec("cat /home/node/.openclaw/openclaw.json 2>/dev/null")
    model = ""
    try:
        model = json.loads(config_raw).get("agents", {}).get("defaults", {}).get("model", "")
    except Exception:
        pass

    # Disk
    disk = kexec("df -h /mnt/openclaw-agents/ 2>/dev/null | tail -1")

    # Uptime (pod age)
    core, _ = get_k8s_clients()
    pod_obj = core.read_namespaced_pod(pod, NAMESPACE)
    started = pod_obj.status.start_time.isoformat() if pod_obj.status.start_time else ""

    return jsonify({
        "running": True,
        "pod": pod,
        "node": pod_obj.spec.node_name or "",
        "health": health.strip(),
        "model": model,
        "disk": disk.strip(),
        "started": started,
    })


@app.route("/api/health-history")
def api_health_history():
    """Return health check history (max 100 entries, 1 per minute)."""
    with health_history_lock:
        history = list(health_history)
    total = len(history)
    ok_count = sum(1 for h in history if h["health"] == "200")
    uptime = round(ok_count / total * 100, 1) if total > 0 else 0
    return jsonify({"history": history, "uptime": uptime, "total": total})


@app.route("/api/config", methods=["GET"])
def api_config_get():
    raw = kexec("cat /home/node/.openclaw/openclaw.json 2>/dev/null")
    try:
        return jsonify(json.loads(raw))
    except Exception:
        return jsonify({"error": "unable to read config"}), 500


@app.route("/api/config", methods=["POST"])
def api_config_post():
    """Write to openclaw.json. Default: deep-merge. Use ?replace=1 for full replacement."""
    patch = request.get_json(force=True)
    full_replace = request.args.get("replace", "0") == "1"

    if full_replace:
        cfg = patch
    else:
        raw = kexec("cat /home/node/.openclaw/openclaw.json 2>/dev/null")
        try:
            cfg = json.loads(raw)
        except Exception:
            return jsonify({"error": "unable to read config"}), 500

        def deep_merge(base, override):
            for k, v in override.items():
                if isinstance(v, dict) and isinstance(base.get(k), dict):
                    deep_merge(base[k], v)
                else:
                    base[k] = v

        deep_merge(cfg, patch)

    ok = kexec_write("/home/node/.openclaw/openclaw.json", json.dumps(cfg, indent=2))
    return jsonify({"ok": ok})


@app.route("/api/config/model", methods=["POST"])
def api_config_model():
    data = request.get_json(force=True)
    model = data.get("model", "")
    if not model:
        return jsonify({"error": "model required"}), 400
    # Use openclaw CLI to set the model — this does a surgical JSON update
    # without reformatting the file or losing runtime-added fields.
    result = kexec(f'openclaw config set agents.defaults.model "{model}" 2>&1')
    ok = "error" not in result.lower() if result else False
    if not ok:
        # Fallback: read-modify-write
        raw = kexec("cat /home/node/.openclaw/openclaw.json 2>/dev/null")
        try:
            cfg = json.loads(raw)
        except Exception:
            return jsonify({"error": "unable to read config", "ok": False}), 500
        cfg.setdefault("agents", {}).setdefault("defaults", {})["model"] = model
        ok = kexec_write("/home/node/.openclaw/openclaw.json", json.dumps(cfg, indent=2))
    return jsonify({"ok": ok, "model": model})


@app.route("/api/env", methods=["GET"])
def api_env_get():
    content = kexec("cat /home/node/.openclaw/workspace/.env 2>/dev/null")
    return jsonify({"content": content})


@app.route("/api/env", methods=["POST"])
def api_env_post():
    data = request.get_json(force=True)
    content = data.get("content", "")
    ok = kexec_write("/home/node/.openclaw/workspace/.env", content)
    return jsonify({"ok": ok})


@app.route("/api/soul", methods=["GET"])
def api_soul_get():
    content = kexec("cat /home/node/.openclaw/workspace/SOUL.md 2>/dev/null")
    return jsonify({"content": content})


@app.route("/api/soul", methods=["POST"])
def api_soul_post():
    data = request.get_json(force=True)
    content = data.get("content", "")
    ok = kexec_write("/home/node/.openclaw/workspace/SOUL.md", content)
    return jsonify({"ok": ok})


@app.route("/api/channels")
def api_channels():
    raw = kexec("cat /home/node/.openclaw/openclaw.json 2>/dev/null")
    try:
        channels = json.loads(raw).get("channels", {})
        return jsonify(channels)
    except Exception:
        return jsonify({"error": "unable to read"}), 500


@app.route("/api/plugins")
def api_plugins():
    raw = kexec("ls /home/node/.openclaw/agents/_extensions/ 2>/dev/null")
    plugins = [p.strip() for p in raw.strip().split("\n") if p.strip()]
    result = []
    for p in plugins:
        size = kexec(f"du -sh /home/node/.openclaw/agents/_extensions/{p}/ 2>/dev/null").split("\t")[0] if p else ""
        result.append({"name": p, "size": size})
    return jsonify(result)


@app.route("/api/cron")
def api_cron():
    raw = kexec("cat /home/node/.openclaw/cron/jobs.json 2>/dev/null")
    try:
        return jsonify(json.loads(raw))
    except Exception:
        return jsonify([])


@app.route("/api/logs")
def api_logs():
    lines = request.args.get("lines", "100")
    pod = get_gateway_pod()
    if not pod:
        return jsonify({"logs": "Gateway pod not running."})
    try:
        result = subprocess.run(
            ["kubectl", "logs", pod, "-n", NAMESPACE, "-c", "openclaw-gateway", f"--tail={lines}"],
            capture_output=True, text=True, timeout=15,
        )
        return jsonify({"logs": result.stdout or result.stderr})
    except Exception as e:
        return jsonify({"logs": f"Error: {e}"})


@app.route("/api/restart", methods=["POST"])
def api_restart():
    try:
        result = subprocess.run(
            ["kubectl", "rollout", "restart", "deployment/openclaw-gateway", "-n", NAMESPACE],
            capture_output=True, text=True, timeout=15,
        )
        ok = result.returncode == 0
        return jsonify({"ok": ok, "message": result.stdout.strip() or result.stderr.strip()})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


# =========================================================
# Setup wizard (from original setup-wizard/app.py)
# =========================================================

def configure_gateway(ai_provider, ai_api_key, ai_model):
    pod = get_gateway_pod()
    if not pod:
        return
    if ai_provider and ai_api_key:
        auth_key = AI_AUTH_KEY.get(ai_provider)
        if auth_key:
            auth_json = json.dumps({
                "version": 1,
                "profiles": {
                    auth_key: {"type": "api_key", "key": ai_api_key, "provider": auth_key}
                }
            })
            kexec(
                f'mkdir -p /home/node/.openclaw/agents/main/agent && '
                f"echo '{auth_json}' > /home/node/.openclaw/agents/main/agent/auth-profiles.json"
            )
        raw_model = ai_model or AI_MODEL_MAP.get(ai_provider, "")
        if raw_model and "/" not in raw_model:
            raw_model = f"{ai_provider}/{raw_model}"
        if raw_model:
            kexec(f'openclaw config set agents.defaults.model "{raw_model}"')
    time.sleep(2)
    kexec(
        'openclaw devices list 2>/dev/null | grep -oP "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" '
        '| while read req; do openclaw devices approve "$req" 2>/dev/null; done'
    )


def switch_cloudflare_route():
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/cfd_tunnel/{CF_TUNNEL_ID}/configurations"
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


def run_setup(params):
    gateway_token = params["gateway_token"]
    db_password = params["db_password"]
    ai_provider = params.get("ai_provider", "")
    ai_api_key = params.get("ai_api_key", "")
    ai_model = params.get("ai_model", "")
    try:
        set_state(step=1, step_label="Creating encryption keys...")
        secret_data = {"OPENCLAW_GATEWAY_TOKEN": gateway_token, "POSTGRES_PASSWORD": db_password}
        if ai_provider and ai_api_key:
            env_name = AI_ENV_MAP.get(ai_provider, "")
            if env_name:
                secret_data[env_name] = ai_api_key
        create_secret(secret_data)

        set_state(step=2, step_label="Starting database engine...")
        scale_deployment("openclaw-db", 1)

        set_state(step=3, step_label="Launching AI gateway...")
        scale_deployment("openclaw-gateway", 1)

        set_state(step=4, step_label="Waiting for system readiness...")
        if not wait_for_gateway(timeout=180):
            set_state(done=True, success=False, running=False,
                      error="Gateway did not start within 180 seconds.")
            return

        set_state(step=5, step_label="Configuring AI & channels...")
        try:
            configure_gateway(ai_provider, ai_api_key, ai_model)
        except Exception as e:
            log.warning(f"Gateway config partially failed: {e}")

        set_state(step=6, step_label="Switching network routes...")
        try:
            switch_cloudflare_route()
        except Exception as e:
            set_state(done=True, success=False, running=False,
                      error=f"Cloudflare route switch failed: {e}")
            return

        set_state(step=7, step_label="Deployment complete!",
                  done=True, success=True, running=False,
                  message=f"https://{DOMAIN}/#token={gateway_token}")

    except Exception as e:
        log.exception("Setup pipeline failed.")
        set_state(done=True, success=False, running=False, error=f"Unexpected error: {e}")


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
        "gateway_token": gateway_token, "db_password": db_password,
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
