# Pre-Launch Full Test Suite Design

## Overview

全自動端到端測試套件，涵蓋 OpenClaw K3s PaaS 所有功能。6 輪測試從基礎設施到進階功能逐層驗證，使用 Playwright + bash 腳本自動化，產出 HTML 測試報告。

## Architecture

```
tests/
├── pre-launch/
│   ├── run-all.sh                    # 主執行腳本（6 輪全跑）
│   ├── config.env                    # 測試環境變數
│   ├── round1-infra.sh               # 第 1 輪：基礎設施
│   ├── round2-security.sh            # 第 2 輪：安全暴力測試
│   ├── round3-llm-switch.sh          # 第 3 輪：LLM 多模型切換
│   ├── round4-channel.sh             # 第 4 輪：Channel 雙向測試
│   ├── round5-features.sh            # 第 5 輪：Cron/Skills/進階功能
│   ├── round6-resilience.sh          # 第 6 輪：穩定性恢復測試
│   ├── lib/
│   │   ├── assert.sh                 # 測試斷言函式庫
│   │   ├── line-webhook.sh           # LINE webhook 模擬工具
│   │   └── report.sh                 # HTML 報告產生器
│   └── playwright/
│       ├── playwright.config.mjs     # Playwright 配置
│       ├── gui-login.spec.mjs        # GUI 登入測試
│       ├── gui-channels.spec.mjs     # GUI channel 設定測試
│       ├── gui-cron.spec.mjs         # GUI cron 管理測試
│       └── gui-llm-switch.spec.mjs   # GUI LLM 切換測試
```

## Test Configuration

```bash
# config.env
DOMAIN="cindytech1-openclaw.woowtech.io"
GATEWAY_TOKEN="YOUR_GATEWAY_TOKEN"
NAMESPACE="openclaw-tenant-1"

# LINE
LINE_CHANNEL_SECRET="YOUR_LINE_CHANNEL_SECRET"
LINE_ACCESS_TOKEN="YOUR_LINE_CHANNEL_ACCESS_TOKEN"
LINE_USER_ID="YOUR_LINE_USER_ID"

# OpenRouter (multi-LLM testing)
OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY"
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"

# OpenAI (current)
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"

# Test models via OpenRouter
TEST_MODELS="openrouter/google/gemini-2.0-flash-001 openrouter/anthropic/claude-3.5-haiku openrouter/meta-llama/llama-3.1-8b-instruct openrouter/mistralai/mistral-small-3.1-24b-instruct"
```

## Round Details

### Round 1: Infrastructure Health (12 tests)

驗證所有 K8s 元件正常運行。

| # | Test | Method | Pass Criteria |
|---|------|--------|---------------|
| 1.1 | Gateway pod Running | `kubectl get pods` | STATUS=Running, READY=1/1 |
| 1.2 | DB pod Running | `kubectl get pods` | STATUS=Running |
| 1.3 | Cloudflared pod Running | `kubectl get pods` | STATUS=Running |
| 1.4 | Gateway service endpoint | `kubectl get endpoints` | Has IP:port |
| 1.5 | External HTTPS access | `curl https://domain/` ×10 | 10/10 = 200 |
| 1.6 | Cloudflare tunnel healthy | CF API `/cfd_tunnel/{id}` | status=healthy, 1 client only |
| 1.7 | DB connection | `kubectl exec -- pg_isready` | exit 0 |
| 1.8 | Gateway config valid | `kubectl exec -- cat openclaw.json` | Valid JSON, trustedProxies set |
| 1.9 | 8 workspace files exist | `kubectl exec -- ls workspace/*.md` | 8 files, all non-empty |
| 1.10 | LINE channel running | `openclaw channels status` | LINE: running |
| 1.11 | Cron scheduler active | `openclaw cron status` | enabled=true, jobs≥3 |
| 1.12 | Auth profiles configured | `cat auth-profiles.json` | openai key present |

