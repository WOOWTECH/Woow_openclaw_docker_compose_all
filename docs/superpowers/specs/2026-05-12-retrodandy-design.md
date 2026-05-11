# Mark Studio Design System — Retrodandy-Inspired

> Reusable design spec for the Mark Studio (馬克健身) Odoo 18 website.
> Reference: https://www.retrodandy.com/
> Apply this spec to any page built in the `markstudio_website` module.

---

## 1. Design Philosophy

**Style**: Modern vintage / editorial minimalism
**Mood**: Clean, sophisticated, confident — like a high-end lifestyle magazine
**Key Principle**: Let content breathe. Typography and whitespace do the heavy lifting. No gratuitous decoration.

### Contrast with Previous Design (Dr.stretch)

| Aspect | Dr.stretch (old) | Retrodandy (new) |
|--------|-----------------|-------------------|
| Palette | Dark maroon + gold | Black + white + warm accents |
| Typography | EB Garamond serif italic | Noto Serif TC upright serif |
| Backgrounds | Heavy dark sections | Predominantly white, black nav/footer |
| Decoration | Dot patterns, gold borders | None — clean edges, thin borders |
| Buttons | Filled gold | Outlined black / filled black |
| Cards | No cards (text blocks) | Product-style cards with clean images |
| Spacing | Moderate | Very generous whitespace |

---

## 2. Color Palette

### Primary

| Token | Value | Usage |
|-------|-------|-------|
| `--mk-black` | `#000000` | Nav bg, headings, primary text, filled buttons |
| `--mk-white` | `#FFFFFF` | Page bg, nav text, card bg |
| `--mk-dark` | `#1a1a1a` | Footer bg, dark sections |

### Secondary

| Token | Value | Usage |
|-------|-------|-------|
| `--mk-gray-100` | `#f5f5f5` | Hover states, alternate section bg |
| `--mk-gray-200` | `#ececec` | Borders, dividers |
| `--mk-gray-400` | `#999999` | Secondary text, captions |
| `--mk-gray-600` | `#666666` | Body text in dark sections |

### Accent

| Token | Value | Usage |
|-------|-------|-------|
| `--mk-gold` | `#C5962A` | CTA highlight, booking button, price accent |
| `--mk-navy` | `#051C62` | Outline button text (optional) |
| `--mk-sale` | `#B22222` | Strikethrough prices, sale badges |

### Usage Rules
- **Page background**: Always `--mk-white`
- **Section alternation**: White → `--mk-gray-100` → White (for rhythm)
- **Dark sections**: Only hero, footer, and special CTA blocks use `--mk-black` / `--mk-dark`
- **Never**: Gradient backgrounds, colored borders, dotted patterns

---

## 3. Typography

### Font Stack

```css
:root {
    --mk-serif: 'Noto Serif TC', 'Georgia', serif;
    --mk-sans: 'Noto Sans TC', 'Helvetica Neue', sans-serif;
}
```

**Primary font**: `Noto Serif TC` — used for headings, section titles, brand name
**Secondary font**: `Noto Sans TC` — used for body text, buttons, metadata, navigation

### Type Scale

| Element | Font | Size | Weight | Letter-spacing | Transform |
|---------|------|------|--------|---------------|-----------|
| Hero title | serif | clamp(48px, 8vw, 96px) | 700 | 4px | uppercase |
| Section title (H2) | serif | 36px | 700 | 2px | none |
| Section subtitle | sans | 16px | 400 | 0.5px | none |
| Card title | sans | 16px | 500 | 0 | none |
| Body text | sans | 15px | 400 | 0 | none |
| Button text | sans | 14px | 500 | 1px | uppercase |
| Caption/meta | sans | 13px | 400 | 0.5px | none |
| Nav items | sans | 14px | 500 | 1.5px | uppercase |

### Line Heights
- Headings: `1.3`
- Body: `1.8`
- Buttons: `1`
- Nav: `1.4`

---

## 4. Spacing System

Base unit: **8px**

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | 4px | Icon gaps |
| `--space-sm` | 8px | Tight padding |
| `--space-md` | 16px | Card padding, element gaps |
| `--space-lg` | 32px | Section inner padding |
| `--space-xl` | 64px | Section top/bottom padding |
| `--space-2xl` | 100px | Hero padding, major section breaks |

### Container
- Max-width: `1200px`
- Padding: `0 20px` (mobile), `0 40px` (tablet+)

### Section Rhythm
- Each major section: `padding: var(--space-2xl) 0`
- Between-section divider: `1px solid var(--mk-gray-200)` (optional, not required)

---

## 5. Navigation Bar

### Structure
```
[HOME  PRODUCTS  STOCKIST  ABOUT]     LOGO     [search] [user] [cart]
```

