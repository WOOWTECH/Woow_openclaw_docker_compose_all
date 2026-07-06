# tenant-template — parameterized Odoo 18 + FCM push tenant

Apply-ready manifests for a **from-scratch** Odoo 18 tenant with the self-enrolling
FCM push sidecar. Derived from the live, working `fcm-e2e` namespace on the k3s
cluster. Every value that differs per tenant is a `__PLACEHOLDER__`.

## Placeholder convention

| Placeholder | Meaning | Example | Constraints |
|---|---|---|---|
| `__TENANT__` | Tenant slug = **namespace** AND resource-name prefix | `bnidistrict` | DNS label: lowercase `[a-z0-9-]`, start/end alphanumeric |
| `__DBNAME__` | Postgres **db name and role** | `bnidistrict` | **Alphanumeric, NO dashes** (used unquoted in odoo.conf/SQL) |
| `__DBPASS__` | Postgres password | *(generated)* | Rendered at deploy time; **never commit a rendered copy** |
| `__ADMIN_PASSWD__` | Odoo master (DB-mgmt) password | *(generated)* | odoo.conf `admin_passwd` |
| `__FIREBASE_PROJECT__` | Firebase project id | `woow-odoo-de2cb` | Must match the master SA's project in central |
| `__DOMAIN__` | Public FQDN (Cloudflare only) | `bni.woowtech.app` | Only used by `optional-cloudflared/` + VERIFY |

Substitute with `deploy-tenant.sh` (recommended) or a manual `sed` (see DEPLOY-RUNBOOK.md Phase 3).

## Apply order (files are numbered; `kubectl apply -f tenant-template/` is non-recursive)

| # | File | Kind |
|---|---|---|
| 00 | `00-namespace.yaml` | Namespace |
| 05 | `05-pvcs.yaml` | 3 PVCs (odoo-data, odoo-addons, db-pvc) |
| 10 | `10-configmaps.yaml` | odoo.conf + nginx.conf ConfigMaps |
| 15 | `15-postgres.yaml` | Postgres Service + Deployment |
| 20 | `20-odoo.yaml` | **Odoo Deployment** (5 initContainers, 3 containers, 8 volumes) |
| 25 | `25-odoo-svc.yaml` | Odoo Service |
| 30 | `30-fcm-sidecar-sa.yaml` | ServiceAccount `fcm-sidecar` |
| 40 | `40-networkpolicy.yaml` | Tenant egress/ingress NetworkPolicy |
| — | `optional-cloudflared/50-cloudflared.yaml` | **Opt-in** public ingress (apply separately) |

## Secrets are NOT in this directory (created out-of-band, before apply)

These are created via `kubectl create secret` with placeholders/paths — never committed:

- `__TENANT__-postgres-secret` — keys `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `ghcr-pull` — docker-registry secret (read:packages PAT) to pull `ghcr.io/woowtech/fcm-sidecar`
- `github-token` — key `token` (Contents:read PAT) for the private plugin clone
- `__TENANT__-cf-tunnel-token` — key `TUNNEL_TOKEN` (only if using `optional-cloudflared/`)

See DEPLOY-RUNBOOK.md Phase 3 for the exact create commands.
