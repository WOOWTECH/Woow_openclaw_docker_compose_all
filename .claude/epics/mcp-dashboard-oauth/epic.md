---
name: mcp-dashboard-oauth
status: active
created: 2026-07-23T03:59:57Z
updated: 2026-07-23T05:38:20Z
progress: 0%
prd: .claude/prds/mcp-dashboard-oauth.md
github: https://github.com/WOOWTECH/Woow_hermes_agent_docker_compose_all/issues/1
---

# Epic: mcp-dashboard-oauth

## Overview

為 Hermes Agent 實作 WebUI Proxy OAuth Callback 機制，讓使用者可以從 Dashboard 直接完成 MCP server 的 OAuth 認證，不需要 CLI 存取。

核心改動：將 OAuth redirect_uri 從 Pod localhost 改為 Hermes 的公開 URL，新增 callback/status API 端點，並在前端加入 OAuth 按鈕和 popup 流程。

## Architecture Decisions

### AD-1: Redirect URI 策略 — 基於 HERMES_BASE_URL 環境變數

**選擇**: 當 `HERMES_BASE_URL` 存在時，使用 `{HERMES_BASE_URL}/api/mcp/oauth/callback/{server_name}` 作為 redirect_uri；否則維持 localhost。

**理由**:
- 最小改動原則 — CLI 流程完全不受影響
- `HERMES_BASE_URL` 已存在於 K8s ConfigMap（`hermes-config`），不需新增環境變數
- 與 MCP OAuth 2.1 規範完全相容

### AD-2: 前後端通訊 — Popup + Polling 模式

**選擇**: 前端開 popup 到 OAuth provider，callback 回到 Agent API，前端輪詢 auth status。

**替代方案考慮**:
- WebSocket 推送 — 增加複雜度，popup 場景不需要
- iframe — 多數 OAuth provider 阻擋 iframe 嵌入
- 同頁 redirect — 會中斷使用者的 Dashboard 操作

### AD-3: Authorization URL 取得方式 — 兩階段 Auth API

**選擇**: `POST /auth` 不再阻塞，而是：
1. 第一階段：Agent 執行 OAuth discovery + dynamic registration → 回傳 `authorization_url`
2. 使用者在 popup 完成授權 → callback 回到 `GET /api/mcp/oauth/callback/{name}`
3. Agent 在 callback handler 中交換 code → token

**理由**: 原本的阻塞設計（等 315 秒）在 Dashboard 場景下 UX 極差且必定超時。

### AD-4: State 管理 — 進程內 dict + 磁碟 token

**選擇**: 使用 `_pending_oauth_flows: dict[str, OAuthFlowState]` 儲存進行中的 OAuth flow 狀態（code_verifier、state 等），token 完成後寫入磁碟 `mcp-tokens/`。

**理由**:
- OAuth flow 是短暫的（< 5 分鐘），不需持久化
- 與現有 `HermesTokenStorage` 磁碟快取完全相容
- 與 `MCPOAuthManager` singleton 模式一致

## Technical Approach

### Backend Changes (Agent Python)

#### 1. `mcp_oauth.py` — Dashboard Mode

新增函式 `build_dashboard_oauth_flow()`:
- 接收 `server_name`, `server_url`, `base_url` (from HERMES_BASE_URL)
- 構建 `OAuthClientMetadata` with `redirect_uris = ["{base_url}/api/mcp/oauth/callback/{server_name}"]`
- 執行 OAuth discovery (PRM + ASM metadata)
- 執行 dynamic client registration (RFC 7591)
- 生成 PKCE code_verifier + code_challenge
- 構建 authorization_url
- 回傳 `OAuthFlowState(authorization_url, code_verifier, state, client_info, metadata)`

修改 `_build_client_metadata()`:
- 新增 `external_redirect_uri` 參數（可選）
- 如果提供，使用外部 URI 而非 localhost

#### 2. `web_server.py` — API 端點

**修改 `POST /api/mcp/servers/{name}/auth`**:
```python
# Before: 阻塞 315 秒等 localhost callback
# After:
# 1. 檢查 HERMES_BASE_URL
# 2. 如果有 → Dashboard mode: build flow, return authorization_url
# 3. 如果沒有 → 維持原本阻塞流程 (CLI backward compat)
```

**新增 `GET /api/mcp/oauth/callback/{server_name}`**:
```python
# 1. 從 _pending_oauth_flows 取出 flow state
# 2. 驗證 state 參數
# 3. 使用 code + code_verifier 交換 token
# 4. 寫入 HermesTokenStorage
# 5. 回傳 HTML: "授權成功" + window.close()
```

