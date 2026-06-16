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

### Dashboard TUI 權限修復
部署後必須執行：
```bash
kubectl exec POD -c hermes-agent -- chown -R hermes:hermes /opt/hermes/ui-tui/
```

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

## 部署後自動化步驟（腳本包含）
1. TUI 權限修復 (`chown -R hermes:hermes /opt/hermes/ui-tui/`)
2. Agent 原始碼複製 (`/opt/hermes` -> `/opt/data/hermes-agent`，WebUI gateway 模式所需)
3. tmux 安裝 (支援 parallel agent dispatch)
4. Superpowers skills 安裝 (obra/superpowers GitHub)
5. 全部 skills 啟用 (透過 WebUI `/api/skills/toggle` API)
6. 品牌注入至 `hermeswebui_init.bash`（`server.py` 啟動前自動執行 `replace_icons.sh`）

## 檔案清單
| 檔案 | 用途 |
|------|------|
| `deploy-woowtech-hermes.sh` | 一鍵部署腳本（含全部優化） |
| `apply_branding_woowtech.py` | WoowTech 品牌替換邏輯 |
| `replace_icons.sh` | postStart 入口腳本 |
| `icons/` | 7 個 favicon/PWA icon 檔案 |
