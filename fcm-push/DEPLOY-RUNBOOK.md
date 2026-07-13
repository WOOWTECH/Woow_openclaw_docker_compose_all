# DEPLOY-RUNBOOK — Odoo 18 + FCM Push on WoowTech k3s (from scratch)

> **Status: VERIFIED on real k3s.** The tenant manifests in `tenant-template/` are
> a parameterized copy of the live, working `fcm-e2e` namespace (Odoo 18 + FCM
> sidecar + real iPhone push received, 2026-07-07). Central (`woow-fcm-central`)
> is running. This runbook takes you from **nothing** to **a fresh Odoo tenant
> that self-enrolls and sends FCM push**.
>
> **Audience: a human OR an LLM agent.** Every step is an exact command in order.
> Nothing is left to "figure out". Placeholders are explicit (`__TENANT__` etc.).
> `kubectl apply -f <dir>` is used everywhere (this cluster does **NOT** use kustomize).
>
> **Golden rules (never break):**
> 1. Never print or commit a secret value. Secrets are created from files/env at deploy time.
> 2. The Google master Service Account lives ONLY in central's `fcm-master-sa` secret — never in a tenant, never in git.
> 3. A tenant self-enrolls only if central has a `namespace_tenant_map[<ns>]` row. No row → enroll returns **403** (this is the authorization gate, on purpose).

---

## 1. Architecture (one paragraph + one diagram)

A tenant runs its own Odoo 18 pod. Inside that pod, a hardened **`fcm-sidecar`**
container boots, reads a **projected Kubernetes ServiceAccount token** (audience
`central`), and **self-enrolls** by `POST`ing it to the shared **central**
control plane (`woow-fcm-central`). Central verifies the token via the k8s
TokenReview API, looks the namespace up in `namespace_tenant_map` (fail-closed
403 if unmapped), and mints a per-tenant `box_uuid` + `api_key`. Thereafter the
sidecar vends short-lived **Google FCM OAuth bearers** from central's
token-vending-service and hands them to Odoo over a **unix socket** in a shared
`emptyDir`. The Odoo plugin `woow_fcm_push` (git-cloned into the pod at boot) uses
that bearer to send push. The master Google SA never leaves central.

```
  ┌── tenant namespace: __TENANT__ ───────────────────────────────────┐
  │  Odoo pod (Deployment __TENANT__-odoo)                             │
  │   ┌────────┐   ┌───────┐   ┌───────────────────────────────────┐  │
  │   │ odoo   │   │ nginx │   │ fcm-sidecar (uid 10001, drop-ALL)  │  │
  │   │ uid100 │   │ :8080 │   │  1. read SA token (aud=central)    │  │
  │   └───┬────┘   └───────┘   │  2. POST /v1/enroll ──────────────┐│  │
  │       │ unix socket        │  3. POST /v1/issue-fcm-token ────┐││  │
  │       └── /run/fcm-sidecar/sock ◄── vend bearer ──────────────┘││  │
  │   Deployment __TENANT__-postgres (Odoo DB)                     ││  │
  └───────────────────────────────────────────────────────────────┼┼──┘
                    │ in-cluster HTTP (NetworkPolicy-guarded)       ││
                    ▼                                               ▼▼
  ┌── namespace: woow-fcm-central (deploy ONCE per cluster) ──────────┐
  │  whitelist-service :8000   /v1/enroll → TokenReview(aud=central,  │
  │     SA=fcm-sidecar) → namespace_tenant_map → mint box_uuid/api_key│
  │  token-vending-service :8001  /v1/issue-fcm-token → Google bearer │
  │  postgres (boxes, namespace_tenant_map, enrollment_audit)         │
  │  secret fcm-master-sa  (Google master SA — in-memory only)        │
  └──────────────────────────────────────────────────────────────────┘
```

---

## 2. PREREQUISITES — inputs the operator must provide

### 2.1 Per-tenant inputs (you choose / are given these)

| Input | Placeholder | Example | Notes |
|---|---|---|---|
| Tenant slug | `__TENANT__` | `bnidistrict` | DNS label; becomes the **namespace** and every resource prefix |
| Public FQDN | `__DOMAIN__` | `bni.woowtech.app` | Only for Cloudflare ingress + VERIFY; optional if internal-only |
| Firebase project id | `__FIREBASE_PROJECT__` | `woow-odoo-de2cb` | Must match the master SA's Google project in central |
| Postgres db/role name | `__DBNAME__` | `bnidistrict` | Alphanumeric, **no dashes**. Default = tenant slug with dashes stripped |
| Stable tenant id | `TENANT_ID` | `bnidistrict` | The id stored in `namespace_tenant_map`; may equal the slug |

