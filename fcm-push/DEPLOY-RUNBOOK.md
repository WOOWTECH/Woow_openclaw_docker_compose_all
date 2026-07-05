# DEPLOY-RUNBOOK — Option H′ FCM Push on WoowTech k3s (Mode A, self-enrolling)

> **Status: VERIFIED (2026-07-05).** Full E2E passed: self-enrollment + SH-1
> sidecar fix + real iPhone push received. All sections are **✅ E2E-verified**.
>
> **E2E verdict (2026-07-05):** Self-enrollment PASSED end-to-end on real
> k3s — fresh sidecars in namespaces `fcm-selftest` and `fcm-e2e` self-registered
> with zero manual box_uuid. `POST /v1/enroll → 200`; `enrollment_audit=enroll_ok_new`;
> SH-1 fix deployed (mlockall removed) — sidecar stays Running, 0 restarts,
> `VmSwap==0 kB`; real Google FCM token vended via master SA; real push
> delivered to an iPhone. See **§11 Known issues** for resolution history.
>
> **What this is.** A copy-pasteable runbook a human *or* an LLM agent can follow to
> stand up "FCM push on Odoo" for the WoowTech k3s multi-tenant SaaS, using the
> **self-enrolling** provisioning model (a fresh tenant's `fcm-sidecar` registers
> with central automatically via its k8s ServiceAccount — zero manual UUID work).
>
> **What this is NOT.** Not the design rationale (see the `optionH-prime-implementation`
> repo: `docs/self-enrollment-design.md`, `docs/prd.md`, the SE-1 story). Not the
> application source (that lives in `woow_odoo_fcm_push` + `woow_fcm_central`).

---

## 0. Where everything lives (source of truth)

| Artifact | Repo / branch | Path |
|---|---|---|
| **Deploy manifests + this runbook** | `github.com/WOOWTECH/Woow_openclaw_docker_compose_all` @ **`feature/fcm-optionH-selfenroll`** (off `main`) | `fcm-push/` |
| Reference Odoo deployment (the 8-file convention) | same repo, per-client branch e.g. **`vk/989e-woow-k3s-odoo`** | `odoo-deployments/bnidistrict-odoo/05-odoo.yaml` |
| Sidecar source (Go) | `github.com/WOOWTECH/woow_odoo_fcm_push` @ `feature/optionH-prime` | `sidecar/` |
| Central source (Python) | `github.com/WOOWTECH/woow_fcm_central` @ `main` | `whitelist-service/`, `token-vending-service/`, `migrations/` |
| Design / PRD / SE-1 story | `optionH-prime-implementation` | `docs/` |

> **Git-hygiene rule (non-negotiable):** the per-tenant sidecar overlay
> (`fcm-on-odoo/05-odoo.sidecar-overlay.yaml`) is a **TEMPLATE**. It is committed
> ONLY on `feature/fcm-optionH-selfenroll`. It is **never** committed onto a client
> branch — when a real client adopts FCM, their onboarding applies the overlay onto
> that client's own branch. Client branches stay byte-for-byte unchanged by this work.

---

## 1. Architecture recap (self-enroll, one screen)

```
 ┌── tenant Odoo pod (per-tenant namespace) ──────────────┐
 │  Odoo(uid100) ──unix socket /run/fcm-sidecar/sock──┐   │
 │                                                    ▼   │
 │  fcm-sidecar (uid10001:10002, caps=drop-ALL, SH-1)     │
 │     │ 1. on boot, if box.uuid/api.key MISSING:         │
 │     │    POST /v1/enroll  {type:k8s-sa-token, value:<projected SA JWT aud=central>}
 │     ▼                                                  │
 └─────┼──────────────────────────────────────────────────┘
       │  (plain HTTP in-cluster, guarded by NetworkPolicy)
       ▼
 ┌── namespace woow-fcm-central ─────────────────────────┐
 │  whitelist-service :8000                               │
 │    /v1/enroll  → TokenReview(aud=central, SA=fcm-sidecar)
 │               → namespace_tenant_map[ns] → tenant_id (403 if unmapped)
 │               → mint/rotate box_uuid + api_key (hashed at rest)
 │    /internal/... (issue path uses api_key + whitelist DB only)
 │  token-vending-service :8001                           │
 │    /v1/issue-fcm-token → short-lived Google FCM bearer (master SA in-mem only)
 │  postgres (boxes, namespace_tenant_map, enrollment_audit)
 └───────────────────────────────────────────────────────┘
```

