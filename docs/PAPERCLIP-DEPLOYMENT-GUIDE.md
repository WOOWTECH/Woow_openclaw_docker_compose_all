# Paperclip AI 部署指南 — 與 OpenClaw 整合

> 適用於已有 OpenClaw + Nerve 的環境（Podman / Docker Compose）

## 架構總覽

```
                    ┌─────────────────┐
                    │   反向代理       │  Nginx / Caddy / CF Tunnel
                    └───┬────────┬────┘
                        │        │
           ┌────────────▼──┐  ┌──▼────────────┐
           │  Nerve UI     │  │  Paperclip UI  │
           │  個人操作面板  │  │  企業管理面板   │
           │  :3080        │  │  :3100         │
           └──────┬────────┘  └──────┬─────────┘
                  │    WebSocket     │
                  └────────┬────────┘
                    ┌──────▼──────┐
                    │  OpenClaw   │
                    │  Gateway    │     ← 已存在
                    │  :18789     │
                    └─────────────┘
```

| 角色 | 用途 | Port |
|------|------|------|
| **OpenClaw Gateway** | AI Agent 執行引擎（已存在） | 18789 |
| **Nerve** | 個人即時操作面板（已存在） | 3080 |
| **Paperclip** | 企業級 Agent 管理平台（新增） | 3100 |
| **Paperclip DB** | Paperclip 專用 PostgreSQL 17 | 5433 (避免衝突) |

---

## 前置條件

- 已有 OpenClaw gateway 在 `:18789` 運行
- 已知 OpenClaw gateway token（例如 `woowtech`）
- Podman 或 Docker Compose 已安裝

---

## 一、docker-compose.yml

```yaml
# Paperclip AI — 與 OpenClaw 整合
# 放在與 OpenClaw 相同的 compose 網路中

services:
  # ── Paperclip PostgreSQL 17 ──────────────────────
  paperclip-db:
    image: postgres:17-alpine
    container_name: paperclip-db
    environment:
      POSTGRES_DB: paperclip
      POSTGRES_USER: paperclip
      POSTGRES_PASSWORD: ${PAPERCLIP_DB_PASSWORD:-paperclip2026}
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - paperclip-db-data:/var/lib/postgresql/data
    ports:
      - "5433:5432"   # 用 5433 避免與 OpenClaw DB 衝突
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U paperclip -d paperclip"]
      interval: 5s
      timeout: 5s
      retries: 30
    restart: unless-stopped

  # ── Paperclip Server ─────────────────────────────
  paperclip:
    image: ghcr.io/paperclipai/paperclip:latest
    container_name: paperclip
    depends_on:
      paperclip-db:
        condition: service_healthy
    environment:
      # 資料庫
      DATABASE_URL: postgres://paperclip:${PAPERCLIP_DB_PASSWORD:-paperclip2026}@paperclip-db:5432/paperclip
      # 伺服器
      PORT: "3100"
      HOST: "0.0.0.0"
      SERVE_UI: "true"
      NODE_ENV: production
      # Paperclip 設定
      PAPERCLIP_HOME: /paperclip
      PAPERCLIP_INSTANCE_ID: default
      PAPERCLIP_DEPLOYMENT_MODE: authenticated
      PAPERCLIP_DEPLOYMENT_EXPOSURE: public
      PAPERCLIP_PUBLIC_URL: ${PAPERCLIP_PUBLIC_URL:-http://localhost:3100}
      PAPERCLIP_MIGRATION_AUTO_APPLY: "true"
      # Auth
      PAPERCLIP_AUTH_BASE_URL_MODE: explicit
      PAPERCLIP_AUTH_PUBLIC_BASE_URL: ${PAPERCLIP_PUBLIC_URL:-http://localhost:3100}
      BETTER_AUTH_SECRET: ${BETTER_AUTH_SECRET}
      BETTER_AUTH_TRUSTED_ORIGINS: ${PAPERCLIP_PUBLIC_URL:-http://localhost:3100},http://localhost:3100
      # Agent JWT
      PAPERCLIP_AGENT_JWT_SECRET: ${PAPERCLIP_AGENT_JWT_SECRET}
      # 關閉遙測
      PAPERCLIP_TELEMETRY_DISABLED: "true"
    volumes:
      - paperclip-data:/paperclip
    ports:
      - "3100:3100"
    restart: unless-stopped

volumes:
  paperclip-db-data:
  paperclip-data:

# 如果 OpenClaw 在同一個 compose，加入同一個 network：
# networks:
#   default:
#     external: true
#     name: openclaw_default  # 替換為你的 OpenClaw 網路名稱
```

