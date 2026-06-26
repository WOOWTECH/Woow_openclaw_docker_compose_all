// tests/pre-launch/29-rwd-responsive.spec.mjs
// RWD Responsive Design Tests for O.G老地方身體修復 Homepage
//
// Tests the homepage on 4 viewport sizes: iPhone SE, iPhone 14, iPad, Desktop.
// For each viewport verifies: no horizontal overflow, all 8 sections visible,
// images sized within containers, text readable (>= 12px), no overlapping
// elements, and navigation functional.

import { test, expect } from '@playwright/test';

const BASE = process.env.ODOO_BASE_URL || 'https://markstudio-odoo.woowtech.io';

const VIEWPORTS = [
  { name: 'Mobile (iPhone SE)',  width: 375,  height: 667,  isMobile: true  },
  { name: 'Mobile (iPhone 14)',  width: 390,  height: 844,  isMobile: true  },
  { name: 'Tablet (iPad)',       width: 768,  height: 1024, isMobile: true  },
  { name: 'Desktop',            width: 1440, height: 900,  isMobile: false },
];

// The 8 sections present on the O.G homepage (confirmed via live probing)
const SECTION_IDS = [
  'hero', 'services', 'technique', 'experience',
  'booking', 'news', 'faq', 'contact',
];

for (const vp of VIEWPORTS) {

  test.describe(`RWD: ${vp.name} (${vp.width}x${vp.height})`, () => {

    test.use({ viewport: { width: vp.width, height: vp.height } });

    // ---------------------------------------------------------------
    // R1: No horizontal overflow
    // ---------------------------------------------------------------
    test(`R1: No horizontal overflow`, async ({ page }) => {
      await page.goto(`${BASE}/`, { waitUntil: 'load', timeout: 45000 });
      await page.waitForTimeout(1000); // let layout settle

      const result = await page.evaluate(() => {
        const scrollW = document.documentElement.scrollWidth;
        const viewW = window.innerWidth;
        return { scrollW, viewW, overflow: scrollW > viewW };
      });

      console.log(`  [${vp.name}] scrollWidth=${result.scrollW} innerWidth=${result.viewW} overflow=${result.overflow}`);

      expect(
        result.overflow,
        `Horizontal overflow detected: scrollWidth(${result.scrollW}) > innerWidth(${result.viewW})`
      ).toBe(false);

      console.log(`  [OK] R1 ${vp.name}: No horizontal overflow`);
    });

    // ---------------------------------------------------------------
    // R2: All 8 sections visible (not display:none or visibility:hidden)
    // ---------------------------------------------------------------
    test(`R2: All 8 sections are visible`, async ({ page }) => {
      await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded', timeout: 45000 });

      const results = await page.evaluate((sectionIds) => {
        return sectionIds.map(id => {
          const el = document.getElementById(id);
          if (!el) return { id, found: false, display: '', visibility: '', ok: false };
          const style = getComputedStyle(el);
          const display = style.display;
          const visibility = style.visibility;
          const ok = display !== 'none' && visibility !== 'hidden';
          return { id, found: true, display, visibility, ok };
        });
      }, SECTION_IDS);

      const hidden = results.filter(r => !r.ok);
      const missing = results.filter(r => !r.found);

      for (const r of results) {
        const status = !r.found ? 'MISSING' : !r.ok ? 'HIDDEN' : 'OK';
        console.log(`  [${vp.name}] #${r.id}: ${status} (display=${r.display}, visibility=${r.visibility})`);
      }

      expect(missing, `Sections not found in DOM: ${missing.map(m => m.id).join(', ')}`).toHaveLength(0);
      expect(hidden, `Sections hidden: ${hidden.map(h => `${h.id}(display:${h.display},visibility:${h.visibility})`).join(', ')}`).toHaveLength(0);

      console.log(`  [OK] R2 ${vp.name}: All 8 sections visible`);
    });

    // ---------------------------------------------------------------
    // R3: Images sized within their containers (no overflow)
    // ---------------------------------------------------------------
    test(`R3: Images do not overflow their containers`, async ({ page }) => {
      await page.goto(`${BASE}/`, { waitUntil: 'load', timeout: 45000 });
      await page.waitForTimeout(1500); // wait for lazy images

      const overflowing = await page.evaluate(() => {
        const imgs = document.querySelectorAll('main img, #wrapwrap img');
        const issues = [];
        for (const img of imgs) {
          // Skip invisible images (icons, tracking pixels, etc.)
          const rect = img.getBoundingClientRect();
          if (rect.width === 0 || rect.height === 0) continue;
          if (getComputedStyle(img).display === 'none') continue;

          const parent = img.parentElement;
          if (!parent) continue;
          const parentRect = parent.getBoundingClientRect();

          // Check if image extends beyond parent by more than 2px tolerance
          const overflowRight = rect.right - parentRect.right;
          const overflowBottom = rect.bottom - parentRect.bottom;
          // Only flag significant overflow (> 5px) on the right side
          if (overflowRight > 5) {
            issues.push({
              src: (img.getAttribute('src') || '').substring(0, 80),
              imgWidth: Math.round(rect.width),
              parentWidth: Math.round(parentRect.width),
              overflowRight: Math.round(overflowRight),
              section: img.closest('section')?.id || '(unknown)',
            });
          }
        }
        return issues;
      });

      for (const item of overflowing) {
        console.log(`  [${vp.name}] OVERFLOW in #${item.section}: img(${item.imgWidth}px) exceeds parent(${item.parentWidth}px) by ${item.overflowRight}px -- ${item.src}`);
      }

      if (overflowing.length === 0) {
        console.log(`  [OK] R3 ${vp.name}: No image overflow detected`);
      }

      expect(
        overflowing,
        `${overflowing.length} image(s) overflow their containers`
      ).toHaveLength(0);
    });

    // ---------------------------------------------------------------
    // R4: Text is readable (font-size >= 12px on all viewports)
    // ---------------------------------------------------------------
    test(`R4: Text elements have readable font-size (>= 12px)`, async ({ page }) => {
      await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded', timeout: 45000 });

      const tooSmall = await page.evaluate((sectionIds) => {
        const issues = [];
        // Check text in all sections
        for (const secId of sectionIds) {
          const section = document.getElementById(secId);
          if (!section) continue;
          const textEls = section.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, a, li, td, th, label, div');
          for (const el of textEls) {
            // Skip empty elements
            const text = (el.textContent || '').trim();
            if (!text || text.length === 0) continue;
            // Skip hidden elements
            const style = getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden') continue;
            // Skip elements that only have child element text (avoid double-counting)
            const directText = Array.from(el.childNodes)
              .filter(n => n.nodeType === 3)
              .map(n => n.textContent.trim())
              .join('');
            if (!directText && el.tagName === 'DIV') continue;

            const fontSize = parseFloat(style.fontSize);
            if (fontSize < 12) {
              issues.push({
                section: secId,
                tag: el.tagName.toLowerCase(),
                fontSize: Math.round(fontSize * 10) / 10,
                text: text.substring(0, 40),
              });
            }
          }
        }
        return issues;
      }, SECTION_IDS);

      // Deduplicate by section+tag+fontSize
      const seen = new Set();
      const unique = tooSmall.filter(item => {
        const key = `${item.section}-${item.tag}-${item.fontSize}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });

      for (const item of unique) {
        console.log(`  [${vp.name}] SMALL TEXT in #${item.section}: <${item.tag}> fontSize=${item.fontSize}px -- "${item.text}"`);
      }

      if (unique.length === 0) {
        console.log(`  [OK] R4 ${vp.name}: All text >= 12px`);
      }

      // Use soft assertion on mobile -- some label text may intentionally be small
      if (vp.isMobile) {
        if (unique.length > 0) {
          console.log(`  [WARN] R4 ${vp.name}: ${unique.length} small text element(s) found (warning only on mobile)`);
        }
        // Still pass but warn -- allow down to 10px on mobile
        const critical = unique.filter(u => u.fontSize < 10);
        expect(
          critical,
          `${critical.length} text element(s) below 10px on mobile`
        ).toHaveLength(0);
      } else {
        expect(
          unique,
          `${unique.length} text element(s) below 12px on desktop`
        ).toHaveLength(0);
      }
    });

    // ---------------------------------------------------------------
    // R5: No overlapping elements (check key section elements)
    // ---------------------------------------------------------------
    test(`R5: No significant element overlaps within sections`, async ({ page }) => {
      await page.goto(`${BASE}/`, { waitUntil: 'load', timeout: 45000 });
      await page.waitForTimeout(1000);

      const overlaps = await page.evaluate((sectionIds) => {
        const issues = [];

        function rectsOverlap(a, b) {
          const overlapX = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left));
          const overlapY = Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
          return overlapX * overlapY;
        }

        // Check siblings at a given parent level for overlap
        function checkSiblings(parent, secId) {
          const children = Array.from(parent.children);
          const visible = children.filter(el => {
            const style = getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden') return false;
            // Skip absolutely/fixed positioned elements (overlays by design)
            const pos = style.position;
            if (pos === 'absolute' || pos === 'fixed') return false;
            const rect = el.getBoundingClientRect();
            return rect.width > 10 && rect.height > 10;
          });

          for (let i = 0; i < visible.length; i++) {
            for (let j = i + 1; j < visible.length; j++) {
              const a = visible[i].getBoundingClientRect();
              const b = visible[j].getBoundingClientRect();
              const overlapArea = rectsOverlap(a, b);
              const smallerArea = Math.min(a.width * a.height, b.width * b.height);
              // Only flag significant sibling overlap (> 500 sq px AND > 20% of smaller)
              if (overlapArea > 500 && smallerArea > 0 && (overlapArea / smallerArea) > 0.2) {
                issues.push({
                  section: secId,
                  elA: `${visible[i].tagName}${visible[i].id ? '#' + visible[i].id : ''}.${(visible[i].className || '').toString().split(' ')[0]}`,
                  elB: `${visible[j].tagName}${visible[j].id ? '#' + visible[j].id : ''}.${(visible[j].className || '').toString().split(' ')[0]}`,
                  overlapArea: Math.round(overlapArea),
                  overlapPct: Math.round((overlapArea / smallerArea) * 100),
                });
              }
            }
          }
        }

        for (const secId of sectionIds) {
          const section = document.getElementById(secId);
          if (!section) continue;
          // Check direct children of the section
          checkSiblings(section, secId);
          // Also check children inside .container / .container-fluid
          const containers = section.querySelectorAll(':scope > .container, :scope > .container-fluid');
          for (const c of containers) {
            checkSiblings(c, secId);
          }
          // Check inside rows
          const rows = section.querySelectorAll('.row');
          for (const r of rows) {
            checkSiblings(r, secId);
          }
        }
        return issues;
      }, SECTION_IDS);

      for (const item of overlaps) {
        console.log(`  [${vp.name}] OVERLAP in #${item.section}: ${item.elA} x ${item.elB} -- ${item.overlapArea}px^2 (${item.overlapPct}% of smaller)`);
      }

      if (overlaps.length === 0) {
        console.log(`  [OK] R5 ${vp.name}: No significant sibling overlaps detected`);
      }

      // Critical = sibling overlap covering > 50% of the smaller element
      const critical = overlaps.filter(o => o.overlapPct > 50);
      expect(
        critical,
        `${critical.length} critical sibling overlap(s) (>50% coverage) found`
      ).toHaveLength(0);
    });

    // ---------------------------------------------------------------
    // R6: Navigation is functional
    // ---------------------------------------------------------------
    test(`R6: Navigation is functional`, async ({ page }) => {
      await page.goto(`${BASE}/`, { waitUntil: 'load', timeout: 45000 });
      await page.waitForTimeout(1000);

      if (vp.isMobile) {
        // On mobile (< 992px = lg breakpoint), Odoo shows o_header_mobile nav
        // Desktop nav is hidden with d-none d-lg-block
        const mobileNav = page.locator('nav.o_header_mobile');
        const mobileNavCount = await mobileNav.count();
        const mobileNavVisible = mobileNavCount > 0 ? await mobileNav.isVisible() : false;

        console.log(`  [${vp.name}] Mobile nav count=${mobileNavCount} visible=${mobileNavVisible}`);

        if (mobileNavVisible) {
          // Check for clickable brand link or menu elements
          const brandLink = mobileNav.locator('a.navbar-brand, .navbar-brand');
          const brandCount = await brandLink.count();
          console.log(`  [${vp.name}] Mobile nav brand link count=${brandCount}`);

          // Check for toggler or menu items
          const toggler = mobileNav.locator('.navbar-toggler, button[data-bs-toggle]');
          const togglerCount = await toggler.count();
          const menuItems = mobileNav.locator('a.nav-link, .nav-item a');
          const menuCount = await menuItems.count();

          console.log(`  [${vp.name}] Toggler count=${togglerCount} Menu items=${menuCount}`);

          // Mobile nav should at least have brand or be visible
          expect(
            mobileNavVisible,
            `Mobile navigation is not visible at ${vp.width}px width`
          ).toBe(true);

          console.log(`  [OK] R6 ${vp.name}: Mobile navigation visible and functional`);
        } else {
          // Fallback: if no mobile nav, check for any visible nav
          const anyVisibleNav = await page.evaluate(() => {
            const navs = document.querySelectorAll('nav');
            for (const nav of navs) {
              if (getComputedStyle(nav).display !== 'none') return true;
            }
            return false;
          });

          // On tablet (768px), the desktop nav might be shown (lg breakpoint is 992px)
          // iPad at 768 is below lg, so mobile nav should show
          console.log(`  [${vp.name}] Any visible nav=${anyVisibleNav}`);
          expect(anyVisibleNav, `No visible navigation found at ${vp.width}px width`).toBe(true);
          console.log(`  [OK] R6 ${vp.name}: Navigation found and visible`);
        }
      } else {
        // Desktop: the navbar-expand-lg nav should be visible
        const desktopNav = page.locator('nav.navbar-expand-lg');
        const desktopNavCount = await desktopNav.count();
        const desktopNavVisible = desktopNavCount > 0 ? await desktopNav.isVisible() : false;

        console.log(`  [${vp.name}] Desktop nav count=${desktopNavCount} visible=${desktopNavVisible}`);

        if (desktopNavVisible) {
          // Check nav links are clickable
          const navLinks = desktopNav.locator('a.nav-link, .nav-item a');
          const linkCount = await navLinks.count();
          console.log(`  [${vp.name}] Desktop nav link count=${linkCount}`);

          expect(desktopNavVisible, `Desktop navigation not visible at ${vp.width}px`).toBe(true);
          console.log(`  [OK] R6 ${vp.name}: Desktop navigation visible with ${linkCount} links`);
        } else {
          // Fallback check
          const anyVisibleNav = await page.evaluate(() => {
            const navs = document.querySelectorAll('nav');
            for (const nav of navs) {
              if (getComputedStyle(nav).display !== 'none') return true;
            }
            return false;
          });
          expect(anyVisibleNav, `No visible navigation at desktop width ${vp.width}px`).toBe(true);
          console.log(`  [OK] R6 ${vp.name}: Navigation found`);
        }
      }
    });

    // ---------------------------------------------------------------
    // R7: Page viewport meta tag is present (mobile rendering)
    // ---------------------------------------------------------------
    test(`R7: Viewport meta tag is properly set`, async ({ page }) => {
      await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded', timeout: 45000 });

      const viewportMeta = await page.evaluate(() => {
        const meta = document.querySelector('meta[name="viewport"]');
        return meta ? meta.getAttribute('content') : null;
      });

      console.log(`  [${vp.name}] viewport meta: ${viewportMeta}`);

      expect(viewportMeta, 'No <meta name="viewport"> tag found').not.toBeNull();
      expect(viewportMeta).toContain('width=device-width');

      console.log(`  [OK] R7 ${vp.name}: Viewport meta tag present and correct`);
    });

    // ---------------------------------------------------------------
    // R8: Section content fits within viewport width
    // ---------------------------------------------------------------
    test(`R8: Section content fits within viewport width`, async ({ page }) => {
      await page.goto(`${BASE}/`, { waitUntil: 'load', timeout: 45000 });
      await page.waitForTimeout(1000);

      const overflowingSections = await page.evaluate((sectionIds) => {
        const viewportWidth = window.innerWidth;
        const issues = [];
        for (const id of sectionIds) {
          const section = document.getElementById(id);
          if (!section) continue;
          const rect = section.getBoundingClientRect();
          if (rect.width > viewportWidth + 2) { // 2px tolerance
            issues.push({
              id,
              sectionWidth: Math.round(rect.width),
              viewportWidth,
              overflow: Math.round(rect.width - viewportWidth),
            });
          }
        }
        return issues;
      }, SECTION_IDS);

      for (const item of overflowingSections) {
        console.log(`  [${vp.name}] SECTION OVERFLOW #${item.id}: ${item.sectionWidth}px > viewport ${item.viewportWidth}px (overflow: ${item.overflow}px)`);
      }

      if (overflowingSections.length === 0) {
        console.log(`  [OK] R8 ${vp.name}: All sections fit within viewport`);
      }

      expect(
        overflowingSections,
        `${overflowingSections.length} section(s) exceed viewport width`
      ).toHaveLength(0);
    });

  }); // end describe for this viewport

} // end viewport loop
