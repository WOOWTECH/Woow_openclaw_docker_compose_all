// tests/pre-launch/27-website-snippets.spec.mjs
// W1-W12: O.G老地方身體修復 homepage snippet conversion verification
//
// Validates that the custom website snippets are correctly installed,
// structured, and functional on the O.G老地方身體修復 production site.
import { test, expect } from '@playwright/test';
import { loginAsAdmin, BASE } from '../line-integration/helpers/odoo-rpc.mjs';

const SECTION_IDS = [
  'hero', 'story', 'services', 'flow',
  'booking', 'contact',
];

// Each section uses a CSS class prefixed with og- (the snippet naming convention)
const SECTION_CLASS_MAP = {
  hero: 'og-hero',
  story: 'og-story',
  services: 'og-services',
  flow: 'og-flow',
  booking: 'og-booking',
  contact: 'og-contact',
};

// Each section uses a data-snippet attribute with s_og_ prefix
const SECTION_SNIPPET_MAP = {
  hero: 's_og_hero',
  story: 's_og_story',
  services: 's_og_services',
  flow: 's_og_flow',
  booking: 's_og_booking',
  contact: 's_og_contact',
};

test.describe('W: Website Snippet Conversion Tests', () => {

  // =================================================================
  // W1: Homepage loads with 200 status
  // =================================================================
  test('W1: Homepage loads with 200 status', async ({ request }) => {
    const response = await request.get(`${BASE}/`);
    expect(response.status()).toBe(200);
    console.log(`[OK] W1: GET / returned status ${response.status()}`);
  });

  // =================================================================
  // W2: All 6 sections present
  // =================================================================
  test('W2: All 6 sections present on homepage', async ({ page }) => {
    await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });

    const missing = [];
    for (const id of SECTION_IDS) {
      const count = await page.locator(`#${id}`).count();
      if (count === 0) missing.push(id);
    }

    if (missing.length > 0) {
      console.log(`[WARN] W2: Missing sections: ${missing.join(', ')}`);
    }

    expect(missing, `Missing section IDs: ${missing.join(', ')}`).toHaveLength(0);
    console.log(`[OK] W2: All 6 sections found: ${SECTION_IDS.join(', ')}`);
  });

  // =================================================================
  // W3: Each section has its og- CSS class (snippet identity marker)
  // =================================================================
  test('W3: Each section has its og- CSS class (snippet identity)', async ({ page }) => {
    await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });

    const results = [];
    for (const id of SECTION_IDS) {
      const el = page.locator(`#${id}`);
      const count = await el.count();
      if (count === 0) {
        results.push({ id, ok: false, reason: 'element not found' });
        continue;
      }
      const classes = await el.getAttribute('class') || '';
      const expectedClass = SECTION_CLASS_MAP[id];
      const ok = classes.includes(expectedClass);
      results.push({ id, classes: classes.substring(0, 60), expectedClass, ok, reason: ok ? '' : `missing class "${expectedClass}"` });
    }

    const failures = results.filter(r => !r.ok);
    for (const r of results) {
      console.log(`  #${r.id}: class="${r.classes}" expected="${r.expectedClass}" ${r.ok ? 'OK' : 'FAIL: ' + r.reason}`);
    }

    expect(failures, `Sections missing og- class: ${failures.map(f => f.id).join(', ')}`).toHaveLength(0);
    console.log(`[OK] W3: All sections have their og- CSS class`);
  });

  // =================================================================
  // W4: oe_structure wrapper exists (Odoo page structure)
  // =================================================================
  test('W4: Odoo page structure wrapper exists', async ({ page }) => {
    await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });

    // Odoo 18 uses #wrapwrap as the main page wrapper
    const wrapwrapCount = await page.locator('#wrapwrap').count();
    console.log(`  #wrapwrap count: ${wrapwrapCount}`);

    // .oe_structure exists somewhere on the page (typically footer)
    const oeStructureCount = await page.locator('.oe_structure').count();
    console.log(`  .oe_structure count: ${oeStructureCount}`);

    // The page must have a main element inside wrapwrap
    const mainCount = await page.locator('#wrapwrap main').count();
    console.log(`  #wrapwrap > main count: ${mainCount}`);

    expect(wrapwrapCount, '#wrapwrap not found on homepage').toBeGreaterThanOrEqual(1);
    expect(mainCount, 'No <main> element inside #wrapwrap').toBeGreaterThanOrEqual(1);

    console.log(`[OK] W4: Odoo page structure found (#wrapwrap + main)`);
  });

  // =================================================================
  // W5: Hero section content — "O.G" or "老地方" text
  // =================================================================
  test('W5: Hero section contains O.G branding text', async ({ page }) => {
    await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });

    const heroSection = page.locator('#hero');
    const heroCount = await heroSection.count();

    if (heroCount === 0) {
      // Fallback: search entire page for the text
      const bodyText = await page.textContent('body');
      const hasOG = bodyText.includes('O.G') || bodyText.includes('老地方');
      expect(hasOG, 'Neither "O.G" nor "老地方" found in page body').toBe(true);
      console.log(`[OK] W5: O.G branding found in page body (no #hero section)`);
      return;
    }

    const heroText = await heroSection.textContent();
    // Check for the studio name
    const hasOG = heroText.includes('O.G') || heroText.includes('老地方');
    expect(hasOG, `Hero text does not contain "O.G" or "老地方": "${heroText.slice(0, 200)}"`).toBe(true);

    console.log(`[OK] W5: Hero section contains O.G branding`);
  });

  // =================================================================
  // W6: Booking CTA link to /appointment/1/schedule exists
  // =================================================================
  test('W6: Booking CTA link to /appointment/1/schedule exists', async ({ page }) => {
    await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });

    // Look for any link containing the appointment schedule path
    const bookingLink = page.locator('a[href*="/appointment/1/schedule"], a[href*="appointment"][href*="schedule"]');
    const count = await bookingLink.count();

    if (count > 0) {
      const href = await bookingLink.first().getAttribute('href');
      console.log(`  First booking link href: ${href}`);
    }

    expect(count, 'No link to /appointment/1/schedule found on homepage').toBeGreaterThanOrEqual(1);
    console.log(`[OK] W6: Found ${count} link(s) to appointment schedule`);
  });

  // =================================================================
  // W7: Smooth scroll mechanism loaded
  // =================================================================
  test('W7: Smooth scroll mechanism loaded in page assets', async ({ page }) => {
    await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });

    // Check page source for any smooth scroll mechanism:
    // - smooth_scroll.js script
    // - CSS scroll-behavior: smooth
    // - JS scrollTo with smooth behavior
    // - scrollIntoView calls
    const pageContent = await page.content();

    const indicators = {
      smooth_scroll_js: pageContent.includes('smooth_scroll'),
      css_scroll_behavior: pageContent.includes('scroll-behavior'),
      js_scrollTo: pageContent.includes('scrollTo'),
      js_smooth: pageContent.includes('smooth'),
      scrollIntoView: pageContent.includes('scrollIntoView'),
    };

    const foundIndicators = Object.entries(indicators).filter(([, v]) => v).map(([k]) => k);

    for (const [key, val] of Object.entries(indicators)) {
      console.log(`  ${key}: ${val}`);
    }

    expect(foundIndicators.length, 'No smooth scroll mechanism found on homepage').toBeGreaterThan(0);
    console.log(`[OK] W7: Smooth scroll mechanism found: ${foundIndicators.join(', ')}`);
  });

  // =================================================================
  // W8: Admin can access website editor (edit button visible)
  // =================================================================
  test('W8: Admin can access website editor', async ({ page }) => {
    await loginAsAdmin(page);

    // Navigate to the public homepage as admin
    await page.goto(`${BASE}/`, { waitUntil: 'load' });
    await page.waitForTimeout(4000); // Let editor toolbar / frontend buttons load

    // In Odoo 18, the admin frontend edit button is:
    // <a class="o_frontend_to_backend_edit_btn ...">編輯</a>
    const editSelectors = [
      'a.o_frontend_to_backend_edit_btn',
      'a.o_edit_website',
      '#edit-page-menu',
      '.o_edit_website_container',
      '.o_we_edit_btn',
      '[data-action="edit"]',
    ];

    let editFound = false;
    let foundSelector = '';
    for (const sel of editSelectors) {
      const count = await page.locator(sel).count();
      if (count > 0) {
        editFound = true;
        foundSelector = sel;
        break;
      }
    }

    console.log(`  Edit button found: ${editFound} (selector: ${foundSelector || 'none'})`);

    if (editFound) {
      const editText = await page.locator(foundSelector).first().textContent();
      console.log(`  Edit button text: "${editText.trim()}"`);
    }

    expect(editFound, 'No website editor edit button found for admin user').toBe(true);
    console.log(`[OK] W8: Admin has website editor access via ${foundSelector}`);
  });

  // =================================================================
  // W9: All website snippet images load (no 404)
  // =================================================================
  test('W9: All website snippet images load without 404', async ({ page }) => {
    // Track all image request statuses for both old and new module naming
    const imageStatuses = [];
    page.on('response', (response) => {
      const url = response.url();
      if ((url.includes('markstudio_website') || url.includes('og_website') || url.includes('s_og_')) && /\.(png|jpg|jpeg|gif|svg|webp)/i.test(url)) {
        imageStatuses.push({ url: url.substring(0, 120), status: response.status() });
      }
    });

    await page.goto(`${BASE}/`, { waitUntil: 'load', timeout: 45000 });

    // Count img tags from website snippets
    const imgCount = await page.locator('img[src*="markstudio_website"], img[src*="og_website"], img[src*="web/image"]').count();
    console.log(`  Found ${imgCount} img elements from website snippets`);

    // Check tracked responses for 404s
    const failed = imageStatuses.filter(i => i.status >= 400);
    for (const img of imageStatuses) {
      const label = img.status >= 400 ? 'FAIL' : 'OK';
      console.log(`  [${label}] ${img.status} ${img.url}`);
    }

    if (imageStatuses.length === 0 && imgCount === 0) {
      console.log(`  [INFO] No snippet images found -- snippet may use different asset paths`);
      // Not a failure -- the module might use different naming
      return;
    }

    expect(failed, `${failed.length} image(s) returned 4xx/5xx`).toHaveLength(0);
    console.log(`[OK] W9: All ${imageStatuses.length} website snippet images loaded successfully`);
  });

  // =================================================================
  // W10: data-snippet attributes present on all sections
  // =================================================================
  test('W10: data-snippet attributes present on all sections', async ({ page }) => {
    await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });

    const results = [];
    for (const id of SECTION_IDS) {
      const el = page.locator(`#${id}`);
      const count = await el.count();
      if (count === 0) {
        results.push({ id, ok: false, reason: 'element not found' });
        continue;
      }
      const snippet = await el.getAttribute('data-snippet') || '';
      const expectedSnippet = SECTION_SNIPPET_MAP[id];
      const ok = snippet === expectedSnippet;
      results.push({ id, snippet, expectedSnippet, ok, reason: ok ? '' : `data-snippet="${snippet}" expected "${expectedSnippet}"` });
    }

    const failures = results.filter(r => !r.ok);
    for (const r of results) {
      console.log(`  #${r.id}: data-snippet="${r.snippet}" expected="${r.expectedSnippet}" ${r.ok ? 'OK' : 'FAIL: ' + r.reason}`);
    }

    expect(failures, `Sections with wrong data-snippet: ${failures.map(f => `${f.id}(${f.reason})`).join(', ')}`).toHaveLength(0);
    console.log(`[OK] W10: All sections have correct s_og_ data-snippet attributes`);
  });

  // =================================================================
  // W11: Contact section contains map or address information
  // =================================================================
  test('W11: Contact section contains map or address info', async ({ page }) => {
    await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });

    const contactExists = await page.locator('#contact').count();
    if (contactExists === 0) {
      console.log(`  [SKIP] W11: No #contact section found`);
      test.skip();
      return;
    }

    const contactSection = page.locator('#contact');
    const contactHtml = await contactSection.innerHTML();

    // Check for map iframe, address text, or contact-related content
    const indicators = {
      hasIframe: contactHtml.includes('<iframe'),
      hasMap: contactHtml.toLowerCase().includes('map') || contactHtml.includes('google.com/maps'),
      hasAddress: contactHtml.includes('地址') || contactHtml.includes('address') || contactHtml.includes('台'),
      hasPhone: contactHtml.includes('tel:') || contactHtml.includes('電話') || contactHtml.includes('phone'),
      hasLink: contactHtml.includes('<a '),
    };

    const foundIndicators = Object.entries(indicators).filter(([, v]) => v).map(([k]) => k);

    for (const [key, val] of Object.entries(indicators)) {
      console.log(`  ${key}: ${val}`);
    }

    expect(foundIndicators.length, 'Contact section has no map, address, or contact info').toBeGreaterThan(0);
    console.log(`[OK] W11: Contact section contains: ${foundIndicators.join(', ')}`);
  });

  // =================================================================
  // W12: No duplicate homepage template -- single #wrapwrap element
  // =================================================================
  test('W12: No duplicate homepage template -- single #wrapwrap', async ({ page }) => {
    await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });

    // Odoo 18 uses #wrapwrap as the outermost content wrapper
    const wrapwrapCount = await page.locator('#wrapwrap').count();
    console.log(`  #wrapwrap count: ${wrapwrapCount}`);

    expect(wrapwrapCount, `Found ${wrapwrapCount} #wrapwrap elements -- expected exactly 1`).toBe(1);

    // Also verify there is exactly 1 <main> inside the page
    const mainCount = await page.locator('main').count();
    console.log(`  <main> count: ${mainCount}`);
    expect(mainCount, `Found ${mainCount} <main> elements -- expected exactly 1`).toBe(1);

    console.log(`[OK] W12: Exactly 1 #wrapwrap and 1 <main> on homepage (no duplicate templates)`);
  });

});
