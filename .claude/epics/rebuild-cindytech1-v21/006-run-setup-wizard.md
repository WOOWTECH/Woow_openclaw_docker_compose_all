---
name: Complete initial setup via web wizard
status: open
created: 2026-03-23T22:18:11Z
updated: 2026-03-23T22:18:11Z
github:
depends_on: [005]
parallel: false
conflicts_with: []
---

# Task: Complete initial setup via web wizard

## Description
User fills in setup wizard form: gateway token, DB password, AI provider + API key. Wizard provisions secrets, starts DB and gateway, switches CF route, self-destructs.

## Acceptance Criteria
- [ ] Wizard completes all 7 steps
- [ ] Gateway pod Running
- [ ] DB pod Running
- [ ] Dashboard accessible at https://cindytech1-openclaw.woowtech.io
- [ ] AI model responds to messages

## Technical Details
User action via browser. Verify with:
```bash
kubectl -n openclaw-tenant-1 get pods
curl -sSk -o /dev/null -w "%{http_code}" https://cindytech1-openclaw.woowtech.io/
```

## Effort Estimate
- Size: S
- Hours: 0.1

## Definition of Done
- [ ] Dashboard loads, AI responds
