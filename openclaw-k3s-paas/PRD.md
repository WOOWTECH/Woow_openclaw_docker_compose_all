# OpenClaw PaaS - Product Requirements Document (PRD)

## 1. Product Overview

**Product Name**: OpenClaw PaaS Tenant Auto-Deployment & Route Hot-Switching System
**Version**: 2.0.0
**Platform**: K3s (v1.34.3+k3s1) on 4-node cluster
**Domain**: `cindytech1-openclaw.woowtech.io`
**Brand**: Woowtech Smart Space Solution

### Mission
Provide a one-click, self-service deployment system for OpenClaw AI Gateway instances, enabling non-technical users to deploy a production-grade AI gateway through a guided web wizard — with full persistence of agents, skills, channels, and config across pod restarts.

---

## 2. Architecture

```
Internet → Cloudflare Tunnel → K3s Cluster (openclaw-tenant-1)
                                    ├── cloudflared (always-on)
                                    ├── setup-wizard (replicas: 1 → 0)
                                    ├── postgresql/pgvector (replicas: 0 → 1)
                                    └── openclaw-gateway (custom image, PVC-backed)
                                         ├── agents/     → PVC (agent configs, auth keys)
                                         ├── skills/     → PVC (managed skills)
                                         ├── workspace/  → PVC (user-installed skills)
                                         └── openclaw.json → PVC (channels, model, all settings)
```

### Lifecycle Phases
| Phase | State | Active Components |
|-------|-------|-------------------|
| 1. Initial | Hibernating | cloudflared, setup-wizard |
| 2. User Config | Wizard active | User fills form via external domain |
| 3. Wake-up | Provisioning | Wizard creates secrets, scales up DB + Gateway |
| 4. Route Switch | Cutover | Wizard switches CF tunnel to Gateway |
| 5. Self-destruct | Production | Gateway + DB only, Wizard at 0 replicas |

---

## 3. v2.0 Features (2026-03-23)

### 3.1 Agent 持久化與多模型切換

**問題**: 使用者透過 web GUI 建立的 agent 在 pod 重啟後消失。

**解法**:
- PVC (`openclaw-agents-pvc`, 1Gi) 掛載在 `/mnt/openclaw-agents`
- Symlink 連接到 `/home/node/.openclaw/agents`、`workspace/skills`、`skills`
- `auth-profiles.json` 使用**合併模式**（讀取既有 → 合併 env vars → 寫回）
- 使用者透過 OpenClaw 內建的左上角下拉選單切換 agent/model

**持久化矩陣**:

| 資料 | PVC 路徑 | 用途 |
|------|---------|------|
| `openclaw.json` | `_openclaw.json` | 頻道設定、模型、所有 runtime config |
| Agent 設定 | `main/` | GPT/MiniMax/DeepSeek 等 agent profiles |
| API Keys | `main/agent/auth-profiles.json` | 各 provider 的 API keys |
| User skills | `_workspace-skills/` | 透過 GUI/聊天安裝的 skill（如 homeassistant） |
| Managed skills | `_managed-skills/` | 透過 clawhub 安裝的 skill |

### 3.2 AI Provider 擴充

Setup Wizard 和 Gateway 新增支援：

| Provider | env var | 預設模型 | auth key |
|----------|---------|---------|----------|
| OpenAI | `OPENAI_API_KEY` | `openai/gpt-4o` | `openai` |
| Anthropic | `ANTHROPIC_API_KEY` | `anthropic/claude-sonnet-4-20250514` | `anthropic` |
| Google | `GEMINI_API_KEY` | `google/gemini-2.0-flash` | `google` |
| **MiniMax** | `MINIMAX_API_KEY` | `minimax/MiniMax-M2.5` | `minimax` |
| **DeepSeek** | `DEEPSEEK_API_KEY` | `deepseek/deepseek-chat` | `deepseek` |
| **Qwen** | `QWEN_API_KEY` | `qwen/qwen-max` | `qwen` |
| Ollama | `OLLAMA_HOST` | `ollama/llama3` | — |

啟動腳本**自動偵測可用 API key** 設定預設模型（OpenAI > MiniMax > DeepSeek > Anthropic > Google > Qwen）。

### 3.3 自訂 Docker Image（Skill 依賴）

`Dockerfile.custom` 基於 `ghcr.io/openclaw/openclaw:latest`，預裝 skill 依賴：

| 類型 | 套件 | 啟用的 Skills |
|------|------|-------------|
| apt | `jq`, `ripgrep` | session-logs |
| apt | `tmux` | tmux |
| apt | `ffmpeg` | video-frames |
| apt repo | `gh` (GitHub CLI) | github, gh-issues |
| npm | `clawhub` | clawhub |
| npm | `mcporter` | mcporter |
| npm | `gog` | gog (Google Workspace) |
| npm | `goplaces` | goplaces |
| npm | `summarize` | summarize |
| curl | `uv` | nano-banana-pro |

**結果**: 15 個 skills ready（從原本 6 個）。