Adapted for Mark Studio:
```
[服務介紹  最新消息]     馬克健身 LOGO     [立即預約 btn]
```

### Styles
- Background: `var(--mk-black)` (solid black, not transparent)
- Text: `var(--mk-white)`, uppercase, 14px, letter-spacing 1.5px
- Logo: Centered, serif font or image, white
- Height: ~70px
- Sticky on scroll
- CTA button in nav: outlined white border, white text, hover fills white with black text

### Mobile
- Hamburger menu icon (right side)
- Full-screen overlay menu on black bg

---

## 6. Buttons

### Primary (Filled)
```css
.mk-btn-primary {
    background: var(--mk-black);
    color: var(--mk-white);
    border: 2px solid var(--mk-black);
    padding: 14px 40px;
    font-family: var(--mk-sans);
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
    border-radius: 0;          /* sharp corners — retro style */
    transition: all 0.3s ease;
}
.mk-btn-primary:hover {
    background: var(--mk-white);
    color: var(--mk-black);
}
```

### Secondary (Outlined)
```css
.mk-btn-outline {
    background: transparent;
    color: var(--mk-black);
    border: 2px solid var(--mk-black);
    padding: 14px 40px;
    font-family: var(--mk-sans);
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
    border-radius: 0;
    transition: all 0.3s ease;
}
.mk-btn-outline:hover {
    background: var(--mk-black);
    color: var(--mk-white);
}
```

### CTA (Gold accent)
```css
.mk-btn-cta {
    background: var(--mk-gold);
    color: var(--mk-black);
    border: 2px solid var(--mk-gold);
    padding: 16px 48px;
    font-weight: 700;
    letter-spacing: 2px;
}
.mk-btn-cta:hover {
    background: transparent;
    color: var(--mk-gold);
}
```

### Button Rules
- **Border-radius: 0** (square corners, retro aesthetic)
- Always uppercase
- Min-width: 160px for primary actions
- No box-shadow

---

## 7. Cards

### Service Card
```
┌─────────────────────────┐
│                         │
│      [ IMAGE ]          │  ← aspect-ratio: 4/3, object-fit: cover
│      (dark bg photo)    │
│                         │
├─────────────────────────┤
│  Service Title           │  ← sans 16px, weight 500
│  NT$ 1,200               │  ← sans 14px, weight 400
│                         │
└─────────────────────────┘
```

### Styles
```css
.mk-card {
    background: var(--mk-white);
    border: none;
    border-radius: 0;          /* square corners */
    overflow: hidden;
    transition: opacity 0.3s;
}
.mk-card:hover {
    opacity: 0.85;
}
.mk-card-img {
    width: 100%;
    aspect-ratio: 4 / 3;
    object-fit: cover;
}
.mk-card-body {
    padding: 16px 0;          /* no horizontal padding — edge-to-edge feel */
}
.mk-card-title {
    font-family: var(--mk-sans);
    font-size: 16px;
    font-weight: 500;
    color: var(--mk-black);
    margin-bottom: 8px;
}
.mk-card-price {
    font-family: var(--mk-sans);
    font-size: 14px;
    color: var(--mk-black);
}
```

### Card Grid
- 4 columns on desktop (gap: 24px)
- 2 columns on tablet
- 1 column on mobile
- No card borders, no shadows — images do the work

### Booking Card (special)
Same as previous implementation but update to match new design:
- White bg, no border-radius (square)
- Thin 1px border `var(--mk-gray-200)` instead of heavy shadow
- Gold CTA button

---

## 8. Hero Section

### Structure
- Full viewport height (100vh)
- Large background image (dark, moody photography)
- Centered or bottom-left title text
- Minimal overlay (no gradient, just slight darkening)

### Styles
```css
.mk-hero {
    height: 100vh;
    min-height: 500px;
    position: relative;
    background: var(--mk-black);
    overflow: hidden;
}
.mk-hero-bg {
    position: absolute;
    inset: 0;
    background-size: cover;
    background-position: center;
    filter: brightness(0.7);
}
.mk-hero-title {
    font-family: var(--mk-serif);
    font-size: clamp(48px, 8vw, 96px);
    font-weight: 700;
    color: var(--mk-white);
    letter-spacing: 4px;
    text-transform: uppercase;
}
```

### Navigation dots (for carousel if used)
- Small circles, 8px diameter
- White fill for active, white outline for inactive
- Centered below hero image

---

## 9. Section Patterns

### Standard Section
```
[  SECTION TITLE  ]          ← serif 36px, centered
                             ← 48px gap
[  content grid  ]           ← 4-col cards or 2-col text+image
                             ← 48px gap
[  瀏覽全部  ]               ← outlined button, centered
```