Generated automatically by `deploy-tenant.sh` (or generate with `openssl rand`):
`__DBPASS__` (postgres password), `__ADMIN_PASSWD__` (Odoo master password).

### 2.2 Secret material you must have on disk (never committed)

| Secret file (env var) | What it is | Scope needed |
|---|---|---|
| `GHCR_PULL_PAT_FILE` | GitHub PAT to pull `ghcr.io/woowtech/*` images | **`read:packages`** only |
| `GITHUB_CLONE_PAT_FILE` | GitHub PAT to clone the private plugin repo | **`Contents:read`** on `WOOWTECH/woow_odoo_fcm_push` |
| `secrets/fcm-sa-key.json` | Google master Service Account JSON | central-only; **never** in a tenant |
| `CF_TUNNEL_TOKEN_FILE` | Cloudflare tunnel token (optional) | only if exposing a public URL |

> Store all of the above under `fcm-push/secrets/` (git-ignored) or an out-of-repo
> secure path. **Never** the `gh auth token` (write-scoped) in production.

### 2.3 Tooling

`kubectl` (context set to the WoowTech k3s cluster), `bash`, `sed`, `openssl`,
`git`. For central migration: `python3` + the `woow_fcm_central` repo cloned
locally (or use the `--raw-sql` fallback which needs neither).

---

## 3. PHASE 0 — gate checks (run every time, read-only)

```bash
# Right cluster?
kubectl config current-context           # MUST be the WoowTech k3s context
kubectl get nodes -o wide                 # expect k3s v1.34, Ready

# Secrets are git-ignored (STOP if any real secret is tracked)
cd fcm-push
git check-ignore secrets/ 2>/dev/null && echo "secrets/ ignored OK" || echo "STOP: secrets/ not git-ignored"
```

**STOP** if the context is wrong or `secrets/` is not ignored.

---

## 4. PHASE 1 — publish images to GHCR (once per image change)

The three images are **private** org packages on `ghcr.io/woowtech`. This is the
sudo-free path (no `k3s ctr import`, which needs node root this cluster does not grant).

```bash
# Log in with a PAT that has write:packages (build machine only, NOT committed)
echo "$(cat "$GHCR_WRITE_PAT_FILE")" | podman login ghcr.io -u WOOWTECH --password-stdin

for img in whitelist-service token-vending-service fcm-sidecar; do
  podman tag  localhost/woow-fcm/$img:dev  ghcr.io/woowtech/$img:dev
  podman push ghcr.io/woowtech/$img:dev
done
# Confirm all three packages are PRIVATE. Every namespace that runs them needs a
# ghcr-pull secret (created in Phase 2/3 from a read:packages PAT).
```

> If the images are already published (they are, as of 2026-07-07), skip this phase.

---

## 5. PHASE 2 — deploy central (ONCE per cluster)

> Skip this whole phase if `kubectl get ns woow-fcm-central` already exists and is
> healthy (it is, as of 2026-07-07 — jump to Phase 3). These steps are for a fresh cluster.

```bash
cd fcm-push/woow-fcm-central

# 2.1 Namespace
kubectl apply -f 00-namespace.yaml

# 2.2 Create the REAL secrets (values from files/generated; never echoed).
#     These MUST exist before postgres/services start, and we do NOT apply the
#     placeholder 01-secrets.yaml (it would clobber these).
kubectl -n woow-fcm-central create secret generic db-credentials \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -base64 32)" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n woow-fcm-central create secret generic admin-session \
  --from-literal=ADMIN_SESSION_SECRET="$(openssl rand -base64 48)" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n woow-fcm-central create secret generic fcm-master-sa \
  --from-file=fcm_master_sa.json="../secrets/fcm-sa-key.json" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n woow-fcm-central create secret docker-registry ghcr-pull \
  --docker-server=ghcr.io --docker-username=WOOWTECH \
  --docker-password="$(cat "$GHCR_PULL_PAT_FILE")" \
  --dry-run=client -o yaml | kubectl apply -f -

# 2.3 Apply everything EXCEPT the placeholder secrets file (00-namespace re-apply is harmless)
for f in *.yaml; do
  [ "$f" = "01-secrets.yaml" ] && continue
  kubectl apply -f "$f"
done

# 2.4 Wait for postgres, then run the schema migration
kubectl -n woow-fcm-central rollout status statefulset/postgres --timeout=180s
# Default = alembic (needs the woow_fcm_central repo cloned + python3):
#   git clone https://github.com/WOOWTECH/woow_fcm_central.git /tmp/woow_fcm_central
CENTRAL_PW="$(kubectl -n woow-fcm-central get secret db-credentials -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)"
WOOW_FCM_CENTRAL_REPO=/tmp/woow_fcm_central bash run-migration.sh "$CENTRAL_PW"
#   OR raw-SQL fallback (no python/pip needed):
#   bash run-migration.sh --raw-sql "$CENTRAL_PW"

# 2.5 Wait for the services
kubectl -n woow-fcm-central rollout status deploy/whitelist-service deploy/token-vending-service --timeout=180s
```

