---
name: Export and import images to K3s containerd
status: open
created: 2026-03-23T22:18:11Z
updated: 2026-03-23T22:18:11Z
github:
depends_on: [002, 003]
parallel: false
conflicts_with: []
---

# Task: Export and import images to K3s containerd

## Description
Export both Docker images to tar archives and import them into K3s containerd namespace.

## Acceptance Criteria
- [ ] openclaw-custom:latest in containerd
- [ ] openclaw-setup-wizard:latest in containerd

## Technical Details
```bash
sudo buildah push openclaw-custom:latest docker-archive:/tmp/openclaw-custom.tar:openclaw-custom:latest
sudo ctr -n k8s.io images import /tmp/openclaw-custom.tar
sudo buildah push openclaw-setup-wizard:latest docker-archive:/tmp/setup-wizard.tar:openclaw-setup-wizard:latest
sudo ctr -n k8s.io images import /tmp/setup-wizard.tar
```

## Effort Estimate
- Size: XS
- Hours: 0.1

## Definition of Done
- [ ] Both images listed in `ctr -n k8s.io images list`
