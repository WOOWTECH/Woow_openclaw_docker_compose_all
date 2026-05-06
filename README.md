# Woow OpenClaw — AI Agent Platform Deployment

**OpenClaw AI Gateway — Multi-Environment Deployment**
**OpenClaw AI 閘道器 — 多環境部署方案**

Deploy OpenClaw AI platform with Nerve WebGUI, Paperclip AI orchestration, Ollama local inference, 3 plugins, 62+ tools, and multi-channel support (Telegram, WhatsApp, LINE, Web).

部署 OpenClaw AI 平台，包含 Nerve WebGUI、Paperclip AI 編排、Ollama 本地推論、3 個插件、62+ 個工具、多頻道支援。

---

## Deployment Options / 部署方式

| Branch | Environment | Description |
|--------|-------------|-------------|
| **`k3s`** | K3s Cluster | Production multi-node deployment with Kubernetes manifests, Cloudflare Tunnel, PVC persistence |
| **`main`** | Reference | Architecture docs, shared manifests, deployment guides |

> **For installation, switch to the [`k3s`](../../tree/k3s) branch.**

---

## Architecture / 架構

```
Internet (HTTPS)
    |
    v
+------------------------------------------------+
|  Cloudflare Edge (DDoS + TLS)                  |
+------------------------------------------------+
    |  QUIC Tunnel
    v
+================================================+
| K3s Cluster — Namespace: openclaw-tenant-1     |
|                                                |
|  +----------------+   +--------------------+   |
|  | cloudflared    |-->| openclaw-gateway   |   |
|  | (tunnel)       |   | :18789             |   |
|  +-----+----------+   | +-- AI Agent       |   |
|        |               | +-- Telegram       |   |
|        |               | +-- WhatsApp       |   |
|        |               | +-- LINE           |   |
|        |               | +-- 62+ Tools      |   |
|        |               +--------+-----------+   |
|        |                        |               |
|        |  +----------------+   +--------+       |
|        +->| Nerve WebGUI   |<--| sidecar|       |
|        |  | :3080          |   +--------+       |
|        |  +----------------+       |            |
|        |                     +-----------+      |
|        |                     | PostgreSQL |      |
|        |                     | :5432+pgv  |      |
|        |                     +-----------+      |
|        |                                        |
|        |  +--------------------+                |
|        +->| Paperclip AI       |                |
|        |  | :3100              |                |
|        |  | Agent Orchestration|                |
|        |  +--------------------+                |
|        |                                        |
|        |  +--------------------+                |
|        +->| OpenClaw Console   |                |
|        |  | :18790 + :7681     |                |
|        |  | Dashboard + Setup  |                |
|        |  +--------------------+                |
|        |                                        |
|        |  +--------------------+                |
|        +->| Ollama             |                |
|           | :11434             |                |
|           | nomic-embed-text   |                |
|           | llama3:8b          |                |
|           +--------------------+                |
+================================================+
```

---

## Services / 服務

| Service | Port | Description |
|---------|------|-------------|
| **OpenClaw Gateway** | 18789 | AI agent engine, WebSocket API, multi-channel |
| **Nerve WebGUI** | 3080 | Chat UI, memory, cron/tasks, workspace management |
| **Paperclip AI** | 3100 | Enterprise agent orchestration, issue tracking, org chart |
| **OpenClaw Console** | 18790 | Management dashboard, setup wizard, config editor |
| **Terminal (ttyd)** | 7681 | Browser-based kubectl shell |
| **PostgreSQL (pgvector)** | 5432 | Vector database for memory + embeddings |
| **Ollama** | 11434 | Local LLM inference (embedding + extraction) |

---

## Plugins / 插件

| Plugin | Function |
|--------|----------|
| **memory-lancedb-pro** | Vector memory with Ollama embedding + smart extraction |
| **openclaw-homeassistant** | 34 native Home Assistant tools |
| **lossless-claw-enhanced** | DAG-based lossless context management |

---

## K3s Quick Start / K3s 快速開始

```bash
# 1. Clone and switch to k3s branch
git clone https://github.com/WOOWTECH/Woow_openclaw_docker_compose_all.git
cd Woow_openclaw_docker_compose_all
git checkout k3s

# 2. Configure secrets
vi k8s-manifests/02-secrets.yaml

# 3. Configure domain
vi k8s-manifests/03-config.yaml

# 4. Deploy
kubectl apply -f k8s-manifests/

# 5. Verify
kubectl get pods -n openclaw-tenant-1
```

See [`k8s-manifests/`](k8s-manifests/) for full manifest reference.
See [`docs/PAPERCLIP-DEPLOYMENT-GUIDE.md`](docs/PAPERCLIP-DEPLOYMENT-GUIDE.md) for Paperclip integration.

---

## K3s Manifests / K3s 清單

| Manifest | Component |
|----------|-----------|
| `00-namespace.yaml` | Namespace `openclaw-tenant-1` |
| `01-rbac.yaml` | RBAC policies |
| `02-secrets.yaml` | API keys, tokens, credentials |
| `03-config.yaml` | Cloudflare config, Nerve public URL |
| `04-cloudflared.yaml` | Cloudflare Tunnel connector |
| `06-openclaw-core.yaml` | Gateway + Nerve + PostgreSQL |
| `07-ollama.yaml` | Ollama local inference |
| `08-ollama-model-init.yaml` | Model download job |
| `10-openclaw-console.yaml` | Console management UI |
| `11-console-configmaps.yaml` | Console HTML + scripts |
| `12-network-policy.yaml` | Network isolation |
| `15-paperclip.yaml` | Paperclip AI + PostgreSQL 17 |

---

## License / 授權

MIT License — Copyright (c) 2026 Woowtech Smart Space Solution
