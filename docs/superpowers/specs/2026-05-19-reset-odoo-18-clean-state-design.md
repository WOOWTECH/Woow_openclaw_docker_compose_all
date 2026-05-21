# Design: Reset Inzense Odoo 18 to Clean Initial State

## Goal

Completely reset the Inzense Odoo 18 database and filestore back to a bare Odoo 18 installation with only the `base` module installed. The system should be in the most minimal, clean state possible — ready for a fresh rebuild.

## Decisions

| Item | Decision |
|---|---|
| Target state | Bare Odoo 18, only `base` module |
| WOOWTECH Addons PVC | Keep as-is, not installed |
| Odoo Filestore PVC | Delete and recreate |
| PostgreSQL Data PVC | Delete and recreate |
| Language / Locale | Traditional Chinese (zh_TW) / Asia/Taipei |
| Init Job | Modify existing `07-init-db-job.yaml` to only init `base` |
| ConfigMap (`odoo.conf`) | No changes |
| Cloudflare Tunnel | Untouched |
| Addons PVC | Untouched |
| Namespace / Secrets | Untouched |

## What Gets Destroyed

- PostgreSQL database `inzense` — all tables, all data
- Odoo filestore — all uploaded files, attachments, images
- All product data (188 products), POS configuration, AI configuration
- All theme/visual customizations applied via scripts

## What Is Preserved

- K3s namespace `inzense`
- Cloudflare Tunnel deployment and secret (`08-cloudflared.yaml`)
- WOOWTECH addons files on `inzense-odoo-addons-pvc`
- All K8s Secrets (`inzense-db-secret`, `github-token`)
- ConfigMap `odoo-config` (`odoo.conf`)
- All scripts in `scripts/` directory (for future re-use)
- All images in `images/` directory

## Execution Plan

### Step 1: Scale Down Odoo

```bash
kubectl scale deployment inzense-odoo -n inzense --replicas=0
```

Stop the Odoo application first to release PVC claims cleanly.

### Step 2: Scale Down PostgreSQL

```bash
kubectl scale deployment inzense-postgres -n inzense --replicas=0
```

Stop PostgreSQL to release the data PVC.

### Step 3: Delete Data PVCs

```bash
kubectl delete pvc inzense-postgres-pvc -n inzense
kubectl delete pvc inzense-odoo-filestore-pvc -n inzense
```

This permanently destroys all database data and uploaded files. Addons PVC (`inzense-odoo-addons-pvc`) is NOT deleted.

### Step 4: Recreate PVCs

```bash
kubectl apply -f manifests/03-pvc.yaml
```

This recreates all three PVCs (postgres, filestore, addons). Since addons PVC already exists, only the deleted two will be created.

### Step 5: Start PostgreSQL

```bash
kubectl scale deployment inzense-postgres -n inzense --replicas=1
```

Wait for PostgreSQL to become Ready before proceeding. The fresh PVC means PostgreSQL will initialize a new empty data directory.

### Step 6: Modify Init Job Manifest

Edit `manifests/07-init-db-job.yaml`:

**Before:**
```yaml
- --init=base,contacts,project,calendar,mail,account,mrp,point_of_sale,stock,website,website_sale,loyalty,website_blog,purchase,sale_management,hr,crm
- --load-language=zh_TW
```

**After:**
```yaml
- --init=base
- --load-language=zh_TW
```

Changes:
- Remove all modules except `base`
- Keep `--load-language=zh_TW` for Taiwan locale

### Step 7: Delete Old Init Job (if exists)

```bash
kubectl delete job inzense-odoo-init -n inzense --ignore-not-found
```

K8s Jobs are immutable once created; must delete before re-applying.

### Step 8: Run Init Job

```bash
kubectl apply -f manifests/07-init-db-job.yaml
```

Wait for the job to complete successfully. This creates the `inzense` database with only the `base` module.

### Step 9: Start Odoo

```bash
kubectl scale deployment inzense-odoo -n inzense --replicas=1
```

### Step 10: Verify

- Check Odoo pod is Running and Ready
- Access `https://inzense-odoo.woowtech.io/` (or port-forward to `localhost:8069`)
- Confirm the Odoo login screen appears
- Login with `admin` / `admin`
- Verify only `base` module is installed (Settings > Apps)
- Confirm no products, no POS, no contacts, no custom data

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| PVC deletion might hang if pod still has a mount | Scale down deployments first (Steps 1-2) |
| Init job fails | `backoffLimit: 2` allows retries; check logs with `kubectl logs job/inzense-odoo-init -n inzense` |
| Cloudflare Tunnel shows error during downtime | Expected — tunnel remains up but Odoo backend is temporarily unavailable. Resolves after Step 9 |
| Addons PVC re-creation conflict | `kubectl apply` is idempotent — existing PVC won't be modified |

## Rollback

There is no rollback for this operation. Once PVCs are deleted, all data is permanently lost. This is intentional — the goal is a clean slate.

If a rollback were needed, it would require:
1. Re-running all 49 setup scripts in order
2. Or restoring from a backup (none currently exists)