---

## 二、.env 檔案

```bash
# ── 必填 ────────────────────────────────────────
# 生成方式：openssl rand -hex 32
BETTER_AUTH_SECRET=你的隨機64字元hex
PAPERCLIP_AGENT_JWT_SECRET=你的隨機64字元hex

# ── 資料庫 ──────────────────────────────────────
PAPERCLIP_DB_PASSWORD=paperclip2026

# ── 公開 URL ────────────────────────────────────
# 如果有反向代理 (HTTPS)：
# PAPERCLIP_PUBLIC_URL=https://paperclip.your-domain.com
# 如果直接存取 (開發/內網)：
PAPERCLIP_PUBLIC_URL=http://localhost:3100

# ── OpenClaw 連線資訊（給 Paperclip Agent 用）──
OPENCLAW_GATEWAY_URL=ws://localhost:18789
OPENCLAW_GATEWAY_TOKEN=woowtech
```

生成 secrets：
```bash
echo "BETTER_AUTH_SECRET=$(openssl rand -hex 32)" >> .env
echo "PAPERCLIP_AGENT_JWT_SECRET=$(openssl rand -hex 32)" >> .env
```

---

## 三、部署步驟

### 1. 啟動服務

```bash
# Podman Compose
podman compose up -d

# 或 Docker Compose
docker compose up -d
```

### 2. 建立 config.json（首次啟動需要）

```bash
podman exec paperclip sh -c '
mkdir -p /paperclip/instances/default
cat > /paperclip/instances/default/config.json << EOF
{
  "\$meta": {"version": 1, "updatedAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'", "source": "onboard"},
  "database": {"mode": "postgres", "connectionString": "postgres://paperclip:paperclip2026@paperclip-db:5432/paperclip"},
  "logging": {"mode": "file", "logDir": "/paperclip/instances/default/logs"},
  "server": {"deploymentMode": "authenticated", "exposure": "public", "bind": "lan", "host": "0.0.0.0", "port": 3100, "serveUi": true},
  "telemetry": {"enabled": false}
}
EOF
echo "Config created"
'
```

### 3. 建立 CEO 帳號

```bash
# 安裝 CLI 工具
podman exec paperclip sh -c 'npm install --prefix /tmp/pcli paperclipai --loglevel=error'

# 生成 CEO 邀請連結
podman exec paperclip sh -c '/tmp/pcli/node_modules/.bin/paperclipai auth bootstrap-ceo --base-url http://localhost:3100'
```

輸出範例：
```
◆  Created bootstrap CEO invite.
│  Invite URL: http://localhost:3100/invite/pcp_bootstrap_xxxxx
│  Expires: 2026-04-21T10:00:00.000Z
```

### 4. 接受邀請（在容器內完成）

```bash
TOKEN="pcp_bootstrap_xxxxx"  # 替換為上面的 token

podman exec paperclip node -e "
const http = require('http');
function api(method, path, data) {
  return new Promise(resolve => {
    const body = data ? JSON.stringify(data) : '';
    const opts = { hostname:'localhost', port:3100, path, method,
      headers: {'Content-Type':'application/json','Origin':'http://localhost:3100',
        ...(body?{'Content-Length':Buffer.byteLength(body)}:{})} };
    if(global._c) opts.headers['Cookie']=global._c;
    const req = http.request(opts, res => {
      let d=''; const sc=res.headers['set-cookie'];
      if(sc) global._c=sc.map(c=>c.split(';')[0]).join('; ');
      res.on('data',c=>d+=c);
      res.on('end',()=>{try{resolve({status:res.statusCode,data:JSON.parse(d)})}catch{resolve({status:res.statusCode,data:d})}});
    }); if(body) req.write(body); req.end();
  });
}
(async()=>{
  // 註冊帳號
  const signup = await api('POST','/api/auth/sign-up/email',{name:'Admin',email:'admin@company.com',password:'YourPassword123!'});
  console.log('Signup:', signup.status);
  // 登入
  const login = await api('POST','/api/auth/sign-in/email',{email:'admin@company.com',password:'YourPassword123!'});
  console.log('Login:', login.status);
  // 接受邀請
  const accept = await api('POST','/api/invites/${TOKEN}/accept',{requestType:'human'});
  console.log('Accept:', accept.status, JSON.stringify(accept.data).substring(0,100));
})();
"
```

