# Option H-prime FCM Push — K3s Deploy Templates

K8s manifests for WoowTech's Option H-prime FCM push notification system on k3s.

## Architecture

```
                    ┌─────────────────────────────────┐
                    │  woow-fcm-central namespace     │
                    │  ┌──────────────┐ ┌───────────┐ │
  POST /v1/enroll → │  │  whitelist    │ │  TVS      │ │ ← POST /v1/issue-fcm-token
  (SA token auth)   │  │  :8000       │ │  :8001    │ │   (api_key auth)
                    │  └──────┬───────┘ └─────┬─────┘ │
                    │         │ DB            │ SA    │
                    │  ┌──────▼───────┐ ┌─────▼─────┐ │
                    │  │  postgres    │ │  master   │ │
                    │  │  (Pg14)      │ │  SA file  │ │
                    │  └──────────────┘ └───────────┘ │
                    └─────────────────────────────────┘
                                  ▲
           ┌──────────────────────┼──────────────────────┐
           │ tenant namespace     │                      │
           │  ┌───────────────────┴────────────────────┐ │
           │  │  Odoo pod (existing 05-odoo.yaml)      │ │
           │  │  ┌──────┐ ┌───────┐ ┌──────────────┐   │ │
           │  │  │ Odoo │ │ Nginx │ │ fcm-sidecar  │   │ │
           │  │  │      │ │       │ │ (self-enroll)│   │ │
           │  │  └──┬───┘ └───────┘ └──────┬───────┘   │ │
           │  │     │ unix socket          │           │ │
           │  │     └──────────────────────┘           │ │
           │  └────────────────────────────────────────┘ │
           └─────────────────────────────────────────────┘
```

## Source repos

| Component | Repo | Branch |
|-----------|------|--------|
| Central (TVS + whitelist + admin) | `WOOWTECH/woow_fcm_central` | `main` |
| Sidecar (Go) + Odoo plugin | `WOOWTECH/woow_odoo_fcm_push` | `feature/optionH-prime` |
| These deploy templates | `WOOWTECH/Woow_openclaw_docker_compose_all` | `feature/fcm-optionH-selfenroll` |

## Deploying

### Central (one-time)

```bash
kubectl apply -f fcm-push/woow-fcm-central/
# Then inject real secrets (see 01-secrets.yaml header comments)
# Then run migration (default = alembic upgrade head):
bash fcm-push/woow-fcm-central/run-migration.sh "$REAL_PG_PASSWORD"
# Raw SQL fallback (explicit opt-in, no pip needed):
# bash fcm-push/woow-fcm-central/run-migration.sh --raw-sql "$REAL_PG_PASSWORD"
```

### Per-tenant sidecar (self-enroll, zero manual box_uuid)

1. Create SA: `kubectl apply -f fcm-on-odoo/00-sa.yaml` (replace `$NAMESPACE`)
2. Create ghcr-pull + github-token secrets in the tenant namespace (see `02-github-token-secret.yaml`)
3. Insert mapping: `INSERT INTO namespace_tenant_map (namespace, tenant_id, created_by) VALUES ('$NAMESPACE', '$TENANT', 'operator')`
4. Patch the tenant's `05-odoo.yaml` per `fcm-on-odoo/01-sidecar-overlay.reference.yaml`
5. The sidecar self-enrolls on first boot — no manual box_uuid needed

## Security notes

- **ghcr-pull secret**: PRODUCTION deployments MUST use a dedicated GitHub PAT with
  `read:packages` scope only. Never use the `gh` CLI token (which has `write:packages`).
  The PAT is git-ignored and injected at deploy time.
- **Master SA**: The Google Service Account JSON is NEVER committed to git. It is
  injected via `kubectl create secret generic fcm-master-sa --from-file=...` at deploy time.
- **SH-1**: Process-wide `mlockall` was removed (CrashLooped on k3s default 8 MiB
  RLIMIT_MEMLOCK). Anti-swap relies on node-layer guarantees (k8s NoSwap, VmSwap==0).
  `capabilities.add: [IPC_LOCK]` is NOT required.

## Verified on

- k3s v1.34.3+k3s1 (10-node cluster, Ubuntu 24.04)
- Self-enrollment E2E: `POST /v1/enroll` → 200, `enroll_ok_new` + `enroll_ok_rotate`
- Pod stays Running (0 restarts) with SH-1 hardening fix
- Full broadcast E2E: real Odoo 18 tenant (fcm-e2e) + real master SA + real iPhone push received
