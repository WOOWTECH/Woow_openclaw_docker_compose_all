# Hermes Agent — Podman 部署

## 快速開始

```bash
# 1. 生成設定檔
bash deploy.sh

# 2. 編輯 API Key
nano .env   # 填入 MINIMAX_API_KEY

# 3. 啟動
bash deploy.sh
```

## 架構

所有容器在同一個 Podman Pod 中，共享 localhost：

```
Podman Pod: hermes
├── hermes-agent      :8642 (Gateway) + :9119 (Dashboard + TUI)
├── hermes-webui      :8787 (Web 介面)
├── postgresql        :5432
└── redis             :6379
```

## 雙 GUI

| 介面 | URL | 用途 |
|------|-----|------|
| WebUI | http://localhost:8787 | 對話/排程/技能/SOUL 性格 |
| Dashboard | http://localhost:9119 | Config/API Keys/MCP/Model 切換/Terminal |

## Cloudflare Tunnel 整合

如已有 CF tunnel，加入路由：
```bash
# WebUI
hostname: name-hermes.woowtech.io → http://localhost:8787

# Dashboard
hostname: name-dashboard.woowtech.io → http://localhost:9119
```

## 管理

```bash
podman-compose ps          # 查看狀態
podman-compose logs -f     # 查看日誌
podman-compose restart     # 重啟
podman-compose down        # 停止
podman-compose down -v     # 停止並刪除資料
```