---

## 四、建立公司與 AI Agent

### 透過容器內 API 建立

```bash
podman exec paperclip node -e "
const http = require('http');
function api(method, path, data) {
  return new Promise(resolve => {
    const body = data ? JSON.stringify(data) : '';
    const opts = { hostname:'localhost', port:3100, path, method,
      headers: {'Content-Type':'application/json','Origin':'http://localhost:3100',
        ...(body?{'Content-Length':Buffer.byteLength(body)}:{})} };
    if(global._c) opts.headers['Cookie']=global._c;
    const req = http.request(opts, res => {
      let d=''; const sc=res.headers['set-cookie'];
      if(sc) global._c=sc.map(c=>c.split(';')[0]).join('; ');
      res.on('data',c=>d+=c);
      res.on('end',()=>{try{resolve({status:res.statusCode,data:JSON.parse(d)})}catch{resolve({status:res.statusCode,data:d})}});
    }); if(body) req.write(body); req.end();
  });
}
(async()=>{
  // 登入
  await api('POST','/api/auth/sign-in/email',{email:'admin@company.com',password:'YourPassword123!'});
  // 建立公司
  const co = await api('POST','/api/companies',{name:'My Company',slug:'my-company'});
  const cid = co.data?.id;
  console.log('Company:', cid);
  // 建立 OpenClaw Agent
  const agent = await api('POST','/api/companies/'+cid+'/agents',{
    name: 'AI Developer',
    title: 'Full-Stack Developer',
    adapterType: 'openclaw_gateway',
    jobDescription: 'Writes code, reviews PRs, manages infrastructure.',
    adapterConfig: {
      url: 'ws://host.containers.internal:18789',  // Podman: 用這個存取 host
      // url: 'ws://openclaw-gateway:18789',         // 同 compose 網路: 用 service 名稱
      headers: { 'x-openclaw-token': 'woowtech' },  // 你的 gateway token
      sessionKeyStrategy: 'issue',
      waitTimeoutMs: 120000
    }
  });
  console.log('Agent:', agent.status, agent.data?.id);
})();
"
```

---

## 五、OpenClaw Gateway 連線方式

### 關鍵：`adapterConfig` 設定

Paperclip 透過 `openclaw_gateway` adapter 用 **WebSocket** 連接 OpenClaw gateway。

```json
{
  "url": "ws://openclaw-gateway:18789",
  "headers": {
    "x-openclaw-token": "你的gateway_token"
  },
  "sessionKeyStrategy": "issue",
  "waitTimeoutMs": 120000
}
```

### URL 選擇

| 場景 | URL |
|------|-----|
| **同一個 compose 網路** | `ws://openclaw-gateway:18789`（用 service 名稱） |
| **Podman 獨立容器** | `ws://host.containers.internal:18789`（存取 host） |
| **K3s 叢集** | `ws://openclaw-gateway-svc:18789`（K8s service） |
| **遠端機器** | `wss://your-domain.com`（透過反向代理 + TLS） |

### Auth 方式（擇一）

```json
// 方式 1: x-openclaw-token header（推薦）
{ "headers": { "x-openclaw-token": "你的token" } }

// 方式 2: authToken 欄位
{ "authToken": "你的token" }

// 方式 3: password（如果 gateway 用 password auth）
{ "password": "你的password" }
```

### Session 策略

| 策略 | 說明 |
|------|------|
| `issue` | 每個 issue 一個獨立 session（預設，推薦） |
| `fixed` | 所有任務共用一個 session |
| `run` | 每次執行建立新 session |

---

## 六、網路拓撲

### Podman 獨立容器（OpenClaw 在 host 上）