Key invariants (do not break):
- **Master SA never leaves central** — mounted mode-0400 file, in-memory only, never in env/DB/logs/health.
- **Identity comes ONLY from the TokenReview subject** — the enroll body carries no tenant_id/namespace (anti-IDOR).
- **Unmapped namespace → 403 fail-closed.** `namespace_tenant_map` (written at onboarding) IS the business-authorization gate.
- **api_key hashed at rest; re-enroll rotates** (self-heals an ephemeral emptyDir sidecar). A revoked tenant → 403, no resurrection.
- **Isolation = detection + revocation, NOT cryptographic.** The FCM bearer is project-scoped (shared Firebase project). Per-tenant box_uuid bounds audit/rate-limit/revoke blast radius.

---

## 2. Prerequisites — GATE 0 (read-only, run every time)

```bash
# Correct cluster + you are NOT about to touch a client branch
kubectl config current-context           # MUST be the woow-k3s context
git -C "<k3s-repo>" rev-parse --abbrev-ref HEAD   # MUST be feature/fcm-optionH-selfenroll (never a client branch)

# Secrets are git-ignored (STOP if any of these is tracked)
git -C "<k3s-repo>" check-ignore fcm-push/secrets/ fcm-push/**/*sa-key.json fcm-push/**/*.pat

# Cluster facts (expected: k3s v1.34, NetworkPolicy enforced, VmSwap==0 at node layer)
kubectl get nodes -o wide
```
**STOP** if the context is wrong, the branch is a client branch, or any secret file is tracked.

---

## 3. One-time — publish images to GHCR (the sudo-free path) ✅ E2E-verified

> **Why GHCR, not `k3s ctr import`.** Odoo tenants pull **all** images from public
> registries (docker.io + ghcr.io) with `imagePullPolicy: IfNotPresent/Always`,
> **zero** `k3s ctr import`, **zero** imagePullSecret. `ctr import` needs node root
> (containerd.sock is root-owned) — a hard blocker on this cluster (no passwordless
> sudo). GHCR needs no node root and matches the existing `ghcr.io/tuanle96/mcp-odoo`
> convention.

```bash
# 3.1 Log podman into GHCR using the environment's gh PAT (has write:packages)
echo "$(gh auth token)" | podman login ghcr.io -u WOOWTECH --password-stdin

# 3.2 Tag + push all three images as PRIVATE org packages
for img in whitelist-service token-vending-service fcm-sidecar; do
  podman tag  localhost/woow-fcm/$img:dev  ghcr.io/woowtech/$img:dev
  podman push ghcr.io/woowtech/$img:dev
done

# 3.3 Confirm the three packages are PRIVATE (org default) and record the digests.
```

**Pull credentials (read-only).** Each namespace that runs these images needs a
`ghcr-pull` secret. For **production** use a dedicated **`read:packages`-only** PAT
(git-ignored, never the CLI write token):

```bash
# PROD: ghcr-pull from a read-only PAT stored git-ignored at fcm-push/secrets/ghcr-read.pat
kubectl create secret docker-registry ghcr-pull \
  --docker-server=ghcr.io --docker-username=WOOWTECH \
  --docker-password="$(cat fcm-push/secrets/ghcr-read.pat)" \
  -n <namespace> --dry-run=client -o yaml | kubectl apply -f -
```
> ⚠️ The SE-1 E2E used `gh auth token` (write-scoped) as a shortcut — acceptable for a
> throwaway test namespace ONLY. Never commit that token and never use it in production.

