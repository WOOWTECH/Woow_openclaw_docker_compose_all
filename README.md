# Woow OpenClaw K3s Deployment

**OpenClaw AI Gateway — Enterprise K3s Deployment**
**OpenClaw AI 閘道器 — 企業級 K3s 部署**

Complete, reproducible deployment of OpenClaw AI platform on K3s with Nerve WebGUI, Ollama local inference, 3 plugins, 62 tools, and multi-channel support (Telegram, WhatsApp, LINE, Web).

在 K3s 上完整可重現部署 OpenClaw AI 平台，包含 Nerve WebGUI、Ollama 本地推論、3 個插件、62 個工具、多頻道支援。

---

## Architecture / 架構

```
Internet (HTTPS)
    |
    v
+---------------------------------------------+
|  Cloudflare Edge (DDoS + TLS)               |
+---------------------------------------------+
    |  QUIC Tunnel
    v
+=============================================+
| K3s Cluster — Namespace: openclaw-tenant-1  |
|                                             |
|  +----------------+   +------------------+ |
|  | cloudflared    |-->| openclaw-gateway | |
|  | (tunnel)       |   | :18789           | |
|  +----------------+   |                  | |
|                        | +-- AI Agent    | |
|  +----------------+   | +-- Telegram    | |
|  | setup-wizard   |   | +-- WhatsApp    | |
|  | :18790         |   | +-- LINE        | |
|  +----------------+   | +-- 62 Tools    | |
|                        | +-- Exec(full) | |
|                        +--------+--------+ |
|                                 |           |
|  +----------------+   +--------+--------+  |
|  | Nerve WebGUI   |<--| (same pod)      |  |
|  | :3080          |   | sidecar         |  |
|  | - Chat UI      |   +--------+--------+  |
|  | - Agent Mgmt   |            |            |
|  | - Memory View  |            |            |
|  | - Cron/Tasks   |            v            |
|  +----------------+   +-----------------+   |
|                        | PostgreSQL      |   |
|                        | :5432 + pgvec   |   |
|                        | (10Gi PVC)      |   |
|                        +-----------------+   |
|                                              |
|  +------------------------------------------+
|  | Ollama (Local Inference)                  |
|  | :11434                                    |
|  | +-- nomic-embed-text (274MB, embedding)   |
|  | +-- llama3:8b (4.7GB, smart extraction)   |
|  | (15Gi PVC)                                |
|  +------------------------------------------+
|                                              |
|  +------------------------------------------+
|  | Plugins (PVC-persisted)                   |
|  | +-- memory-lancedb-pro    (vector memory) |
|  | +-- openclaw-homeassistant (34 HA tools)  |
|  | +-- lossless-claw-enhanced (DAG context)  |
|  +------------------------------------------+
|                                              |
|  +------------------------------------------+
|  | PVC: openclaw-agents-pvc (5Gi)            |
|  | +-- _openclaw.json    (runtime config)    |
|  | +-- _workspace/       (SOUL, .env, etc)   |
|  | +-- _extensions/      (plugin backup)     |
|  | +-- _memory/          (LanceDB vectors)   |
|  | +-- _cron/            (scheduled jobs)    |
|  | +-- _telegram/        (session state)     |
|  | +-- _nerve_app/       (built Nerve app)   |
|  +------------------------------------------+
+=============================================+
```

---

## Components / 元件清單

| Manifest | Component | Description |
|----------|-----------|-------------|
| `00-namespace.yaml` | Namespace | `openclaw-tenant-1` |
| `01-rbac.yaml` | RBAC | ServiceAccount + role bindings |
| `02-secrets.yaml` | Secrets | LLM API keys, channel tokens, HASS/Odoo/GOG credentials |
| `03-config.yaml` | ConfigMap | Cloudflare config + `NERVE_PUBLIC_URL` |
| `04-cloudflared.yaml` | Cloudflare Tunnel | QUIC tunnel to Cloudflare edge |
| `05-setup-wizard.yaml` | Setup Wizard | Web UI for initial configuration |
| `06-openclaw-core.yaml` | **Gateway + Nerve** | AI gateway (2 containers: gateway + nerve sidecar), PVC, full init script |
| `07-ollama.yaml` | **Ollama** | Local LLM inference (PVC 15Gi + Deployment + Service) |
| `08-ollama-model-init.yaml` | **Model Init Job** | Pulls `nomic-embed-text` + `llama3:8b` on first deploy |
| `09-nerve-svc.yaml` | **Nerve Service** | ClusterIP service for Nerve WebGUI (:3080) |

---

## Plugins / 插件

