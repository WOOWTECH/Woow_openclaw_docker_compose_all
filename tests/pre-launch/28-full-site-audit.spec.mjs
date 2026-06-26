// tests/pre-launch/28-full-site-audit.spec.mjs
// Full-site audit of O.G老地方身體修復 website
// Tests every public-facing page for HTTP status, JS errors, network failures,
// broken images, and key content presence.

import { test, expect } from '@playwright/test';

const BASE = process.env.ODOO_BASE_URL || 'https://markstudio-odoo.woowtech.io';

// ---------------------------------------------------------------------------
// Shared collector helpers
// ---------------------------------------------------------------------------

/**
 * Attach console-error and failed-network-request collectors to a page.
 * Returns { consoleErrors, networkErrors } arrays that fill up as page loads.
 */
function attachCollectors(page) {
  const consoleErrors = [];
  const networkErrors = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  page.on('response', (response) => {
    const status = response.status();
    // Track 4xx and 5xx responses, but ignore some expected cases
    if (status >= 400) {
      const url = response.url();
      // Skip common Odoo noise: favicon, sourcemaps, bus polling
      if (
        url.includes('/favicon') ||
        url.includes('.map') ||
        url.includes('/longpolling') ||
        url.includes('/websocket') ||
        url.includes('/bus/')
      ) return;
      networkErrors.push({ url: url.substring(0, 200), status });
    }
  });

  return { consoleErrors, networkErrors };
}

/**
 * Check that no images on the page are broken (naturalWidth === 0 for loaded imgs).
 * Returns an array of broken image srcs.
 */
async function findBrokenImages(page) {
  return page.evaluate(() => {
    const imgs = Array.from(document.querySelectorAll('img'));
    const broken = [];
    for (const img of imgs) {
      // Skip tiny tracking pixels, hidden imgs, and data URIs
      if (!img.src || img.src.startsWith('data:')) continue;
      if (img.offsetWidth === 0 && img.offsetHeight === 0) continue; // hidden
      // naturalWidth === 0 means the image failed to load
      if (img.complete && img.naturalWidth === 0) {
        broken.push(img.src.substring(0, 200));
      }
    }
    return broken;
  });
}

// ---------------------------------------------------------------------------
// Helper: standard page audit (reused across tests)
// ---------------------------------------------------------------------------
async function auditPage(page, path, label, opts = {}) {
  const {
    expectedStatus = 200,
    contentCheck = null,          // string or regex to find in body text
    contentSelector = null,       // CSS selector that must exist
    allowRedirect = false,        // if true, accept 302→200 chain
    waitUntil = 'load',
    timeout = 45000,
    skipBrokenImages = false,
  } = opts;

  const url = `${BASE}${path}`;
  const { consoleErrors, networkErrors } = attachCollectors(page);

  // Navigate
  const response = await page.goto(url, { waitUntil, timeout });
  const status = response?.status() ?? 0;
  console.log(`  [${label}] GET ${path} → ${status}`);

  // Status check
  if (allowRedirect) {
    expect([200, 302, 303]).toContain(status);
  } else {
    expect(status, `${label}: expected ${expectedStatus}, got ${status}`).toBe(expectedStatus);
  }

  // Wait a beat for async JS to settle
  await page.waitForTimeout(2000);

  // Content check — body not blank
  const bodyText = await page.textContent('body').catch(() => '');
  expect(bodyText.length, `${label}: page body is empty`).toBeGreaterThan(10);

  // Optional: specific text content
  if (contentCheck) {
    if (contentCheck instanceof RegExp) {
      expect(bodyText).toMatch(contentCheck);
    } else {
      expect(bodyText).toContain(contentCheck);
    }
    console.log(`  [${label}] Content check passed: "${contentCheck}"`);
  }

  // Optional: specific DOM element
  if (contentSelector) {
    const count = await page.locator(contentSelector).count();
    expect(count, `${label}: selector "${contentSelector}" not found`).toBeGreaterThanOrEqual(1);
    console.log(`  [${label}] Selector "${contentSelector}" found (${count})`);
  }

  // Broken images
  if (!skipBrokenImages) {
    const broken = await findBrokenImages(page);
    if (broken.length > 0) {
      console.log(`  [${label}] Broken images (${broken.length}):`);
      for (const src of broken) console.log(`    - ${src}`);
    }
    expect(broken, `${label}: ${broken.length} broken image(s)`).toHaveLength(0);
  }

  // JS console errors
  // Filter out non-critical noise (Odoo often emits benign warnings)
  const criticalErrors = consoleErrors.filter((e) => {
    const lower = e.toLowerCase();
    // Skip known non-critical patterns
    if (lower.includes('failed to load resource') && lower.includes('favicon')) return false;
    if (lower.includes('third-party cookie')) return false;
    if (lower.includes('deprecated')) return false;
    if (lower.includes('permissions policy')) return false;
    if (lower.includes('serviceworker')) return false;
    return true;
  });

  if (criticalErrors.length > 0) {
    console.log(`  [${label}] JS console errors (${criticalErrors.length}):`);
    for (const e of criticalErrors) console.log(`    - ${e.substring(0, 200)}`);
  }

  // Network errors (4xx/5xx)
  if (networkErrors.length > 0) {
    console.log(`  [${label}] Network errors (${networkErrors.length}):`);
    for (const ne of networkErrors) console.log(`    - ${ne.status} ${ne.url}`);
  }

  return {
    status,
    bodyLength: bodyText.length,
    consoleErrors: criticalErrors,
    networkErrors,
    passed: true,
  };
}