```
Host Machine
├── OpenClaw Gateway (:18789)     ← 已存在
├── Nerve (:3080)                 ← 已存在
└── Podman
    ├── paperclip (:3100)         ← 新增
    │   └── ws://host.containers.internal:18789 → OpenClaw
    └── paperclip-db (:5433)      ← 新增
```

### Podman Compose（全部容器化）

```yaml
# 在 OpenClaw 的 docker-compose.yml 加入：
services:
  # ... 現有的 openclaw-gateway, nerve, db ...

  paperclip-db:
    image: postgres:17-alpine
    # ... (同上)

  paperclip:
    image: ghcr.io/paperclipai/paperclip:latest
    # adapterConfig.url = ws://openclaw-gateway:18789
    # ... (同上)
```

---

## 七、持久化 (PVC / Volumes)

| Volume | 路徑 | 內容 |
|--------|------|------|
| `paperclip-db-data` | `/var/lib/postgresql/data` | PostgreSQL 資料 |
| `paperclip-data` | `/paperclip` | config.json、secrets、logs、backups、storage |

### 備份

Paperclip 內建自動備份：
- 預設每 60 分鐘備份一次
- 保留 7 天
- 備份位置：`/paperclip/instances/default/data/backups/`

手動備份：
```bash
# 資料庫
podman exec paperclip-db pg_dump -U paperclip paperclip > paperclip-backup.sql

# 設定 + 資料
podman cp paperclip:/paperclip ./paperclip-data-backup
```

---

## 八、驗證

```bash
# 1. 健康檢查
curl http://localhost:3100/api/health
# 期望: {"status":"ok"}

# 2. 容器狀態
podman ps | grep paperclip
# 期望: paperclip 和 paperclip-db 都 running

# 3. 資料庫連線
podman exec paperclip-db pg_isready -U paperclip
# 期望: accepting connections

# 4. 開啟瀏覽器
# 訪問 http://localhost:3100
# 用 CEO 帳號登入後應看到公司看板
```

---

## 九、常見問題

### Q: "Invalid origin" / "Board access required"

**原因：** `PAPERCLIP_PUBLIC_URL` 與實際存取的 URL 不匹配。

**修復：**
1. 確保 `PAPERCLIP_PUBLIC_URL` 與瀏覽器地址列的 URL 一致
2. 加入 `BETTER_AUTH_TRUSTED_ORIGINS` 允許額外的 origin
3. `PAPERCLIP_DEPLOYMENT_EXPOSURE=public` + `PAPERCLIP_AUTH_BASE_URL_MODE=explicit`

### Q: "Board mutation requires trusted browser origin"

**原因：** API 請求缺少 `Origin` header。

**修復：** 從容器內部用 `http://localhost:3100` 呼叫 API 時加上 `Origin: http://localhost:3100`

### Q: Agent 無法連線到 OpenClaw

**檢查清單：**
1. OpenClaw gateway 是否在運行？ `curl http://localhost:18789/healthz`
2. `adapterConfig.url` 是否正確？（`ws://` 不是 `http://`）
3. Token 是否匹配 `OPENCLAW_GATEWAY_TOKEN`？
4. 網路是否可達？（同 compose 用 service 名，跨 host 用 IP/hostname）

### Q: Secure cookie 問題（HTTPS）

BetterAuth 在 `authenticated` 模式設定 `__Secure-` cookie（需要 HTTPS）。
- **開發環境：** 從容器內 localhost 操作（繞過 HTTPS 限制）
- **生產環境：** 配置反向代理 + TLS 證書

---

## 十、與 K3s 版本的差異

| 項目 | K3s | Podman |
|------|-----|--------|
| Image pull | `imagePullPolicy: IfNotPresent` | 自動 pull |
| 網路 | K8s Service DNS (`svc:port`) | Compose service 名稱 / host.containers.internal |
| 儲存 | PVC (local-path) | Named volumes |
| 反向代理 | Cloudflare Tunnel | Nginx / Caddy / Tailscale |
| NetworkPolicy | K8s NetworkPolicy | Podman network isolation |
| 健康檢查 | TCP probe（避免 auth 403） | Docker healthcheck |
| Secret 管理 | K8s Secret | .env 檔案 |