Manifests reference the images as `image: ghcr.io/woowtech/<name>:dev`,
`imagePullPolicy: Always`, `imagePullSecrets: [{name: ghcr-pull}]`.

---

## 4. PHASE C — deploy central (once per cluster) ✅ E2E-verified

Central runs in its own namespace `woow-fcm-central` (whitelist-service + token-vending-service + postgres), standard file convention + SE-1 additions.

```bash
cd fcm-push/woow-fcm-central

# 4.1 Inject the real Google master SA at deploy time (NEVER in git).
#     Real key lives git-ignored at fcm-push/secrets/fcm-sa-key.json.
kubectl create namespace woow-fcm-central --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic fcm-master-sa \
  --from-file=fcm_master_sa.json=../secrets/fcm-sa-key.json \
  -n woow-fcm-central --dry-run=client -o yaml | kubectl apply -f -
#     Mounted mode 0400 at MASTER_SA_PATH=/etc/fcm/master-sa/fcm_master_sa.json

# 4.2 ghcr-pull secret for the central namespace (see §3)

# 4.3 Apply the namespace file set (postgres first) + TokenReview RBAC + NetworkPolicy
kubectl apply -f .            # 00-namespace..08-rbac-tokenreview (plain apply -f; the repo does NOT use kustomize)
kubectl -n woow-fcm-central rollout status statefulset/postgres --timeout=180s

# 4.4 Run the self-enrollment DB migration (adds boxes.tenant_id UNIQUE,
#     namespace_tenant_map, enrollment_audit, enroll_tokens)
./run-migration.sh           # alembic upgrade head  (revision 20260705_0001)

# 4.5 Wait for services
kubectl -n woow-fcm-central rollout status deploy/whitelist-service deploy/token-vending-service --timeout=180s
```

**GATE C (all must pass before any tenant):**
```bash
kubectl -n woow-fcm-central get pods                      # all Running, restarts stable
kubectl -n woow-fcm-central exec deploy/whitelist-service -- \
  wget -qO- http://localhost:8000/healthz                 # 200, db_connection: ok
kubectl -n woow-fcm-central exec deploy/token-vending-service -- \
  wget -qO- http://localhost:8001/healthz                 # 200
# TokenReview RBAC present:
kubectl auth can-i create tokenreviews \
  --as=system:serviceaccount:woow-fcm-central:whitelist-service   # yes
```
> `whitelist-service` MUST run **`replicas: 1`** (in-process idempotency + audit ring buffer). Do not scale.

---

## 5. PHASE T — onboard a tenant with self-enroll (repeatable, idempotent) ✅ E2E-verified

> **Fully verified:** self-enroll flow (mapping gate → TokenReview → mint → atomic
> persist → audit) + sidecar stays Running (SH-1, 0 restarts) + real push delivered.

Zero manual UUID. The only human input is the **`namespace → tenant_id` mapping** (the authz gate), written by onboarding automation.

