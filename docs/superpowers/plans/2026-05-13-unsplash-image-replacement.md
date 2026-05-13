# Unsplash Image Replacement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all 10 website images with Unsplash sports massage/stretching photos and add CSS grayscale filter for Retrodandy aesthetic.

**Architecture:** Use Unsplash API to search and download images to `static/src/img/`, overwriting existing files (same filenames = zero template changes). Add CSS grayscale filter rules. Footer credit added in homepage template.

**Tech Stack:** Unsplash API (curl), CSS filters, Odoo QWeb templates

**Spec:** `docs/superpowers/specs/2026-05-13-unsplash-image-replacement-design.md`

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `markstudio_website/static/src/img/hero-bg.jpg` | Replace | Hero background |
| `markstudio_website/static/src/img/svc-01-massage.jpg` | Replace | Service 01 + Booking card |
| `markstudio_website/static/src/img/svc-02-stretch.jpg` | Replace | Service 02 |
| `markstudio_website/static/src/img/svc-03-personal.jpg` | Replace | Service 03 |
| `markstudio_website/static/src/img/tech-left.jpg` | Replace | Technique left |
| `markstudio_website/static/src/img/tech-right.jpg` | Replace | Technique right |
| `markstudio_website/static/src/img/exp-01-consult.jpg` | Replace | Experience step 1 |
| `markstudio_website/static/src/img/exp-02-measure.jpg` | Replace | Experience step 2 |
| `markstudio_website/static/src/img/exp-03-stretch.jpg` | Replace | Experience step 3 |
| `markstudio_website/static/src/img/exp-04-advice.jpg` | Replace | Experience step 4 |
| `markstudio_website/static/src/css/markstudio.css` | Modify | Add grayscale filter (~6 lines) |
| `markstudio_website/views/homepage_templates.xml` | Modify | Add Unsplash credit in contact section |

---

### Task 1: Search and download hero + service images (4 images)

**Files:**
- Replace: `markstudio_website/static/src/img/hero-bg.jpg`
- Replace: `markstudio_website/static/src/img/svc-01-massage.jpg`
- Replace: `markstudio_website/static/src/img/svc-02-stretch.jpg`
- Replace: `markstudio_website/static/src/img/svc-03-personal.jpg`

**Requirements per image:**
- Faceless (no visible faces), sports massage/stretching theme
- Landscape orientation
- hero-bg: ≥1920w, svc-*: ~800w

- [ ] **Step 1: Search Unsplash for hero background**

```bash
curl -s "https://api.unsplash.com/search/photos?query=sports+massage+back&orientation=landscape&per_page=5" \
  -H "Authorization: Client-ID ACCESS_KEY" | python3 -c "
import json,sys
data=json.load(sys.stdin)
for p in data['results']:
    print(p['id'], p['urls']['regular'][:80], p['alt_description'] or '')
"
```

Review results. Pick one that shows hands pressing on back/shoulders, no face visible. Note the photo ID.

- [ ] **Step 2: Download hero-bg.jpg**

```bash
# Download the chosen photo (replace PHOTO_URL with urls.raw + size params)
curl -L "PHOTO_URL?w=1920&h=1080&fit=crop" \
  -o markstudio_website/static/src/img/hero-bg.jpg

# Trigger Unsplash download tracking (API requirement)
curl -s "https://api.unsplash.com/photos/PHOTO_ID/download" \
  -H "Authorization: Client-ID ACCESS_KEY" > /dev/null
```

- [ ] **Step 3: Search and download svc-01-massage.jpg**

```bash
curl -s "https://api.unsplash.com/search/photos?query=deep+tissue+massage+hands&orientation=landscape&per_page=5" \
  -H "Authorization: Client-ID ACCESS_KEY" | python3 -c "
import json,sys
data=json.load(sys.stdin)
for p in data['results']:
    print(p['id'], p['urls']['regular'][:80], p['alt_description'] or '')
"
```