**GATE 2 (all must pass before any tenant):**

```bash
kubectl -n woow-fcm-central get pods                      # all Running, restarts stable
kubectl -n woow-fcm-central exec deploy/whitelist-service -- wget -qO- http://localhost:8000/healthz
kubectl -n woow-fcm-central exec deploy/token-vending-service -- wget -qO- http://localhost:8001/healthz
kubectl auth can-i create tokenreviews \
  --as=system:serviceaccount:woow-fcm-central:whitelist-service     # -> yes
```

> `whitelist-service` MUST stay `replicas: 1` (in-process idempotency + audit). Do not scale.

---

## 6. PHASE 3 — deploy a tenant (repeatable, idempotent)

### Option A — one command (recommended)

```bash
cd fcm-push
export GHCR_PULL_PAT_FILE=secrets/ghcr-read.pat        # read:packages PAT
export GITHUB_CLONE_PAT_FILE=secrets/github-read.pat   # Contents:read PAT
export CENTRAL_PG_PASSWORD="$(kubectl -n woow-fcm-central get secret db-credentials -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)"
# optional: export CF_TUNNEL_TOKEN_FILE=secrets/bni-cf-token   # to expose a public URL

# Preview first (renders to /tmp, no cluster writes):
DEPLOY_MODE=render ./deploy-tenant.sh bnidistrict bni.woowtech.app woow-odoo-de2cb

# Then deploy for real:
./deploy-tenant.sh bnidistrict bni.woowtech.app woow-odoo-de2cb
```

`deploy-tenant.sh` renders the placeholders, creates the tenant secrets (postgres,
ghcr-pull, github-token), writes the `namespace_tenant_map` row (if
`CENTRAL_PG_PASSWORD` is set), applies `tenant-template/`, and waits for rollout.
It never prints secret values. Then jump to **Phase 4 (VERIFY)**.

### Option B — manual (if you cannot run the script)

```bash
cd fcm-push
export TENANT=bnidistrict DOMAIN=bni.woowtech.app FIREBASE=woow-odoo-de2cb
export DBNAME=bnidistrict TENANT_ID=bnidistrict
DBPASS="$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)"
ADMIN_PASSWD="$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)"

# 3.1 Render placeholders into a git-ignored working dir (holds the db password)
WORK=/tmp/fcm-tenant-$TENANT; mkdir -p "$WORK/optional-cloudflared"
for f in tenant-template/*.yaml tenant-template/optional-cloudflared/*.yaml; do
  sed -e "s|__TENANT__|$TENANT|g" -e "s|__DBNAME__|$DBNAME|g" \
      -e "s|__DBPASS__|$DBPASS|g" -e "s|__ADMIN_PASSWD__|$ADMIN_PASSWD|g" \
      -e "s|__FIREBASE_PROJECT__|$FIREBASE|g" -e "s|__DOMAIN__|$DOMAIN|g" \
      "$f" > "$WORK/${f#tenant-template/}"
done

# 3.2 Namespace + tenant secrets (created out-of-band, NOT part of the apply set)
kubectl apply -f "$WORK/00-namespace.yaml"
kubectl -n $TENANT create secret generic $TENANT-postgres-secret \
  --from-literal=POSTGRES_USER="$DBNAME" --from-literal=POSTGRES_PASSWORD="$DBPASS" \
  --from-literal=POSTGRES_DB="$DBNAME" --dry-run=client -o yaml | kubectl apply -f -
kubectl -n $TENANT create secret docker-registry ghcr-pull \
  --docker-server=ghcr.io --docker-username=WOOWTECH \
  --docker-password="$(cat secrets/ghcr-read.pat)" --dry-run=client -o yaml | kubectl apply -f -
kubectl -n $TENANT create secret generic github-token \
  --from-literal=token="$(cat secrets/github-read.pat)" --dry-run=client -o yaml | kubectl apply -f -

# 3.3 Apply the tenant manifest set (non-recursive → optional-cloudflared/ skipped)
kubectl apply -f "$WORK/"

# 3.4 Authorization gate: map the namespace in central (WITHOUT this, enroll → 403)
CENTRAL_PW="$(kubectl -n woow-fcm-central get secret db-credentials -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)"
kubectl -n woow-fcm-central exec -i postgres-0 -- sh -c \
  "PGPASSWORD='$CENTRAL_PW' psql -U fcm_central -d fcm_central -v ON_ERROR_STOP=1 -c \
   \"INSERT INTO namespace_tenant_map (namespace, tenant_id, created_by) \
     VALUES ('$TENANT','$TENANT_ID','runbook') ON CONFLICT (namespace) DO NOTHING;\""

# 3.5 (optional) public URL via Cloudflare tunnel
# kubectl -n $TENANT create secret generic $TENANT-cf-tunnel-token \
#   --from-literal=TUNNEL_TOKEN="$(cat secrets/$TENANT-cf-token)" --dry-run=client -o yaml | kubectl apply -f -
# kubectl apply -f "$WORK/optional-cloudflared/"

# 3.6 Wait for rollout (initContainers clone the plugin + init the DB — minutes)
kubectl -n $TENANT rollout status deploy/$TENANT-odoo --timeout=600s

rm -rf "$WORK"   # remove the rendered dir (it holds the db password)
```

