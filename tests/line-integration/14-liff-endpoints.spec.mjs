// tests/line-integration/14-liff-endpoints.spec.mjs
// A1-A8: LIFF HTTP endpoints return correct responses
// Public endpoints — no admin login required
import { test, expect } from '@playwright/test';

const BASE = process.env.ODOO_BASE_URL || 'https://markstudio-odoo.woowtech.io';

test.describe('A: LIFF Endpoints — /liff/* and /api/line/*', () => {

  // A1: GET /liff/redirect returns 200 with LIFF SDK script
  test('A1: GET /liff/redirect returns 200 with LIFF SDK script tag', async ({ page }) => {
    const resp = await page.goto(`${BASE}/liff/redirect`, { waitUntil: 'commit' });
    expect(resp.status()).toBe(200);
    const html = await page.content();
    expect(html).toContain('line-scdn.net/liff');
    console.log('[OK] A1: /liff/redirect returns 200 with LIFF SDK script');
  });

  // A2: GET /liff/redirect/book returns 200 with LIFF bridge page
  test('A2: GET /liff/redirect/book returns 200 with LIFF bridge page', async ({ page }) => {
    const resp = await page.goto(`${BASE}/liff/redirect/book`, { waitUntil: 'commit' });
    expect(resp.status()).toBe(200);
    const html = await page.content();
    // Bridge page should contain LIFF SDK script or a form/hidden input for the target
    const hasLiffSdk = html.includes('line-scdn.net/liff') || html.includes('liff');
    const hasTarget = html.includes('book') || html.includes('target') || html.includes('redirect');
    expect(hasLiffSdk || hasTarget).toBe(true);
    console.log('[OK] A2: /liff/redirect/book returns 200 with LIFF bridge page');
  });

  // A3: GET /liff/redirect/booking/1 returns 200 with LIFF bridge page
  test('A3: GET /liff/redirect/booking/1 returns 200 with LIFF bridge page', async ({ page }) => {
    const resp = await page.goto(`${BASE}/liff/redirect/booking/1`, { waitUntil: 'commit' });
    expect(resp.status()).toBe(200);
    const html = await page.content();
    // Bridge page should contain LIFF SDK script or form elements for routing
    const hasLiffSdk = html.includes('line-scdn.net/liff') || html.includes('liff');
    const hasFormOrScript = html.includes('<form') || html.includes('<script') || html.includes('input');
    expect(hasLiffSdk || hasFormOrScript).toBe(true);
    console.log('[OK] A3: /liff/redirect/booking/1 returns 200 with LIFF bridge page');
  });

  // A4: POST /api/line/bind without token returns error (not 500)
  test('A4: POST /api/line/bind without token returns error (not 500)', async ({ page }) => {
    await page.goto(`${BASE}/web`);  // need a page context for evaluate
    const result = await page.evaluate(async (base) => {
      const resp = await fetch(`${base}/api/line/bind`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      return { status: resp.status, body: await resp.text() };
    }, BASE);

    expect(result.status).not.toBe(500);
    expect([400, 401, 403]).toContain(result.status);
    const body = JSON.parse(result.body);
    expect(body).toHaveProperty('error');
    console.log(`[OK] A4: /api/line/bind without token returns ${result.status} with error`);
  });

  // A5: POST /api/line/me without token returns error
  test('A5: POST /api/line/me without token returns error (not 500)', async ({ page }) => {
    await page.goto(`${BASE}/web`);
    const result = await page.evaluate(async (base) => {
      const resp = await fetch(`${base}/api/line/me`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      return { status: resp.status, body: await resp.text() };
    }, BASE);

    expect(result.status).not.toBe(500);
    expect([400, 401, 403]).toContain(result.status);
    const body = JSON.parse(result.body);
    expect(body).toHaveProperty('error');
    console.log(`[OK] A5: /api/line/me without token returns ${result.status} with error`);
  });

  // A6: POST /api/line/notification/toggle without token returns error
  test('A6: POST /api/line/notification/toggle without token returns error', async ({ page }) => {
    await page.goto(`${BASE}/web`);
    const result = await page.evaluate(async (base) => {
      const resp = await fetch(`${base}/api/line/notification/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: true }),
      });
      return { status: resp.status, body: await resp.text() };
    }, BASE);

    expect(result.status).not.toBe(500);
    expect([400, 401, 403]).toContain(result.status);
    const body = JSON.parse(result.body);
    expect(body).toHaveProperty('error');
    console.log(`[OK] A6: /api/line/notification/toggle without token returns ${result.status}`);
  });

  // A7: GET /liff/debug returns 200
  test('A7: GET /liff/debug returns 200', async ({ page }) => {
    const resp = await page.goto(`${BASE}/liff/debug`);
    expect(resp.status()).toBe(200);
    const html = await page.content();
    // Debug page should contain LIFF SDK for diagnostics
    expect(html).toContain('liff');
    console.log('[OK] A7: /liff/debug returns 200');
  });

  // A8: GET /liff/clear-session returns redirect (302)
  test('A8: GET /liff/clear-session redirects (302)', async ({ request }) => {
    const resp = await request.get(`${BASE}/liff/clear-session`, {
      maxRedirects: 0,
    });
    // clear-session should redirect to /web/login by default
    const status = resp.status();
    expect([301, 302, 303]).toContain(status);
    const location = resp.headers()['location'] || '';
    expect(location).toContain('/web/login');
    console.log(`[OK] A8: /liff/clear-session returns ${status} redirect to ${location}`);
  });

});