Pick a photo showing therapist hands pressing muscle. Download:

```bash
curl -L "PHOTO_URL?w=800&fit=crop" \
  -o markstudio_website/static/src/img/svc-01-massage.jpg
curl -s "https://api.unsplash.com/photos/PHOTO_ID/download" \
  -H "Authorization: Client-ID ACCESS_KEY" > /dev/null
```

- [ ] **Step 4: Search and download svc-02-stretch.jpg**

Search: `assisted+stretching+leg` or `passive+stretch+therapy`, landscape. Pick faceless stretching action shot. Download at w=800.

- [ ] **Step 5: Search and download svc-03-personal.jpg**

Search: `personal+training+stretch` or `one+on+one+stretching`, landscape. Pick a two-person scene with no faces. Download at w=800.

- [ ] **Step 6: Verify all 4 images**

```bash
ls -la markstudio_website/static/src/img/hero-bg.jpg \
      markstudio_website/static/src/img/svc-01-massage.jpg \
      markstudio_website/static/src/img/svc-02-stretch.jpg \
      markstudio_website/static/src/img/svc-03-personal.jpg
# All should be > 10KB (valid JPEG files)
file markstudio_website/static/src/img/*.jpg | head -4
# All should show "JPEG image data"
```

- [ ] **Step 7: Commit**

```bash
git add markstudio_website/static/src/img/hero-bg.jpg \
        markstudio_website/static/src/img/svc-01-massage.jpg \
        markstudio_website/static/src/img/svc-02-stretch.jpg \
        markstudio_website/static/src/img/svc-03-personal.jpg
git commit -m "Replace hero and service images with Unsplash sports massage photos"
```

---

### Task 2: Search and download technique + experience images (6 images)

**Files:**
- Replace: `markstudio_website/static/src/img/tech-left.jpg`
- Replace: `markstudio_website/static/src/img/tech-right.jpg`
- Replace: `markstudio_website/static/src/img/exp-01-consult.jpg`
- Replace: `markstudio_website/static/src/img/exp-02-measure.jpg`
- Replace: `markstudio_website/static/src/img/exp-03-stretch.jpg`
- Replace: `markstudio_website/static/src/img/exp-04-advice.jpg`

- [ ] **Step 1: Search and download tech-left.jpg**

Search: `massage+technique+close+up` or `thumb+pressure+massage`, landscape. Pick close-up of hand technique. Download at w=600.

- [ ] **Step 2: Search and download tech-right.jpg**

Search: `hip+flexor+stretch` or `core+stretching+therapy`, landscape. Pick torso/hip stretch action. Download at w=600.

- [ ] **Step 3: Search and download exp-01-consult.jpg**

Search: `physical+assessment+shoulder` or `body+palpation`, landscape. Pick consultation/examination close-up. Download at w=400.

- [ ] **Step 4: Search and download exp-02-measure.jpg**

Search: `flexibility+test` or `range+of+motion+measurement`, landscape. Pick flexibility measurement action. Download at w=400.

- [ ] **Step 5: Search and download exp-03-stretch.jpg**

Search: `stretching+therapy+session` or `assisted+stretch+arms`, landscape. Pick active stretching scene. Download at w=400.

- [ ] **Step 6: Search and download exp-04-advice.jpg**

Search: `therapist+clipboard+notes` or `fitness+consultation+writing`, landscape. Pick clipboard/notes close-up. Download at w=400.

- [ ] **Step 7: Verify all 6 images**

```bash
file markstudio_website/static/src/img/tech-*.jpg markstudio_website/static/src/img/exp-*.jpg
# All should show "JPEG image data"
```

- [ ] **Step 8: Commit**

```bash
git add markstudio_website/static/src/img/tech-left.jpg \
        markstudio_website/static/src/img/tech-right.jpg \
        markstudio_website/static/src/img/exp-01-consult.jpg \
        markstudio_website/static/src/img/exp-02-measure.jpg \
        markstudio_website/static/src/img/exp-03-stretch.jpg \
        markstudio_website/static/src/img/exp-04-advice.jpg
git commit -m "Replace technique and experience images with Unsplash photos"
```