> The `firebase_project_id` Odoo system parameter is set automatically by the
> `init-db` initContainer (Phase 3 step 5 in `20-odoo.yaml`). No manual UI step.

---

## 7. PHASE 4 — VERIFY (copy-paste; stop on first failure)

```bash
export TENANT=bnidistrict        # the namespace you just deployed

# A. Pod up, all 3 containers Ready
kubectl -n $TENANT get pods -l app.kubernetes.io/name=odoo
#   expect READY 3/3, STATUS Running

# B. Self-enroll succeeded (sidecar wrote its box_uuid + api_key)
kubectl -n $TENANT logs deploy/$TENANT-odoo -c fcm-sidecar | grep -Ei 'enroll|central_reachable'
#   expect "self-enrollment complete" and central_reachable=true

# C. Central recorded the enroll (audit + a box row for this tenant)
CENTRAL_PW="$(kubectl -n woow-fcm-central get secret db-credentials -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)"
kubectl -n woow-fcm-central exec -i postgres-0 -- sh -c \
  "PGPASSWORD='$CENTRAL_PW' psql -U fcm_central -d fcm_central -c \
   \"SELECT event, tenant_id, ts FROM enrollment_audit WHERE tenant_id='$TENANT' ORDER BY ts DESC LIMIT 3;\""
#   expect an enroll_ok_new (or enroll_ok_rotate) row

# D. Odoo↔sidecar socket present, VmSwap==0 (SH-1 anti-swap), no CrashLoop
kubectl -n $TENANT exec deploy/$TENANT-odoo -c fcm-sidecar -- sh -c 'test -S /run/fcm-sidecar/sock && echo socket-ok'
kubectl -n $TENANT exec deploy/$TENANT-odoo -c fcm-sidecar -- sh -c 'grep VmSwap /proc/1/status'   # 0 kB

# E. firebase_project_id is set in Odoo
kubectl -n $TENANT exec -i deploy/$TENANT-odoo -c odoo -- sh -c \
  "python3 -c \"import psycopg2,os; c=psycopg2.connect(host='$TENANT-postgres-svc',dbname='$(kubectl -n $TENANT get secret $TENANT-postgres-secret -o jsonpath='{.data.POSTGRES_DB}'|base64 -d)',user='$(kubectl -n $TENANT get secret $TENANT-postgres-secret -o jsonpath='{.data.POSTGRES_USER}'|base64 -d)',password='$(kubectl -n $TENANT get secret $TENANT-postgres-secret -o jsonpath='{.data.POSTGRES_PASSWORD}'|base64 -d)'); cur=c.cursor(); cur.execute(\\\"SELECT value FROM ir_config_parameter WHERE key='woow_fcm_push.firebase_project_id'\\\"); print(cur.fetchone())\""
#   expect ('woow-odoo-de2cb',)

# F. Fire a test push: in the Odoo UI (or via a test @mention on a chatter record
#    that the plugin watches), trigger a notification for a user whose device is
#    registered. Confirm ONE FCM send in the sidecar/plugin logs:
kubectl -n $TENANT logs deploy/$TENANT-odoo -c fcm-sidecar --tail=50 | grep -Ei 'issue-fcm-token|vend|200'
kubectl -n $TENANT logs deploy/$TENANT-odoo -c odoo --tail=100 | grep -Ei 'fcm|push'
#   expect one token vend (HTTP 200) and one send. FCM 200 != delivered — confirm on the device.
```

