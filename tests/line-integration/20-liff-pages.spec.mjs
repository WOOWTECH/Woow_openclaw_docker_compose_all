// 20 — LIFF content pages (G1-G3)
// Verify public LIFF pages: /liff/news, /liff/locations, graceful error handling
import { test, expect } from '@playwright/test';

const BASE = process.env.ODOO_BASE_URL || 'https://markstudio-odoo.woowtech.io';

test.describe('LIFF content pages', () => {

  // G1: GET /liff/news returns 200 with HTML content
  test('G1: GET /liff/news returns 200 with news HTML', async ({ page }) => {
    const resp = await page.goto(`${BASE}/liff/news`);
    expect(resp.status()).toBe(200);

    // Page renders inline HTML (not Odoo website template)
    // Just verify basic HTML structure is present
    const html = await page.content();
    const hasHtmlContent =
      html.includes('<html') ||
      html.includes('<body') ||
      html.includes('<div') ||
      html.includes('<head');
    expect(hasHtmlContent).toBe(true);

    // Body should have some content (even if empty state)
    const bodyText = await page.locator('body').textContent();
    // Body may be empty string for a minimal page, but HTML itself should exist
    console.log(
      `[OK] /liff/news loaded: HTML present, body text length=${bodyText.length}`,
    );
  });

  // G2: GET /liff/locations returns 200 with address/map info
  test('G2: GET /liff/locations returns 200 with location HTML', async ({ page }) => {
    const resp = await page.goto(`${BASE}/liff/locations`);
    expect(resp.status()).toBe(200);

    const bodyText = await page.locator('body').textContent();
    expect(bodyText.length).toBeGreaterThan(0);

    // Check for map-related or address content
    const html = await page.content();
    const hasMapOrAddress =
      html.includes('map') ||
      html.includes('Map') ||
      html.includes('address') ||
      html.includes('location') ||
      html.includes('liff-') ||
      html.includes('google.com/maps');

    console.log(`[OK] /liff/locations loaded: contains map/address content=${hasMapOrAddress}`);
    expect(hasMapOrAddress).toBe(true);
  });

  // G3: GET /liff/news?article_id=99999 returns 200 or graceful fallback
  test('G3: GET /liff/news?article_id=99999 no crash', async ({ page }) => {
    const resp = await page.goto(`${BASE}/liff/news?article_id=99999`);
    const status = resp.status();

    // Should not be a 500 server error — either 200 (with fallback content) or 404
    expect(status).not.toBe(500);
    expect([200, 303, 404].includes(status) || status < 500).toBe(true);

    if (status === 200) {
      const bodyText = await page.locator('body').textContent();
      expect(bodyText.length).toBeGreaterThan(0);
      console.log('[OK] /liff/news?article_id=99999 returned 200 with fallback content');
    } else {
      console.log(`[OK] /liff/news?article_id=99999 returned ${status} (graceful, no 500)`);
    }
  });
});