---

### Task 3: Add CSS grayscale filter + Unsplash credit

**Files:**
- Modify: `markstudio_website/static/src/css/markstudio.css` (line 41, modify existing hero filter)
- Modify: `markstudio_website/static/src/css/markstudio.css` (after line 242, add new rules before services section images)
- Modify: `markstudio_website/views/homepage_templates.xml` (line ~255, add credit in contact section)

- [ ] **Step 1: Update hero background filter**

In `markstudio.css`, change the existing `.mk-hero-bg` filter from:
```css
filter: brightness(0.6);
```
to:
```css
filter: grayscale(1) brightness(0.5);
```

- [ ] **Step 2: Add grayscale filter for all content images**

In `markstudio.css`, add after the `.mk-step-img img` rule block (around line 252):

```css
/* Retrodandy grayscale — all content images */
.mk-svc-img img,
.mk-step-img img,
.mk-booking-card-img img {
    filter: grayscale(1) brightness(0.85);
}
```

- [ ] **Step 3: Add Unsplash credit in homepage contact section**

In `homepage_templates.xml`, add after the last `.mk-contact-item` div (around line 255):

```xml
<div class="mk-contact-item">
    <span class="mk-contact-label">Photos</span>
    <a href="https://unsplash.com" class="mk-contact-link" target="_blank" rel="noopener noreferrer">Unsplash</a>
</div>
```

- [ ] **Step 4: Commit**

```bash
git add markstudio_website/static/src/css/markstudio.css \
        markstudio_website/views/homepage_templates.xml
git commit -m "Add grayscale filter for Retrodandy aesthetic and Unsplash credit"
```

---

### Task 4: Deploy and verify

- [ ] **Step 1: Deploy to Odoo pod**

```bash
POD=$(kubectl get pod -n markstudio-odoo -l app=odoo -o jsonpath='{.items[0].metadata.name}')
tar czf /tmp/markstudio_website.tar.gz -C . markstudio_website/
kubectl cp /tmp/markstudio_website.tar.gz markstudio-odoo/${POD}:/tmp/markstudio_website.tar.gz -c odoo
kubectl exec -n markstudio-odoo ${POD} -c odoo -- tar xzf /tmp/markstudio_website.tar.gz -C /mnt/extra-addons/
rm -f /tmp/markstudio_website.tar.gz
```

- [ ] **Step 2: Upgrade module**

```bash
kubectl exec -n markstudio-odoo ${POD} -c odoo -- python3 -c "
import xmlrpc.client
url='http://localhost:8069'; db='markstudio'; pwd='admin'
uid=xmlrpc.client.ServerProxy(url+'/xmlrpc/2/common').authenticate(db,'admin',pwd,{})
m=xmlrpc.client.ServerProxy(url+'/xmlrpc/2/object')
ids=m.execute_kw(db,uid,pwd,'ir.module.module','search',[[['name','=','markstudio_website']]])
m.execute_kw(db,uid,pwd,'ir.module.module','button_immediate_upgrade',[ids])
print('Upgraded')
"
```

- [ ] **Step 3: Visual verification with Playwright**

Check desktop (1280x720):
```bash
playwright-cli open https://markstudio-odoo.woowtech.io
playwright-cli screenshot --filename=verify-desktop.png
```

Check mobile (390x844):
```bash
playwright-cli resize 390 844
playwright-cli reload
playwright-cli screenshot --filename=verify-mobile.png
```

Verify:
1. All images load (no broken images)
2. All images are displayed in grayscale
3. Hero background is dark and grayscale
4. Unsplash credit visible in contact/footer section
5. No faces visible in any image

- [ ] **Step 4: Clean up verification screenshots**

```bash
rm -f verify-desktop.png verify-mobile.png
```
