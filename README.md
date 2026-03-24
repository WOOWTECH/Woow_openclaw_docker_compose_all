# Woow OpenClaw Docker Compose All

**OpenClaw AI Gateway — Multi-Platform Deployment**
**OpenClaw AI 閘道器 — 多平台部署**

This repository contains deployment configurations for the OpenClaw AI gateway across different infrastructure platforms. Each branch provides a complete, production-ready deployment with 8 AI providers, Cloudflare Tunnel, and 52 skill CLI dependencies.

本倉庫包含 OpenClaw AI 閘道器在不同基礎設施平台上的部署配置。每個分支提供完整的生產就緒部署，支援 8 個 AI 供應商、Cloudflare Tunnel、52 個技能 CLI 依賴。

---

## Deployment Branches / 部署分支

| Branch | Platform | Use Case | 適用場景 |
|--------|----------|----------|----------|
| [`k3s`](../../tree/k3s) | Kubernetes (K3s) | Production clusters, multi-node, RBAC, auto-scaling | 生產叢集、多節點、RBAC、自動擴展 |
| [`podman`](../../tree/podman) | Docker Compose / Podman | Single server, VPS, homelab, development | 單一伺服器、VPS、家庭實驗室、開發 |

---

## Feature Matrix / 功能對照

| Feature | k3s | podman |
|---------|-----|--------|
| **AI Providers** | 8 (OpenAI, Anthropic, Google, MiniMax, DeepSeek, Qwen, OpenRouter, Ollama) | 8 (same) |
| **Auth Format** | v1 (per-provider profiles) | v1 (per-provider profiles + merge logic) |
| **Setup Wizard** | Dark/light mode, 8 providers | Dark/light mode, 8 providers |
| **Custom Dockerfile** | 12 sections, 52 skill deps | 12 sections, 52 skill deps |
| **Cloudflare Tunnel** | Integrated | Integrated (3x retry) |
| **Database** | PostgreSQL + pgvector (PVC) | PostgreSQL + pgvector (bind mount) |
| **Persistence** | K8s PVC (agents, workspace, memory, cron, telegram, config) | Bind mounts + host .env sync |
| **Chat Channels** | Telegram, WhatsApp, Discord, Slack, Signal | Telegram, WhatsApp, Discord, Slack, Signal |
| **Auto-scaling** | K8s HPA/VPA supported | Manual (single instance) |
| **RBAC** | K8s RBAC + ServiceAccount | Docker socket access |
| **Automated Tests** | 67 pre-launch tests (6 rounds) | Manual verification |
| **Self-Destruct Wizard** | Scales to 0 replicas | Process exit (restart: "no") |

---

## Quick Comparison / 快速比較

### Choose K3s if / 選擇 K3s 如果：
- You have a Kubernetes cluster (K3s, K8s, EKS, GKE, AKS)
- You need auto-scaling, RBAC, and namespace isolation
- You want automated pre-launch testing (67 tests)
- Multi-tenant deployment

### Choose Podman if / 選擇 Podman 如果：
- You have a single server or VPS
- You want simple `podman compose up -d` deployment
- You prefer Docker Compose workflow
- Development and testing environments
- Homelab / self-hosted setup

---

## Shared Features / 共同功能

Both branches include:

- **8 AI Providers**: OpenAI, Anthropic, Google Gemini, MiniMax, DeepSeek, Qwen, OpenRouter, Ollama
- **v1 Auth-Profiles Format**: `{version: 1, profiles: {provider: {type: "api_key", key: ..., provider: ...}}}`
- **Dark/Light Mode**: Setup wizard with CSS variable toggle + localStorage persistence
- **Custom Gateway Image**: 12-section Dockerfile with:
  - System packages (jq, ffmpeg, tmux, ripgrep)
  - npm CLIs (clawhub, mcporter, oracle, gemini-cli, codex)
  - Go 1.23.7 + 13 Go binaries
  - GitHub CLI, 1Password CLI, Himalaya, OpenHue, Obsidian CLI
  - uv (Python), Whisper (CPU), nano-pdf
- **Cloudflare Tunnel**: Secure HTTPS access via Cloudflare edge
- **Bilingual UI/Docs**: English and Traditional Chinese (繁體中文)

---

## AI Provider Details / AI 供應商詳情

| Provider | Default Model | Key Format | Models |
|----------|---------------|------------|--------|
| **OpenAI** | `openai/gpt-4o` | `sk-proj-...` | GPT-4o, o1, GPT-4 Turbo |
| **Anthropic** | `anthropic/claude-sonnet-4-20250514` | `sk-ant-api03-...` | Claude Sonnet, Opus, Haiku |
| **Google** | `google/gemini-2.0-flash` | `AIzaSy...` | Gemini 2.0 Flash, 2.5 Pro |
| **MiniMax** | `minimax/MiniMax-M2.5` | `eyJhbG...` | MiniMax M2.5, Text-01 |
| **DeepSeek** | `deepseek/deepseek-chat` | `sk-...` | DeepSeek Chat, Coder, Reasoner |
| **Qwen** | `qwen/qwen-max` | `sk-...` | Qwen Max, Plus, Turbo |
| **OpenRouter** | `openrouter/auto` | `sk-or-...` | 100+ models via single key |
| **Ollama** | `ollama/llama3` | Host URL | Llama 3, Mistral, CodeLlama, etc. |

---

## Getting Started / 開始使用

```bash
# K3s deployment / K3s 部署
git clone -b k3s https://github.com/WOOWTECH/Woow_openclaw_docker_compose_all.git
cd Woow_openclaw_docker_compose_all
cp .env.example .env  # Fill in credentials
./deploy.sh

# Podman deployment / Podman 部署
git clone -b podman https://github.com/WOOWTECH/Woow_openclaw_docker_compose_all.git
cd Woow_openclaw_docker_compose_all
cp .env.example .env  # Fill in credentials
podman compose build gateway
podman compose up -d
```

---

## Repository Structure / 倉庫結構

```
main          ← This branch: overview + branch navigation
├── k3s       ← Kubernetes/K3s deployment (deploy.sh, k8s-manifests/, tests/)
└── podman    ← Docker Compose/Podman deployment (docker-compose.yml, gateway/)
```

---

## K3s v2.1 Highlights / K3s v2.1 亮點

- **Full Persistence**: All config (channels, agents, skills, memory, cron) survives pod restarts via PVC symlinks
- **Pinned Base Image**: `ghcr.io/openclaw/openclaw@sha256:a5a4c83b` (v2026.3.13) — stable LINE channel support
- **Isolated npm**: Skill CLIs installed to `/opt/openclaw-tools/` to prevent LINE plugin conflicts
- **Auto-Approve Fix**: JSON-based device pairing approval (fixes multiline UUID grep failure)
- **Config Symlink**: `openclaw.json` symlinked to PVC — all web GUI changes persist immediately

---

## License / 授權

MIT License — Copyright (c) 2026 Woowtech Smart Space Solution
