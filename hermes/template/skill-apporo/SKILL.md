# Apporo Hermes 部署樣板

## 概述
基於 Apporoalan Hermes 的完整配置樣板，用於快速建置新的 Hermes AI 助手實例。
包含白色 Apporo 三角形幾何 logo 品牌、完整優化配置、排程監測。

## 部署指令
```bash
bash deploy-apporo-hermes.sh <namespace> <domain> [kubectl-context]
# 範例:
bash deploy-apporo-hermes.sh clientb-hermes clientb-hermes.woowtech.io woow-k3s
```

## 目標叢集
- 預設部署到 **woow-k3s** 遠端叢集 (114.32.21.18)
- 可用第三個參數指定其他 context

## 包含內容
- **品牌**: 白色 Apporo 三角形幾何 logo — favicon/PWA/登入頁/Chat 歡迎頁
- **配置**: golden-config.yaml (cron_mode=yolo, tirith_enabled=false)
- **隱藏**: Kanban + Todos 分頁
- **排程**: 系統心跳 (every 30m)
- **密碼**: 預設 `admin`
- **SOUL**: 通用 AI 助手（無隱私資料）
- **持久化**: postStart hook 確保 Pod 重啟後品牌自動恢復

## 檔案清單
| 檔案 | 用途 |
|------|------|
| `deploy-apporo-hermes.sh` | 一鍵部署腳本 |
| `apply_branding_apporo.py` | Apporo 品牌替換邏輯 (v2) |
| `replace_icons.sh` | postStart 入口腳本 |
| `icons/` | 7 個 favicon/PWA icon 檔案 + 原始 SVG |
