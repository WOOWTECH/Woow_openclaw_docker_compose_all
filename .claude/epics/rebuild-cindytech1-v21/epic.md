---
name: rebuild-cindytech1-v21
status: backlog
created: 2026-03-23T22:16:40Z
progress: 0%
prd: .claude/prds/rebuild-cindytech1-v21.md
github:
---

# Epic: rebuild-cindytech1-v21

## Overview

Full rebuild of cindytech1-openclaw.woowtech.io using the latest k3s branch v2.1 code. Clean slate deployment with all persistence features, multi-model support, custom Docker image with 15 skills, and channel configuration.

## Architecture Decisions

- **Custom Docker image** (`openclaw-custom:latest`) pre-loaded with skill dependencies
- **PVC-backed persistence** for agents, workspace, memory, cron, telegram, config
- **Symlink pattern** to avoid K8s root ownership issues on mount paths
- **nodeSelector** for control-plane node (image locality + PVC affinity)
- **Auto-detect model** from available API keys on startup

## Technical Approach

### Infrastructure
- Full K8s resource cleanup (secrets, PVCs, deployments)
- Rebuild both Docker images (gateway custom + setup wizard)
- Import images to containerd on control-plane node
- Apply all manifests (00-06) in order

### Configuration
- Setup wizard handles initial provisioning (secrets, DB, gateway, CF route)
- Channel configs set via web GUI post-deployment
- All configs persisted on PVC for restart survival

## Task Breakdown Preview

| # | Task | Parallel | Depends On |
|---|------|----------|------------|
| 1 | Full cleanup (secrets, PVCs, scale down) | — | — |
| 2 | Build custom gateway image | — | 1 |
| 3 | Build setup wizard image | yes (with 2) | 1 |
| 4 | Import images to containerd | — | 2, 3 |
| 5 | Apply manifests + start setup wizard | — | 4 |
| 6 | Run setup wizard (user action) | — | 5 |
| 7 | Configure channels (LINE, Telegram) | — | 6 |
| 8 | Verify persistence (restart test) | — | 7 |

## Dependencies

- K3s cluster healthy (4 nodes)
- cloudflared pod running
- buildah available on control-plane node
- User provides: AI API key, gateway token, LINE/Telegram tokens

## Success Criteria (Technical)

- All pods Running (gateway, db, cloudflared)
- `openclaw skills list` shows 15+ ready
- `openclaw channels status` shows LINE + Telegram running
- Pod delete → restart → all config preserved
- Web GUI accessible at `https://cindytech1-openclaw.woowtech.io`

## Estimated Effort

~30 minutes total (mostly waiting for image builds and gateway startup)

## Tasks Created
- [ ] 001.md - Full cleanup of existing resources (parallel: false)
- [ ] 002.md - Build custom gateway Docker image (parallel: true)
- [ ] 003.md - Build setup wizard Docker image (parallel: true)
- [ ] 004.md - Export and import images to K3s containerd (parallel: false)
- [ ] 005.md - Apply K8s manifests and start setup wizard (parallel: false)
- [ ] 006.md - Complete initial setup via web wizard (parallel: false)
- [ ] 007.md - Configure LINE and Telegram channels (parallel: false)
- [ ] 008.md - Verify all data survives pod restart (parallel: false)

Total tasks: 8
Parallel tasks: 2 (002 + 003 can run together)
Sequential tasks: 6
Estimated total effort: ~1 hour
