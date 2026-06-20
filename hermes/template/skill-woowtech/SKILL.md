# WoowTech Hermes 部署樣板

## 概述
基於 WoowTech Hermes 的完整配置樣板，用於快速建置新的 Hermes AI 助手實例。
包含藍色 WoowTech logo 品牌、完整優化配置、雙 GUI（Dashboard + WebUI）、排程監測。

## 部署指令
```bash
bash deploy-woowtech-hermes.sh <namespace> <domain> [kubectl-context]
# 範例:
bash deploy-woowtech-hermes.sh clienta-hermes clienta-hermes.woowtech.io woow-k3s
```

## 目標叢集
- 預設部署到 **woow-k3s** 遠端叢集 (114.32.21.18)
- 可用第三個參數指定其他 context

## 雙 GUI 架構 (Dashboard + WebUI)

每個實例提供兩個獨立的 Web 介面：

| 介面 | 端口 | URL 格式 | 用途 |
|------|------|----------|------|
| **WebUI** | 8787 | `https://NAME.woowtech.io` | 主聊天介面，品牌化登入頁 |
| **Dashboard** | 9119 | `https://NAME-dashboard.woowtech.io` | 管理面板，內嵌 Chat + Terminal (TUI) |

### Dashboard 啟用條件
- `HERMES_DASHBOARD=1` — 啟用 Dashboard
- `HERMES_DASHBOARD_INSECURE=1` — 允許無認證存取
- `HERMES_DASHBOARD_TUI=1` — 啟用內嵌 Chat/Terminal (TUI)

### Dashboard TUI 權限修復（已自動化）
部署腳本自動執行以下步驟：
1. `chown -R hermes:hermes /opt/hermes/ui-tui/` (修復 image layer 權限)
2. 複製 `ui-tui` 到 PVC (`/opt/data/ui-tui`)
3. 設定 `HERMES_TUI_DIR=/opt/data/ui-tui` 環境變數（永久修復，Pod 重啟不受影響）
4. 寫入 `MINIMAX_API_KEY` 到 `/opt/data/.env`（TUI 讀取 .env 檔案，非容器環境變數）

### CF Tunnel 配置
每個實例需要兩個 CF tunnel ingress 規則：
```yaml
- hostname: NAME.woowtech.io
  service: http://NS-webui-svc.NS.svc.cluster.local:8787
- hostname: NAME-dashboard.woowtech.io
  service: http://NS-agent-svc.NS.svc.cluster.local:9119
```

## 包含內容
- **品牌**: 藍色 WoowTech logo (#6183fc) — favicon/PWA/登入頁/Chat 歡迎頁
- **品牌持久化**: branding inject 寫入 hermeswebui_init.bash，Pod 重啟自動恢復
- **配置**: golden-config.yaml (cron_mode=yolo, tirith_enabled=false)
- **Dashboard TUI**: HERMES_DASHBOARD_TUI=1 啟用內嵌 Chat/Terminal
- **隱藏**: Kanban + Todos 分頁
- **排程**: 系統心跳 (every 30m)
- **密碼**: 預設 `admin`
- **SOUL**: 通用 AI 助手（無隱私資料）
- **持久化**: postStart hook + init.bash 注入確保品牌自動恢復
- **Web 搜尋**: ddgs (DuckDuckGo) 套件安裝到 venv，`web.backend: ddgs`

## postStart Lifecycle Hook（每次 Pod 啟動自動執行）
1. 移除未使用工具：argocd, helm, docker
2. 建立 hermes CLI symlink：`/usr/local/bin/hermes`
3. 移除 15 個不需要的內建技能（apple, gaming, email, social-media, yuanbao 等）
4. 安裝 ddgs Python 套件到 venv site-packages（web_search 工具）

## WoowTech 自建技能體系（13 項，三層架構）
```
woowtech/
├── 01-building-tech/     ← Layer 1: 底層技術
│   ├── knx/              ← KNX 建築自動化核心
│   ├── knx-ets/          ← ETS 工程工具
│   ├── knx-ets-parser/   ← ETS 匯出解析
│   ├── knx-training/     ← KNX 培訓與認證
│   ├── basalte/          ← Basalte 硬體
│   ├── home-assistant/   ← HA 自動化
│   └── aiot/             ← AIoT 智慧建築整合
├── 02-certification/     ← Layer 2: 認證標準
│   ├── well-standard/    ← WELL v2 知識庫 (ESG-S)
│   ├── well-strategy/    ← WELL 認證策略
│   ├── leed-bdc/         ← LEED BD+C 總覽 (ESG-E)
│   ├── leed-energy/      ← LEED EAc2 能效
│   └── leed-water/       ← LEED WE 水效
└── 03-esg/               ← Layer 3: ESG 頂層框架
    └── esg-framework/    ← E+S+G 三支柱整合
```

## 部署後自動化步驟（腳本包含）
1. TUI 權限修復 + PVC 永久修復（`HERMES_TUI_DIR=/opt/data/ui-tui`）
2. .env API key 寫入（TUI 讀取 .env 檔案）
3. Agent 原始碼複製（WebUI gateway 模式所需）
4. tmux 安裝（支援 parallel agent dispatch）
5. Superpowers skills 安裝（obra/superpowers, 14 項）
6. WoowTech 自建技能安裝（woowtech/, 13 項）
7. 全部 skills 啟用（透過 WebUI `/api/skills/toggle` API）
8. 品牌注入至 `hermeswebui_init.bash`
9. Web 搜尋啟用（ddgs 套件 + `web.backend: ddgs`）

## Known Issues & Fixes

| 問題 | 原因 | 修復方式 |
|------|------|----------|
| Dashboard TUI 顯示 "No API key configured" | TUI 讀取 `/opt/data/.env` 檔案，非容器環境變數 | 部署腳本自動寫入 `MINIMAX_API_KEY` 到 `.env` |
| Dashboard TUI 在 Pod 重啟後壞掉 | image layer 的 `ui-tui/` 權限被重設 | `HERMES_TUI_DIR=/opt/data/ui-tui` 從 PVC 讀取，永久修復 |
| WebUI model 與 Dashboard 不同步 | WebUI 和 Dashboard 使用獨立的 model 設定 | 在 WebUI Chat 中使用 `/model` 指令切換 |

## 檔案清單
| 檔案 | 用途 |
|------|------|
| `deploy-woowtech-hermes.sh` | 一鍵部署腳本（含全部優化） |
| `apply_branding_woowtech.py` | WoowTech 品牌替換邏輯 |
| `replace_icons.sh` | postStart 入口腳本 |
| `icons/` | 7 個 favicon/PWA icon 檔案 |