**新增 `GET /api/mcp/servers/{name}/auth/status`**:
```python
# 1. 檢查 mcp-tokens/{name}.json 是否存在
# 2. 檢查 token 是否有效 (expires_at)
# 3. 回傳 {authenticated, tools_count, expires_at}
```

### Frontend Changes (WebUI)

#### 3. `panels.js` — OAuth UI

在 `loadMcpServers()` 的 server row rendering 中：
- HTTP transport + 未認證 → 加「🔐 授權登入」按鈕
- HTTP transport + 認證失效 → 加「⚠ 重新授權」按鈕
- 按鈕 onclick → `mcpOAuthLogin(serverName)`

新增 `mcpOAuthLogin()` 函式（~30 行）:
- POST auth API → 取得 authorization_url
- window.open popup
- setInterval 輪詢 auth/status
- popup 關閉後檢查結果 → toast + refresh

#### 4. `style.css` — 按鈕樣式

```css
.mcp-oauth-btn { /* 主要授權按鈕 */ }
.mcp-oauth-btn-reauth { /* 重新授權按鈕 (warning 色調) */ }
```

#### 5. `i18n.js` — 翻譯 key

5 個新 key (中/英)。

## Task Breakdown Preview

| # | Task | 檔案 | 可並行 | 依賴 |
|---|------|------|--------|------|
| 1 | Agent: Dashboard OAuth flow builder | mcp_oauth.py | ✅ | - |
| 2 | Agent: Auth API 改為非阻塞 + callback/status 端點 | web_server.py | ❌ | Task 1 |
| 3 | WebUI: OAuth 按鈕 + popup 邏輯 | panels.js, style.css, i18n.js | ✅ | - |
| 4 | 整合測試：Dashboard → Higgsfield OAuth 全流程 | K8s 部署 | ❌ | Task 2, 3 |
| 5 | 文檔更新 + golden-config 範例 | docs/, config/ | ✅ | Task 4 |

Task 1 和 Task 3 可以完全並行開發。
Task 2 依賴 Task 1 的 `OAuthFlowState` 資料結構。
Task 4 是整合測試，需要 Task 2 + Task 3 都完成。

## Dependencies

- MCP Python SDK 1.26.0 (已安裝在 Agent image)
- `HERMES_BASE_URL` 環境變數 (已在 K8s ConfigMap)
- Cloudflare Tunnel 允許 `/api/mcp/oauth/callback/*` 路由通過
- Higgsfield OAuth server (`https://mcp.higgsfield.ai`) 接受非 localhost redirect_uri

## Success Criteria (Technical)

1. `POST /api/mcp/servers/Higgsfield/auth` 回傳 `authorization_url` (< 5 秒)
2. OAuth callback 成功交換 token 並持久化到 `mcp-tokens/Higgsfield.json`
3. `GET /api/mcp/servers/Higgsfield/auth/status` 回傳 `{"authenticated": true, "tools_count": 47}`
4. CLI `hermes mcp login` 流程不受影響 (regression test)
5. Token refresh 在 access_token 過期後自動完成

## Estimated Effort

| Task | 預估行數 | 複雜度 |
|------|---------|--------|
| mcp_oauth.py 修改 | ~60 行 | Medium |
| web_server.py 修改+新增 | ~120 行 | Medium |
| panels.js 修改 | ~50 行 | Low |
| style.css + i18n.js | ~15 行 | Low |
| 測試 + 部署 | - | Medium |
| **總計** | **~245 行** | **Medium** |

## Tasks Created

- [ ] 001.md - Agent: Dashboard OAuth Flow Builder (parallel: true)
- [ ] 002.md - Agent: Auth/Callback/Status API Endpoints (parallel: false, depends: 001)
- [ ] 003.md - WebUI: OAuth Button + Popup Flow (parallel: true)
- [ ] 004.md - Integration Test: Dashboard → Higgsfield OAuth E2E (parallel: false, depends: 002, 003)
- [ ] 005.md - Docs: Update golden-config + user manual (parallel: true, depends: 004)

Total tasks: 5
Parallel tasks: 3 (001, 003, 005)
Sequential tasks: 2 (002, 004)
Estimated total effort: 12 hours

### Parallelization Graph

```
    ┌─── 001 (Agent OAuth Flow) ───┐
    │                              ├──→ 002 (API Endpoints) ──┐
    │   ┌─── 003 (WebUI Frontend) ─┘                         ├──→ 004 (E2E Test) ──→ 005 (Docs)
    │   │                                                     │
    └───┘  ← 可並行                                           │
```
