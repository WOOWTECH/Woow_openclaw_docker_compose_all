// tests/e2e-line-bridge/liff-redirect.spec.mjs
// LIFF 跳轉中間頁 — bridge 頁面渲染、fallback、token 驗證失敗
import { test, expect } from '@playwright/test';

test.describe('LIFF Redirect Bridge — /liff/redirect/*', () => {

  test('GET /liff/redirect/book returns bridge page with spinner', async ({ page }) => {
    const resp = await page.goto('/liff/redirect/book');
    expect(resp.status()).toBe(200);
    // Loading spinner visible
    const spinner = page.locator('.s');
    await expect(spinner).toBeVisible();
    // Status text
    const status = page.locator('#st');
    await expect(status).toContainText('正在登入中');
  });

  test('bridge page contains LIFF SDK script tag', async ({ page }) => {
    // Bridge page auto-navigates via JS fallback (not in LINE = no token)
    // Use waitUntil: 'commit' to capture the initial HTML before redirect
    await page.goto('/liff/redirect/book', { waitUntil: 'commit' });
    const html = await page.content();
    expect(html).toContain('line-scdn.net/liff');
  });

  test('bridge page inline script contains liff.init call', async ({ page }) => {
    await page.goto('/liff/redirect/my-bookings');
    const html = await page.content();
    expect(html).toContain('liff.init');
    expect(html).toContain('liffId');
  });

  test('bridge page has fallback URLs for all targets', async ({ page }) => {
    await page.goto('/liff/redirect/book');
    const html = await page.content();
    // Fallback URL mapping should be present
    expect(html).toContain('/appointment/1/schedule');
    expect(html).toContain('/my/ext-bookings');
    expect(html).toContain('/my/account');
  });

  test('POST without token redirects to /liff/member?error=no_token', async ({ request }) => {
    const resp = await request.post('/liff/redirect/book', {
      form: {},
      maxRedirects: 0,
    });
    // Should be a redirect (302)
    expect([302, 303]).toContain(resp.status());
    const location = resp.headers()['location'] || '';
    expect(location).toContain('/liff/member');
    expect(location).toContain('error=no_token');
  });

});
