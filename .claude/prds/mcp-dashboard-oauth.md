---
name: mcp-dashboard-oauth
description: Enable OAuth authentication for remote MCP servers directly from the Hermes WebUI Dashboard
status: active
created: 2026-07-23T03:59:57Z
---

# PRD: mcp-dashboard-oauth

## Executive Summary

Hermes Agent 已有完整的 MCP OAuth 2.1 + PKCE 實作（~2600 行），但目前只能在 CLI 互動環境下完成 OAuth 認證。在 K3s Pod 部署場景中，使用者透過 WebUI Dashboard 無法連接需要 OAuth 的遠端 MCP server（如 Higgsfield、Figma MCP），因為 OAuth redirect_uri 固定指向 Pod 的 localhost，使用者瀏覽器無法到達。

本 PRD 定義一個 **WebUI Proxy OAuth Callback** 機制，讓使用者可以直接在 Dashboard 上點擊「授權登入」完成 OAuth 認證，不需要 CLI 存取。

## Problem Statement

### 當前狀態
- Hermes Agent 部署在 K3s Pod 中，使用者透過 Cloudflare Tunnel 存取 WebUI Dashboard
- OAuth callback server 綁定在 `127.0.0.1:<ephemeral-port>` (Pod localhost)
- `_redirect_handler()` 嘗試在 Pod 內開啟瀏覽器（失敗）
- Dashboard 的 MCP Panel 只有 server list + tools browser，沒有 OAuth 登入 UI
- 後端已有 `POST /api/mcp/servers/{name}/auth` 端點，但它阻塞 315 秒等待 localhost callback，在遠端部署下永遠超時

### 影響
- 所有需要 OAuth 認證的 MCP server（Higgsfield、Figma、GitHub MCP、Sentry MCP 等）無法從 Dashboard 設定
- 團隊必須有 kubectl exec 權限或直接 SSH 到 Pod 才能用 `hermes mcp login` 完成認證
- 大幅限制了 MCP 生態系的可用性

### 根因
1. **redirect_uri 指向 Pod localhost** — `mcp_oauth.py` 第 849 行 `_build_client_metadata()` 固定使用 `http://127.0.0.1:{port}/callback`
2. **callback server 綁定 localhost** — 第 655 行 `HTTPServer(("127.0.0.1", _oauth_port), handler_cls)` 只監聽 loopback
3. **auth API 不回傳 authorization_url** — Dashboard 前端拿不到 OAuth 授權頁面 URL
4. **前端沒有 OAuth 流程 UI** — 沒有「授權登入」按鈕，沒有 popup 處理邏輯

## User Stories

### US-1: Dashboard OAuth 認證
**As a** Hermes WebUI 使用者
**I want to** 在 Dashboard 的 MCP Servers 設定中點擊「授權登入」來連接 Higgsfield MCP
**So that** 我不需要 CLI 存取權限就能使用需要 OAuth 的 MCP server

**Acceptance Criteria:**
- Dashboard MCP Panel 中，HTTP transport 的 server 顯示「🔐 授權登入」按鈕
- 點擊按鈕後開啟 popup 視窗跳轉到 OAuth provider 的認證頁面
- 使用者在 popup 中完成登入/授權
- OAuth provider redirect 回 Hermes 公開 URL 的 callback 路由
- popup 自動關閉，Dashboard 顯示連線成功 toast
- Server list 自動刷新，顯示 tool 數量

### US-2: OAuth 重新認證
**As a** Hermes WebUI 使用者
**I want to** 在 token 過期或失效時重新授權
**So that** 我能恢復 MCP server 的連線

**Acceptance Criteria:**
- 已認證但 token 失效的 server 顯示「⚠ 重新授權」按鈕
- 重新授權流程和首次認證流程一致
- 舊 token 在新授權成功後才被替換（snapshot/restore 機制）

### US-3: 新增需要 OAuth 的 MCP server
**As a** Hermes WebUI 使用者
**I want to** 從 Dashboard 新增一個需要 OAuth 的 MCP server（輸入 URL）
**So that** 我能自行擴展可用的 MCP 工具

**Acceptance Criteria:**
- 新增 HTTP server 後，自動偵測是否需要 OAuth（probe 回傳 401 + WWW-Authenticate）
- 如果需要 OAuth，自動觸發授權流程
- 使用者不需要手動設定 `auth: oauth`

## Functional Requirements

### FR-1: Agent 後端 — OAuth Dashboard Mode

**FR-1.1**: `mcp_oauth.py` 新增 Dashboard 模式
- 當 `HERMES_BASE_URL` 環境變數存在時，redirect_uri 使用公開 URL: `{HERMES_BASE_URL}/api/mcp/oauth/callback/{server_name}`
- 否則維持原本 localhost callback（CLI 相容）
- `_redirect_handler` 在 Dashboard 模式下不開瀏覽器，而是把 `authorization_url` 存入 `asyncio.Event` / shared state 讓 API 端點可以取得

