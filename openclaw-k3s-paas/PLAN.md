# OpenClaw PaaS 租戶自動化部署與路由熱切換系統 - 架構計畫書

## 1. 系統架構概覽

```
                    ┌─────────────────────────────────────────────┐
                    │            Cloudflare Edge Network           │
                    │                                             │
                    │  cindytech1-openclaw.woowtech.io            │
                    └──────────────┬──────────────────────────────┘
                                   │ Cloudflare Tunnel
                    ┌──────────────▼──────────────────────────────┐
                    │          K3s Cluster (Node)                  │
                    │   Namespace: openclaw-tenant-1               │
                    │                                             │
                    │  ┌─────────────┐    ┌──────────────────┐    │
                    │  │ cloudflared  │    │  setup-wizard    │    │
                    │  │ (always on)  │───▶│  (replicas: 1)   │    │
                    │  └─────────────┘    │  Port: 18790     │    │
                    │        │            └────────┬─────────┘    │
                    │        │  Route Switch        │ K8s API      │
                    │        │◀────────────────────┤              │
                    │        │                     │ Scale Up      │
                    │        ▼                     ▼              │
                    │  ┌─────────────┐    ┌──────────────────┐    │
                    │  │  openclaw   │    │   PostgreSQL     │    │
                    │  │  gateway    │    │   (pgvector)     │    │
                    │  │  (0 → 1)   │    │   (0 → 1)       │    │
                    │  │  Port:18789│    │   Port: 5432     │    │
                    │  └─────────────┘    │   PVC: 10Gi     │    │
                    │                     └──────────────────┘    │
                    └─────────────────────────────────────────────┘
```

## 2. 生命週期流程

```
Phase 1: 初始部署 (deploy.sh)
  ├── docker build setup-wizard image
  ├── k3s ctr images import
  ├── kubectl create secret (from cf-config.json)
  └── kubectl apply -f k8s-manifests/
      ├── Namespace: openclaw-tenant-1
      ├── RBAC: wizard-sa (ServiceAccount + Role + RoleBinding)
      ├── ConfigMap: cf-config (ACCOUNT_ID, TUNNEL_ID, DOMAIN)
      ├── Cloudflared: replicas=1 (tunnel → setup-wizard-svc:18790)
      ├── Setup Wizard: replicas=1
      ├── PostgreSQL: replicas=0 (hibernating)
      └── OpenClaw Gateway: replicas=0 (hibernating)

Phase 2: 用戶設定 (via Cloudflare Tunnel)
  └── User visits https://cindytech1-openclaw.woowtech.io
      └── Cloudflared routes to setup-wizard-svc:18790
          └── Wizard serves index.html (password form)

Phase 3: 動態喚醒 (POST /setup)
  ├── Step A: Create K8s Secret "openclaw-secrets"
  │   ├── OPENCLAW_GATEWAY_TOKEN (user input)
  │   └── POSTGRES_PASSWORD (user input)
  ├── Step B: Scale up openclaw-db (0 → 1)
  ├── Step C: Scale up openclaw-gateway (0 → 1)
  ├── Step D: Polling wait until openclaw-gateway responds 200
  │   └── GET http://openclaw-gateway-svc:18789 every 2s, timeout 120s
  ├── Step E: Cloudflare API route switch
  │   └── PUT tunnel config: hostname → openclaw-gateway-svc:18789
  └── Step F: Return success to user

Phase 4: 功成身退 (Thread, 5s delay)
  └── Scale down setup-wizard (1 → 0)
      └── Only if ALL previous steps succeeded
```

## 3. 目錄結構

```
openclaw-k3s-paas/
├── PLAN.md                          # 本文件
├── init-cloudflare.py               # Cloudflare 資源初始化腳本
├── cf-config.json                   # 自動生成的 Cloudflare 配置
├── deploy.sh                        # 一鍵部署腳本
├── k8s-manifests/
│   ├── 00-namespace.yaml            # Namespace
│   ├── 01-rbac.yaml                 # ServiceAccount + Role + RoleBinding
│   ├── 02-secrets.yaml              # (由 deploy.sh 動態生成)
│   ├── 03-config.yaml               # ConfigMap
│   ├── 04-cloudflared.yaml          # Cloudflare Tunnel Connector
│   ├── 05-setup-wizard.yaml         # Setup Wizard Deployment + Service
│   └── 06-openclaw-core.yaml        # PostgreSQL + OpenClaw Gateway
└── setup-wizard/
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py                       # Flask 核心邏輯
    └── templates/
        └── index.html               # 前端 UI
```

## 4. 安全設計

| 敏感資料 | 儲存方式 | 消費者 |
|---------|---------|--------|
| CF_API_TOKEN | K8s Secret `cf-secrets` | setup-wizard |
| CF_TUNNEL_TOKEN | K8s Secret `cf-secrets` | cloudflared |
| OPENCLAW_GATEWAY_TOKEN | K8s Secret `openclaw-secrets` (runtime) | openclaw-gateway |
| POSTGRES_PASSWORD | K8s Secret `openclaw-secrets` (runtime) | postgresql, openclaw-gateway |

- 所有敏感 Token 均存於 K8s Secret，不寫入 ConfigMap 或 Deployment env 明文
- `openclaw-secrets` 由 Setup Wizard 在 runtime 透過 K8s API 動態建立
- `cf-secrets` 由 deploy.sh 在部署時從 cf-config.json 建立

## 5. RBAC 權限矩陣

| Resource | Verbs | 用途 |
|----------|-------|------|
| secrets | create, update, get, patch | 建立 openclaw-secrets |
| deployments | get, patch, update | 查看與修改 deployment |
| deployments/scale | get, patch, update | Scale up/down replicas |

## 6. 資源限制 (Resource Limits)

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|------------|-----------|---------------|-------------|
| setup-wizard | 50m | 200m | 64Mi | 256Mi |
| cloudflared | 50m | 200m | 64Mi | 128Mi |
| postgresql | 100m | 500m | 256Mi | 512Mi |
| openclaw-gateway | 200m | 1000m | 256Mi | 1Gi |

## 7. 防呆機制 (Race Condition Prevention)

- Wizard 在 scale up gateway 後，每 2 秒輪詢 `http://openclaw-gateway-svc:18789`
- 最多等待 120 秒 (60 次重試)
- 只有收到 HTTP 200 後才執行 Cloudflare 路由切換
- 若逾時或 Cloudflare API 失敗，回傳錯誤且不自我銷毀
