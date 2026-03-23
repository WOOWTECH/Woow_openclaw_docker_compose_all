---
name: Apply K8s manifests and start setup wizard
status: open
created: 2026-03-23T22:18:11Z
updated: 2026-03-23T22:18:11Z
github:
depends_on: [004]
parallel: false
conflicts_with: []
---

# Task: Apply K8s manifests and start setup wizard

## Description
Apply all K8s manifests (00-06), scale down gateway/db (wait for setup wizard), switch CF route to setup wizard, scale up setup wizard.

## Acceptance Criteria
- [ ] All manifests applied (PVCs recreated)
- [ ] CF route points to setup-wizard-svc:18790
- [ ] Setup wizard pod Running
- [ ] https://cindytech1-openclaw.woowtech.io accessible (HTTP 200)

## Technical Details
```bash
kubectl apply -f k8s-manifests/
kubectl -n openclaw-tenant-1 scale deployment openclaw-gateway --replicas=0
kubectl -n openclaw-tenant-1 scale deployment openclaw-db --replicas=0
# Switch CF route to setup wizard
python3 -c "import requests; ..."
kubectl -n openclaw-tenant-1 scale deployment setup-wizard --replicas=1
```

## Effort Estimate
- Size: S
- Hours: 0.2

## Definition of Done
- [ ] Setup wizard accessible at the domain
