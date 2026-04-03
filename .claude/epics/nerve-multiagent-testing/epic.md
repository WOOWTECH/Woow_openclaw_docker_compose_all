---
name: nerve-multiagent-testing
status: in-progress
created: 2026-04-03T00:00:00Z
updated: 2026-04-03T00:00:00Z
progress: 0%
prd: .claude/prds/nerve-multiagent-testing.md
---

# Epic: Nerve Multi-Agent Enterprise Testing

## Overview
Execute 6 rounds of enterprise-grade testing covering Agent CRUD, CLI↔GUI sync, cross-module interaction, edge cases, persistence, and stress testing.

## Technical Approach
- Playwright headless Chromium for browser automation
- kubectl exec + curl for backend API tests
- Pod restart for persistence validation
- Screenshots archived in /tmp/ for audit trail

## Tasks

### Task 1: Round 1 — Smoke Test (API + Sidebar)
- Verify gateway health
- Verify Nerve health
- Verify /api/gateway/models returns MiniMax-M2.7
- Verify all 9 agents visible in Nerve sidebar
- Verify /api/files/tree works for main and non-main agents

### Task 2: Round 2 — Agent CRUD via GUI
- Create new agent "test-crud" via Nerve GUI
- Verify it appears in sidebar + CLI
- Send message to new agent, verify response
- Verify agent identity in response label

### Task 3: Round 3 — Cross-Agent Conversation
- Switch to each of 5 agents (odoo-erp, ha-assistant, sys-admin, translator, coder)
- Send role-specific query to each
- Verify response matches agent role
- Measure response times

### Task 4: Round 4 — Edge Cases
- Create agent with special characters in name
- Create agent with duplicate name
- Send concurrent messages to 2 agents
- Send very long message (>1000 chars)

### Task 5: Round 5 — Persistence
- Record agent count + session count before restart
- kubectl rollout restart
- Wait for 2/2 Ready
- Record agent count + session count after restart
- Verify delta = 0

### Task 6: Round 6 — Stress Test
- Rapid-switch between 5 agents (2s intervals)
- Send 3 messages per agent without waiting for response
- Verify no crashes, all responses eventually arrive
