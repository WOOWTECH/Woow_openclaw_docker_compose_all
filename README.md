# Woow OpenClaw K3s PaaS

**OpenClaw AI Gateway — Zero-Touch K3s Deployment**
**OpenClaw AI 閘道器 — 零接觸 K3s 部署**

Deploy a production-ready OpenClaw AI gateway on K3s with Cloudflare Tunnel, LINE/Telegram/WhatsApp integration, multi-LLM support, and automated testing.

在 K3s 上部署生產就緒的 OpenClaw AI 閘道器，支援 Cloudflare Tunnel、LINE/Telegram/WhatsApp 整合、多 LLM 切換、自動化測試。

---

## Table of Contents / 目錄

- [Overview / 概述](#overview--概述)
- [Architecture / 架構](#architecture--架構)
- [Services / 服務說明](#services--服務說明)
- [Prerequisites / 前置需求](#prerequisites--前置需求)
- [Quick Start / 快速開始](#quick-start--快速開始)
- [Configuration / 配置說明](#configuration--配置說明)
- [LINE Integration / LINE 整合](#line-integration--line-整合)
- [LLM Switching / LLM 切換](#llm-switching--llm-切換)
- [Common Commands / 常用指令](#common-commands--常用指令)
- [File Structure / 檔案結構](#file-structure--檔案結構)
- [Testing / 測試](#testing--測試)
- [Troubleshooting / 故障排除](#troubleshooting--故障排除)
- [License / 授權](#license--授權)

---

## Overview / 概述

**English:**
OpenClaw is an AI gateway that connects large language models (GPT-4o, Claude, Gemini, Llama) to messaging platforms (LINE, Telegram, WhatsApp). This repository provides a complete K3s deployment with:

- **Setup Wizard**: Web-based zero-touch provisioning
- **Cloudflare Tunnel**: Secure external access without exposed ports
- **Multi-LLM**: Switch between OpenAI, Anthropic, Google, and OpenRouter models
- **Chat Channels**: LINE, Telegram, WhatsApp, Discord, Slack
- **Cron Jobs**: Scheduled AI tasks with channel delivery
- **67-Test Suite**: Automated pre-launch validation

**中文：**
OpenClaw 是一個 AI 閘道器，連接大型語言模型（GPT-4o、Claude、Gemini、Llama）到訊息平台（LINE、Telegram、WhatsApp）。本倉庫提供完整的 K3s 部署方案：

- **Setup Wizard**：基於 Web 的零接觸配置
- **Cloudflare Tunnel**：安全外部存取，不需開放端口
- **多 LLM**：在 OpenAI、Anthropic、Google、OpenRouter 模型間切換
- **聊天頻道**：LINE、Telegram、WhatsApp、Discord、Slack
- **Cron Jobs**：排程 AI 任務，支援頻道推送
- **67 項測試**：自動化上線前驗證

---

## Architecture / 架構

```
Internet (HTTPS)
    │
    ▼
┌──────────────────────────────────────────────────┐
│  Cloudflare Edge (DDoS protection, SSL)          │
└──────────────────┬───────────────────────────────┘
                   │ QUIC Tunnel
                   ▼
┌──────────────────────────────────────────────────┐
│  K3s Cluster — Namespace: openclaw-tenant-1      │
│                                                  │
│  ┌─────────────┐   ┌──────────────────────────┐  │
│  │ cloudflared │──▶│ openclaw-gateway :18789   │  │
│  │   (tunnel)  │   │  ├─ AI Agents (GPT-4o)   │  │
│  └─────────────┘   │  ├─ LINE Channel         │  │
│                     │  ├─ Telegram Channel     │  │
│  ┌─────────────┐   │  ├─ Cron Scheduler       │  │
│  │ setup-wizard│   │  └─ Control UI (WebSocket)│  │
│  │   :18790    │   └──────────┬───────────────┘  │
│  └─────────────┘              │                  │
│                     ┌─────────▼──────────┐       │
│                     │ PostgreSQL (pgvector)│      │
│                     │   :5432 + 10Gi PVC  │      │
│                     └────────────────────┘       │
└──────────────────────────────────────────────────┘
```

---

## Services / 服務說明

| Service | Image | Port | Description | 說明 |
|---------|-------|------|-------------|------|
| **cloudflared** | `cloudflare/cloudflared:latest` | — | Cloudflare Tunnel connector | Cloudflare 隧道連接器 |
| **setup-wizard** | `openclaw-setup-wizard:latest` | 18790 | Web provisioning UI | Web 配置介面 |
| **openclaw-gateway** | `ghcr.io/openclaw/openclaw:latest` | 18789 | AI gateway + Control UI | AI 閘道器 + 管理介面 |
| **openclaw-db** | `pgvector/pgvector:pg16` | 5432 | PostgreSQL with vector extension | PostgreSQL 向量資料庫 |

**Resource Requirements / 資源需求:**

| Service | CPU (req/limit) | Memory (req/limit) |
|---------|-----------------|---------------------|
| cloudflared | 50m / 200m | 64Mi / 128Mi |
| setup-wizard | 50m / 200m | 64Mi / 256Mi |
| openclaw-gateway | 500m / 4000m | 2Gi / 8Gi |
| openclaw-db | 100m / 500m | 256Mi / 512Mi |

---

## Prerequisites / 前置需求

**English:**
- K3s cluster (single node or multi-node)
- `kubectl` configured to access the cluster
- Docker (for building setup-wizard image)
- Python 3.9+ (for `init-cloudflare.py`)
- Cloudflare account with a domain
- AI provider API key (OpenAI, Anthropic, Google, or OpenRouter)

**中文：**
- K3s 叢集（單節點或多節點）
- `kubectl` 已配置可存取叢集
- Docker（用於建構 setup-wizard 映像）
- Python 3.9+（用於 `init-cloudflare.py`）
- Cloudflare 帳號及網域
- AI 供應商 API 金鑰（OpenAI、Anthropic、Google 或 OpenRouter）

---

## Quick Start / 快速開始

### Step 1: Initialize Cloudflare Tunnel / 初始化 Cloudflare Tunnel

```bash
export CF_API_TOKEN="your-cloudflare-api-token"
export OPENCLAW_DOMAIN="your-domain.example.com"
python3 init-cloudflare.py
```

This creates `cf-config.json` with tunnel credentials.
這會建立包含隧道認證的 `cf-config.json`。

### Step 2: Deploy / 部署

```bash
./deploy.sh
```

This will: Build setup-wizard image → Import to K3s → Create namespace/RBAC/secrets → Configure tunnel → Apply manifests.

### Step 3: Setup via Web UI / 透過 Web 介面設定

Visit `https://your-domain.example.com` and fill in:
- **Gateway Token**: Access password for Control UI
- **Database Password**: PostgreSQL password
- **AI Provider**: Select OpenAI/Anthropic/Google and enter API key

### Step 4: Configure Channels / 設定頻道

After setup, visit `https://your-domain.example.com/#token=your-gateway-token`

Go to **Channels** to configure LINE, Telegram, etc.
See [LINE Setup Guide](docs/line-setup.md) for detailed instructions.

### Step 5: Verify / 驗證

```bash
bash tests/pre-launch/run-all.sh
```

---

## Configuration / 配置說明

Copy `.env.example` to `.env` and fill in values:

| Variable | Required | Description | 說明 |
|----------|----------|-------------|------|
| `CF_API_TOKEN` | Yes | Cloudflare API token | Cloudflare API 金鑰 |
| `DOMAIN` | Yes | Your domain name | 你的網域名稱 |
| `GATEWAY_TOKEN` | Yes | Gateway access password | Gateway 存取密碼 |
| `DB_PASSWORD` | Yes | PostgreSQL password | 資料庫密碼 |
| `OPENAI_API_KEY` | Yes* | OpenAI API key | OpenAI API 金鑰 |
| `OPENROUTER_API_KEY` | Alt | OpenRouter key (multi-LLM) | OpenRouter 金鑰（多 LLM） |
| `LINE_CHANNEL_TOKEN` | Opt | LINE channel access token | LINE 頻道存取 token |
| `LINE_CHANNEL_SECRET` | Opt | LINE channel secret | LINE 頻道密鑰 |
| `TELEGRAM_BOT_TOKEN` | Opt | Telegram bot token | Telegram 機器人 token |

*At least one AI provider key required / 至少需要一個 AI 供應商金鑰

---

## LINE Integration / LINE 整合

See [docs/line-setup.md](docs/line-setup.md) for the complete guide.

**Critical / 關鍵：** LINE Official Account Manager → **關閉「聊天」** (chatMode must be "bot")

```bash
# Verify
curl -s https://api.line.me/v2/bot/info -H "Authorization: Bearer $TOKEN"
# Must show: "chatMode":"bot"
```

---

## LLM Switching / LLM 切換

Switch between models via CLI or GUI. Use OpenRouter for 100+ models.
透過 CLI 或 GUI 切換模型。使用 OpenRouter 存取 100+ 模型。

```bash
# Switch to Gemini via OpenRouter
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- \
  openclaw config set agents.defaults.model "openrouter/google/gemini-2.0-flash-001"

# Switch to Claude
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- \
  openclaw config set agents.defaults.model "openrouter/anthropic/claude-3.5-haiku"

# Switch back to GPT-4o
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- \
  openclaw config set agents.defaults.model "openai/gpt-4o"
```

**Tested Models / 已測試模型:** GPT-4o, Gemini 2.0 Flash, Claude 3.5 Haiku, Llama 3.1 8B

---

## Common Commands / 常用指令

```bash
# Pod status / Pod 狀態
kubectl -n openclaw-tenant-1 get pods

# Gateway logs / Gateway 日誌
kubectl -n openclaw-tenant-1 logs deployment/openclaw-gateway --tail=50

# Channel status / 頻道狀態
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- openclaw channels status

# Cron jobs / 排程任務
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- openclaw cron list

# Health check / 健康檢查
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- openclaw doctor

# Restart gateway / 重啟 gateway
kubectl -n openclaw-tenant-1 rollout restart deployment openclaw-gateway

# Full reset / 完全重置
./reset.sh
```

---

## File Structure / 檔案結構

```
.
├── .env.example              # Environment template / 環境變數模板
├── deploy.sh                 # One-click deployment / 一鍵部署
├── init-cloudflare.py        # Cloudflare tunnel init / CF 隧道初始化
├── reset.sh                  # Full reset / 完全重置
├── k8s-manifests/            # Kubernetes manifests (7 files)
├── setup-wizard/             # Flask provisioning UI
├── tests/pre-launch/         # 67 automated tests (6 rounds)
├── utils/                    # Utility scripts
└── docs/                     # LINE setup + troubleshooting
```

---

## Testing / 測試

**67 automated tests, 6 rounds / 67 個自動化測試，6 輪：**

| Round | Tests | Coverage | 涵蓋範圍 |
|-------|-------|----------|----------|
| 1 | 12 | Infrastructure health | 基礎設施健康 |
| 2 | 15 | Security & stress | 安全暴力測試 |
| 3 | 10 | LLM switching | LLM 多模型切換 |
| 4 | 12 | LINE bidirectional | LINE 雙向通訊 |
| 5 | 10 | Cron, skills, hot-reload | 排程、技能 |
| 6 | 8 | Resilience & recovery | 穩定性恢復 |

```bash
bash tests/pre-launch/run-all.sh
# HTML report: tests/pre-launch/report-YYYY-MM-DD.html
```

**Latest: 59/68 pass (95.2%), Round 3 LLM 10/10, Round 6 resilience 8/8**

---

## Troubleshooting / 故障排除

See [docs/troubleshooting.md](docs/troubleshooting.md).

| Issue | Fix |
|-------|-----|
| 502 Bad Gateway | Clean tunnel connections + restart cloudflared |
| LINE not responding | chatMode must be "bot" in LINE OA Manager |
| DB pod Pending | Delete PVC and re-apply manifest |
| Control UI won't load | Re-visit `https://domain/#token=your-token` |

---

## License / 授權

MIT License — Copyright (c) 2026 Woowtech Smart Space Solution
