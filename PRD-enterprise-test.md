# PRD: OpenClaw K3s Enterprise Deployment Validation

## Overview
Comprehensive end-to-end testing of the OpenClaw K3s deployment to validate commercial enterprise-grade readiness. Tests cover all deployed modules, cross-module interactions, edge cases, and real-world scenarios.

## Deployment Under Test
- **Platform**: K3s single-node cluster (woowtechcluster1)
- **Namespace**: `openclaw-tenant-1`
- **Pod**: `openclaw-gateway` (2/2 containers: openclaw-gateway + nerve sidecar)
- **Gateway Version**: OpenClaw v2026.3.31
- **Model**: MiniMax/MiniMax-M2.7 (default)
- **Plugins**: memory-lancedb-pro v1.1.0-beta.9, openclaw-homeassistant
- **Channels**: Telegram (open), WhatsApp (pairing), LINE (error), Web (Nerve)
- **Supporting Services**: Ollama (nomic-embed-text), PostgreSQL, Cloudflare Tunnel

## Test Rounds

### Round 1: Backend API Health & Individual Module Validation
| # | Test | Method | Expected |
|---|------|--------|----------|
| 1.1 | Gateway API health | HTTP GET /api/health | 200 OK, version info |
| 1.2 | Nerve health | HTTP GET nerve:3080/ | 200 OK |
| 1.3 | Exec tool (simple) | API: run `echo hello` | Output: "hello" |
| 1.4 | Exec tool (complex pipes) | API: `ls /tmp \| wc -l` | Numeric output |
| 1.5 | HA plugin status | API: ha_status tool | HA version returned |
| 1.6 | HA sensor list | API: ha_sensor_list | Sensor data array |
| 1.7 | Memory store | API: memory_store | Success ack |
| 1.8 | Memory recall | API: memory_recall | Stored data returned |
| 1.9 | Sessions list | API: sessions_list | Session array |
| 1.10 | Web fetch | API: web_fetch URL | Content returned |
| 1.11 | Cron schedule | API: cron tool | Schedule created |
| 1.12 | Plugin list check | Exec: ls extensions | Both plugins present |

### Round 2: Browser Cross-Module Interaction Tests (Playwright)
| # | Test | Scenario | Expected |
|---|------|----------|----------|
| 2.1 | HA + Memory | "記住：客廳燈是 light.living_room，然後用 ha_light_list 確認" | Memory stored + HA tool used |
| 2.2 | Exec + Read | "讀取 /etc/hostname 的內容並告訴我" | File content returned |
| 2.3 | Multi-tool chain | "查詢HA所有感測器，然後把溫度類的存到記憶裡" | HA query + memory store |
| 2.4 | Session spawn | "建立一個子會話來查詢HA燈光狀態" | Session created + result |
| 2.5 | Web + Memory | "搜尋 OpenAI 最新消息，記住重點" | Web fetch + memory store |

### Round 3: Edge Cases & Error Handling
| # | Test | Scenario | Expected |
|---|------|----------|----------|
| 3.1 | Invalid HA entity | Query non-existent entity | Graceful error message |
| 3.2 | Large output handling | List all HA entities | Truncation/pagination works |
| 3.3 | Concurrent messages | Send 2 messages rapidly | Both processed without crash |
| 3.4 | Empty memory recall | Recall non-existent topic | Empty result, no error |
| 3.5 | Special characters | Message with emoji + unicode | Processed correctly |

### Round 4: End-to-End Real-World Scenarios
| # | Test | Scenario | Expected |
|---|------|----------|----------|
| 4.1 | Smart home morning routine | "幫我設計早上起床的自動化流程：開客廳燈、檢查溫度、報告天氣" | Multi-step plan with HA tools |
| 4.2 | Device status dashboard | "給我一份完整的智慧家庭設備狀態報告" | Comprehensive HA status report |
| 4.3 | Memory-augmented conversation | Multi-turn: store preferences → recall → act on them | Context preserved across turns |
| 4.4 | System administration | "檢查系統健康狀態：磁碟空間、記憶體使用、運行中的程序" | Exec tool returns system info |

### Round 5: Extended Module Coverage
| # | Test | Category | Method | Expected |
|---|------|----------|--------|----------|
| 5.1 | Odoo connectivity | Odoo | exec: xmlrpc version | Server version returned |
| 5.2 | Odoo auth + read | Odoo | exec: xmlrpc res.partner | Customer names returned |
| 5.3 | Odoo product categories | Odoo | exec: xmlrpc product.category | Category list returned |
| 5.4 | GOG token check | Google | exec: grep .env | GOG env vars present |
| 5.5 | GOG API test | Google | exec: curl userinfo | API response (valid/expired) |
| 5.6 | Cron list jobs | Cron | exec: cat jobs.json | 2 active jobs shown |
| 5.7 | Cron run history | Cron | exec: ls runs/ | Execution records |
| 5.8 | Sessions list | Sessions | sessions_list tool | Active sessions counted |
| 5.9 | Sessions spawn | Sessions | sessions_spawn tool | Sub-session created |
| 5.10 | Browser tool | Browser | browser tool → Odoo URL | Page rendered |
| 5.11 | Telegram delivery | Telegram | message tool → Telegram | Message delivered |
| 5.12 | TTS generation | Media | tts tool | Audio generated |
| 5.13 | PVC persistence | Persistence | exec: check .env + extensions | Data intact |

## Success Criteria
- All Round 1 tests: 100% pass rate
- All Round 2 tests: ≥80% pass rate (cross-module may have timing issues)
- All Round 3 tests: 100% graceful handling (no crashes)
- All Round 4 tests: ≥80% functional completion
- All Round 5 tests: ≥80% pass rate (external services may be unavailable)
- No pod restarts during testing
- No OOM kills or resource exhaustion
- All screenshots captured for audit trail

## Test Infrastructure
- Backend API: `kubectl exec` + gateway REST API on port 18789
- Browser: Playwright headless Chromium via Nerve WebGUI
- Screenshots: `/tmp/enterprise-test-*.png`
- Logs: `kubectl logs` post-test analysis