### 3.4 Setup Wizard 改進

- **淺色模式 CSS**: 全面從深色改為淺色主題
- **新 Provider UI**: MiniMax、DeepSeek、Qwen 下拉選項 + model 列表
- **CF 路由修復**: 修正 `CF_TUNNEL_ID` + 3 次重試邏輯
- **configure_gateway 合併模式**: auth-profiles.json 不再覆寫既有 key

### 3.5 Config 持久化

- `openclaw.json` 存在 PVC 上
- **第一次啟動**: 寫入預設 config + 自動偵測 model + 注入 LINE env
- **後續啟動**: 保留既有 config，只更新 gateway token
- LINE、Telegram、Discord、WhatsApp 頻道設定**永久保留**

---

## 4. Stability Test Report

### Test Matrix (12 Tests, All Passing)

| # | Test Case | Category | Result |
|---|-----------|----------|--------|
| 1 | Wizard homepage (GET /) | Smoke | PASS |
| 2a | Empty form submission | Input validation | PASS |
| 2b | Missing one field | Input validation | PASS |
| 3 | Duplicate submission | Race condition | PASS |
| 4 | Status poll before setup | Edge case | PASS |
| 5 | Full happy path | Integration | PASS |
| 6 | Gateway LAN binding | Network | PASS |
| 7 | Cloudflare route switch | Integration | PASS |
| 8 | External domain access | E2E | PASS |
| 9 | Wizard self-destruct | Lifecycle | PASS |
| 10 | Password auth mode | Security | PASS |
| 11 | PVC persistence | Data safety | PASS |
| 12 | Resource limits | OOM protection | PASS |

---

## 5. Security Posture

| Layer | Mechanism |
|-------|-----------|
| Transport | Cloudflare Tunnel (encrypted, no exposed ports) |
| Gateway auth | Token mode (`--auth token --token $TOKEN`) |
| K8s secrets | CF tokens in `cf-secrets`, runtime creds in `openclaw-secrets` |
| RBAC | `wizard-sa` with least-privilege |
| Network | Gateway binds to LAN only within cluster |
| Origin control | `dangerouslyAllowHostHeaderOriginFallback` (required for CF tunnel) |

---

## 6. Resource Allocation

| Component | CPU Req/Limit | Memory Req/Limit |
|-----------|--------------|------------------|
| cloudflared | 50m / 200m | 64Mi / 128Mi |
| setup-wizard | 50m / 200m | 64Mi / 256Mi |
| postgresql | 100m / 500m | 256Mi / 512Mi |
| openclaw-gateway | 500m / 4000m | 2Gi / 8Gi |

### Storage
- PostgreSQL PVC: 10Gi (ReadWriteOnce)
- Agents PVC: 1Gi (ReadWriteOnce) — agents, skills, config

---

## 7. File Structure

```
openclaw-k3s-paas/
├── PRD.md                          ← This document
├── PLAN.md                         ← Architecture plan
├── Dockerfile.custom               ← Custom image with skill dependencies
├── init-cloudflare.py              ← CF resource auto-init
├── deploy.sh                       ← One-click deployment
├── k8s-manifests/
│   ├── 00-namespace.yaml
│   ├── 01-rbac.yaml
│   ├── 02-secrets.yaml
│   ├── 03-config.yaml
│   ├── 04-cloudflared.yaml
│   ├── 05-setup-wizard.yaml
│   └── 06-openclaw-core.yaml      ← DB + Gateway + PVCs
└── setup-wizard/
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py                      ← Flask backend (7 providers)
    └── templates/index.html        ← Light mode UI
```

---

## 8. Deployment

```bash
cd openclaw-k3s-paas

# First time only
python3 init-cloudflare.py

# Build custom image and deploy
sudo buildah build -f Dockerfile.custom -t openclaw-custom:latest .
sudo buildah push openclaw-custom:latest docker-archive:/tmp/openclaw-custom.tar:openclaw-custom:latest
sudo ctr -n k8s.io images import /tmp/openclaw-custom.tar

# Apply manifests
sudo KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl apply -f k8s-manifests/
```

Visit `https://cindytech1-openclaw.woowtech.io` to begin setup.

---

## 9. Changelog

### v2.0.0 (2026-03-23)
1. **Agent persistence** — PVC for agents, skills, and config
2. **Multi-model support** — MiniMax, DeepSeek, Qwen added to setup wizard
3. **Custom Docker image** — 15 skills ready (from 6)
4. **Light mode UI** — Setup wizard CSS redesign
5. **Auto-detect model** — Startup script picks model based on available API keys
6. **Channel persistence** — openclaw.json on PVC, survives pod restarts
7. **CF route fix** — Correct tunnel ID + retry logic
8. **Auth merge mode** — auth-profiles.json and configure_gateway use merge, not overwrite

### v1.0.0 (2026-03-22)
- Initial deployment with setup wizard
- Cloudflare tunnel integration
- LINE/Telegram/WhatsApp channel support
- PostgreSQL + pgvector
- Auto device approval
