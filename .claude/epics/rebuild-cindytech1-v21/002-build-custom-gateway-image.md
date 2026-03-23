---
name: Build custom gateway Docker image
status: open
created: 2026-03-23T22:18:11Z
updated: 2026-03-23T22:18:11Z
github:
depends_on: [001]
parallel: true
conflicts_with: []
---

# Task: Build custom gateway Docker image

## Description
Build openclaw-custom:latest from Dockerfile.custom with all skill dependencies (jq, ripgrep, tmux, ffmpeg, gh, npm CLIs, uv).

## Acceptance Criteria
- [ ] Image built successfully with buildah
- [ ] Image contains: jq, rg, tmux, ffmpeg, gh, clawhub, mcporter, gog, goplaces, summarize, uv

## Technical Details
```bash
cd openclaw-k3s-paas
sudo buildah build -f Dockerfile.custom -t openclaw-custom:latest .
```

## Effort Estimate
- Size: S
- Hours: 0.2 (mostly build time)

## Definition of Done
- [ ] buildah reports successful build