### Dark Section (CTA / Footer)
- Background: `var(--mk-black)` or `var(--mk-dark)`
- All text: white
- Buttons: outlined white or filled gold

### FAQ Section
- Clean accordion on white/light bg
- Thin bottom border between items
- No colored backgrounds on panels

### Contact Section
- 3-column footer: Follow us | We accept | Contact
- Thin top border separator
- Social icons: simple, monochrome
- Copyright: centered, small text, light gray

---

## 10. Image Treatment

### Photography Style
- Dark, moody, warm-toned (think vintage studio lighting)
- Subjects in action (massage, stretching, consultation)
- High contrast, slightly desaturated

### Image Rules
- **No border-radius** on cards (square corners)
- Hero images: `filter: brightness(0.7)` for text contrast
- Card images: No filter, clean and sharp
- Aspect ratios: 4:3 for cards, 16:9 for hero, 1:1 for team/staff

---

## 11. Responsive Breakpoints

| Breakpoint | Container | Columns | Nav |
|-----------|-----------|---------|-----|
| Mobile (<576px) | 100% - 40px | 1 col | Hamburger |
| Tablet (576-991px) | 100% - 60px | 2 col | Hamburger |
| Desktop (992px+) | 1200px | 4 col | Full nav |

---

## 12. Animation & Transitions

### Allowed
- Hover opacity: `opacity 0.3s ease`
- Button color swap: `all 0.3s ease`
- Smooth scroll: `scroll-behavior: smooth`
- Sticky nav: `transform 0.3s ease` (show/hide on scroll)

### Not Allowed
- Parallax effects
- Scroll-triggered fade-ins
- Animated gradients
- Bouncing elements

---

## 13. CSS Custom Properties (Complete Token Set)

```css
:root {
    /* Colors */
    --mk-black: #000000;
    --mk-white: #FFFFFF;
    --mk-dark: #1a1a1a;
    --mk-gray-100: #f5f5f5;
    --mk-gray-200: #ececec;
    --mk-gray-400: #999999;
    --mk-gray-600: #666666;
    --mk-gold: #C5962A;
    --mk-sale: #B22222;

    /* Typography */
    --mk-serif: 'Noto Serif TC', 'Georgia', serif;
    --mk-sans: 'Noto Sans TC', 'Helvetica Neue', sans-serif;

    /* Spacing */
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 32px;
    --space-xl: 64px;
    --space-2xl: 100px;

    /* Layout */
    --container-max: 1200px;
    --nav-height: 70px;
    --border-radius: 0;       /* square corners throughout */

    /* Transitions */
    --transition-default: all 0.3s ease;
}
```

---

## 14. Component Inventory (for future pages)

Each component follows the naming convention `.mk-{component}[-variant]`.

| Component | Class | Usage |
|-----------|-------|-------|
| Button primary | `.mk-btn-primary` | Main actions |
| Button outline | `.mk-btn-outline` | Secondary actions, "瀏覽全部" |
| Button CTA | `.mk-btn-cta` | Booking, gold accent |
| Card | `.mk-card` | Services, products, team |
| Card image | `.mk-card-img` | Inside card |
| Card body | `.mk-card-body` | Text area below image |
| Section | `.mk-section` | Standard padded section |
| Section dark | `.mk-section-dark` | Dark bg variant |
| Section title | `.mk-section-title` | Serif centered H2 |
| Hero | `.mk-hero` | Full-viewport hero |
| Nav | `.mk-nav` | Sticky black nav |
| Footer | `.mk-footer` | 3-col dark footer |
| FAQ item | `.mk-faq-item` | Accordion details/summary |
| Badge | `.mk-badge` | "優惠" sale badge |
| Divider | `.mk-divider` | Thin gray horizontal line |

---

## 15. Page Template (for building new pages)

```xml
<t t-call="website.layout">
    <t t-set="pageName" t-value="'page-name'"/>
    <t t-set="head">
        <link rel="preconnect" href="https://fonts.googleapis.com"/>
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin=""/>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;700&amp;family=Noto+Sans+TC:wght@300;400;500;700&amp;display=swap" rel="stylesheet"/>
    </t>

    <!-- Hero -->
    <section class="mk-hero">...</section>

    <!-- Content sections -->
    <section class="mk-section">
        <div class="container">
            <h2 class="mk-section-title">標題</h2>
            <!-- content -->
        </div>
    </section>

    <section class="mk-section" style="background: var(--mk-gray-100);">
        <div class="container">
            <!-- alternating bg for visual rhythm -->
        </div>
    </section>

    <!-- CTA -->
    <section class="mk-section-dark">
        <div class="container text-center">
            <a href="/appointment" class="mk-btn-cta">立即預約</a>
        </div>
    </section>
</t>
```
