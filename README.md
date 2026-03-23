# Woow OpenClaw Podman Deployment

**OpenClaw AI Gateway — Docker Compose / Podman Deployment**
**OpenClaw AI 閘道器 — Docker Compose / Podman 部署**

Deploy a production-ready OpenClaw AI gateway using Docker Compose (Podman-compatible) with Cloudflare Tunnel, 8 AI providers, dark/light UI, and persistent configuration.

在 Docker Compose（相容 Podman）上部署生產就緒的 OpenClaw AI 閘道器，支援 Cloudflare Tunnel、8 個 AI 供應商、深色/淺色 UI 介面、持久化配置。

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
- [Persistence / 持久化](#persistence--持久化)
- [Common Commands / 常用指令](#common-commands--常用指令)
- [File Structure / 檔案結構](#file-structure--檔案結構)
- [Troubleshooting / 故障排除](#troubleshooting--故障排除)
- [License / 授權](#license--授權)

---

## Overview / 概述

**English:**
OpenClaw is an AI gateway that connects large language models to messaging platforms (Telegram, WhatsApp, Discord, Slack). This branch provides a Docker Compose / Podman deployment with:

- **Setup Wizard**: Web-based zero-touch provisioning with dark/light mode
- **Cloudflare Tunnel**: Secure external access without exposed ports (3x retry)
- **8 AI Providers**: OpenAI, Anthropic, Google, MiniMax, DeepSeek, Qwen, OpenRouter, Ollama
- **Custom Gateway Image**: 12-section Dockerfile with 52 skill CLI dependencies baked in
- **Auth-Profiles Merge**: Adding a new provider doesn't overwrite existing keys
- **Full Persistence**: All config, skills, LLM settings survive `podman compose down/up`
- **Host .env Sync**: API keys persist in host `.env` file across restarts

**中文：**
OpenClaw 是一個 AI 閘道器，連接大型語言模型到訊息平台（Telegram、WhatsApp、Discord、Slack）。本分支提供 Docker Compose / Podman 部署方案：

- **Setup Wizard**：基於 Web 的零接觸配置，支援深色/淺色模式
- **Cloudflare Tunnel**：安全外部存取，不需開放端口（3 次重試）
- **8 個 AI 供應商**：OpenAI、Anthropic、Google、MiniMax、DeepSeek、Qwen、OpenRouter、Ollama
- **自訂 Gateway 映像**：12 段式 Dockerfile，內建 52 個技能 CLI 依賴
- **Auth-Profiles 合併**：新增供應商不會覆蓋已有金鑰
- **完整持久化**：所有配置、技能、LLM 設定在 `podman compose down/up` 後保留
- **主機 .env 同步**：API 金鑰同步寫入主機 `.env` 檔案，重啟後自動載入

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
│  Docker Compose / Podman                         │
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
│                               │                  │
│  Bind Mounts:                 │                  │
│  ./data/openclaw ←──────────→ /home/node/.openclaw│
│  ./data/postgres ←──────────→ /var/lib/postgresql │
│                     ┌─────────▼──────────┐       │
│                     │ PostgreSQL (pgvector)│      │
│                     │   :5432             │      │
│                     └────────────────────┘       │
└──────────────────────────────────────────────────┘
```

---

## Services / 服務說明

| Service | Image | Port | Description | 說明 |
|---------|-------|------|-------------|------|
| **cloudflared** | `cloudflare/cloudflared:latest` | — | Cloudflare Tunnel connector | Cloudflare 隧道連接器 |
| **gateway** | `openclaw-gateway-custom:latest` | 18789 | AI gateway + Control UI (custom build) | AI 閘道器 + 管理介面（自訂映像） |
| **db** | `pgvector/pgvector:pg16` | 5432 | PostgreSQL with vector extension | PostgreSQL 向量資料庫 |

> **Note / 備註**: The setup-wizard runs as a separate container during initial provisioning. After setup completes, it exits automatically.
> Setup wizard 在初次配置時作為獨立容器運行，配置完成後自動退出。

---

## Prerequisites / 前置需求

**English:**
- Podman 4.x+ or Docker 24.x+ with Docker Compose v2
- At least 4 GB RAM, 2 CPU cores
- Cloudflare account with a domain (for tunnel)
- At least one AI provider API key

**中文：**
- Podman 4.x+ 或 Docker 24.x+（含 Docker Compose v2）
- 至少 4 GB RAM、2 CPU 核心
- Cloudflare 帳號及網域（用於隧道）
- 至少一個 AI 供應商 API 金鑰

---

## Quick Start / 快速開始

### Step 1: Clone and Configure / 複製並配置

```bash
git clone -b podman https://github.com/WOOWTECH/Woow_openclaw_docker_compose_all.git
cd Woow_openclaw_docker_compose_all
cp .env.example .env
# Edit .env with your credentials / 編輯 .env 填入認證資訊
```

### Step 2: Build Custom Gateway Image / 建構自訂映像

```bash
podman compose build gateway
# Or with Docker: docker compose build gateway
```

This builds a custom image with all 52 skill CLI dependencies (Go binaries, npm CLIs, Python tools, etc.).
這會建構包含所有 52 個技能 CLI 依賴的自訂映像。

### Step 3: Start Services / 啟動服務

```bash
podman compose up -d
```

### Step 4: Setup via Web UI / 透過 Web 介面設定

Visit `http://localhost:18790` and fill in:
- **Gateway Token**: Access password for Control UI
- **Database Password**: PostgreSQL password
- **AI Provider**: Select from 8 providers and enter API key

### Step 5: Access Control UI / 存取管理介面

After setup, visit `https://your-domain.example.com/#token=your-gateway-token`

Go to **Channels** to configure Telegram, WhatsApp, etc.

---

## Configuration / 配置說明

Copy `.env.example` to `.env` and fill in values:

| Variable | Required | Description | 說明 |
|----------|----------|-------------|------|
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password | 資料庫密碼 |
| `OPENCLAW_VERSION` | No | Gateway image tag (default: latest) | Gateway 映像標籤 |
| `GATEWAY_PORT` | No | Host port (default: 18789) | 主機連接埠 |
| `WIZARD_PORT` | No | Setup wizard port (default: 18790) | 設定精靈連接埠 |
| `CF_API_TOKEN` | Opt | Cloudflare API token | Cloudflare API 金鑰 |
| `CF_ACCOUNT_ID` | Opt | Cloudflare Account ID | Cloudflare 帳戶 ID |
| `CF_TUNNEL_ID` | Opt | Tunnel ID | 隧道 ID |
| `CF_TUNNEL_TOKEN` | Opt | Tunnel token | 隧道 Token |
| `CF_TUNNEL_DOMAIN` | Opt | Tunnel domain | 隧道網域 |
| `MINIMAX_API_KEY` | Opt | MiniMax API key | MiniMax API 金鑰 |
| `OPENAI_API_KEY` | Opt | OpenAI API key | OpenAI API 金鑰 |
| `ANTHROPIC_API_KEY` | Opt | Anthropic API key | Anthropic API 金鑰 |
| `DEEPSEEK_API_KEY` | Opt | DeepSeek API key | DeepSeek API 金鑰 |
| `QWEN_API_KEY` | Opt | Qwen/DashScope API key | 通義千問 API 金鑰 |
| `OPENROUTER_API_KEY` | Opt | OpenRouter API key | OpenRouter API 金鑰 |
| `GOOGLE_API_KEY` | Opt | Google Gemini API key | Google Gemini API 金鑰 |

*At least one AI provider key is required / 至少需要一個 AI 供應商金鑰*

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

Switch models via CLI:
```bash
podman exec openclaw-gateway openclaw config set agents.defaults.model "deepseek/deepseek-chat"
```

---

## Custom Gateway Image / 自訂 Gateway 映像

The `gateway/Dockerfile` extends the official OpenClaw image with 12 install sections:

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

Rebuild with upstream update:
```bash
podman compose build --pull gateway
```

---

## Persistence / 持久化

All data persists via bind mounts:

| Host Path | Container Path | Content | 說明 |
|-----------|---------------|---------|------|
| `./data/openclaw` | `/home/node/.openclaw` | Skills, agents, auth, cron, workspace, memory | 技能、代理、認證、排程、工作區、記憶 |
| `./data/postgres` | `/var/lib/postgresql/data` | Database files | 資料庫檔案 |
| `./data/whisper-cache` | `/home/node/.cache/whisper` | Whisper model cache | Whisper 模型快取 |

**What survives `podman compose down && up -d`:**
- All installed skills and configurations
- LLM model selection and auth-profiles
- Chat channel settings (Telegram, WhatsApp, etc.)
- Cron jobs and workspace files
- Memory and conversation history
- API keys (synced to host `.env` file)

---

## Common Commands / 常用指令

```bash
# Start all services / 啟動所有服務
podman compose up -d

# Stop all services / 停止所有服務
podman compose down

# View logs / 查看日誌
podman logs -f openclaw-gateway

# Check skill count / 檢查技能數量
podman exec openclaw-gateway openclaw skills list 2>/dev/null | tail -1

# Switch AI model / 切換 AI 模型
podman exec openclaw-gateway openclaw config set agents.defaults.model "openai/gpt-4o"

# Channel status / 頻道狀態
podman exec openclaw-gateway openclaw channels status

# Cron jobs / 排程任務
podman exec openclaw-gateway openclaw cron list

# Health check / 健康檢查
podman exec openclaw-gateway openclaw doctor

# Rebuild custom image / 重建自訂映像
podman compose build --pull gateway

# Full restart / 完全重啟
podman compose down && podman compose up -d
```

---

## File Structure / 檔案結構

```
.
├── .env.example              # Environment template / 環境變數模板
├── .gitignore                # Git ignore rules
├── docker-compose.yml        # Docker Compose / Podman services definition
├── gateway/
│   └── Dockerfile            # Custom gateway image (12 sections, 21 layers)
├── setup-wizard/
│   ├── Dockerfile            # Setup wizard image
│   ├── app.py                # Flask provisioning backend (8 providers, v1 auth)
│   ├── requirements.txt      # Python dependencies
│   └── templates/
│       └── index.html        # Setup UI (dark/light toggle, 8 providers)
├── scripts/
│   └── init-tunnel.sh        # Cloudflare tunnel bootstrapping
└── data/                     # Persistent data (gitignored)
    ├── openclaw/             # Gateway config, skills, agents
    ├── postgres/             # Database files
    └── whisper-cache/        # Whisper model cache
```

---

## Troubleshooting / 故障排除

| Issue | Fix | 修復方式 |
|-------|-----|----------|
| Gateway shows "(starting)" | Wait 60s for health check, or check `podman logs openclaw-gateway` | 等待 60 秒或檢查日誌 |
| Skills not loading | Rebuild: `podman compose build --pull gateway && podman compose up -d` | 重新建構映像 |
| DB connection error | Check `POSTGRES_PASSWORD` matches in `.env` | 確認 `.env` 中密碼一致 |
| Tunnel not connecting | Verify `CF_TUNNEL_TOKEN` in `.env` | 確認 tunnel token 正確 |
| Permission denied on data/ | Data dir owned by container uid (100999): `sudo chown -R 100999:100999 data/` | 修改資料目錄權限 |
| API key not persisting | Check `HOST_ENV_FILE` mount in compose | 確認 .env 掛載正確 |
| Auth-profiles overwritten | Update to latest setup-wizard (uses merge logic) | 更新至最新版（使用合併邏輯）|

---

## License / 授權

MIT License — Copyright (c) 2026 Woowtech Smart Space Solution
