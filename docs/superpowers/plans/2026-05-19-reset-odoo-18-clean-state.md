# Reset Inzense Odoo 18 to Clean State — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wipe the Inzense Odoo 18 database and filestore, then reinitialize with only the `base` module for a completely fresh start.

**Architecture:** Delete PostgreSQL data PVC and Odoo filestore PVC while preserving the namespace, Cloudflare Tunnel, addons PVC, secrets, and ConfigMap. Modify the existing init job manifest to only install `base`, then re-run it against a fresh PostgreSQL instance.

**Tech Stack:** K3s (Kubernetes), kubectl CLI, PostgreSQL 16, Odoo 18.0

**Spec:** `docs/superpowers/specs/2026-05-19-reset-odoo-18-clean-state-design.md`

---

### Task 1: Pre-flight checks

Verify current cluster state before making destructive changes.

**Files:** None (read-only operations)

- [ ] **Step 1: Verify namespace and deployments exist**

```bash
kubectl get namespace inzense
kubectl get deployments -n inzense
```

Expected: namespace `inzense` exists, deployments `inzense-odoo`, `inzense-postgres`, and `inzense-cloudflared` are listed.

- [ ] **Step 2: Verify PVCs exist**

```bash
kubectl get pvc -n inzense
```

Expected: three PVCs listed — `inzense-postgres-pvc`, `inzense-odoo-filestore-pvc`, `inzense-odoo-addons-pvc`, all `Bound`.

- [ ] **Step 3: Verify Cloudflare Tunnel is running**

```bash
kubectl get pods -n inzense -l app=cloudflared --no-headers
```

Expected: one pod in `Running` status. This pod must remain untouched throughout.

---

### Task 2: Scale down Odoo

Stop Odoo first so it releases its PVC mounts cleanly.

**Files:** None

- [ ] **Step 1: Scale Odoo to 0 replicas**

```bash
kubectl scale deployment inzense-odoo -n inzense --replicas=0
```

Expected: `deployment.apps/inzense-odoo scaled`

- [ ] **Step 2: Wait for Odoo pod to terminate**

```bash
kubectl wait --for=delete pod -l app.kubernetes.io/name=inzense-odoo,app.kubernetes.io/component=application -n inzense --timeout=120s 2>/dev/null; kubectl get pods -n inzense -l app.kubernetes.io/component=application --no-headers
```

Expected: no Odoo application pods listed (or "No resources found").

---

### Task 3: Scale down PostgreSQL

Stop PostgreSQL so its PVC can be deleted.

**Files:** None

- [ ] **Step 1: Scale PostgreSQL to 0 replicas**

```bash
kubectl scale deployment inzense-postgres -n inzense --replicas=0
```

Expected: `deployment.apps/inzense-postgres scaled`

- [ ] **Step 2: Wait for PostgreSQL pod to terminate**

```bash
kubectl wait --for=delete pod -l app.kubernetes.io/name=inzense-odoo,app.kubernetes.io/component=database -n inzense --timeout=120s 2>/dev/null; kubectl get pods -n inzense -l app.kubernetes.io/component=database --no-headers
```

Expected: no database pods listed (or "No resources found").

---

### Task 4: Delete data PVCs

Permanently destroy PostgreSQL data and Odoo filestore. **This is irreversible.**

**Files:** None

- [ ] **Step 1: Delete PostgreSQL PVC**

```bash
kubectl delete pvc inzense-postgres-pvc -n inzense
```

Expected: `persistentvolumeclaim "inzense-postgres-pvc" deleted`

- [ ] **Step 2: Delete Odoo filestore PVC**

```bash
kubectl delete pvc inzense-odoo-filestore-pvc -n inzense
```

Expected: `persistentvolumeclaim "inzense-odoo-filestore-pvc" deleted`

- [ ] **Step 3: Verify only addons PVC remains**

```bash
kubectl get pvc -n inzense
```

Expected: only `inzense-odoo-addons-pvc` listed, still `Bound`.

---

### Task 5: Recreate PVCs

**Files:**
- Read: `manifests/03-pvc.yaml`

- [ ] **Step 1: Apply PVC manifest**

```bash
kubectl apply -f "manifests/03-pvc.yaml"
```

Expected output (addons PVC unchanged, two new PVCs created):
```
persistentvolumeclaim/inzense-postgres-pvc created
persistentvolumeclaim/inzense-odoo-filestore-pvc created
persistentvolumeclaim/inzense-odoo-addons-pvc unchanged
```

- [ ] **Step 2: Verify all three PVCs exist**

```bash
kubectl get pvc -n inzense
```

Expected: three PVCs listed. The two new ones may show `Pending` until a pod mounts them (normal for `local-path` provisioner).

---

### Task 6: Start PostgreSQL

**Files:** None

- [ ] **Step 1: Scale PostgreSQL back up**

```bash
kubectl scale deployment inzense-postgres -n inzense --replicas=1
```

Expected: `deployment.apps/inzense-postgres scaled`

- [ ] **Step 2: Wait for PostgreSQL to become Ready**

