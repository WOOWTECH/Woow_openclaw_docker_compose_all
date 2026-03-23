---
name: deploy-optimize-v2
status: backlog
created: 2026-03-22T02:30:43Z
progress: 0%
prd: .claude/prds/deploy-optimize-v2.md
github: (will be set on sync)
---

# Epic: deploy-optimize-v2

## Overview

Harden the OpenClaw K3s PaaS deployment pipeline and runtime stability. This epic tackles five concrete issues surfaced during the first production deployment: setup wizard redirect stall, missing MEMORY.md, noisy event-gap warnings, zero cron jobs, and Cloudflare Tunnel ghost connections causing 502s.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Setup wizard redirect | Client-side JS polling | No backend changes needed; wizard already serves HTML |
| MEMORY.md bootstrap | Shell script in gateway entrypoint | Consistent with existing LINE token injection pattern |
| Event gap handling | Config-level mitigation + docs | Cannot modify OpenClaw core UI; trustedProxies reduces gaps |
| Cron jobs | OpenClaw CLI `cron add` | Native OpenClaw feature; persists in gateway config |
| Cloudflared stability | preStop hook + Recreate strategy | Prevents dual connectors and ghost connections |

## Technical Approach

### Frontend Components

**Setup Wizard (`setup-wizard/templates/index.html`)**
- Add JS polling after step 6 ("Switching network routes") completes
- `setInterval` fetch to gateway URL every 3s
- On 200 response → show "系統就緒" → `window.location.href` redirect with token
- Fallback: after 30s show manual link

### Backend Services

**Gateway Startup Script (`06-openclaw-core.yaml`)**
- Add MEMORY.md creation block after LINE token injection
- Path: `/home/node/.openclaw/workspace/MEMORY.md`
- Guard: `[ -f "$FILE" ] || cat > "$FILE"`
- Content: basic agent instructions in Traditional Chinese

**Cron Jobs (via `openclaw cron add`)**
- Job 1: `*/5 * * * *` — heartbeat/health check
- Job 2: `0 * * * *` — hourly status summary
- Job 3: `0 1 * * *` — daily report (9 AM UTC+8)

### Infrastructure

**Cloudflared Deployment (`04-cloudflared.yaml`)**
- Add `lifecycle.preStop.exec.command: ["sh", "-c", "sleep 5"]`
- Set `terminationGracePeriodSeconds: 30`
- Change strategy to `Recreate` (prevent dual connectors)
- Add connection cleanup script as post-start annotation

**Gateway Config**
- Set `gateway.trustedProxies: ["10.42.0.0/16"]` (pod CIDR) to reduce proxy header warnings and WebSocket disconnects

## Implementation Strategy

1. **Parallel track A** (infra): Cloudflared stability + gateway trustedProxies — touches `04-cloudflared.yaml` and `06-openclaw-core.yaml` (infra section only)
2. **Parallel track B** (bootstrap): MEMORY.md creation in gateway startup script — touches `06-openclaw-core.yaml` (startup script section)
3. **Parallel track C** (frontend): Setup wizard redirect — touches `setup-wizard/templates/index.html`
4. **Sequential**: Cron jobs — requires gateway running, done via CLI after deploy
5. **Sequential**: Validation — verify all 5 success criteria after deployment

Tracks A, B, C can run in parallel since they touch different sections/files.

## Task Breakdown Preview

1. Add cloudflared preStop hook and Recreate strategy (`04-cloudflared.yaml`)
2. Add gateway trustedProxies config (`06-openclaw-core.yaml`)
3. Add MEMORY.md bootstrap to gateway startup script (`06-openclaw-core.yaml`)
4. Add auto-redirect polling to setup wizard frontend (`index.html`)
5. Create 3 cron jobs via OpenClaw CLI
6. Deploy and validate all changes

## Dependencies

- Tasks 1-4 can run in parallel (different files/sections)
- Task 5 depends on task 2+3 (gateway must be running with new config)
- Task 6 depends on all previous tasks

## Success Criteria (Technical)

1. `curl` to domain returns 200 within 30s of cloudflared pod restart (no 502)
2. `/home/node/.openclaw/workspace/MEMORY.md` exists after gateway startup
3. Setup wizard redirects to `https://domain/#token=<token>` within 10s of gateway ready
4. `openclaw cron list` shows 3 configured jobs
5. No "event gap" warnings after setting trustedProxies (or significantly reduced)

## Estimated Effort

- Tasks 1-4: ~30 min each (parallel = 30 min total)
- Task 5: ~15 min (CLI commands)
- Task 6: ~15 min (validation)
- **Total: ~1 hour**

## Tasks Created
- [ ] 001.md - Cloudflared graceful shutdown and Recreate strategy (parallel: true)
- [ ] 002.md - Add trustedProxies and MEMORY.md bootstrap to gateway startup (parallel: true)
- [ ] 003.md - Setup wizard auto-redirect after gateway ready (parallel: true)
- [ ] 004.md - Create 3 test cron jobs via OpenClaw CLI (parallel: false, depends: 002)
- [ ] 005.md - Deploy all changes and validate success criteria (parallel: false, depends: 001-004)

Total tasks: 5
Parallel tasks: 3
Sequential tasks: 2
Estimated total effort: 2.25 hours
