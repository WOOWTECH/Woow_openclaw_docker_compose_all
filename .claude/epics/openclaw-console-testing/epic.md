---
name: openclaw-console-testing
status: in-progress
created: 2026-04-02T03:55:38Z
updated: 2026-04-02T03:55:38Z
progress: 0%
prd: .claude/prds/openclaw-console-testing.md
github: (will be set on sync)
---

# Epic: openclaw-console-testing

## Overview

Enterprise-grade comprehensive testing of the OpenClaw Console — a unified Flask + ttyd web app serving as both setup wizard and management dashboard. Tests cover all 16 API endpoints, frontend UI interactions, terminal integration, data integrity round-trips, error handling, and multi-round regression.

## Architecture Decisions

- **Test runner**: Shell scripts using `curl` for API tests, direct HTTPS calls for frontend verification
- **No external test framework**: Tests are self-contained bash scripts that output PASS/FAIL
- **Test against live deployment**: All tests hit the production endpoint (https://cindytech1-tui.woowtech.io)
- **Non-destructive**: Tests that write data restore original values after testing
- **Multiple rounds**: Each test task runs its full suite, regression tasks re-run all previous tests

## Technical Approach

### Test Categories
1. **API Positive Tests** — All endpoints return expected data
2. **API Write/Read Round-trips** — Config, env, soul write → read → verify
3. **API Negative Tests** — Error handling when gateway is unavailable or input is invalid
4. **Frontend Rendering** — HTML page loads, tabs work, modals render
5. **Terminal Integration** — ttyd endpoint accessible, auth works
6. **Regression** — Re-run all tests to confirm stability

### Test Execution Pattern
Each test uses curl with JSON output parsing:
```bash
# Positive test pattern
RESULT=$(curl -s https://cindytech1-tui.woowtech.io/api/status)
HEALTH=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('health',''))")
[ "$HEALTH" = "200" ] && echo "PASS" || echo "FAIL"
```

## Task Breakdown Preview

| # | Task | Parallel | Description |
|---|------|----------|-------------|
| 1 | API Positive Tests (Round 1) | Yes | All 16 endpoints return correct data |
| 2 | Data Integrity Round-trips | Yes | Write → read → verify for config, env, soul, model |
| 3 | Frontend & Terminal Tests | Yes | Page rendering, tabs, modals, ttyd endpoint |
| 4 | Error Handling & Edge Cases | No (after 1-3) | Invalid inputs, missing pod scenarios |
| 5 | Regression Round 2 | No (after 4) | Re-run all tests from tasks 1-3 |
| 6 | Final Report | No (after 5) | Summarize results, document any bugs fixed |

## Dependencies

- Console pod running and accessible via Cloudflare tunnel
- Gateway pod running for positive tests
- kubectl RBAC permissions working

## Success Criteria (Technical)

- 100% PASS rate on all positive API tests
- Write/read round-trips return identical data
- No HTTP 500 errors during normal operation
- Terminal endpoint returns 401 (auth required)
- All bugs found are fixed and verified in regression

## Estimated Effort

6 tasks, ~3 can run in parallel. Total: ~30 minutes of test execution.