```bash
kubectl rollout status deployment/inzense-postgres -n inzense --timeout=120s
```

Expected: `deployment "inzense-postgres" successfully rolled out`

- [ ] **Step 3: Verify PostgreSQL is accepting connections**

```bash
kubectl exec deployment/inzense-postgres -n inzense -- pg_isready -U inzense -d inzense
```

Expected: `inzense-postgres:5432 - accepting connections` (or similar success message). Note: on first boot with an empty PVC, PostgreSQL initializes a fresh data directory and creates the `inzense` database automatically (via `POSTGRES_DB` env var).

---

### Task 7: Modify init job manifest

Strip the init job down to only install `base`.

**Files:**
- Modify: `manifests/07-init-db-job.yaml:46-47`

- [ ] **Step 1: Edit the init job manifest**

In `manifests/07-init-db-job.yaml`, replace lines 46-47:

**Before:**
```yaml
            - --init=base,contacts,project,calendar,mail,account,mrp,point_of_sale,stock,website,website_sale,loyalty,website_blog,purchase,sale_management,hr,crm
            - --load-language=zh_TW
```

**After:**
```yaml
            - --init=base
```

This removes all modules except `base` and removes the `zh_TW` language loading.

- [ ] **Step 2: Verify the change**

```bash
grep -n "init=" "manifests/07-init-db-job.yaml"
```

Expected: one line showing `--init=base` only.

```bash
grep "load-language" "manifests/07-init-db-job.yaml"
```

Expected: no output (line removed).

- [ ] **Step 3: Commit the manifest change**

```bash
git add manifests/07-init-db-job.yaml
git commit -m "Simplify init job to only install base module for clean reset"
```

---

### Task 8: Run init job

**Files:** None

- [ ] **Step 1: Delete old init job if it exists**

```bash
kubectl delete job inzense-odoo-init -n inzense --ignore-not-found
```

Expected: either `job.batch "inzense-odoo-init" deleted` or `No resources found`.

- [ ] **Step 2: Apply the init job**

```bash
kubectl apply -f "manifests/07-init-db-job.yaml"
```

Expected: `job.batch/inzense-odoo-init created`

- [ ] **Step 3: Wait for the init job to complete**

```bash
kubectl wait --for=condition=complete job/inzense-odoo-init -n inzense --timeout=600s
```

Expected: `job.batch/inzense-odoo-init condition met`

If it fails, check logs:
```bash
kubectl logs job/inzense-odoo-init -n inzense --tail=50
```

- [ ] **Step 4: Verify job succeeded**

```bash
kubectl get job inzense-odoo-init -n inzense
```

Expected: `COMPLETIONS` shows `1/1`.

---

### Task 9: Start Odoo

**Files:** None

- [ ] **Step 1: Scale Odoo back up**

```bash
kubectl scale deployment inzense-odoo -n inzense --replicas=1
```

Expected: `deployment.apps/inzense-odoo scaled`

- [ ] **Step 2: Wait for Odoo to become Ready**

```bash
kubectl rollout status deployment/inzense-odoo -n inzense --timeout=300s
```

Expected: `deployment "inzense-odoo" successfully rolled out`

---

### Task 10: Verify clean state

**Files:** None

- [ ] **Step 1: Check all pods are healthy**

```bash
kubectl get pods -n inzense
```

Expected: `inzense-odoo-*` Running/Ready, `inzense-postgres-*` Running/Ready, `inzense-cloudflared-*` Running, init job pod `Completed`.

- [ ] **Step 2: Verify Odoo responds via port-forward**

```bash
kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069 &
PF_PID=$!
sleep 3
curl -s -o /dev/null -w "%{http_code}" http://localhost:8069/web/health
kill $PF_PID 2>/dev/null
```

Expected: HTTP status `200`.

- [ ] **Step 3: Verify only base module is installed via XML-RPC**

```bash
kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069 &
PF_PID=$!
sleep 3
python3 -c "
import xmlrpc.client
url = 'http://localhost:8069'
db = 'inzense'
uid = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common').authenticate(db, 'admin', 'admin', {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
installed = models.execute_kw(db, uid, 'admin', 'ir.module.module', 'search_read',
    [[['state', '=', 'installed']]],
    {'fields': ['name'], 'order': 'name'})
print(f'Total installed modules: {len(installed)}')
for m in installed:
    print(f'  - {m[\"name\"]}')
"
kill $PF_PID 2>/dev/null
```

Expected: a small number of modules (base + its auto-dependencies like `bus`, `web`, `web_editor`, etc.), and critically **no** `point_of_sale`, `sale_management`, `website`, `crm`, `mrp`, `project`, `account`, or `stock`.

- [ ] **Step 4: Verify Cloudflare Tunnel still works**

```bash
curl -s -o /dev/null -w "%{http_code}" https://inzense-odoo.woowtech.io/web/health
```

Expected: HTTP status `200` — confirms the tunnel is still routing to Odoo correctly.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "Reset Odoo 18 to clean base-only state — verified working"
```

(Only if there are any remaining uncommitted changes.)
