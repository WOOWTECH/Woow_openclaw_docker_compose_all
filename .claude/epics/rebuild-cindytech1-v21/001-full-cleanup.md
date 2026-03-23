---
name: Full cleanup of existing resources
status: open
created: 2026-03-23T22:18:11Z
updated: 2026-03-23T22:18:11Z
github:
depends_on: []
parallel: false
conflicts_with: []
---

# Task: Full cleanup of existing resources

## Description
Scale down gateway and DB, delete openclaw-secrets, delete all PVCs (openclaw-agents-pvc, openclaw-db-pvc).

## Acceptance Criteria
- [ ] Gateway deployment scaled to 0
- [ ] DB deployment scaled to 0
- [ ] openclaw-secrets deleted
- [ ] openclaw-agents-pvc deleted
- [ ] openclaw-db-pvc deleted

## Technical Details
```bash
kubectl -n openclaw-tenant-1 scale deployment openclaw-gateway --replicas=0
kubectl -n openclaw-tenant-1 scale deployment openclaw-db --replicas=0
kubectl -n openclaw-tenant-1 delete secret openclaw-secrets
kubectl -n openclaw-tenant-1 delete pvc openclaw-agents-pvc openclaw-db-pvc
```

## Effort Estimate
- Size: XS
- Hours: 0.1

## Definition of Done
- [ ] All resources deleted, only cloudflared pod running
