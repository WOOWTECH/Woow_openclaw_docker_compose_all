# Retrodandy Visual Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reskin the Mark Studio one-page website from Dr.stretch maroon/gold to Retrodandy black/white monochrome, updating all 9 sections' colors, fonts, corners, and buttons.

**Architecture:** Two-file change — rewrite CSS tokens and all section styles, then update the QWeb template for hero text and to remove dot-pattern divs. No structural changes to sections, routes, JS, or images.

**Tech Stack:** Odoo QWeb XML, CSS custom properties, kubectl deploy

---

## Files

| File | Action | What changes |
|------|--------|-------------|
| `markstudio_website/static/src/css/markstudio.css` | **REWRITE** | Full CSS — new tokens, every section restyled |
| `markstudio_website/views/homepage_templates.xml` | **MODIFY** | Hero text, remove `mk-stats-dots` divs, remove `mk-svc-hl` spans, update Google Fonts link, booking card button class |

**NOT changed:** smooth_scroll.js, controller, manifest, images, menus

---

### Task 1: Rewrite the complete CSS

**Files:**
- Modify: `markstudio_website/static/src/css/markstudio.css` (full rewrite, 732→~650 lines)

- [ ] **Step 1: Replace the entire CSS file**

The new CSS replaces every section. Key changes summarized:

