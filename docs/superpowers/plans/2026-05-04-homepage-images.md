# Homepage Images Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all gray placeholder images on the Mark Studio homepage with real photos from Unsplash, making the site look production-ready.

**Architecture:** Download 10 free-license images from Unsplash source URLs (no API key needed), save to the module's `static/src/img/` directory, update the QWeb template to use `<img>` tags referencing Odoo static paths, update CSS for hero background-image, then redeploy the module to K8s.

**Tech Stack:** Unsplash (source images), curl (download), Odoo QWeb XML templates, CSS background-image, kubectl (deploy)

---

## File Structure

```
markstudio_website/
  static/src/
    img/                          ← CREATE directory
      hero-bg.jpg                 ← Hero full-viewport background
      svc-01-massage.jpg          ← Service 01: deep tissue massage
      svc-02-stretch.jpg          ← Service 02: relaxation stretch
      svc-03-personal.jpg         ← Service 03: one-on-one session
      tech-left.jpg               ← Technique section left photo
      tech-right.jpg              ← Technique section right photo
      exp-01-consult.jpg          ← Experience step 01: consultation
      exp-02-measure.jpg          ← Experience step 02: measurement
      exp-03-stretch.jpg          ← Experience step 03: stretching
      exp-04-advice.jpg           ← Experience step 04: advice
    css/markstudio.css            ← MODIFY: add hero bg-image, img styles
  views/homepage_templates.xml    ← MODIFY: replace placeholders with <img>
```

## Unsplash Image Sources

Unsplash allows direct linking via `https://images.unsplash.com/<photo-id>?w=<width>&q=80&auto=format`. No API key needed for downloads. All Unsplash images are free for commercial use.

| Slot | Search Intent | Unsplash Photo ID | Description |
|------|--------------|-------------------|-------------|
| hero-bg | dark massage studio | `gJtDg6WfMlQ` | Dark gym/studio environment |
| svc-01 | deep tissue massage | `nOvIa_x_tfo` | Professional massage close-up |
| svc-02 | stretching relaxed | `CQfNt66ttZM` | Person being stretched |
| svc-03 | personal trainer | `20jX9b35r_M` | One-on-one training session |
| tech-left | massage technique | `UFHZOySNFgc` | Massage therapy technique |
| tech-right | anatomy muscles | `R-LK3sqLiBw` | Fitness/body anatomy |
| exp-01 | consultation | `5fNmWej4tAA` | Health consultation |
| exp-02 | flexibility test | `gkbCKxqZ2Hc` | Body assessment |
| exp-03 | stretching action | `pFyKRmDiWEA` | Active stretching |
| exp-04 | trainer advice | `sHfo3WOgGTU` | Trainer giving advice |

**Note:** Unsplash photo IDs may become unavailable. If any download fails, search Unsplash manually for a replacement with similar terms and download at 1200px width.

---

### Task 1: Create image directory and download all images

**Files:**
- Create: `markstudio_website/static/src/img/` (directory)
- Create: 10 `.jpg` files in that directory

- [ ] **Step 1: Create the img directory**

```bash
mkdir -p "/var/tmp/vibe-kanban/worktrees/925d-/k3s project/markstudio_website/static/src/img"
```

- [ ] **Step 2: Download hero background image (1920px wide, dark/moody)**

```bash
cd "/var/tmp/vibe-kanban/worktrees/925d-/k3s project/markstudio_website/static/src/img"
curl -sL "https://images.unsplash.com/photo-1540497077202-7c8a3999166f?w=1920&q=80&auto=format" -o hero-bg.jpg
```

Verify: `file hero-bg.jpg` should show JPEG image data. If download fails (404/empty), use WebSearch to find an alternative Unsplash photo of "dark massage studio" and download at 1920px width.

- [ ] **Step 3: Download service section images (1200px wide)**

```bash
curl -sL "https://images.unsplash.com/photo-1544161515-4ab6ce6db874?w=1200&q=80&auto=format" -o svc-01-massage.jpg
curl -sL "https://images.unsplash.com/photo-1552196563-55cd4e45efb3?w=1200&q=80&auto=format" -o svc-02-stretch.jpg
curl -sL "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=1200&q=80&auto=format" -o svc-03-personal.jpg
```

Verify each: `ls -la svc-*.jpg` — each should be > 50KB.

- [ ] **Step 4: Download technique section images (800px wide)**

```bash
curl -sL "https://images.unsplash.com/photo-1519823551278-64ac92734314?w=800&q=80&auto=format" -o tech-left.jpg
curl -sL "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&q=80&auto=format" -o tech-right.jpg
```

- [ ] **Step 5: Download experience step images (600px wide, square crop)**

