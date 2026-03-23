---
name: Build setup wizard Docker image
status: open
created: 2026-03-23T22:18:11Z
updated: 2026-03-23T22:18:11Z
github:
depends_on: [001]
parallel: true
conflicts_with: []
---

# Task: Build setup wizard Docker image

## Description
Build openclaw-setup-wizard:latest from setup-wizard/Dockerfile with latest code (7 providers, light mode, CF retry).

## Acceptance Criteria
- [ ] Image built successfully
- [ ] Contains latest app.py and index.html

## Technical Details
```bash
cd openclaw-k3s-paas/setup-wizard
sudo buildah build -f Dockerfile -t openclaw-setup-wizard:latest .
```

## Effort Estimate
- Size: XS
- Hours: 0.1

## Definition of Done
- [ ] buildah reports successful build