```bash
export TENANT_NS=<tenant-namespace>       # single source of truth — echo-confirm
export TENANT_ID=<stable-tenant-id>       # a STABLE id you assign per customer (NOT the ns name)
echo "onboarding ns=$TENANT_NS tenant=$TENANT_ID"

# 5.1 Write the authorization mapping (business gate). Unmapped ns → enroll 403.
kubectl -n woow-fcm-central exec deploy/whitelist-service -- \
  psql "$DATABASE_URL" -c \
  "INSERT INTO namespace_tenant_map (namespace, tenant_id, created_by)
   VALUES ('$TENANT_NS','$TENANT_ID','onboarding-automation')
   ON CONFLICT (namespace) DO NOTHING;"

# 5.2 In the tenant namespace: create the fcm-sidecar SA + ghcr-pull secret,
#     then apply the sidecar overlay onto THIS tenant's 05-odoo (on the client branch,
#     never on feature/fcm-optionH-selfenroll).
kubectl -n "$TENANT_NS" apply -f - <<'EOF'
apiVersion: v1
kind: ServiceAccount
metadata: { name: fcm-sidecar }     # EXACT name — central pins it
EOF
#     ghcr-pull secret: see §3

# 5.3 Patch the tenant's 05-odoo.yaml with the sidecar overlay (fcm-on-odoo/ template):
#       - init clone_repo woow_fcm_push (into the existing clone-modules init)
#       - container fcm-sidecar (ghcr image, caps=drop-ALL, non-root 10001:10002, seccomp)
#       - projected token volume: audience=central, path enroll-token, expirationSeconds 3600
#       - env FCM_SIDECAR_ENROLL_ENDPOINT=http://whitelist-service.woow-fcm-central.svc.cluster.local:8000/v1/enroll
#             FCM_SIDECAR_CENTRAL_ENDPOINT=http://token-vending-service.woow-fcm-central.svc.cluster.local:8001/v1/issue-fcm-token
#             FCM_SIDECAR_SA_TOKEN_PATH=/var/run/secrets/tokens/enroll-token
#             FCM_SIDECAR_STATE_DIR=/var/lib/fcm-sidecar  FCM_SIDECAR_RUNTIME_DIR=/run/fcm-sidecar
#       - emptyDirs fcm-sidecar-state + fcm-sidecar-run; Odoo mounts /run/fcm-sidecar readOnly
#       - pod securityContext: fsGroup:101 + supplementalGroups:[10002]
#       - NO seed-credentials init + NO <tenant>-fcm-secret Secret (self-enroll replaces them)
#     Set Odoo system param woow_fcm_push.firebase_project_id = woow-odoo-de2cb
kubectl apply -f odoo-deployments/<tenant>/     # on the CLIENT branch (plain apply -f)
```

**Definition of Done (per self-enrolled tenant):**
1. `namespace_tenant_map` row exists (ns → tenant_id).
2. Pod has the `fcm-sidecar` SA + `audience: central` projected token.
3. Sidecar log: `self-enrollment complete`; `box.uuid` + `api.key` present (mode 0400) in the state dir.
4. `enrollment_audit` has an `enroll_ok_new` row for the tenant.
5. `kubectl exec -c fcm-sidecar -- /usr/local/bin/healthz` → `central_reachable=true`.
6. A push reaches the tenant's device (end-to-end).

---

## 6. Verification — layered, fail-closed (stop on first fail)

| Layer | Check | PASS bar |
|---|---|---|
| **A central** | pods Ready, `/healthz` 200 on 8000 + 8001 | stable, db_connection ok |
| **B enroll** | fresh sidecar → `POST /v1/enroll` | **200**; `box_uuid`+`api_key` returned once; `enrollment_audit=enroll_ok_new` |
| **C sidecar** | `test -S /run/fcm-sidecar/sock`; `healthz` (full); `grep VmSwap /proc/1/status` | `central_reachable=true`; **`VmSwap == 0 kB`** (secrets never swapped — SH-1); no CrashLoop; startup log shows `memlock_posture mlockall=disabled(SH-1)` |
| **D Odoo→bearer** | from odoo container `test -S sock`; force a cache-miss | one miss→vend→200 in sidecar log |
| **E real push** | device / app ack with correlation-id | receipt confirmed (FCM 200 ≠ delivered) |