| Plugin | Source | Function |
|--------|--------|----------|
| **memory-lancedb-pro** | `openclaw plugins install` | Vector memory with Ollama embedding (nomic-embed-text) + smart extraction (llama3:8b) |
| **openclaw-homeassistant** | `@elvatis_com/openclaw-homeassistant` | 34 native Home Assistant tools (lights, sensors, switches, climate, media, automation) |
| **lossless-claw-enhanced** | `github.com/win4r/lossless-claw-enhanced` | DAG-based lossless context management with CJK token fix |

All plugins are:
- Auto-installed on first boot (from npm/GitHub)
- Backed up to PVC `_extensions/`
- Auto-restored on pod restart
- Config auto-injected into `openclaw.json`

---

## Tools (62) / 工具

| Category | Tools |
|----------|-------|
| **Core** | exec, read, write, edit, web_fetch, web_search |
| **Sessions** | sessions_list, sessions_history, sessions_spawn, sessions_send, sessions_yield, session_status |
| **Memory** | memory_recall, memory_store, memory_forget, memory_update |
| **Media** | browser, canvas, image, pdf, tts |
| **System** | cron, agents_list, gateway, message, process, nodes, subagents |
| **Home Assistant** (34) | ha_status, ha_light_on/off/toggle/list, ha_switch_on/off/toggle, ha_climate_set_temp/mode/preset/list, ha_media_play/pause/stop/volume/play_media, ha_cover_open/close/position, ha_scene_activate, ha_script_run, ha_automation_trigger, ha_sensor_list, ha_history, ha_logbook, ha_call_service, ha_fire_event, ha_render_template, ha_notify, ha_list_entities, ha_get_state, ha_search_entities, ha_list_services |

---

## Channels / 頻道

| Channel | Status | Policy |
|---------|--------|--------|
| **Telegram** | Active | dmPolicy: open, groupPolicy: open, streaming: partial |
| **WhatsApp** | Active | dmPolicy: pairing, groupPolicy: allowlist |
| **LINE** | Error | runtime-line.contract module issue |
| **Web (Nerve)** | Active | Full WebGUI with chat, memory, cron, agents |

---

## Quick Start / 快速開始

```bash
# 1. Clone
git clone https://github.com/WOOWTECH/Woow_openclaw_docker_compose_all.git
cd Woow_openclaw_docker_compose_all

# 2. Configure secrets (edit with real credentials)
vi k8s-manifests/02-secrets.yaml
#    MINIMAX_API_KEY, TELEGRAM_BOT_TOKEN, HASS_SERVER, HASS_TOKEN, etc.

# 3. Configure domain
vi k8s-manifests/03-config.yaml
#    NERVE_PUBLIC_URL: "https://your-nerve-domain.example.com"

# 4. Update node selector for Ollama (match your node hostname)
vi k8s-manifests/07-ollama.yaml
vi k8s-manifests/08-ollama-model-init.yaml

# 5. Deploy
kubectl apply -f k8s-manifests/

# 6. Wait for model init job to complete (~5min)
kubectl logs -n openclaw-tenant-1 job/ollama-model-init -f

# 7. Verify
kubectl get pods -n openclaw-tenant-1
# Expected: openclaw-gateway 2/2, ollama 1/1, openclaw-db 1/1, cloudflared 1/1
```

---

## First Boot Automation / 首次啟動自動化

On first boot with empty PVC, the init script automatically:

1. Creates `openclaw.json` with default model (auto-detected from API keys), 62 tools, browser config
2. Creates `exec-approvals.json` with `security: full`, `ask: off`
3. Injects `tools.exec.security=full` for unrestricted exec
4. Injects channel credentials (Telegram botToken, LINE tokens) from K8s secrets
5. Sets gateway `allowedOrigins` from `NERVE_PUBLIC_URL`
6. Writes auth-profiles.json for all configured LLM providers
7. Bootstraps 8 workspace files (SOUL.md, IDENTITY.md, MEMORY.md, etc.)
8. Installs 3 plugins (memory-lancedb-pro, openclaw-homeassistant, lossless-claw-enhanced)
9. Injects plugin configs into `openclaw.json` (Ollama endpoints, HA credentials, LCM settings)
10. Installs workspace skills (homeassistant, odoo-manager, agent-browser)

---

## Enterprise Test Results / 企業級測試結果

29/29 tests passed (100% effective) across 5 rounds:

| Round | Scope | Result |
|-------|-------|--------|
| Round 1 | Individual modules (exec, HA, memory) | 6/6 |
| Round 2 | Cross-module interactions | 4/4 |
| Round 3 | Edge cases & error handling | 3/3 |
| Round 4 | End-to-end real-world scenarios | 3/3 |
| Round 5 | Odoo, Google, Cron, Sessions, Browser, Telegram, TTS | 13/13 |

See `TEST-REPORT-enterprise.md` and `REPORT-minimax-m27-intelligence.md` for details.

---

## License / 授權

MIT License — Copyright (c) 2026 Woowtech Smart Space Solution