### Round 2: Security & Stress (15 tests)

暴力和邊緣情況攻擊。

| # | Test | Method | Pass Criteria |
|---|------|--------|---------------|
| 2.1 | XSS in webhook body | POST webhook with `<script>` | 200 OK, no execution |
| 2.2 | SQL injection in webhook | POST with `'; DROP TABLE` | 200 OK, no DB impact |
| 2.3 | Invalid LINE signature | POST with wrong HMAC | 400 or 401 |
| 2.4 | Empty signature header | POST without x-line-signature | 400 |
| 2.5 | Oversized payload (1MB) | POST 1MB JSON body | 413 or handled gracefully |
| 2.6 | Malformed JSON | POST `{invalid json` | 400 |
| 2.7 | Binary data in body | POST random bytes | 400 |
| 2.8 | 50 concurrent requests | `xargs -P50 curl` | No 5xx, all responded |
| 2.9 | Rapid fire (100 req/s) | Sequential fast POSTs | No crash, rate limited or OK |
| 2.10 | Path traversal | GET `/../../../etc/passwd` | 404, no file content |
| 2.11 | CRLF injection | Header with `\r\n` | No header injection |
| 2.12 | Unicode bomb | 10KB of emoji in message | Handled, no crash |
| 2.13 | Null bytes in payload | JSON with `\x00` chars | Rejected or sanitized |
| 2.14 | Replay attack | Same webhook event twice | Idempotent handling |
| 2.15 | Wrong HTTP method | GET /line/webhook | 404 or 405 |

### Round 3: LLM Multi-Model Switch (10 tests)

透過 OpenRouter 測試多個 LLM。

| # | Test | Method | Pass Criteria |
|---|------|--------|---------------|
| 3.1 | Current GPT-4o works | Send message, check response | Valid response in session |
| 3.2 | Add OpenRouter auth profile | `openclaw config set` | Config updated |
| 3.3 | Switch to Gemini Flash | `config set agents.defaults.model` | Hot reload applied |
| 3.4 | Gemini conversation test | Send webhook, check session | Response from Gemini |
| 3.5 | Switch to Claude Haiku | `config set model` | Hot reload applied |
| 3.6 | Claude conversation test | Send webhook, check session | Response from Claude |
| 3.7 | Switch to Llama 3.1 | `config set model` | Hot reload applied |
| 3.8 | Llama conversation test | Send webhook, check session | Response from Llama |
| 3.9 | Switch back to GPT-4o | Restore original config | Hot reload applied |
| 3.10 | GPT-4o recovery test | Send webhook, check session | Original provider restored |

### Round 4: LINE Channel Bidirectional (12 tests)

完整 LINE webhook 進出測試。

| # | Test | Method | Pass Criteria |
|---|------|--------|---------------|
| 4.1 | Webhook verify (empty events) | POST signed `{"events":[]}` | 200, `{"status":"ok"}` |
| 4.2 | Single message in | POST signed message event | 200, new session entry |
| 4.3 | AI response generated | Check session log | assistant message exists |
| 4.4 | Push API reply out | LINE Push API to user | 200, sentMessages returned |
| 4.5 | Multi-turn conversation | 3 sequential webhook messages | Session has 6+ entries (3 user + 3 assistant) |
| 4.6 | Follow event | POST signed follow event | 200, handled |
| 4.7 | Empty text message | Webhook with `""` text | Handled gracefully |
| 4.8 | Max length message | Webhook with 5000 char text | Processed, response received |
| 4.9 | Emoji-only message | Webhook with `🎉🔥💯` | Processed |
| 4.10 | Image event (unsupported) | Webhook with image message type | Handled gracefully, no crash |
| 4.11 | Sticker event | Webhook with sticker type | Handled gracefully |
| 4.12 | Concurrent 5 webhooks | 5 parallel signed POSTs | All 200, no race condition |