**Self-enroll decision-table fingerprints** (for triage):
- **401** → SA token audience/name wrong (check projected `audience: central` + SA name `fcm-sidecar`).
- **403 `no_mapping`** → `namespace_tenant_map` row missing (onboarding didn't write it).
- **403 `revoked`** → tenant revoked (expected; no resurrection).
- **503** → whitelist-service or k8s TokenReview transiently unavailable → sidecar retries (availability-negative, NOT collapsed into "proceed").

**mlockall-fail vs central-fail (mutually exclusive):** mlockall fail → socket never binds + log `mlockall_failed` + CapEff lacks ipc_lock. central fail → socket binds but `central_reachable=false`.

---

## 7. Rollback / revoke / rotate

- **Rollback central:** `kubectl delete -k fcm-push/woow-fcm-central` (drops the whole namespace). Tenants keep their cached bearer ≤1h; enroll/issue fail-closed after.
- **Revoke a tenant:** set the tenant's box `status='revoked'` in `boxes`. Re-enroll → 403. Cached bearer expires ≤1h (online-recoverable revocation window).
- **Rotate api_key:** simply re-enroll the (non-revoked) verified identity → central rotates (new key/hash, old invalidated). For a wedged emptyDir sidecar: delete the pod to clear state → it self-enrolls fresh on restart.
- **Kill switch:** revoke + remove the `namespace_tenant_map` row → re-enroll refused (403 `no_mapping`).

---

## 8. Security non-negotiables (from adversarial review)

1. TokenReview MUST verify `aud=central` AND pin SA name `fcm-sidecar` (namespace membership alone ≠ authorization, CWE-863).
2. Enroll body MUST NOT accept tenant_id/namespace (identity only from the verifier).
3. Unmapped namespace → fail-closed 403; a 503 is never collapsed into "no mapping → proceed".
4. api_key hashed at rest; rotate-not-reissue; revoked never resurrected.
5. No plaintext credentials in the Odoo plugin, ever. No master SA outside central memory.
6. NetworkPolicy is load-bearing (it replaces the compose `internal:true` isolation): enroll(8000)+issue(8001) ingress from `fcm-sidecar` pods only; postgres ingress from whitelist/TVS only. **No policy = no deploy.**
7. GHCR pull secret in production = a dedicated `read:packages`-only PAT, git-ignored. Never commit any token, box_uuid, api_key, or SA key.

---

## 9. Git model (anti-pollution)

```
Woow_openclaw_docker_compose_all
├── main ─────────────── feature/fcm-optionH-selfenroll   ← FCM manifests + this runbook
│                          fcm-push/
│                            woow-fcm-central/   (central 8-file + rbac + migration)
│                            fcm-on-odoo/        (per-tenant sidecar OVERLAY template)
│                            DEPLOY-RUNBOOK.md   README.md   .gitignore
└── vk/989e-woow-k3s-odoo (bnidistrict) ... other client branches ← UNTOUCHED
```
- Persist by opening a **PR against `main`** from `feature/fcm-optionH-selfenroll`; **do not merge without human review**.
- Adoption per client: that client's onboarding applies the `fcm-on-odoo/` overlay onto its **own** branch — never the reverse.

---

## 10. Deviations / open items (flag to reviewers)

- **Provision model:** self-enroll (SE-1) replaces the admin-UI `POST /admin/ui/provision` manual path for Mode A tenants. Manual UI provision remains available (Mode B / fallback).
- **Mode B (HAOS set-top-box) enroll-token flow:** deferred (SE-1 Task 6). `enroll_tokens` table + `{type:"enroll-token"}` dispatch point exist; the single-use consume verifier is a follow-up story.
- **whitelist-service single-replica:** in-process idempotency/audit — multi-replica needs the check_and_claim/audit sink moved to the DB (separate follow-up).
- **Native sidecar (k8s ≥1.29):** prefer `initContainers` + `restartPolicy: Always` to guarantee start order + graceful shutdown (kills the socket-bind race). Confirm against the E2E-chosen shape.
- **mlockall observability:** `hardening.go` could discriminate EPERM/ENOMEM + log `IPC_LOCK` (non-blocking nice-to-fix).

---

## 11. Known issues (from the E2E) — MUST fix before production

### 11.1 ✅ RESOLVED (Story SH-1) — verified on real k3s 2026-07-05

process-wide `mlockall(MCL_FUTURE)` was **removed** from the sidecar (`hardening.Apply`). Anti-swap is
delegated to the **node layer** (no-swap pods; acceptance = `VmSwap==0`); `LockedBuffer` (tested) is
available for targeted locking but intentionally unwired (PO decision: 2/3 secrets are on disk, the
bearer is a copied Go string → in-process locking is near-theatre). The `IPC_LOCK` capability is
**dropped** from the sidecar spec. **On-cluster result (commit 2a00d55 image, fcm-selftest):**
`restartCount=0, 1/1 Ready` — **CrashLoop fixed**; startup log `memlock_posture:
mlockall=disabled(SH-1); rlimit_memlock_bytes=8388608; anti-swap=node-layer(VmSwap==0)`; **`VmSwap: 0
kB`**; socket + healthz serving; self-enroll `200` + api_key rotation confirmed. (Real Google token
vend, Layer D, is gated on installing the real master SA — an environmental secret, not an SH-1 gap.)

<details><summary>Original blocker (for history)</summary>

**Symptom (E2E 2026-07-05):**

**Symptom (E2E 2026-07-05):**
```
{"level":"ERROR","msg":"hardening failed","err":"hardening: mlockall_failed: cannot allocate memory"}
```
**Root cause:** `mlockall(MCL_CURRENT|MCL_FUTURE)` tries to lock the *entire* current +
future address space. The Go runtime maps hundreds of MB of virtual address space, which
exceeds the container's **8 MiB `RLIMIT_MEMLOCK`** → `ENOMEM`. Getting `ENOMEM` (not
`EPERM`) means the limit is being enforced — i.e. **`CAP_IPC_LOCK` is not effective** for
the non-root (uid 10001) process as configured (with the cap effective, the limit is
bypassed). This is the R1 gate from `k3s-deployment-technical-data.md` §6 failing in
practice (the paper analysis guessed it would "likely" pass — the E2E proved otherwise).

