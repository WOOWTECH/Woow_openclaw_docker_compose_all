---
name: Configure LINE and Telegram channels
status: open
created: 2026-03-23T22:18:11Z
updated: 2026-03-23T22:18:11Z
github:
depends_on: [006]
parallel: false
conflicts_with: []
---

# Task: Configure LINE and Telegram channels

## Description
Set up LINE channel (Access Token + Secret) and Telegram bot (Bot Token) via the web GUI Channels page.

## Acceptance Criteria
- [ ] LINE channel: Configured=Yes, Running=Yes
- [ ] Telegram channel: Configured=Yes, Running=Yes

## Technical Details
User action via web GUI at https://cindytech1-openclaw.woowtech.io → Channels tab.

Verify:
```bash
kubectl -n openclaw-tenant-1 exec deployment/openclaw-gateway -- openclaw channels status
```

## Effort Estimate
- Size: XS
- Hours: 0.1

## Definition of Done
- [ ] Both channels running