| Area | Old (Dr.stretch) | New (Retrodandy) |
|------|------------------|-------------------|
| Tokens | `--mk-maroon`, `--mk-gold`, `--mk-teal`, `--mk-light`, `--mk-oswald`, EB Garamond | `--mk-gray-100/200/400`, Noto Serif TC, no maroon/gold/teal/oswald |
| Hero title | EB Garamond italic 120px | Noto Serif TC 700 (not italic), add subtitle |
| Stats bg | maroon + dot pattern + gold borders | `--mk-gray-100` + black thin borders, no dots |
| Stats numbers | gold serif | black serif |
| Services bg | maroon + dot pattern | pure black |
| Service headings | teal highlight on black bg | plain white, no highlight background |
| Service numbers | translucent white italic | translucent white (keep italic) |
| All border-radius | 12px (images), 4px (buttons), 16px (booking card) | 0 everywhere |
| Buttons | gold filled, rounded | outlined black/white, square corners |
| Nav CTA | gold filled | gold filled but square corners (keep gold for CTA emphasis) |
| Technique bg | `--mk-light` (#f0ebe5) | `--mk-gray-100` (#f5f5f5) |
| Technique subtitle | gold underline | black, no underline decoration |
| Experience step nums | Oswald font | Noto Sans TC |
| FAQ | dark panels on light bg | white bg, thin gray border separators |
| Contact link color | #5ac8fa | #999 (monochrome) |
| Booking CTA bg | maroon-deep + dot pattern | pure black |
| Booking card | rounded, shadow | square corners, thin border, no shadow |
| News bg | `--mk-dark` | pure black |
| Social placeholders | rounded 12px, dashed | square corners, dashed |
| Social icon badges | colored (IG gradient, FB blue, YT red) | monochrome black circles |
| Social links | gold border | white border (on dark bg) |

Write the complete new CSS file:

```css
/* ============================================================
   Mark Studio — Retrodandy-inspired Design System
   Reference: retrodandy.com — monochrome editorial minimalism
   ============================================================ */

/* --- Do NOT use @import — breaks Odoo CSS pipeline --- */

/* --- Tokens --- */
:root {
    --mk-black: #000;
    --mk-white: #fff;
    --mk-dark: #1a1a1a;
    --mk-gray-100: #f5f5f5;
    --mk-gray-200: #ececec;
    --mk-gray-400: #999;
    --mk-gold: #C5962A;
    --mk-serif: 'Noto Serif TC', 'Georgia', serif;
    --mk-sans: 'Noto Sans TC', 'Helvetica Neue', sans-serif;
}

/* Smooth scroll for anchor navigation */
html { scroll-behavior: smooth; }
section[id] { scroll-margin-top: 80px; }

/* ============================================================
   HERO
   ============================================================ */
.mk-hero {
    position: relative;
    width: 100%;
    height: 100vh;
    min-height: 600px;
    background: #111;
    overflow: hidden;
}

.mk-hero-bg {
    position: absolute;
    inset: 0;
    background: url('/markstudio_website/static/src/img/hero-bg.jpg') center center / cover no-repeat;
    filter: brightness(0.6);
}

.mk-hero-content {
    position: absolute;
    bottom: 12%;
    left: 0;
    right: 0;
    z-index: 2;
    text-align: center;
}

.mk-hero-title {
    font-family: var(--mk-serif);
    font-size: clamp(48px, 8vw, 96px);
    font-weight: 700;
    color: var(--mk-white);
    letter-spacing: 4px;
    text-transform: uppercase;
    line-height: 1.1;
    margin: 0;
}

.mk-hero-subtitle {
    font-family: var(--mk-sans);
    font-size: clamp(14px, 2vw, 20px);
    color: rgba(255,255,255,0.7);
    letter-spacing: 4px;
    margin-top: 16px;
    font-weight: 300;
}

/* ============================================================
   STATS — black-bordered circles on light bg
   ============================================================ */
.mk-stats {
    position: relative;
    background: var(--mk-gray-100);
    padding: 0 0 60px;
    overflow: visible;
}

.mk-stats-circles {
    position: relative;
    z-index: 1;
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-top: -100px;
    padding: 0 40px;
    flex-wrap: wrap;
}

.mk-stat-circle {
    width: 220px;
    height: 220px;
    border-radius: 50%;
    border: 2px solid var(--mk-black);
    background: var(--mk-white);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 24px;
    transition: opacity 0.3s;
}

.mk-stat-circle:hover { opacity: 0.85; }

.mk-stat-desc {
    font-family: var(--mk-sans);
    font-size: 14px;
    color: #333;
    font-weight: 500;
    line-height: 1.5;
}

.mk-stat-num {
    font-family: var(--mk-serif);
    font-size: 48px;
    font-weight: 700;
    color: var(--mk-black);
    line-height: 1;
}

.mk-stat-num sup { font-size: 24px; }

.mk-stat-unit {
    font-family: var(--mk-sans);
    font-size: 16px;
    color: #333;
}

.mk-stat-icon {
    font-size: 40px;
    color: var(--mk-black);
    margin-top: 8px;
}

/* ============================================================
   SERVICES — black bg, white text, numbered 01/02/03
   ============================================================ */
.mk-services {
    position: relative;
    background: var(--mk-black);
    padding: 100px 0 40px;
    overflow: hidden;
}

.mk-sec-title {
    font-family: var(--mk-serif);
    font-size: 36px;
    font-weight: 700;
    color: var(--mk-white);
    text-align: center;
    margin-bottom: 8px;
    letter-spacing: 2px;
}

.mk-sec-title-dark {
    color: var(--mk-black);
}

.mk-sec-line {
    width: 40px;
    height: 2px;
    background: var(--mk-white);
    margin: 0 auto 48px;
}

.mk-why-title {
    font-family: var(--mk-serif);
    font-size: clamp(36px, 6vw, 72px);
    font-weight: 700;
    color: var(--mk-white);
    text-align: center;
    margin-bottom: 60px;
    line-height: 1.1;
}

.mk-svc {
    display: flex;
    gap: 40px;
    margin-bottom: 80px;
    align-items: flex-start;
    flex-wrap: wrap;
}

.mk-svc-left {
    flex: 0 0 38%;
    min-width: 280px;
}

.mk-svc-right {
    flex: 1;
    min-width: 300px;
}

.mk-svc-num {
    font-family: var(--mk-serif);
    font-size: 72px;
    font-weight: 700;
    font-style: italic;
    color: rgba(255, 255, 255, 0.1);
    line-height: 1;
    margin-bottom: 4px;
}

.mk-svc-heading {
    margin-bottom: 16px;
    line-height: 1.8;
}

.mk-svc-hl {
    background: none;
    color: var(--mk-white);
    font-family: var(--mk-sans);
    font-size: 20px;
    font-weight: 700;
    padding: 0;
}

.mk-svc-text {
    font-family: var(--mk-sans);
    font-size: 15px;
    color: rgba(255,255,255,0.7);
    line-height: 1.8;
    margin-top: 16px;
}

.mk-svc-img {
    overflow: hidden;
}

/* Images — square corners */
.mk-svc-img img,
.mk-step-img img {
    width: 100%;
    height: auto;
    display: block;
    object-fit: cover;
    border-radius: 0;
}

.mk-svc-img img {
    min-height: 320px;
    max-height: 400px;
}

.mk-step-img img {
    min-height: 200px;
    max-height: 260px;
}

/* Placeholders — square corners */
.mk-placeholder {
    background: #333;
    min-height: 320px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    color: #666;
    font-size: 14px;
    font-family: var(--mk-sans);
    border-radius: 0;
}

.mk-placeholder i { font-size: 28px; }

.mk-placeholder-light {
    background: #e8e8e8;
    color: #999;
}

/* ============================================================
   TECHNIQUE — light bg, serif title
   ============================================================ */
.mk-technique {
    background: var(--mk-gray-100);
    padding: 100px 0 60px;
}

.mk-big-serif {
    font-family: var(--mk-serif);
    font-size: clamp(32px, 5vw, 56px);
    font-weight: 700;
    color: var(--mk-black);
    text-align: center;
    margin-bottom: 16px;
    line-height: 1.2;
}

.mk-technique-sub {
    font-family: var(--mk-sans);
    font-size: 20px;
    font-weight: 500;
    color: var(--mk-black);
    text-align: center;
    margin-bottom: 24px;
    text-decoration: none;
}

.mk-technique-text {
    font-family: var(--mk-sans);
    font-size: 15px;
    color: #333;
    line-height: 1.8;
    max-width: 800px;
    margin: 0 auto;
    text-align: left;
}

/* ============================================================
   EXPERIENCE — white bg, 4-col square cards
   ============================================================ */
.mk-experience {
    background: var(--mk-white);
    padding: 100px 0;
}

.mk-exp-sub {
    font-family: var(--mk-sans);
    font-size: 15px;
    color: var(--mk-gray-400);
    text-align: center;
    max-width: 600px;
    margin: 0 auto 48px;
}

.mk-steps {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 24px;
}

.mk-step {
    text-align: center;
    transition: opacity 0.3s;
}

.mk-step:hover { opacity: 0.85; }

.mk-step-num {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: var(--mk-black);
    color: var(--mk-white);
    font-family: var(--mk-sans);
    font-size: 18px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 12px;
}

.mk-step-title {
    font-family: var(--mk-sans);
    font-size: 16px;
    font-weight: 500;
    color: var(--mk-black);
    margin-bottom: 16px;
}

.mk-step-img { overflow: hidden; }

/* ============================================================
   FAQ — white bg, thin gray separators
   ============================================================ */
.mk-faq {
    background: var(--mk-white);
    padding: 100px 0;
}

.mk-faq-list {
    max-width: 800px;
    margin: 0 auto;
}

.mk-faq-item {
    border-bottom: 1px solid var(--mk-gray-200);
}

.mk-faq-item summary {
    background: none;
    color: var(--mk-black);
    padding: 20px 0;
    font-family: var(--mk-sans);
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;
    list-style: none;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: color 0.2s;
}

.mk-faq-item summary::-webkit-details-marker { display: none; }
.mk-faq-item summary:hover { color: var(--mk-gray-400); }

.mk-faq-item summary i {
    font-size: 12px;
    transition: transform 0.3s;
    margin-left: 16px;
    flex-shrink: 0;
    color: var(--mk-gray-400);
}

.mk-faq-item[open] summary i { transform: rotate(180deg); }

.mk-faq-ans {
    background: none;
    color: #555;
    padding: 0 0 20px;
    font-family: var(--mk-sans);
    font-size: 14px;
    line-height: 1.8;
}

.mk-faq-ans p { margin: 0; }

/* ============================================================
   CONTACT — dark bg, monochrome
   ============================================================ */
.mk-contact {
    background: var(--mk-black);
    padding: 80px 0;
}

.mk-contact-body {
    max-width: 600px;
    margin: 0 auto;
}

.mk-contact-item {
    border-bottom: 1px solid #333;
    padding: 20px 0;
}

.mk-contact-label {
    display: block;
    font-family: var(--mk-sans);
    font-size: 13px;
    color: var(--mk-gray-400);
    margin-bottom: 8px;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.mk-contact-link {
    font-family: var(--mk-sans);
    font-size: 16px;
    color: var(--mk-white);
    text-decoration: none;
}

.mk-contact-link:hover {
    color: var(--mk-gray-400);
}

/* ============================================================
   BOOKING CTA — black bg, outlined button
   ============================================================ */
.mk-booking-cta {
    position: relative;
    background: var(--mk-black);
    padding: 100px 0;
    overflow: hidden;
}

.mk-booking-sub {
    font-family: var(--mk-sans);
    font-size: 18px;
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 40px;
}

.mk-cta-btn {
    display: inline-block;
    background: transparent;
    color: var(--mk-white);
    font-family: var(--mk-sans);
    font-size: 14px;
    font-weight: 500;
    padding: 14px 48px;
    border: 2px solid var(--mk-white);
    border-radius: 0;
    text-decoration: none;
    letter-spacing: 2px;
    text-transform: uppercase;
    transition: all 0.3s;
}

.mk-cta-btn:hover {
    background: var(--mk-white);
    color: var(--mk-black);
    text-decoration: none;
}

.mk-cta-btn-lg {
    font-size: 16px;
    padding: 18px 64px;
    letter-spacing: 3px;
}

/* Booking appointment card */
.mk-booking-card {
    display: flex;
    background: transparent;
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 0;
    overflow: hidden;
    max-width: 800px;
    margin: 40px auto 0;
    transition: border-color 0.3s;
}

.mk-booking-card:hover {
    border-color: var(--mk-white);
}

.mk-booking-card-img {
    flex: 0 0 280px;
    overflow: hidden;
}

.mk-booking-card-img img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 0;
}

.mk-booking-card-body {
    flex: 1;
    padding: 32px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.mk-booking-card-title {
    font-family: var(--mk-serif);
    font-size: 24px;
    font-weight: 700;
    color: var(--mk-white);
    margin-bottom: 12px;
}

.mk-booking-card-meta {
    display: flex;
    gap: 20px;
    margin-bottom: 16px;
    flex-wrap: wrap;
}

.mk-booking-card-meta span {
    font-family: var(--mk-sans);
    font-size: 13px;
    color: rgba(255,255,255,0.5);
}

.mk-booking-card-meta i {
    margin-right: 6px;
    color: rgba(255,255,255,0.5);
}

.mk-booking-card-desc {
    font-family: var(--mk-sans);
    font-size: 14px;
    color: rgba(255,255,255,0.6);
    line-height: 1.8;
    margin-bottom: 24px;
}

@media (max-width: 768px) {
    .mk-booking-card { flex-direction: column; }
    .mk-booking-card-img { flex: none; height: 200px; }
}

/* ============================================================
   NEWS / SOCIAL — black bg
   ============================================================ */
.mk-news {
    background: var(--mk-black);
    padding: 100px 0;
}

.mk-news-sub {
    font-family: var(--mk-sans);
    font-size: 15px;
    color: var(--mk-gray-400);
    text-align: center;
    margin-bottom: 48px;
}

.mk-social-block {
    margin-bottom: 48px;
    padding-bottom: 48px;
    border-bottom: 1px solid #333;
}

.mk-social-block:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
}

.mk-social-heading {
    font-family: var(--mk-sans);
    font-size: 20px;
    font-weight: 500;
    color: var(--mk-white);
}

.mk-social-placeholder {
    background: #111;
    border-radius: 0;
    border: 1px dashed #444;
    min-height: 200px;
    color: #666;
}

.mk-social-link {
    display: inline-block;
    color: var(--mk-white);
    font-family: var(--mk-sans);
    font-size: 13px;
    text-decoration: none;
    border: 1px solid rgba(255,255,255,0.4);
    padding: 10px 24px;
    border-radius: 0;
    letter-spacing: 1px;
    text-transform: uppercase;
    transition: all 0.3s;
}

.mk-social-link:hover {
    background: var(--mk-white);
    color: var(--mk-black);
    text-decoration: none;
}

/* Social icon badges — monochrome */
.markstudio-social-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    border-radius: 0;
    color: var(--mk-white);
    background: var(--mk-black);
    border: 1px solid #444;
}

.markstudio-ig { background: var(--mk-black); }
.markstudio-fb { background: var(--mk-black); }
.markstudio-yt { background: var(--mk-black); }
.markstudio-video-card { transition: opacity 0.3s; }
.markstudio-video-card:hover { opacity: 0.85; }

/* ============================================================
   NAVBAR — CTA button (keep gold, square corners)
   ============================================================ */
#top_menu > li:last-child > a {
    background: var(--mk-gold);
    color: var(--mk-black) !important;
    font-weight: 700;
    padding: 8px 24px !important;
    border-radius: 0;
    margin-left: 16px;
    letter-spacing: 1px;
    transition: all 0.3s;
}

#top_menu > li:last-child > a:hover {
    background: #d4a63a;
    transform: translateY(-1px);
}

/* Section-specific divider for FAQ */
.mk-faq .mk-sec-line {
    background: var(--mk-black);
}

/* ============================================================
   RESPONSIVE
   ============================================================ */
@media (max-width: 991px) {
    .mk-stats-circles { gap: 24px; margin-top: -80px; }
    .mk-stat-circle { width: 180px; height: 180px; }
    .mk-stat-num { font-size: 40px; }
    .mk-svc { flex-direction: column; }
    .mk-svc-left { flex: 1; }
    .mk-steps { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 576px) {
    .mk-hero-title { font-size: 36px; }
    .mk-stats-circles { flex-direction: column; align-items: center; margin-top: -60px; }
    .mk-stat-circle { width: 160px; height: 160px; }
    .mk-stat-num { font-size: 32px; }
    .mk-svc-num { font-size: 48px; }
    .mk-svc-hl { font-size: 16px; }
    .mk-why-title { font-size: 32px; }
    .mk-steps { grid-template-columns: 1fr; }
}
```

- [ ] **Step 2: Commit CSS**

```bash
cd "/var/tmp/vibe-kanban/worktrees/925d-/k3s project"
git add markstudio_website/static/src/css/markstudio.css
git commit -m "Reskin CSS: Retrodandy monochrome design system"
```

---

### Task 2: Update QWeb template

**Files:**
- Modify: `markstudio_website/views/homepage_templates.xml`

Changes needed:
1. **Google Fonts link** — remove EB Garamond, Lato, Oswald; add Noto Serif TC
2. **Hero** — change title to Chinese + English, add subtitle
3. **Stats** — remove `<div class="mk-stats-dots"/>`
4. **Services** — remove `<div class="mk-stats-dots"/>`
5. **Booking CTA** — remove `<div class="mk-stats-dots"/>`, change button class

- [ ] **Step 1: Update Google Fonts link (line 10)**

Replace:
```xml
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,700;0,800;1,400;1,700;1,800&amp;family=Noto+Sans+TC:wght@300;400;500;700;900&amp;family=Lato:wght@300;400;700;900&amp;family=Oswald:wght@400;500;700&amp;display=swap" rel="stylesheet"/>
```
With:
```xml
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;700&amp;family=Noto+Sans+TC:wght@300;400;500;700&amp;display=swap" rel="stylesheet"/>
```

- [ ] **Step 2: Update Hero section (lines 14-19)**

Replace:
```xml
<section id="hero" class="mk-hero">
    <div class="mk-hero-bg"/>
    <div class="mk-hero-content">
        <h1 class="mk-hero-title">STRETCH YOUR BODY</h1>
    </div>
</section>
```
With:
```xml
<section id="hero" class="mk-hero">
    <div class="mk-hero-bg"/>
    <div class="mk-hero-content">
        <h1 class="mk-hero-title">MARK STUDIO</h1>
        <p class="mk-hero-subtitle">專業按摩 · 伸展 · 放鬆</p>
    </div>
</section>
```

- [ ] **Step 3: Remove dot patterns from Stats (line 23)**

Delete this line:
```xml
<div class="mk-stats-dots"/>
```

- [ ] **Step 4: Remove dot patterns from Services (line 46)**

Delete this line:
```xml
<div class="mk-stats-dots"/>
```

- [ ] **Step 5: Remove dot patterns from Booking CTA (line 139)**

Delete this line:
```xml
<div class="mk-stats-dots"/>
```

- [ ] **Step 6: Update Booking card button (line 159)**

Replace:
```xml
<a href="/appointment/1" class="mk-cta-btn">立即預約</a>
```
With:
```xml
<a href="/appointment/1" class="mk-cta-btn">立 即 預 約</a>
```

- [ ] **Step 7: Commit template**

```bash
git add markstudio_website/views/homepage_templates.xml
git commit -m "Update template: Retrodandy hero text, remove dot patterns"
```

---

### Task 3: Deploy to K8s and verify

- [ ] **Step 1: Package and copy module to pod**

```bash
cd "/var/tmp/vibe-kanban/worktrees/925d-/k3s project"
tar czf /tmp/markstudio_website.tar.gz markstudio_website/
ODOO_POD=$(kubectl get pod -n markstudio-odoo -l app=odoo -o jsonpath='{.items[0].metadata.name}')
kubectl cp /tmp/markstudio_website.tar.gz "markstudio-odoo/${ODOO_POD}:/tmp/markstudio_website.tar.gz" -c odoo
kubectl exec -n markstudio-odoo "${ODOO_POD}" -c odoo -- tar xzf /tmp/markstudio_website.tar.gz -C /mnt/extra-addons/
```

- [ ] **Step 2: Clear asset cache and upgrade module**

```bash
kubectl exec -n markstudio-odoo deploy/odoo-db -- psql -U odoo -d markstudio \
  -c "DELETE FROM ir_attachment WHERE name LIKE '%assets%' OR url LIKE '%/web/assets%';"

PGPASS=$(kubectl get secret odoo-secrets -n markstudio-odoo -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)
kubectl exec -n markstudio-odoo deploy/odoo -c odoo -- odoo -d markstudio \
  -u markstudio_website --stop-after-init --no-http \
  --db_host=odoo-db-svc --db_port=5432 --db_user=odoo --db_password="$PGPASS"
```

- [ ] **Step 3: Restart and wait**

```bash
kubectl rollout restart deployment/odoo -n markstudio-odoo
kubectl wait --for=condition=Ready pod -l app=odoo -n markstudio-odoo --timeout=120s
```

- [ ] **Step 4: Verify with Playwright — hero**

```bash
kill $(lsof -ti :18069) 2>/dev/null
kubectl port-forward -n markstudio-odoo svc/odoo-web-svc 18069:8069 &
sleep 3
playwright-cli open http://localhost:18069/
playwright-cli resize 1280 720
playwright-cli screenshot --filename=verify-hero.png
```

Check: Black/white hero, "MARK STUDIO" serif title, Chinese subtitle.

- [ ] **Step 5: Verify services section**

```bash
playwright-cli eval "window.scrollTo(0, 1200)"
playwright-cli screenshot --filename=verify-services.png
```

Check: Pure black bg, white text, square-corner images, no colored highlights.

- [ ] **Step 6: Verify FAQ section**

```bash
playwright-cli eval "window.scrollTo(0, document.getElementById('faq').offsetTop - 80)"
playwright-cli screenshot --filename=verify-faq.png
```

Check: White bg, thin gray separators between items, no dark panels.

- [ ] **Step 7: Verify booking CTA**

```bash
playwright-cli eval "window.scrollTo(0, document.getElementById('booking').offsetTop - 80)"
playwright-cli screenshot --filename=verify-booking.png
```

Check: Black bg, outlined white button, square card with thin border.

- [ ] **Step 8: Clean up**

```bash
playwright-cli close
kill $(lsof -ti :18069) 2>/dev/null
rm -f verify-*.png
```