```bash
curl -sL "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=600&q=80&auto=format&fit=crop&crop=faces" -o exp-01-consult.jpg
curl -sL "https://images.unsplash.com/photo-1571019613576-2b22c76fd955?w=600&q=80&auto=format&fit=crop" -o exp-02-measure.jpg
curl -sL "https://images.unsplash.com/photo-1573384666979-2b1e160d2d08?w=600&q=80&auto=format&fit=crop" -o exp-03-stretch.jpg
curl -sL "https://images.unsplash.com/photo-1551836022-d5d88e9218df?w=600&q=80&auto=format&fit=crop&crop=faces" -o exp-04-advice.jpg
```

- [ ] **Step 6: Verify all 10 images downloaded successfully**

```bash
ls -lh "/var/tmp/vibe-kanban/worktrees/925d-/k3s project/markstudio_website/static/src/img/"
```

Expected: 10 `.jpg` files, each > 20KB. If any are 0 bytes or missing, re-download with an alternative Unsplash URL found via WebSearch for the corresponding search term.

- [ ] **Step 7: Commit images**

```bash
cd "/var/tmp/vibe-kanban/worktrees/925d-/k3s project"
git add markstudio_website/static/src/img/
git commit -m "Add homepage images from Unsplash for all sections"
```

---

### Task 2: Update CSS for hero background image and image styles

**Files:**
- Modify: `markstudio_website/static/src/css/markstudio.css:27-40` (hero section)
- Modify: `markstudio_website/static/src/css/markstudio.css:235-260` (placeholder/image styles)

- [ ] **Step 1: Update `.mk-hero-bg` to use the background image**

In `markstudio.css`, replace the `.mk-hero-bg` rule (around line 35):

```css
/* BEFORE */
.mk-hero-bg {
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, #222 0%, #111 100%);
    opacity: 0.9;
}

/* AFTER */
.mk-hero-bg {
    position: absolute;
    inset: 0;
    background: url('/markstudio_website/static/src/img/hero-bg.jpg') center center / cover no-repeat;
    opacity: 0.9;
}
```

- [ ] **Step 2: Add image styles for service and experience photos**

After the `.mk-placeholder-light` rule (around line 260), add:

```css
/* Real images replacing placeholders */
.mk-svc-img img,
.mk-step-img img {
    width: 100%;
    height: auto;
    display: block;
    object-fit: cover;
}

.mk-svc-img img {
    min-height: 320px;
    max-height: 400px;
    object-fit: cover;
}

.mk-step-img img {
    min-height: 200px;
    max-height: 260px;
    object-fit: cover;
}
```

- [ ] **Step 3: Commit CSS changes**

```bash
git add markstudio_website/static/src/css/markstudio.css
git commit -m "Update CSS: hero background image and img element styles"
```

---

### Task 3: Update QWeb template to replace placeholders with real images

**Files:**
- Modify: `markstudio_website/views/homepage_templates.xml`

All `<img>` tags use Odoo's static file path format: `/markstudio_website/static/src/img/<filename>.jpg`

- [ ] **Step 1: Replace Service 01 placeholder (line 67-69)**

```xml
<!-- BEFORE -->
<div class="mk-svc-img">
    <div class="mk-placeholder"><i class="fa fa-image"/>深層按摩服務照片</div>
</div>

<!-- AFTER -->
<div class="mk-svc-img">
    <img src="/markstudio_website/static/src/img/svc-01-massage.jpg" alt="深層按摩服務" loading="lazy"/>
</div>
```

- [ ] **Step 2: Replace Service 02 placeholder (line 86-88)**

```xml
<!-- BEFORE -->
<div class="mk-svc-img">
    <div class="mk-placeholder"><i class="fa fa-image"/>伸展服務照片</div>
</div>

<!-- AFTER -->
<div class="mk-svc-img">
    <img src="/markstudio_website/static/src/img/svc-02-stretch.jpg" alt="專業伸展服務" loading="lazy"/>
</div>
```

- [ ] **Step 3: Replace Service 03 placeholder (line 106-108)**

```xml
<!-- BEFORE -->
<div class="mk-svc-img">
    <div class="mk-placeholder"><i class="fa fa-image"/>一對一伸展照片</div>
</div>

<!-- AFTER -->
<div class="mk-svc-img">
    <img src="/markstudio_website/static/src/img/svc-03-personal.jpg" alt="一對一專業伸展" loading="lazy"/>
</div>
```

- [ ] **Step 4: Replace Technique section placeholders (lines 126-133)**

