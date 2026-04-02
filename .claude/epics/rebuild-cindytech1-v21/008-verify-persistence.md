---
name: Verify all data survives pod restart
status: open
created: 2026-03-23T22:18:11Z
updated: 2026-03-23T22:18:11Z
github:
depends_on: [007]
parallel: false
conflicts_with: []
---

# Task: Verify all data survives pod restart

## Description
Delete the gateway pod to force a restart. Verify all persisted data survives: config (channels), agents, workspace (skills), memory, cron, telegram state.

## Acceptance Criteria
- [ ] openclaw.json preserved (channels still configured)
- [ ] agents/ preserved (auth-profiles intact)
- [ ] workspace/ preserved (skills still installed)
- [ ] memory/ preserved
- [ ] cron/ preserved (jobs.json)
- [ ] telegram/ preserved (bot state)
- [ ] 15+ skills ready

## Technical Details
```bash
kubectl -n openclaw-tenant-1 delete pod -l app=openclaw-gateway
# Wait for new pod
kubectl -n openclaw-tenant-1 rollout status deployment/openclaw-gateway
# Verify
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- openclaw channels status
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- openclaw skills list | grep ready
```

## Effort Estimate
- Size: S
- Hours: 0.2

## Definition of Done
- [ ] All data preserved after restart
- [ ] Channels still running
- [ ] Skills still ready