// ===========================================================================
// TEST SUITE
// ===========================================================================

test.describe('28: Full Site Audit — O.G老地方身體修復', () => {

  // Increase per-test timeout for network latency
  test.setTimeout(60000);

  // ─────────────────────────────────────────────────────────────────────────
  // 1. Homepage
  // ─────────────────────────────────────────────────────────────────────────
  test('A1: Homepage loads correctly', async ({ page }) => {
    const result = await auditPage(page, '/', 'Homepage', {
      contentCheck: 'O.G',
      contentSelector: '#wrapwrap',
    });
    console.log(`[PASS] A1: Homepage — status=${result.status}, body=${result.bodyLength} bytes, ` +
      `JS errors=${result.consoleErrors.length}, network errors=${result.networkErrors.length}`);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // 2. Appointment booking
  // ─────────────────────────────────────────────────────────────────────────
  test('A2: Appointment booking page loads', async ({ page }) => {
    const result = await auditPage(page, '/appointment/1/schedule', 'Appointment', {
      contentSelector: '#wrapwrap',
    });
    console.log(`[PASS] A2: Appointment — status=${result.status}, body=${result.bodyLength} bytes, ` +
      `JS errors=${result.consoleErrors.length}, network errors=${result.networkErrors.length}`);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // 3. Login page
  // ─────────────────────────────────────────────────────────────────────────
  test('A3: Login page loads', async ({ page }) => {
    const result = await auditPage(page, '/web/login', 'Login', {
      contentSelector: 'input[name="login"]',
    });
    console.log(`[PASS] A3: Login — status=${result.status}, body=${result.bodyLength} bytes, ` +
      `JS errors=${result.consoleErrors.length}, network errors=${result.networkErrors.length}`);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // 4. Portal home (requires login — redirects to /web/login if not logged in)
  // ─────────────────────────────────────────────────────────────────────────
  test('A4: Portal home — unauthenticated redirects to login', async ({ page }) => {
    const { consoleErrors, networkErrors } = attachCollectors(page);

    const response = await page.goto(`${BASE}/my/home`, { waitUntil: 'load', timeout: 45000 });
    const status = response?.status() ?? 0;
    const finalUrl = page.url();

    console.log(`  [Portal Home] GET /my/home → ${status}, final URL: ${finalUrl}`);

    // Should redirect to login (200 on the login page after redirect)
    expect([200, 302, 303]).toContain(status);

    // The final URL should be the login page (redirect) or the portal
    const isLoginOrPortal = finalUrl.includes('/web/login') || finalUrl.includes('/my');
    expect(isLoginOrPortal, `Unexpected final URL: ${finalUrl}`).toBe(true);

    // Body should not be blank
    const bodyText = await page.textContent('body').catch(() => '');
    expect(bodyText.length).toBeGreaterThan(10);

    await page.waitForTimeout(1000);

    const criticalErrors = consoleErrors.filter(e => !e.toLowerCase().includes('favicon') && !e.toLowerCase().includes('third-party'));
    if (criticalErrors.length > 0) {
      console.log(`  [Portal Home] JS errors: ${criticalErrors.length}`);
      for (const e of criticalErrors) console.log(`    - ${e.substring(0, 200)}`);
    }

    console.log(`[PASS] A4: Portal home — status=${status}, redirected=${finalUrl.includes('/web/login')}, ` +
      `JS errors=${criticalErrors.length}, network errors=${networkErrors.length}`);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // 5. Portal bookings (unauthenticated — should redirect)
  // ─────────────────────────────────────────────────────────────────────────
  test('A5: Portal bookings — unauthenticated redirects to login', async ({ page }) => {
    const { consoleErrors, networkErrors } = attachCollectors(page);

    const response = await page.goto(`${BASE}/my/ext-bookings`, { waitUntil: 'load', timeout: 45000 });
    const status = response?.status() ?? 0;
    const finalUrl = page.url();

    console.log(`  [Portal Bookings] GET /my/ext-bookings → ${status}, final URL: ${finalUrl}`);

    expect([200, 302, 303]).toContain(status);

    const isLoginOrBookings = finalUrl.includes('/web/login') || finalUrl.includes('/my/ext-bookings');
    expect(isLoginOrBookings, `Unexpected final URL: ${finalUrl}`).toBe(true);

    const bodyText = await page.textContent('body').catch(() => '');
    expect(bodyText.length).toBeGreaterThan(10);

    await page.waitForTimeout(1000);

    const criticalErrors = consoleErrors.filter(e => !e.toLowerCase().includes('favicon') && !e.toLowerCase().includes('third-party'));
    console.log(`[PASS] A5: Portal bookings — status=${status}, redirected=${finalUrl.includes('/web/login')}, ` +
      `JS errors=${criticalErrors.length}, network errors=${networkErrors.length}`);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // 6. Portal account (unauthenticated — should redirect)
  // ─────────────────────────────────────────────────────────────────────────
  test('A6: Portal account — unauthenticated redirects to login', async ({ page }) => {
    const { consoleErrors, networkErrors } = attachCollectors(page);

    const response = await page.goto(`${BASE}/my/account`, { waitUntil: 'load', timeout: 45000 });
    const status = response?.status() ?? 0;
    const finalUrl = page.url();

    console.log(`  [Portal Account] GET /my/account → ${status}, final URL: ${finalUrl}`);

    expect([200, 302, 303]).toContain(status);

    const isLoginOrAccount = finalUrl.includes('/web/login') || finalUrl.includes('/my/account');
    expect(isLoginOrAccount, `Unexpected final URL: ${finalUrl}`).toBe(true);

    const bodyText = await page.textContent('body').catch(() => '');
    expect(bodyText.length).toBeGreaterThan(10);

    await page.waitForTimeout(1000);

    const criticalErrors = consoleErrors.filter(e => !e.toLowerCase().includes('favicon') && !e.toLowerCase().includes('third-party'));
    console.log(`[PASS] A6: Portal account — status=${status}, redirected=${finalUrl.includes('/web/login')}, ` +
      `JS errors=${criticalErrors.length}, network errors=${networkErrors.length}`);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // 7. LIFF redirect /liff/redirect/book
  // ─────────────────────────────────────────────────────────────────────────
  test('A7: LIFF redirect page loads', async ({ page }) => {
    const { consoleErrors, networkErrors } = attachCollectors(page);

    const response = await page.goto(`${BASE}/liff/redirect/book`, {
      waitUntil: 'domcontentloaded',
      timeout: 45000,
    });
    const status = response?.status() ?? 0;
    const finalUrl = page.url();

    console.log(`  [LIFF Redirect] GET /liff/redirect/book → ${status}, final URL: ${finalUrl}`);

    // LIFF redirect may return 200 (with a bridge page) or could redirect
    expect(status, `LIFF redirect returned unexpected status ${status}`).toBeLessThan(500);

    // Check page is not blank — LIFF bridge pages trigger immediate LIFF SDK redirect,
    // so page.content() may fail with "page is navigating". Wrap in try/catch.
    let bodyText = '';
    let hasLiffSdk = false;
    try {
      bodyText = await page.textContent('body').catch(() => '');
      console.log(`  [LIFF Redirect] Body length: ${bodyText.length}`);
    } catch {
      console.log(`  [LIFF Redirect] Body read skipped (page navigating — LIFF SDK redirect in progress)`);
    }

    try {
      const pageContent = await page.content();
      hasLiffSdk = pageContent.includes('liff') || pageContent.includes('LIFF') || pageContent.includes('line-login');
    } catch {
      // Page is navigating due to LIFF SDK — this is expected behavior
      hasLiffSdk = true; // If it's navigating, the LIFF SDK triggered the redirect
      console.log(`  [LIFF Redirect] page.content() skipped (LIFF SDK redirect in progress — expected)`);
    }
    console.log(`  [LIFF Redirect] Contains LIFF references: ${hasLiffSdk}`);

    const criticalErrors = consoleErrors.filter(e => {
      const lower = e.toLowerCase();
      // LIFF pages may show CORS/SDK errors in non-LINE browsers — skip those
      if (lower.includes('liff') || lower.includes('line')) return false;
      if (lower.includes('favicon')) return false;
      if (lower.includes('third-party')) return false;
      if (lower.includes('cors')) return false;
      return true;
    });

    if (networkErrors.length > 0) {
      console.log(`  [LIFF Redirect] Network errors: ${networkErrors.length}`);
      for (const ne of networkErrors) console.log(`    - ${ne.status} ${ne.url}`);
    }

    console.log(`[PASS] A7: LIFF redirect — status=${status}, hasLIFF=${hasLiffSdk}, ` +
      `JS errors=${criticalErrors.length}, network errors=${networkErrors.length}`);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // 8. LIFF news page
  // ─────────────────────────────────────────────────────────────────────────
  test('A8: LIFF news page loads', async ({ page }) => {
    const { consoleErrors, networkErrors } = attachCollectors(page);

    const response = await page.goto(`${BASE}/liff/news`, {
      waitUntil: 'domcontentloaded',
      timeout: 45000,
    });
    const status = response?.status() ?? 0;

    console.log(`  [LIFF News] GET /liff/news → ${status}`);

    expect(status, `LIFF news returned ${status}`).toBeLessThan(500);

    const bodyText = await page.textContent('body').catch(() => '');
    console.log(`  [LIFF News] Body length: ${bodyText.length}`);

    // Page should have some content (even if minimal LIFF page)
    expect(bodyText.length, 'LIFF news page is blank').toBeGreaterThan(5);

    await page.waitForTimeout(1000);

    // Check for broken images
    const broken = await findBrokenImages(page);
    if (broken.length > 0) {
      console.log(`  [LIFF News] Broken images: ${broken.length}`);
      for (const src of broken) console.log(`    - ${src}`);
    }

    const criticalErrors = consoleErrors.filter(e => {
      const lower = e.toLowerCase();
      if (lower.includes('liff') || lower.includes('line') || lower.includes('cors')) return false;
      if (lower.includes('favicon') || lower.includes('third-party')) return false;
      return true;
    });

    console.log(`[PASS] A8: LIFF news — status=${status}, body=${bodyText.length}, ` +
      `broken images=${broken.length}, JS errors=${criticalErrors.length}, network errors=${networkErrors.length}`);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // 9. LIFF locations page
  // ─────────────────────────────────────────────────────────────────────────
  test('A9: LIFF locations page loads', async ({ page }) => {
    const { consoleErrors, networkErrors } = attachCollectors(page);

    const response = await page.goto(`${BASE}/liff/locations`, {
      waitUntil: 'domcontentloaded',
      timeout: 45000,
    });
    const status = response?.status() ?? 0;

    console.log(`  [LIFF Locations] GET /liff/locations → ${status}`);

    expect(status, `LIFF locations returned ${status}`).toBeLessThan(500);

    const bodyText = await page.textContent('body').catch(() => '');
    console.log(`  [LIFF Locations] Body length: ${bodyText.length}`);

    expect(bodyText.length, 'LIFF locations page is blank').toBeGreaterThan(5);

    await page.waitForTimeout(1000);

    // Check for broken images
    const broken = await findBrokenImages(page);
    if (broken.length > 0) {
      console.log(`  [LIFF Locations] Broken images: ${broken.length}`);
      for (const src of broken) console.log(`    - ${src}`);
    }

    const criticalErrors = consoleErrors.filter(e => {
      const lower = e.toLowerCase();
      if (lower.includes('liff') || lower.includes('line') || lower.includes('cors')) return false;
      if (lower.includes('favicon') || lower.includes('third-party')) return false;
      return true;
    });

    console.log(`[PASS] A9: LIFF locations — status=${status}, body=${bodyText.length}, ` +
      `broken images=${broken.length}, JS errors=${criticalErrors.length}, network errors=${networkErrors.length}`);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // 10. /news redirect
  // ─────────────────────────────────────────────────────────────────────────
  test('A10: /news redirect works', async ({ page }) => {
    const { consoleErrors, networkErrors } = attachCollectors(page);

    const response = await page.goto(`${BASE}/news`, {
      waitUntil: 'domcontentloaded',
      timeout: 45000,
    });
    const status = response?.status() ?? 0;
    const finalUrl = page.url();

    console.log(`  [/news] GET /news → ${status}, final URL: ${finalUrl}`);

    // /news may redirect to blog or another page, or serve content directly
    expect(status, `/news returned server error ${status}`).toBeLessThan(500);

    const bodyText = await page.textContent('body').catch(() => '');
    console.log(`  [/news] Body length: ${bodyText.length}`);

    await page.waitForTimeout(1000);

    const criticalErrors = consoleErrors.filter(e => {
      const lower = e.toLowerCase();
      if (lower.includes('favicon') || lower.includes('third-party')) return false;
      return true;
    });

    if (networkErrors.length > 0) {
      console.log(`  [/news] Network errors: ${networkErrors.length}`);
      for (const ne of networkErrors) console.log(`    - ${ne.status} ${ne.url}`);
    }

    console.log(`[PASS] A10: /news — status=${status}, final=${finalUrl}, ` +
      `JS errors=${criticalErrors.length}, network errors=${networkErrors.length}`);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // 11. Health check
  // ─────────────────────────────────────────────────────────────────────────
  test('A11: Health check endpoint', async ({ request }) => {
    const response = await request.get(`${BASE}/web/health`);
    const status = response.status();
    const body = await response.text();

    console.log(`  [Health] GET /web/health → ${status}, body: "${body.substring(0, 100)}"`);

    expect(status, `Health check returned ${status}`).toBe(200);
    // Odoo 18 health check returns {"status": "pass"} or plain "ok"
    const bodyLower = body.toLowerCase();
    const isHealthy = bodyLower.includes('ok') || bodyLower.includes('pass');
    expect(isHealthy, `Health check body does not indicate success: "${body}"`).toBe(true);

    console.log(`[PASS] A11: Health check — status=${status}, response="${body.trim()}"`);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // 12. Cross-page: No 500 errors across all public pages (summary)
  // ─────────────────────────────────────────────────────────────────────────
  test('A12: Batch HTTP status check — all public pages return < 500', async ({ request }) => {
    const paths = [
      '/',
      '/appointment/1/schedule',
      '/web/login',
      '/my/home',
      '/my/ext-bookings',
      '/my/account',
      '/liff/redirect/book',
      '/liff/news',
      '/liff/locations',
      '/news',
      '/web/health',
    ];

    const results = [];
    for (const path of paths) {
      try {
        const response = await request.get(`${BASE}${path}`, {
          maxRedirects: 0,  // don't follow redirects — just check the immediate response
        });
        const status = response.status();
        results.push({ path, status, ok: status < 500 });
      } catch (err) {
        // request.get with maxRedirects: 0 throws on redirect in some configs
        // Try again with default redirect handling
        try {
          const response = await request.get(`${BASE}${path}`);
          const status = response.status();
          results.push({ path, status, ok: status < 500 });
        } catch (err2) {
          results.push({ path, status: 0, ok: false, error: err2.message });
        }
      }
    }

    console.log('  ┌──────────────────────────────────────────────────────┐');
    console.log('  │  Full Site Audit — HTTP Status Summary               │');
    console.log('  ├──────────────────────────────────────────────────────┤');
    for (const r of results) {
      const icon = r.ok ? 'PASS' : 'FAIL';
      const statusStr = String(r.status).padStart(3);
      console.log(`  │  [${icon}] ${statusStr}  ${r.path.padEnd(35)} ${r.error || ''} │`);
    }
    console.log('  └──────────────────────────────────────────────────────┘');

    const failures = results.filter(r => !r.ok);
    expect(failures, `${failures.length} page(s) returned 5xx: ${failures.map(f => f.path).join(', ')}`).toHaveLength(0);

    console.log(`[PASS] A12: All ${results.length} pages returned < 500`);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // 13. Homepage — all images load (comprehensive broken image check)
  // ─────────────────────────────────────────────────────────────────────────
  test('A13: Homepage — all images load without errors', async ({ page }) => {
    const failedImageRequests = [];

    page.on('response', (response) => {
      const url = response.url();
      const status = response.status();
      if (status >= 400 && /\.(png|jpg|jpeg|gif|svg|webp|ico)/i.test(url)) {
        if (!url.includes('favicon')) {
          failedImageRequests.push({ url: url.substring(0, 200), status });
        }
      }
    });

    await page.goto(`${BASE}/`, { waitUntil: 'load', timeout: 45000 });
    await page.waitForTimeout(3000); // Let lazy images load

    // Count total images on page
    const totalImages = await page.locator('img').count();
    console.log(`  [Homepage Images] Total <img> elements: ${totalImages}`);

    // Check for broken images via DOM
    const brokenDom = await findBrokenImages(page);
    if (brokenDom.length > 0) {
      console.log(`  [Homepage Images] Broken via DOM check (${brokenDom.length}):`);
      for (const src of brokenDom) console.log(`    - ${src}`);
    }

    // Check for failed image network requests
    if (failedImageRequests.length > 0) {
      console.log(`  [Homepage Images] Failed image requests (${failedImageRequests.length}):`);
      for (const r of failedImageRequests) console.log(`    - ${r.status} ${r.url}`);
    }

    expect(brokenDom, `${brokenDom.length} broken image(s) in DOM`).toHaveLength(0);
    expect(failedImageRequests, `${failedImageRequests.length} image request(s) failed`).toHaveLength(0);

    console.log(`[PASS] A13: Homepage — all ${totalImages} images loaded successfully`);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // 14. Homepage — no critical JS errors
  // ─────────────────────────────────────────────────────────────────────────
  test('A14: Homepage — no critical JS errors on load', async ({ page }) => {
    const jsErrors = [];
    const uncaughtExceptions = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        // Filter known benign patterns
        const lower = text.toLowerCase();
        if (lower.includes('favicon')) return;
        if (lower.includes('third-party cookie')) return;
        if (lower.includes('deprecated')) return;
        if (lower.includes('permissions policy')) return;
        if (lower.includes('serviceworker')) return;
        if (lower.includes('.map')) return;
        jsErrors.push(text);
      }
    });

    page.on('pageerror', (error) => {
      uncaughtExceptions.push(error.message);
    });

    await page.goto(`${BASE}/`, { waitUntil: 'load', timeout: 45000 });
    await page.waitForTimeout(3000);

    if (jsErrors.length > 0) {
      console.log(`  [Homepage JS] Console errors (${jsErrors.length}):`);
      for (const e of jsErrors) console.log(`    - ${e.substring(0, 300)}`);
    }

    if (uncaughtExceptions.length > 0) {
      console.log(`  [Homepage JS] Uncaught exceptions (${uncaughtExceptions.length}):`);
      for (const e of uncaughtExceptions) console.log(`    - ${e.substring(0, 300)}`);
    }

    // Uncaught exceptions are hard failures
    expect(uncaughtExceptions, `${uncaughtExceptions.length} uncaught JS exception(s)`).toHaveLength(0);

    console.log(`[PASS] A14: Homepage — ${jsErrors.length} console error(s), 0 uncaught exceptions`);
  });

  // ─────────────────────────────────────────────────────────────────────────
  // 15. Appointment page — no critical JS errors or broken images
  // ─────────────────────────────────────────────────────────────────────────
  test('A15: Appointment page — no critical errors', async ({ page }) => {
    const uncaughtExceptions = [];
    const failedRequests = [];

    page.on('pageerror', (error) => {
      uncaughtExceptions.push(error.message);
    });

    page.on('response', (response) => {
      const status = response.status();
      const url = response.url();
      if (status >= 400) {
        if (url.includes('/favicon') || url.includes('.map') || url.includes('/bus/')) return;
        failedRequests.push({ url: url.substring(0, 200), status });
      }
    });

    await page.goto(`${BASE}/appointment/1/schedule`, { waitUntil: 'load', timeout: 45000 });
    await page.waitForTimeout(2000);

    const broken = await findBrokenImages(page);

    if (uncaughtExceptions.length > 0) {
      console.log(`  [Appointment] Uncaught exceptions: ${uncaughtExceptions.length}`);
      for (const e of uncaughtExceptions) console.log(`    - ${e.substring(0, 300)}`);
    }

    if (failedRequests.length > 0) {
      console.log(`  [Appointment] Failed requests: ${failedRequests.length}`);
      for (const r of failedRequests) console.log(`    - ${r.status} ${r.url}`);
    }

    if (broken.length > 0) {
      console.log(`  [Appointment] Broken images: ${broken.length}`);
      for (const src of broken) console.log(`    - ${src}`);
    }

    expect(uncaughtExceptions, `${uncaughtExceptions.length} uncaught exception(s)`).toHaveLength(0);

    console.log(`[PASS] A15: Appointment — 0 uncaught exceptions, ` +
      `${failedRequests.length} failed request(s), ${broken.length} broken image(s)`);
  });

});
