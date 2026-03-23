# Woow OpenClaw Docker Compose All

**OpenClaw AI Gateway — Multi-Platform Deployment**
**OpenClaw AI 閘道器 — 多平台部署**

## Deployment Options / 部署方式

| Branch | Method | Status |
|--------|--------|--------|
| [`k3s`](../../tree/k3s) | **K3s / Kubernetes** | ✅ Production Ready (v2.1) |
| `main` | Docker Compose | 🚧 Coming Soon |
| `podman` | Podman Compose | 🚧 Coming Soon |

## K3s Deployment (v2.1) / K3s 部署

👉 **[Switch to k3s branch for complete deployment guide](../../tree/k3s)**

### Features / 功能

**Multi-Model AI Gateway / 多模型 AI 閘道**
- 7 AI providers: OpenAI, Anthropic, Google, MiniMax, DeepSeek, Qwen, Ollama
- Switch models via web GUI dropdown (left-top agent selector)
- Auto-detect default model from available API keys

**Full Persistence / 完整持久化**
- All settings survive pod restarts (PVC-backed)
- Channels (LINE, Telegram, WhatsApp, Discord), agent configs, API keys
- Conversation memory (SQLite), workspace files, uploaded documents
- User-installed skills, cron jobs, Telegram bot state

**15 Built-in Skills Ready / 15 個內建技能可用**
- Custom Docker image with pre-installed dependencies
- GitHub CLI, ffmpeg, tmux, jq, ripgrep, clawhub, and more
- Install additional skills via web GUI or chat

**Zero-Touch Setup Wizard / 零接觸設定精靈**
- Light mode web UI with provider selection
- Cloudflare Tunnel integration (auto route switching)
- Self-destruct after deployment

**Chat Platform Integration / 聊天平台整合**
- LINE, Telegram, WhatsApp, Discord, Slack
- Configure channels via web dashboard

### Architecture / 架構

```
Internet --> Cloudflare Tunnel --> K3s Cluster
                                    |-- cloudflared
                                    |-- setup-wizard (scales to 0 after setup)
                                    |-- postgresql/pgvector (10Gi PVC)
                                    +-- openclaw-gateway (custom image)
                                         |-- agents/     --> PVC
                                         |-- workspace/  --> PVC (skills, files, .md)
                                         |-- memory/     --> PVC (conversation history)
                                         |-- cron/       --> PVC (scheduled tasks)
                                         |-- telegram/   --> PVC (bot state)
                                         +-- openclaw.json --> PVC (all config)
```

### Quick Start / 快速開始

```bash
git checkout k3s
cd openclaw-k3s-paas

# First time: init Cloudflare resources
CF_API_TOKEN=your_token python3 init-cloudflare.py

# Build custom image & deploy
sudo buildah build -f Dockerfile.custom -t openclaw-custom:latest .
sudo buildah push openclaw-custom:latest docker-archive:/tmp/oc.tar:openclaw-custom:latest
sudo ctr -n k8s.io images import /tmp/oc.tar
sudo KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl apply -f k8s-manifests/
```

Visit `https://your-domain.example.com` to begin setup.

---

© 2026 Woowtech Smart Space Solution