**FR-1.2**: `web_server.py` 修改 auth 端點
- `POST /api/mcp/servers/{name}/auth` 改為非阻塞：
  1. 啟動 OAuth discovery + 取得 authorization_url
  2. 立即回傳 `{"authorization_url": "https://...", "state": "..."}`
  3. 前端自行開 popup

**FR-1.3**: `web_server.py` 新增 callback 端點
- `GET /api/mcp/oauth/callback/{server_name}?code=...&state=...`
  1. 接收 OAuth authorization code
  2. 把 code 交給 OAuthClientProvider 交換 token
  3. 持久化 token 到 `mcp-tokens/`
  4. 回傳 HTML 頁面：「✅ 授權成功，此視窗將自動關閉」+ `window.close()` script

**FR-1.4**: `web_server.py` 新增 status 端點
- `GET /api/mcp/servers/{name}/auth/status`
  1. 檢查 `mcp-tokens/{name}.json` 是否存在且有效
  2. 回傳 `{"authenticated": bool, "tools_count": int, "expires_at": str | null}`

### FR-2: WebUI 前端 — OAuth UI

**FR-2.1**: MCP Server Row 新增 OAuth 按鈕
- HTTP transport server 且未認證或認證失效 → 顯示「🔐 授權登入」
- 已認證但 status 異常 → 顯示「⚠ 重新授權」
- 已認證且 active → 顯示綠色 badge，不顯示按鈕

**FR-2.2**: OAuth Popup 流程
```javascript
async function mcpOAuthLogin(serverName) {
  const res = await api(`/api/mcp/servers/${serverName}/auth`, {method:'POST'});
  if (!res.authorization_url) { showToast(res.error, 'error'); return; }
  const popup = window.open(res.authorization_url, 'mcp_oauth', 'width=600,height=700');
  const poll = setInterval(async () => {
    if (popup.closed) {
      clearInterval(poll);
      const status = await api(`/api/mcp/servers/${serverName}/auth/status`);
      if (status.authenticated) {
        showToast(t('mcp_oauth_success', serverName), 'success');
        loadMcpServers();
      } else {
        showToast(t('mcp_oauth_failed'), 'error');
      }
    }
  }, 1000);
}
```

**FR-2.3**: i18n 翻譯 key
- `mcp_oauth_login`: "授權登入" / "Authorize"
- `mcp_oauth_reauth`: "重新授權" / "Re-authorize"
- `mcp_oauth_success`: "{name} 已連接" / "{name} connected"
- `mcp_oauth_failed`: "授權失敗" / "Authorization failed"
- `mcp_oauth_popup_blocked`: "請允許彈出視窗" / "Please allow popups"

### FR-3: OAuth Auto-Detection

**FR-3.1**: 新增 HTTP server 時，agent probe 偵測 401 + `WWW-Authenticate: Bearer` 回應
**FR-3.2**: 如果偵測到需要 OAuth，自動設定 `auth: oauth` 並觸發授權流程
**FR-3.3**: 如果偵測到 401 但沒有標準 OAuth metadata，顯示提示讓使用者手動設定 `headers`

## Non-Functional Requirements

### NFR-1: 安全性
- OAuth state 參數必須使用 CSRF-safe random token
- Callback 端點驗證 state 參數一致性
- Token 存儲維持現有 `0o600` 檔案權限
- 不在 API response 中暴露 access_token/refresh_token

### NFR-2: 相容性
- 維持現有 CLI `hermes mcp login` 流程不變
- 維持現有 stdio transport MCP server 不受影響
- 支援 MCP SDK 1.26.0 的 OAuthClientProvider 介面

### NFR-3: 可靠性
- OAuth flow 超時 300 秒（與現有一致）
- Token refresh 失敗時觸發重新授權提示
- snapshot/restore 機制保護現有 token

### NFR-4: UX
- 整個流程在 15 秒內完成（不含使用者在 OAuth provider 的操作時間）
- popup 被瀏覽器阻擋時顯示明確提示
- 支援多個 MCP server 同時進行 OAuth（不同 popup）

## Success Criteria

1. **從 Dashboard 成功連接 Higgsfield MCP** — 點擊授權 → Higgsfield OAuth 頁面 → 授權 → 回到 Dashboard → 顯示 47 tools
2. **Token 自動刷新** — 連接成功後 access_token 過期時自動 refresh，不需使用者操作
3. **CLI 流程不受影響** — `hermes mcp login Higgsfield` 在本地開發環境仍然正常運作
4. **重新授權正常** — token 失效後點擊「重新授權」能完成流程

