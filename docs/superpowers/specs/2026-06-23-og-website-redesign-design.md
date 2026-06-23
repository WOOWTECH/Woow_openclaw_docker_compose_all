# O.G 老地方身體修復 — Website Redesign Spec

## Overview

Redesign the Mark Studio website module (`markstudio_website`) into a new brand identity for "O.G老地方身體修復" — a body restoration studio specializing in joint mobilization, fascia tension balancing, and ISATM fascia blade therapy.

The brand personality: an Old School craftsman who rides heavy motorcycles, is a big-frame fitness coach, and applies meticulous hand skills with deep anatomical knowledge. The website reflects this: no-nonsense, industrial minimalism with warmth from rust-iron accents.

## Brand Identity

### Name & Slogan
- **Brand name**: O.G 老地方
- **Subtitle**: 身體修復
- **Slogan**: 不修表面，修根本。

### Brand Story Concept: "Old School Craft"
Your body isn't broken — it's misaligned. Years of posture, training, and life accumulate into fascia knots and joint restrictions. O.G doesn't wait for pain to show up. Like an old-school mechanic who knows every bolt by feel, we work joint by joint, layer by layer, restoring your body to the state it was meant to be in. No gimmicks. Just hands, knowledge, and craft.

### Color System

| Token | Hex | Usage |
|-------|-----|-------|
| `--og-black` | `#0D0D0D` | Primary background |
| `--og-dark` | `#1A1A1A` | Section backgrounds |
| `--og-gray` | `#2A2A2A` | Card backgrounds |
| `--og-mid` | `#777777` | Secondary text |
| `--og-light` | `#E5E5E5` | Borders, dividers |
| `--og-white` | `#F5F5F5` | Primary text, light backgrounds |
| `--og-rust` | `#C75B12` | Accent color (rust iron orange) |

### Typography
- **Headings (Chinese)**: `'Noto Serif TC'` — weight, gravitas
- **Body (Chinese)**: `'Noto Sans TC'` — clean readability
- **Display (English)**: `'Oswald'` — industrial condensed uppercase (Google Fonts)
- All headings use uppercase English + Chinese pairing

### Visual Treatment
- Dark background throughout (`#0D0D0D`)
- Images: grayscale with warm overlay (`mix-blend-mode` or CSS filter)
- Rust-orange accent for: CTAs, section dividers, hover states, key highlights
- Subtle texture: noise grain overlay on hero (optional)

## Page Structure (6 Sections)

### Section 1: Hero
- **data-snippet**: `s_og_hero`
- **Layout**: Full viewport height, centered content over background image
- **Content**:
  - English display: `O.G`
  - Chinese title: `老地方`
  - Subtitle: `身體修復`
  - Slogan: `不修表面，修根本。`
- **Background**: Unsplash image — hands working on body/muscles, grayscale with warm overlay
- **Interaction**: Subtle parallax or fixed background

### Section 2: Brand Story
- **data-snippet**: `s_og_story`
- **Layout**: Centered text block with rust-orange accent line
- **Content**:
  - English heading: `Why O.G?`
  - Body text: "你的身體不是壞了，是偏了。生活、姿勢、訓練累積的代償，讓筋膜糾結、關節卡住。O.G 不是等你痛了才來的地方——是讓你的身體回到它原本該有的狀態。老派的手藝，解決根本的問題。"
- **Visual**: Minimal — text-focused with generous whitespace (on dark bg)

### Section 3: Services
- **data-snippet**: `s_og_services`
- **Layout**: 3-column grid (stacks on mobile), each with number + title + description + image
- **Content**:
  - **01 關節鬆動**: "鬆開卡住的關節活動度，讓動作回到正軌。透過精準的手法，恢復關節該有的活動範圍，減少代償動作帶來的二次傷害。"
  - **02 筋膜張力平衡**: "平衡全身筋膜張力鏈，從根源消除代償。筋膜是串聯全身的網絡，一處緊繃可能牽動全身。我們從整體張力出發，重新校準你的身體。"
  - **03 ISATM 筋膜刀**: "精準處理軟組織沾黏，加速修復與還原。使用專業器械深入處理纖維化組織，打破沾黏循環，讓組織重新獲得彈性與滑動能力。"
- **Images**: Unsplash — close-up hands-on therapy, muscle work, professional tools

