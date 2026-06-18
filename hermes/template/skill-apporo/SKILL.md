# Apporo Hermes 部署樣板

## 概述
基於 Apporo Hermes 的完整配置樣板，用於快速建置新的 Hermes AI 助手實例。
包含白色 Apporo 三角形幾何 logo 品牌、完整優化配置、雙 GUI（Dashboard + WebUI）、排程監測。

## 部署指令
```bash
bash deploy-apporo-hermes.sh <namespace> <domain> [kubectl-context]
# 範例:
bash deploy-apporo-hermes.sh clientb-hermes clientb-hermes.woowtech.io woow-k3s
```

## 目標叢集
- 預設部署到 **woow-k3s** 遠端叢集 (114.32.21.18)
- 可用第三個參數指定其他 context

## Minimax API Key 注意事項
Apporo 實例必須使用 **Token Plan key** (`sk-cp-` prefix)，**不要使用** pay-as-you-go key。

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
- **品牌**: 白色 Apporo 三角形幾何 logo — favicon/PWA/登入頁/Chat 歡迎頁
- **品牌持久化**: branding inject 寫入 hermeswebui_init.bash，Pod 重啟自動恢復
- **配置**: golden-config.yaml (cron_mode=yolo, tirith_enabled=false)
- **Dashboard TUI**: HERMES_DASHBOARD_TUI=1 啟用內嵌 Chat/Terminal
- **隱藏**: Kanban + Todos 分頁
- **排程**: 系統心跳 (every 30m)
- **密碼**: 預設 `admin`
- **SOUL**: 通用 AI 助手（無隱私資料）
- **持久化**: postStart hook + init.bash 注入確保品牌自動恢復

## 部署後自動化步驟（腳本包含）
1. TUI 權限修復 (`chown -R hermes:hermes /opt/hermes/ui-tui/`)
2. **TUI PVC 永久修復**: 複製 `ui-tui` 到 `/opt/data/ui-tui` (PVC)，設定 `HERMES_TUI_DIR=/opt/data/ui-tui` 環境變數（Pod 重啟後不需重新 chown）
3. **.env API key 寫入**: 寫入 `MINIMAX_API_KEY` 到 `/opt/data/.env`（TUI 讀取 .env 檔案，非容器環境變數）
4. Agent 原始碼複製 (`/opt/hermes` -> `/opt/data/hermes-agent`，WebUI gateway 模式所需)
5. tmux 安裝 (支援 parallel agent dispatch)
6. Superpowers skills 安裝 (obra/superpowers GitHub)
7. 全部 skills 啟用 (透過 WebUI `/api/skills/toggle` API)
8. 品牌注入至 `hermeswebui_init.bash`（`server.py` 啟動前自動執行 `replace_icons.sh`）

## Known Issues & Fixes

| 問題 | 原因 | 修復方式 |
|------|------|----------|
| Dashboard TUI 顯示 "No API key configured" | TUI 讀取 `/opt/data/.env` 檔案，非容器環境變數 | 部署腳本自動寫入 `MINIMAX_API_KEY` 到 `.env` |
| Dashboard TUI 在 Pod 重啟後壞掉 | image layer 的 `ui-tui/` 權限被重設 | `HERMES_TUI_DIR=/opt/data/ui-tui` 從 PVC 讀取，永久修復 |
| WebUI model 與 Dashboard 不同步 | WebUI 和 Dashboard 使用獨立的 model 設定 | 在 WebUI Chat 中使用 `/model` 指令切換 |

## 檔案清單
| 檔案 | 用途 |
|------|------|
| `deploy-apporo-hermes.sh` | 一鍵部署腳本（含全部優化） |
| `apply_branding_apporo.py` | Apporo 品牌替換邏輯 (v2) |
| `replace_icons.sh` | postStart 入口腳本 |
| `icons/` | 7 個 favicon/PWA icon 檔案 + 原始 SVG |