## Constraints & Assumptions

### Constraints
- Hermes Agent image 是 `nousresearch/hermes-agent`，我們修改的是 Agent 原始碼 (`/opt/hermes/`)
- WebUI 是 `ghcr.io/nesquena/hermes-webui`，前端靜態檔在 `/app/static/`
- MCP SDK 版本固定在 1.26.0（不升級）
- OAuth provider 必須支援 RFC 7591 Dynamic Client Registration 或提供預註冊 client_id

### Assumptions
- `HERMES_BASE_URL` 環境變數已在 K8s ConfigMap 中設定（目前已有 `HERMES_BASE_URL` 在 configmap）
- Cloudflare Tunnel 允許 OAuth callback 的 GET 請求通過
- 使用者瀏覽器允許 popup（或能夠解除阻擋）
- OAuth provider（Higgsfield）的 authorization server 接受非 localhost 的 redirect_uri

## Out of Scope

1. **Device Code Flow (RFC 8628)** — MCP SDK 1.26.0 不支援，Higgsfield 的 device auth server 也未上線
2. **Client Credentials Flow** — 需要 provider 預先註冊 service account，屬於 M2M 場景
3. **WebUI MCP server CRUD** — Dashboard 的 server 新增/刪除功能（已有 API，但前端標記為 read-only）
4. **MCP SDK 升級** — 不在此 PRD 範圍內
5. **多使用者 token 隔離** — 目前 Hermes 是單一密碼登入，不區分使用者身份

## Dependencies

### 內部依賴
- `HERMES_BASE_URL` 環境變數（K8s ConfigMap `hermes-config` 中的 `HERMES_BASE_URL`）
- Agent API server 的 routing framework (FastAPI/Starlette)
- WebUI 前端的 `panels.js` MCP Panel

### 外部依賴
- MCP Python SDK 1.26.0 (`OAuthClientProvider`, `OAuthClientMetadata`, `HermesTokenStorage`)
- OAuth 2.1 provider（Higgsfield: `https://mcp.higgsfield.ai`）
- Cloudflare Tunnel（callback URL 必須能被外部瀏覽器存取）

## Architecture Reference

### 修改檔案清單

| 檔案位置 (Pod 內) | 修改類型 | 說明 |
|-------------------|---------|------|
| `/opt/hermes/tools/mcp_oauth.py` | 修改 | Dashboard mode redirect_uri + shared state for auth URL |
| `/opt/hermes/hermes_cli/web_server.py` | 修改+新增 | 修改 auth API + 新增 callback/status 端點 |
| `/app/static/panels.js` (WebUI) | 修改 | OAuth 按鈕 + popup 邏輯 |
| `/app/static/style.css` (WebUI) | 修改 | OAuth 按鈕樣式 |
| `/app/static/i18n.js` (WebUI) | 修改 | 翻譯 key |

### 完整 OAuth 流程

```
Dashboard (瀏覽器)              Agent API (Pod)              OAuth Provider
     │                              │                           │
  ① POST /api/mcp/servers/{name}/auth                          │
     │──────────────────────────────>│                           │
     │                              │── GET /.well-known/       │
     │                              │   oauth-protected-resource│
     │                              │──────────────────────────>│
     │                              │<──────────────────────────│
     │                              │                           │
     │                              │── POST /oauth2/register   │
     │                              │   (Dynamic Registration)  │
     │                              │──────────────────────────>│
     │                              │<── client_id ─────────────│
     │                              │                           │
     │                              │── Build authorization_url │
     │  {"authorization_url": "..."} │   with PKCE code_challenge│
     │<──────────────────────────────│                           │
     │                              │                           │
  ② window.open(authorization_url)  │                           │
     │══════════════════════════════════════════════════════════>│
     │                              │                     (使用者登入)
     │                              │                           │
  ③ Redirect to:                    │                           │
     │  {HERMES_BASE_URL}/api/mcp/oauth/callback/{name}        │
     │              ?code=xxx&state=yyy                         │
     │──────────────────────────────>│                           │
     │                              │── POST /oauth2/token      │
     │                              │   code + code_verifier    │
     │                              │──────────────────────────>│
     │                              │<── access_token ──────────│
     │                              │                           │
     │  HTML: "✅ 授權成功"          │── Save to mcp-tokens/    │
     │<──────────────────────────────│                           │
     │  (popup 自動關閉)             │                           │
     │                              │                           │
  ④ GET /api/mcp/servers/{name}/auth/status                    │
     │──────────────────────────────>│                           │
     │  {"authenticated": true}      │                           │
     │<──────────────────────────────│                           │
     │                              │                           │
  ⑤ loadMcpServers() 刷新列表       │── Connect to MCP server  │
     │                              │──────────────────────────>│
     │                              │<── tools/list ────────────│
```