### Section 4: Restoration Flow
- **data-snippet**: `s_og_flow`
- **Layout**: Horizontal step cards (vertical on mobile), numbered 01-04
- **Content**:
  - **01 身體評估** — "了解你的身體歷史、疼痛模式與日常習慣"
  - **02 問題定位** — "透過動作測試與觸診，精準找出失衡根源"
  - **03 手技修復** — "針對問題源頭，逐層鬆解、調校、還原"
  - **04 維護建議** — "給你帶得走的修復知識，延續調校效果"
- **Visual**: Each step with subtle icon or number treatment, connected by rust-orange line

### Section 5: Booking CTA
- **data-snippet**: `s_og_booking`
- **Layout**: Dark section with centered text + prominent CTA button
- **Content**:
  - Heading: `準備好了？`
  - Subtext: `讓身體回到它該有的狀態。`
  - Button: `立即預約` → links to `/appointment/1/schedule`
- **Style**: Rust-orange button, high contrast

### Section 6: Contact Info
- **data-snippet**: `s_og_contact`
- **Layout**: Simple centered grid with contact details
- **Content**: Phone, address, business hours, social media links
- **Style**: Clean, minimal, rust-orange accent on links

## Unsplash Image Strategy

Use the Unsplash API (Access Key: `HFvKPMvcx9_uxsOuvNFFkI4eBjhqyH1gGp4pCJe7uTM`) to source images matching:

| Section | Search Query | Treatment |
|---------|-------------|-----------|
| Hero BG | `massage therapy hands muscles dark` | Grayscale + warm overlay |
| Service 01 | `joint mobilization physiotherapy` | Grayscale + warm overlay |
| Service 02 | `fascia massage deep tissue` | Grayscale + warm overlay |
| Service 03 | `sports therapy tools professional` | Grayscale + warm overlay |
| Flow steps | Icon/number-based, no photos needed | — |

Download and save to `static/src/img/` with descriptive filenames.

## Technical Implementation

### Module Changes
- Rename internal references from `mk-*` to `og-*` CSS classes
- Replace all `markstudio_website` content with O.G content
- Keep the same snippet architecture (9 → 6 snippets)
- Keep `oe_structure` + `data-snippet` + `inherit_id="website.homepage"` pattern
- Keep Odoo 18 website builder compatibility

### File Changes

| File | Action |
|------|--------|
| `__manifest__.py` | Update name, version, summary |
| `static/src/css/markstudio.css` | Full rewrite → `og.css` with new design system |
| `views/homepage_templates.xml` | Replace all 9 MK sections with 6 OG sections |
| `views/snippets/s_mk_*.xml` | Replace with `s_og_*.xml` (6 files) |
| `views/snippets/snippets.xml` | Update snippet registration |
| `static/src/img/*` | Replace with Unsplash images |
| `controllers/main.py` | No change (already cleaned up) |

### CSS Architecture
- Replace all `--mk-*` tokens with `--og-*` tokens
- Replace all `.mk-*` classes with `.og-*` classes
- Dark-first design (current is white-first with dark sections)
- Add `'Oswald'` Google Font for English display text
- Maintain responsive breakpoints

### Snippet Files (6 total)
1. `views/snippets/s_og_hero.xml`
2. `views/snippets/s_og_story.xml`
3. `views/snippets/s_og_services.xml`
4. `views/snippets/s_og_flow.xml`
5. `views/snippets/s_og_booking.xml`
6. `views/snippets/s_og_contact.xml`
7. `views/snippets/snippets.xml` (registration)

### Deployment
- Copy to pod via `kubectl cp` + tar (markstudio_website is not git-cloned by init container)
- Upgrade module: `odoo -u markstudio_website`
- Restart pod

## Testing Criteria

1. Homepage loads with 200, all 6 sections present
2. Each section has `data-snippet="s_og_*"` attribute
3. `oe_structure` wrapper exists
4. Admin can enter website builder edit mode
5. Each block is editable (text, images)
6. Each block is deletable and reorderable
7. "O.G老地方" snippet group appears in builder panel
8. All images load (no 404)
9. Booking CTA links to `/appointment/1/schedule`
10. Responsive on mobile viewport
11. Smooth scroll to anchor IDs works
12. `/news` redirect still works (if kept)

## Out of Scope
- About the master page (removed per user request)
- Customer testimonials (removed per user request)
- FAQ section (removed per user request)
- Multilingual support
- Blog/news CMS