**Enroll failure fingerprints (for triage):**

| Symptom | Meaning | Fix |
|---|---|---|
| enroll **401** | SA token audience/name wrong | check projected `audience: central` + SA name is exactly `fcm-sidecar` |
| enroll **403 no_mapping** | `namespace_tenant_map` row missing | run Phase 3.4 |
| enroll **403 revoked** | tenant revoked | expected; no resurrection |
| enroll **503** | whitelist/TokenReview transiently down | sidecar retries with backoff; wait |
| sidecar CrashLoop + `mlockall_failed` | old image (pre-SH-1) | rebuild sidecar without `mlockall` (Phase 1) |

---

## 8. Rollback / revoke / rotate

- **Roll back a tenant:** `kubectl delete namespace __TENANT__` (removes the whole
  tenant: Odoo, postgres, secrets, sidecar). Central is untouched.
- **Revoke a tenant (keep it running, cut FCM):** set its box `status='revoked'`
  in central `boxes`, and delete its `namespace_tenant_map` row. Re-enroll → 403.
  Any cached bearer expires within ~1 hour.
- **Rotate the tenant api_key:** delete the Odoo pod
  (`kubectl -n __TENANT__ delete pod -l app.kubernetes.io/name=odoo`); the fresh
  sidecar re-enrolls and central rotates the key (old one invalidated).
- **Roll back central:** `kubectl delete namespace woow-fcm-central`. All tenants
  keep their cached bearer ≤1h, then enroll/issue fail-closed.

---

## 9. Source of truth (repos / branches)

| Artifact | Repo / branch | Path |
|---|---|---|
| These manifests + this runbook | `WOOWTECH/Woow_openclaw_docker_compose_all` @ `feature/fcm-optionH-selfenroll` | `fcm-push/` |
| Central (Python) | `WOOWTECH/woow_fcm_central` @ `main` | `whitelist-service/`, `token-vending-service/`, `migrations/` |
| Sidecar (Go) + Odoo plugin | `WOOWTECH/woow_odoo_fcm_push` @ `feature/optionH-prime` | `sidecar/`, plugin at repo root |

## 10. File map of `fcm-push/`

```
fcm-push/
├── DEPLOY-RUNBOOK.md              # this file
├── deploy-tenant.sh               # one-command tenant deploy (Phase 3 Option A)
├── .gitignore                     # ignores secrets/ + rendered tenant dirs
├── woow-fcm-central/              # central control plane (deploy ONCE per cluster)
│   ├── 00-namespace.yaml … 07-rbac-tokenreview.yaml
│   └── run-migration.sh           # alembic (default) or --raw-sql fallback
└── tenant-template/               # parameterized fresh-tenant manifests (Phase 3)
    ├── README.md                  # placeholder convention + apply order
    ├── 00-namespace.yaml
    ├── 05-pvcs.yaml               # odoo-data, odoo-addons, db-pvc
    ├── 10-configmaps.yaml         # odoo.conf + nginx.conf
    ├── 15-postgres.yaml           # Odoo DB (Service + Deployment)
    ├── 20-odoo.yaml               # Odoo Deployment: 5 initContainers, 3 containers, 8 volumes
    ├── 25-odoo-svc.yaml
    ├── 30-fcm-sidecar-sa.yaml     # ServiceAccount fcm-sidecar (name is pinned by central)
    ├── 40-networkpolicy.yaml      # tenant egress/ingress scoping (recommended)
    └── optional-cloudflared/50-cloudflared.yaml   # opt-in public URL (apply separately)
```

> `fcm-on-odoo/` (the older commented sidecar OVERLAY reference) is superseded by
> the self-contained `tenant-template/` for from-scratch tenants. Keep it only as
> a guide for retrofitting the sidecar onto a pre-existing client Odoo.

---

_Authored 2026-07-07. Tenant manifests are a parameterized copy of the live,
verified `fcm-e2e` namespace. Central is live and healthy. `kubectl apply -f`
throughout — this cluster does not use kustomize._
