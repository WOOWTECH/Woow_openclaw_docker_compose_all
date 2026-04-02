---
name: openclaw-console-testing
description: Enterprise-grade testing of the unified OpenClaw Console (Flask + ttyd)
status: active
created: 2026-04-02T03:54:45Z
---

# PRD: openclaw-console-testing

## Executive Summary

The OpenClaw Console is a newly built unified web application that merges the setup wizard and management TUI into a single Flask + ttyd deployment. Before it can be considered production-ready for enterprise deployment, it requires comprehensive multi-round testing covering all API endpoints, frontend interactions, terminal integration, edge cases, and error handling.

## Problem Statement

The console was just deployed and verified at a basic level (HTTP 200, API responses). No systematic testing has been performed. For enterprise/commercial deployment, we need verified reliability across:
- All 14 API endpoints under normal and failure conditions
- Frontend UI rendering and interactions on mobile browsers
- Terminal (ttyd) connectivity through Cloudflare tunnel
- Data integrity when editing configurations
- Graceful degradation when the gateway pod is down
- Multiple regression rounds to confirm stability

## User Stories

### US-1: API Endpoint Verification
**As** a platform operator, **I want** all management API endpoints to return correct data and handle errors gracefully, **so that** the console is reliable for day-to-day operations.

**Acceptance Criteria:**
- All 14 endpoints respond with correct HTTP status codes
- JSON responses are well-formed and contain expected fields
- Endpoints return meaningful errors when gateway pod is unavailable
- Config write endpoints correctly persist changes and are readable back

### US-2: Frontend Dashboard Functionality
**As** a platform operator using a mobile browser, **I want** the Dashboard tab to display live service status, allow model changes, and provide config editing, **so that** I can manage OpenClaw from my phone.

**Acceptance Criteria:**
- Dashboard auto-loads when gateway is running
- Status card shows health badge, node, disk, uptime
- Model selector modal opens, selects, confirms, and persists changes
- Config/env/soul editor modals open, load content, save, and verify persistence
- Plugins, channels, cron, logs cards display correct data

### US-3: Terminal Tab
**As** a platform operator, **I want** the Terminal tab to provide a working shell into the gateway container via the browser, **so that** I can run CLI commands without SSH access.

**Acceptance Criteria:**
- Terminal iframe loads ttyd from cindytech1-terminal.woowtech.io
- ttyd authentication works (admin + gateway token)
- Shell connects to the correct gateway pod
- Commands execute and output displays correctly
- Session auto-reconnects after disconnect

### US-4: Setup Wizard Flow
**As** a new user, **I want** the Setup tab to provision a fresh OpenClaw instance, **so that** I can onboard without manual K8s commands.

**Acceptance Criteria:**
- Setup form renders with all fields (credentials, AI provider, model)
- AI provider selection dynamically shows/hides API key and model fields
- Form validation rejects empty required fields
- (Functional deploy test is out of scope — only UI rendering and validation)

### US-5: Error Handling & Edge Cases
**As** a platform operator, **I want** the console to handle failures gracefully, **so that** errors don't break the UI or corrupt data.

**Acceptance Criteria:**
- API returns proper errors when gateway pod is not running
- Frontend displays "Offline" badge when status check fails
- Saving invalid JSON to config endpoint returns an error (not silent corruption)
- Restart confirmation modal prevents accidental restarts
- Theme toggle persists across page reloads

## Functional Requirements

### FR-1: Backend API Testing (14 endpoints)
| # | Endpoint | Method | Test |
|---|----------|--------|------|
| 1 | /api/detect | GET | Returns {running: true/false, pod: string} |
| 2 | /api/status | GET | Returns health, model, disk, node, started |
| 3 | /api/config | GET | Returns valid JSON matching openclaw.json |
| 4 | /api/config | POST | Partial merge persists and is readable back |
| 5 | /api/config/model | POST | Model change persists in openclaw.json |
| 6 | /api/env | GET | Returns workspace/.env content |
| 7 | /api/env | POST | Write persists and is readable back |
| 8 | /api/soul | GET | Returns SOUL.md content |
| 9 | /api/soul | POST | Write persists and is readable back |
| 10 | /api/channels | GET | Returns channel config object |
| 11 | /api/plugins | GET | Returns array of {name, size} |
| 12 | /api/cron | GET | Returns cron jobs array/object |
| 13 | /api/logs | GET | Returns gateway logs (supports ?lines=N) |
| 14 | /api/restart | POST | Triggers rollout restart, returns {ok, message} |
| 15 | /setup | POST | Setup wizard endpoint (UI validation only) |
| 16 | /setup/status | GET | Returns setup progress state |

### FR-2: Frontend UI Testing
- Tab navigation (Dashboard / Setup / Terminal)
- Auto-detect routing (gateway running → Dashboard, not running → Setup)
- All modal dialogs (model selector, config editor, restart confirmation)
- Theme toggle (dark ↔ light)
- Responsive layout on mobile viewport

### FR-3: Terminal Integration Testing
- ttyd iframe loading via Cloudflare tunnel
- Authentication flow
- Shell command execution
- Session reconnection

### FR-4: Data Integrity Testing
- Write config → read back → verify match
- Write .env → read back → verify match
- Change model → read status → verify new model
- Concurrent reads don't interfere with writes

## Non-Functional Requirements

- All API responses must complete within 15 seconds
- Frontend must render correctly on mobile Chrome (user's primary browser)
- No JavaScript console errors on any page
- All API endpoints must return proper Content-Type: application/json
- No sensitive data leaked in error messages

## Success Criteria

1. **All 16 API endpoints** pass positive and negative test cases
2. **Zero critical bugs** found in final regression round
3. **Data integrity** verified: write → read round-trip for config, env, soul
4. **Terminal** connects and executes commands successfully
5. **Dashboard** displays all cards with correct data
6. **Error handling** gracefully degrades when gateway is offline

## Constraints & Assumptions

- Testing is done via curl (API), browser fetch simulation, and direct HTTPS endpoint access
- No Selenium/Playwright — tests are CLI-driven and API-driven
- The gateway pod is assumed running during positive tests
- We do NOT test the actual setup wizard deployment pipeline (would disrupt live instance)
- Mobile browser testing is verified through responsive API/endpoint testing, not physical device automation

## Out of Scope

- Load/performance testing (not applicable for single-tenant management console)
- Security penetration testing
- Actual setup wizard deployment (would destroy/recreate the live instance)
- Cross-browser testing beyond Chrome
- Automated CI/CD test pipeline setup

## Dependencies

- OpenClaw gateway pod must be running (currently: openclaw-gateway-5865b5d475-8h8x6)
- OpenClaw console pod must be running (currently: openclaw-console deployment)
- Cloudflare tunnel must route both subdomains
- kubectl access from console pod to gateway pod (RBAC configured)