```xml
<!-- BEFORE -->
<div class="col-md-6">
    <div class="mk-svc-img">
        <div class="mk-placeholder mk-placeholder-light"><i class="fa fa-image"/>按摩技術照片</div>
    </div>
</div>
<div class="col-md-6">
    <div class="mk-svc-img">
        <div class="mk-placeholder mk-placeholder-light"><i class="fa fa-image"/>肌肉結構示意圖</div>
    </div>
</div>

<!-- AFTER -->
<div class="col-md-6">
    <div class="mk-svc-img">
        <img src="/markstudio_website/static/src/img/tech-left.jpg" alt="按摩技術" loading="lazy"/>
    </div>
</div>
<div class="col-md-6">
    <div class="mk-svc-img">
        <img src="/markstudio_website/static/src/img/tech-right.jpg" alt="核心肌群伸展" loading="lazy"/>
    </div>
</div>
```

- [ ] **Step 5: Replace Experience step 01 placeholder (line 148-150)**

```xml
<!-- BEFORE -->
<div class="mk-step-img">
    <div class="mk-placeholder mk-placeholder-light"><i class="fa fa-clipboard"/>問診照片</div>
</div>

<!-- AFTER -->
<div class="mk-step-img">
    <img src="/markstudio_website/static/src/img/exp-01-consult.jpg" alt="確認身體狀況" loading="lazy"/>
</div>
```

- [ ] **Step 6: Replace Experience step 02 placeholder (line 155-157)**

```xml
<div class="mk-step-img">
    <img src="/markstudio_website/static/src/img/exp-02-measure.jpg" alt="測量身體柔軟度" loading="lazy"/>
</div>
```

- [ ] **Step 7: Replace Experience step 03 placeholder (line 162-164)**

```xml
<div class="mk-step-img">
    <img src="/markstudio_website/static/src/img/exp-03-stretch.jpg" alt="伸展" loading="lazy"/>
</div>
```

- [ ] **Step 8: Replace Experience step 04 placeholder (line 169-171)**

```xml
<div class="mk-step-img">
    <img src="/markstudio_website/static/src/img/exp-04-advice.jpg" alt="提供專業建議" loading="lazy"/>
</div>
```

- [ ] **Step 9: Commit template changes**

```bash
git add markstudio_website/views/homepage_templates.xml
git commit -m "Replace all placeholder divs with real Unsplash images"
```

---

### Task 4: Deploy to K8s and verify

**Files:**
- No file changes — deployment commands only

- [ ] **Step 1: Package and copy module to pod**

```bash
cd "/var/tmp/vibe-kanban/worktrees/925d-/k3s project"
tar czf /tmp/markstudio_website.tar.gz markstudio_website/
ODOO_POD=$(kubectl get pod -n markstudio-odoo -l app=odoo -o jsonpath='{.items[0].metadata.name}')
kubectl cp /tmp/markstudio_website.tar.gz "markstudio-odoo/${ODOO_POD}:/tmp/markstudio_website.tar.gz" -c odoo
kubectl exec -n markstudio-odoo "${ODOO_POD}" -c odoo -- tar xzf /tmp/markstudio_website.tar.gz -C /mnt/extra-addons/
```

- [ ] **Step 2: Clear Odoo asset cache (forces CSS rebuild)**

```bash
kubectl exec -n markstudio-odoo deploy/odoo-db -- psql -U odoo -d markstudio \
  -c "DELETE FROM ir_attachment WHERE name LIKE '%assets%' OR url LIKE '%/web/assets%';"
```

- [ ] **Step 3: Upgrade module**

```bash
PGPASS=$(kubectl get secret odoo-secrets -n markstudio-odoo -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)
kubectl exec -n markstudio-odoo deploy/odoo -c odoo -- odoo -d markstudio \
  -u markstudio_website \
  --stop-after-init --no-http \
  --db_host=odoo-db-svc --db_port=5432 --db_user=odoo --db_password="$PGPASS"
```

Expected last line: `Stopping gracefully`

- [ ] **Step 4: Restart Odoo and wait for readiness**

```bash
kubectl rollout restart deployment/odoo -n markstudio-odoo
# Wait ~45 seconds
kubectl wait --for=condition=Ready pod -l app=odoo -n markstudio-odoo --timeout=120s
```

- [ ] **Step 5: Verify images load via playwright-cli**

```bash
kill $(lsof -ti :18069) 2>/dev/null
kubectl port-forward -n markstudio-odoo svc/odoo-web-svc 18069:8069 &
sleep 3

playwright-cli open http://localhost:18069/
# Screenshot hero
playwright-cli screenshot --filename=verify-hero.png
# Scroll to services
playwright-cli eval "window.scrollTo(0, 1200)"
playwright-cli screenshot --filename=verify-services.png
# Scroll to experience
playwright-cli eval "window.scrollTo(0, 3500)"
playwright-cli screenshot --filename=verify-experience.png

playwright-cli close
kill $(lsof -ti :18069) 2>/dev/null
```

Verify each screenshot shows real photos instead of gray placeholders.

- [ ] **Step 6: Clean up verification screenshots and final commit**

```bash
rm -f verify-*.png
git add -A
git status  # Should be clean if all was committed in prior tasks
```
