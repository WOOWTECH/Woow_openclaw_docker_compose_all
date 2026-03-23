# Woow OpenClaw K3s PaaS

**OpenClaw AI Gateway — Zero-Touch K3s Deployment**
**OpenClaw AI 閘道器 — 零接觸 K3s 部署**

Deploy a production-ready OpenClaw AI gateway on K3s with Cloudflare Tunnel, 8 AI providers, dark/light UI, Telegram/WhatsApp integration, and automated testing.

在 K3s 上部署生產就緒的 OpenClaw AI 閘道器，支援 Cloudflare Tunnel、8 個 AI 供應商、深色/淺色 UI、Telegram/WhatsApp 整合、自動化測試。

---

## Table of Contents / 目錄

- [Overview / 概述](#overview--概述)
- [Architecture / 架構](#architecture--架構)
- [Services / 服務說明](#services--服務說明)
- [Prerequisites / 前置需求](#prerequisites--前置需求)
- [Quick Start / 快速開始](#quick-start--快速開始)
- [Configuration / 配置說明](#configuration--配置說明)
- [AI Providers / AI 供應商](#ai-providers--ai-供應商)
- [Custom Gateway Image / 自訂 Gateway 映像](#custom-gateway-image--自訂-gateway-映像)
- [LLM Switching / LLM 切換](#llm-switching--llm-切換)
- [Common Commands / 常用指令](#common-commands--常用指令)
- [File Structure / 檔案結構](#file-structure--檔案結構)
- [Testing / 測試](#testing--測試)
- [Troubleshooting / 故障排除](#troubleshooting--故障排除)
- [License / 授權](#license--授權)

---

## Overview / 概述

**English:**
OpenClaw is an AI gateway that connects large language models to messaging platforms (Telegram, WhatsApp, Discord, Slack). This branch provides a complete K3s deployment with:

- **Setup Wizard**: Web-based zero-touch provisioning with dark/light mode
- **Cloudflare Tunnel**: Secure external access without exposed ports
- **8 AI Providers**: OpenAI, Anthropic, Google, MiniMax, DeepSeek, Qwen, OpenRouter, Ollama
- **v1 Auth-Profiles**: Modern auth format with per-provider key management
- **Chat Channels**: Telegram, WhatsApp, Discord, Slack, Signal
- **Custom Dockerfile**: 12-section build with 52 skill CLI dependencies
- **Cron Jobs**: Scheduled AI tasks with channel delivery
- **67-Test Suite**: Automated pre-launch validation

**中文：**
OpenClaw 是一個 AI 閘道器，連接大型語言模型到訊息平台（Telegram、WhatsApp、Discord、Slack）。本分支提供完整的 K3s 部署方案：

- **Setup Wizard**：基於 Web 的零接觸配置，支援深色/淺色模式
- **Cloudflare Tunnel**：安全外部存取，不需開放端口
- **8 個 AI 供應商**：OpenAI、Anthropic、Google、MiniMax、DeepSeek、Qwen、OpenRouter、Ollama
- **v1 Auth-Profiles**：現代認證格式，支援各供應商獨立金鑰管理
- **聊天頻道**：Telegram、WhatsApp、Discord、Slack、Signal
- **自訂 Dockerfile**：12 段式建構，52 個技能 CLI 依賴
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
│  │   (tunnel)  │   │  ├─ AI Agents (8 LLMs)   │  │
│  └─────────────┘   │  ├─ Telegram Channel     │  │
│                     │  ├─ WhatsApp Channel     │  │
│  ┌─────────────┐   │  ├─ Cron Scheduler       │  │
│  │ setup-wizard│   │  ├─ 52 Skills (CLI deps)  │  │
│  │   :18790    │   │  └─ Control UI (WebSocket)│  │
│  └─────────────┘   └──────────┬───────────────┘  │
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
| **setup-wizard** | `openclaw-setup-wizard:latest` | 18790 | Web provisioning UI (dark/light) | Web 配置介面（深色/淺色）|
| **openclaw-gateway** | Custom (12-section Dockerfile) | 18789 | AI gateway + Control UI | AI 閘道器 + 管理介面 |
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
- Docker (for building custom images)
- Python 3.9+ (for `init-cloudflare.py`)
- Cloudflare account with a domain
- At least one AI provider API key (OpenAI, Anthropic, Google, MiniMax, DeepSeek, Qwen, or OpenRouter)

**中文：**
- K3s 叢集（單節點或多節點）
- `kubectl` 已配置可存取叢集
- Docker（用於建構自訂映像）
- Python 3.9+（用於 `init-cloudflare.py`）
- Cloudflare 帳號及網域
- 至少一個 AI 供應商 API 金鑰（OpenAI、Anthropic、Google、MiniMax、DeepSeek、Qwen 或 OpenRouter）

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

This will: Build custom image → Import to K3s → Create namespace/RBAC/secrets → Configure tunnel → Apply manifests.

### Step 3: Setup via Web UI / 透過 Web 介面設定

Visit `https://your-domain.example.com` and fill in:
- **Gateway Token**: Access password for Control UI
- **Database Password**: PostgreSQL password
- **AI Provider**: Select from 8 providers and enter API key

### Step 4: Configure Channels / 設定頻道

After setup, visit `https://your-domain.example.com/#token=your-gateway-token`

Go to **Channels** to configure Telegram, WhatsApp, etc.

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
| `OPENAI_API_KEY` | Opt | OpenAI API key | OpenAI API 金鑰 |
| `ANTHROPIC_API_KEY` | Opt | Anthropic API key | Anthropic API 金鑰 |
| `GEMINI_API_KEY` | Opt | Google Gemini API key | Google Gemini API 金鑰 |
| `MINIMAX_API_KEY` | Opt | MiniMax API key | MiniMax API 金鑰 |
| `DEEPSEEK_API_KEY` | Opt | DeepSeek API key | DeepSeek API 金鑰 |
| `QWEN_API_KEY` | Opt | Qwen API key | 通義千問 API 金鑰 |
| `OPENROUTER_API_KEY` | Opt | OpenRouter key (100+ models) | OpenRouter 金鑰（100+ 模型） |
| `TELEGRAM_BOT_TOKEN` | Opt | Telegram bot token | Telegram 機器人 token |

*At least one AI provider key required / 至少需要一個 AI 供應商金鑰*

---

## AI Providers / AI 供應商

| Provider | Default Model | API Key Format | 說明 |
|----------|---------------|----------------|------|
| **OpenAI** | `openai/gpt-4o` | `sk-proj-...` | GPT-4o, o1, GPT-4 Turbo |
| **Anthropic** | `anthropic/claude-sonnet-4-20250514` | `sk-ant-api03-...` | Claude Sonnet/Opus/Haiku |
| **Google** | `google/gemini-2.0-flash` | `AIzaSy...` | Gemini 2.0 Flash, 2.5 Pro |
| **MiniMax** | `minimax/MiniMax-M2.5` | `eyJhbG...` | MiniMax M2.5, Text-01 |
| **DeepSeek** | `deepseek/deepseek-chat` | `sk-...` | DeepSeek Chat, Coder, Reasoner |
| **Qwen** | `qwen/qwen-max` | `sk-...` | Qwen Max, Plus, Turbo |
| **OpenRouter** | `openrouter/auto` | `sk-or-...` | 100+ models via single key |
| **Ollama** | `ollama/llama3` | Host URL | Local models (self-hosted) |

---

## Custom Gateway Image / 自訂 Gateway 映像

The `openclaw-k3s-paas/Dockerfile.custom` extends the official image with 12 install sections:

| Section | Components | 內容 |
|---------|------------|------|
| 1 | System packages (jq, ffmpeg, tmux, ripgrep) | 系統套件 |
| 2 | npm CLIs (clawhub, mcporter, oracle, gemini-cli, codex) | npm CLI 工具 |
| 3 | Go 1.23.7 compiler | Go 編譯器 |
| 4 | 13 Go binaries (blogwatcher, blucli, sonos, gifgrep, etc.) | Go 二進位程式 |
| 5 | GitHub CLI (gh 2.67.0) | GitHub CLI |
| 6 | 1Password CLI (op 2.30.3) | 1Password CLI |
| 7 | Himalaya (email CLI) | 電子郵件 CLI |
| 8 | OpenHue CLI (smart lights) | 智慧燈光 CLI |
| 9 | Obsidian CLI (notesmd-cli 0.3.4) | Obsidian 筆記 CLI |
| 10 | uv (Python package manager) | Python 套件管理器 |
| 11 | OpenAI Whisper (CPU-only) | 語音轉文字 |
| 12 | nano-pdf (PDF processing) | PDF 處理 |

---

## LLM Switching / LLM 切換

Switch between models via CLI or GUI.
透過 CLI 或 GUI 切換模型。

```bash
# Switch to MiniMax
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- \
  openclaw config set agents.defaults.model "minimax/MiniMax-M2.5"

# Switch to DeepSeek
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- \
  openclaw config set agents.defaults.model "deepseek/deepseek-chat"

# Switch to Claude
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- \
  openclaw config set agents.defaults.model "anthropic/claude-sonnet-4-20250514"

# Switch to GPT-4o
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- \
  openclaw config set agents.defaults.model "openai/gpt-4o"

# Switch via OpenRouter (100+ models)
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- \
  openclaw config set agents.defaults.model "openrouter/google/gemini-2.0-flash"
```

**Tested Models / 已測試模型:** GPT-4o, Claude Sonnet, Gemini 2.0 Flash, MiniMax M2.5, DeepSeek Chat, Llama 3

---

## Common Commands / 常用指令

```bash
# Pod status / Pod 狀態
kubectl -n openclaw-tenant-1 get pods

# Gateway logs / Gateway 日誌
kubectl -n openclaw-tenant-1 logs deployment/openclaw-gateway --tail=50

# Channel status / 頻道狀態
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- openclaw channels status

# Skill count / 技能數量
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- openclaw skills list 2>/dev/null | tail -1

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
├── openclaw-k3s-paas/
│   ├── Dockerfile.custom     # Custom gateway image (12 sections)
│   └── setup-wizard/         # Synced copy of setup-wizard
├── setup-wizard/             # Flask provisioning UI (8 providers, dark/light)
├── tests/pre-launch/         # 67 automated tests (6 rounds)
├── utils/                    # Utility scripts
└── docs/                     # Troubleshooting guides
```

---

## Testing / 測試

**67 automated tests, 6 rounds / 67 個自動化測試，6 輪：**

| Round | Tests | Coverage | 涵蓋範圍 |
|-------|-------|----------|----------|
| 1 | 12 | Infrastructure health | 基礎設施健康 |
| 2 | 15 | Security & stress | 安全暴力測試 |
| 3 | 10 | LLM switching | LLM 多模型切換 |
| 4 | 12 | Channel bidirectional | 頻道雙向通訊 |
| 5 | 10 | Cron, skills, hot-reload | 排程、技能 |
| 6 | 8 | Resilience & recovery | 穩定性恢復 |

```bash
bash tests/pre-launch/run-all.sh
# HTML report: tests/pre-launch/report-YYYY-MM-DD.html
```

---

## Troubleshooting / 故障排除

See [docs/troubleshooting.md](docs/troubleshooting.md).

| Issue | Fix | 修復方式 |
|-------|-----|----------|
| 502 Bad Gateway | Clean tunnel connections + restart cloudflared | 清除隧道連線 + 重啟 cloudflared |
| DB pod Pending | Delete PVC and re-apply manifest | 刪除 PVC 重新套用 manifest |
| Control UI won't load | Re-visit `https://domain/#token=your-token` | 重新訪問帶 token 的 URL |
| Skills not loading | Rebuild with `Dockerfile.custom` | 使用自訂 Dockerfile 重建 |

---

## License / 授權

MIT License — Copyright (c) 2026 Woowtech Smart Space Solution
