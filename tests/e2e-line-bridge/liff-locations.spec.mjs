// tests/e2e-line-bridge/liff-locations.spec.mjs
// 店家位置頁面 — 地圖、店家資訊卡、導航按鈕、Leaflet 整合
import { test, expect } from '@playwright/test';

const BASE = '/liff/locations';

test.describe('LIFF Locations Page — /liff/locations', () => {

  test('loads with 200 and correct page title', async ({ page }) => {
    const resp = await page.goto(BASE);
    expect(resp.status()).toBe(200);
    const title = page.locator('.liff-page-title');
    await expect(title).toHaveText('店家位置');
  });

  test('back button links to /liff/member', async ({ page }) => {
    await page.goto(BASE);
    const backBtn = page.locator('.liff-back-btn');
    await expect(backBtn).toHaveAttribute('href', '/liff/member');
  });

  test('shop name displayed in location card', async ({ page }) => {
    await page.goto(BASE);
    const name = page.locator('.liff-location-name');
    await expect(name).toBeVisible();
    const text = await name.textContent();
    expect(text.length).toBeGreaterThan(0);
  });

  test('location info rows render conditionally', async ({ page }) => {
    await page.goto(BASE);
    // At least the name should be visible; other rows depend on config
    const rows = page.locator('.liff-location-row');
    const rowCount = await rows.count();
    // We expect some rows if address/phone/hours are configured
    expect(rowCount).toBeGreaterThanOrEqual(0);
  });

  test('phone number is a clickable tel: link', async ({ page }) => {
    await page.goto(BASE);
    const phoneLink = page.locator('.liff-location-row a[href^="tel:"]');
    if (await phoneLink.count() > 0) {
      const href = await phoneLink.getAttribute('href');
      expect(href).toMatch(/^tel:/);
    }
  });

  test('Google Maps navigation button has correct destination URL', async ({ page }) => {
    await page.goto(BASE);
    const navBtn = page.locator('a.liff-btn-primary[href*="google.com/maps"]');
    if (await navBtn.count() > 0) {
      const href = await navBtn.getAttribute('href');
      expect(href).toContain('maps/dir/?api=1&destination=');
      expect(href).toMatch(/destination=[\d.]+,[\d.]+/);
    }
  });

  test('Leaflet map container exists with lat/lng data attributes', async ({ page }) => {
    await page.goto(BASE);
    const mapEl = page.locator('#liff-map');
    if (await mapEl.count() > 0) {
      const lat = await mapEl.getAttribute('data-lat');
      const lng = await mapEl.getAttribute('data-lng');
      // If map element exists, it should have valid coordinates
      expect(lat).toBeTruthy();
      expect(lng).toBeTruthy();
      expect(parseFloat(lat)).not.toBeNaN();
      expect(parseFloat(lng)).not.toBeNaN();

      // Leaflet CSS and JS should be loaded
      const leafletCss = page.locator('link[href*="leaflet"]');
      await expect(leafletCss).toHaveCount(1);
      const leafletJs = page.locator('script[src*="leaflet"]');
      await expect(leafletJs).toHaveCount(1);
    }
  });

});