**Impact:** enrollment is unaffected (it runs *before* hardening, main.go 58→74), but the
sidecar fail-closes (exit 1) immediately after → pod exits → emptyDir lost → CrashLoop.
The sidecar cannot serve the local socket, so Odoo never gets a bearer. Layers C–E and DoD
3/5/6 cannot pass until this is fixed.

**Fix options (follow-up story, decide 1):**
1. **Targeted `mlock()` of only the secret-bearing pages instead of `mlockall(MCL_FUTURE)`**
   (recommended). Locks a few KB (the api_key/box_uuid/bearer buffers), fits well under
   8 MiB even without the cap, and is the correct least-privilege posture. Code change in
   `hardening.go`.
2. **Make `CAP_IPC_LOCK` effective via ambient capabilities** (a `setpriv --ambient-caps`
   wrapper, same pattern as the HAOS Mode B fix). Keeps `mlockall` but still risks ENOMEM
   under real memory pressure (locking hundreds of MB × many pods) and needs a wrapper in
   the distroless image.
3. **Raise `RLIMIT_MEMLOCK`** — k8s has no pod field for this; requires a node/runtime
   change. Not portable; not recommended.

**Interim:** do NOT ship the sidecar to a tenant until option 1 or 2 lands. Tracked as
**Story SH-1** (`_bmad-output/stories/SH-1-sidecar-mlockall-k8s-memlock-fix.md`), which also
folds in the EPERM/ENOMEM/IPC_LOCK log discrimination (R8) so the failure self-diagnoses.

</details>

### 11.2 ✅ Confirmed-correct behaviours observed
- **503-retry works:** 1st enroll got 503 (whitelist still initializing) → sidecar backed
  off 2 s → 2nd attempt 200. The availability-negative path is not collapsed into failure.
- **NetworkPolicy works:** cross-namespace `fcm-selftest → woow-fcm-central:8000` allowed;
  identity chain (authenticated, aud=central verified, SA `fcm-sidecar` matched) enforced.
- **GHCR private pull works:** all pods pulled `ghcr.io/woowtech/*` via `ghcr-pull` — the
  sudo-free image path is proven.

---

## 12. Landing this in the k3s repo + deploy cowork with the build agent

### 12.1 How our manifests "land" — yes, it's new YAML in a new directory (never editing existing files)