### Round 5: Cron / Skills / Advanced Features (10 tests)

進階功能驗證。

| # | Test | Method | Pass Criteria |
|---|------|--------|---------------|
| 5.1 | List cron jobs | `openclaw cron list` | 3 jobs displayed |
| 5.2 | Manual run heartbeat | `openclaw cron run <id>` | status=ok, summary returned |
| 5.3 | Cron delivery to LINE | Check LINE Push after cron run | Message received |
| 5.4 | Add new cron job | `openclaw cron add` | Job created, 4 total |
| 5.5 | Disable cron job | `openclaw cron disable <id>` | enabled=false |
| 5.6 | Remove cron job | `openclaw cron rm <id>` | Job removed, back to 3 |
| 5.7 | web_fetch skill | Send "fetch https://example.com" | Tool call executed, content returned |
| 5.8 | Workspace file persistence | Write file, restart pod, check | File survives restart (if PVC) or recreated |
| 5.9 | Config hot-reload | Change config, no restart | `[reload]` log entry |
| 5.10 | Doctor health check | `openclaw doctor` | No critical errors |

### Round 6: Resilience & Recovery (8 tests)

穩定性和災難恢復。

| # | Test | Method | Pass Criteria |
|---|------|--------|---------------|
| 6.1 | Gateway pod kill recovery | `kubectl delete pod` | New pod ready in <120s |
| 6.2 | Service continuity | Curl during recovery | 200 within 120s of restart |
| 6.3 | Cloudflared restart | `rollout restart` | 0 ghost connections, 100% 200 |
| 6.4 | Tunnel ghost check | CF API connection count | Exactly 4 connections, 1 client |
| 6.5 | DB restart recovery | Kill DB pod, wait, test gateway | Gateway reconnects to new DB |
| 6.6 | Session preservation | Send message before restart, check after | Session data intact |
| 6.7 | Memory under load | Check RSS after 50 requests | <6GB RSS |
| 6.8 | Full test timing | Time entire test suite | All 6 rounds complete <30min |

## Playwright GUI Tests

### gui-login.spec.mjs
- Navigate to `https://domain/#token=YOUR_GATEWAY_TOKEN`
- Verify WebSocket connection established
- Dashboard loads with status cards
- No red "Gateway Error" warnings

### gui-channels.spec.mjs
- Navigate to Channels page
- Verify LINE channel shows "configured, running"
- Verify channel access token is redacted
- Verify Allow From shows `*`

### gui-cron.spec.mjs
- Navigate to Cron Jobs page
- Verify 3 jobs listed
- Click "Run" on heartbeat
- Verify status changes to "ok"
- Click "History" and verify run entries

### gui-llm-switch.spec.mjs
- Navigate to Agents/Config page
- Change model via GUI dropdown
- Verify hot-reload applied (no page refresh needed)
- Send test message via webchat
- Verify response uses new model

## Report Format

HTML report with:
- Summary: total/pass/fail/skip per round
- Timing: per-test and per-round duration
- Details: expandable test output for failures
- Saved to `tests/pre-launch/report-YYYY-MM-DD.html`

## Success Criteria

- **Pass rate**: ≥95% (allow ≤3 known-skip for non-critical)
- **Zero critical failures**: Rounds 1, 4, 6 must be 100%
- **LLM switch**: At least 3 of 4 alternative models respond correctly
- **Total time**: Complete suite runs in <30 minutes

## Dependencies

- kubectl access to `openclaw-tenant-1` namespace
- Playwright installed (`npx playwright install chromium`)
- curl, jq, openssl (for HMAC signing)
- OpenRouter API key with $18+ credits
- LINE Channel Access Token and Secret

## Constraints

- Tests run on the live production instance
- Each round cleans up after itself (restore original LLM, delete test cron jobs)
- Webhook tests use unique message IDs to avoid collision
- LLM tests use cheap/fast models to minimize cost (~$0.50 estimated total)