The k3s repo (`WOOWTECH/Woow_openclaw_docker_compose_all`) is GitOps, but **NOT kustomize** (confirmed
by the build agent reading the live repo, 2026-07-05): each namespace is a self-contained directory of
numbered YAMLs applied with **plain `kubectl apply -f <dir>/`**. There is **no root `kustomization.yaml`,
no root `deploy.sh`** that enumerates namespaces (the root `deploy.sh` is OpenClaw-specific); the
reference `odoo-deployments/bnidistrict-odoo/` has neither a `kustomization.yaml` nor a `deploy.sh` —
it is a pure `apply -f` set. Tenants coexist as sibling dirs under `odoo-deployments/`. Landing FCM push
is therefore **purely additive**:

```
# On branch feature/fcm-optionH-selfenroll (off main) — NOT any client branch:
fcm-push/
  woow-fcm-central/                 # NEW namespace dir — a pure `kubectl apply -f` set
    00-namespace.yaml … 07-networkpolicy.yaml
    08-rbac-tokenreview.yaml         # SE-1 addition (system:auth-delegator)
    run-migration.sh
  fcm-on-odoo/                       # per-tenant sidecar OVERLAY *template* (applied per client later)
    05-odoo.sidecar-overlay.yaml     # a COPY of a client 05-odoo.yaml + sidecar, $TENANT placeholders
    fcm-sidecar-sa.yaml
  DEPLOY-RUNBOOK.md  README.md  .gitignore
```

- **It is "adding new YAML", yes — exactly that.** A self-contained `fcm-push/` tree. **No existing
  file needs editing** — no root orchestrator, no shared kustomization, no manifest registry. We do
  **not** modify any tenant's `05-odoo.yaml` on its client branch; the sidecar bits live as a
  **template** in `fcm-on-odoo/`, adopted per client during that client's onboarding (§5).
- Central deploys with `kubectl apply -f fcm-push/woow-fcm-central/`. Existing deployments are
  untouched because it's a brand-new namespace + a brand-new directory.
- **SH-1 template change:** the sidecar container in `05-odoo.sidecar-overlay.yaml` **drops
  `capabilities.add: [IPC_LOCK]`** (no longer needed) and the tenant pods are marked no-swap.

### 12.2 Deploy cowork with the vibekanban build agent (post-SH-1 image rebuild)

The build agent (on the cluster node) owns image build/push + `kubectl`; we own the code + manifests.
The handoff after an SH-1 code change:

1. **We** commit+push the sidecar change to `woow_odoo_fcm_push@feature/optionH-prime` (the trigger).
2. **Agent** pulls that commit → `podman build` the sidecar → `podman push ghcr.io/woowtech/fcm-sidecar:dev`
   (the proven sudo-free path, §3).
3. **Agent** redeploys the `fcm-selftest` sidecar pod (IPC_LOCK cap dropped, no-swap) — a fresh pod, no
   existing tenant touched.
4. **Agent verifies (SH-1 Task 5 / §6 Layer C):** pod **Ready, no CrashLoop**; startup log shows
   `memlock_posture ... mlockall=disabled(SH-1)`; `grep VmSwap /proc/1/status` **== 0 kB**;
   `healthz central_reachable=true`; then a Layer C→D vend (the piece the first E2E could not finish
   because the sidecar CrashLooped).
5. **Agent reports** the results back; we reconcile §11.1 to fully "resolved".

All of the above stays in throwaway namespaces (`woow-fcm-central`, `fcm-selftest`) + `/tmp/se1-scratch`;
nothing is committed to a client branch. Persisting the reviewed templates to
`feature/fcm-optionH-selfenroll` (§12.1) happens only after human review.

---

_Authored 2026-07-05 alongside SE-1 + SH-1 E2E. Verified on real k3s cluster:
self-enroll PASS, SH-1 mlockall fix PASS, real iPhone push PASS. Committed to
`fcm-push/DEPLOY-RUNBOOK.md` on `feature/fcm-optionH-selfenroll`._
