// tests/e2e-line-bridge/liff-member.spec.mjs
// 會員中心頁面 — UI 結構、品牌元素、錯誤狀態、LIFF SDK 載入
import { test, expect } from '@playwright/test';

const BASE = '/liff/member';

test.describe('LIFF Member Page — /liff/member', () => {

  test('loads with 200 and correct title containing shop name', async ({ page }) => {
    const resp = await page.goto(BASE);
    expect(resp.status()).toBe(200);
    await expect(page).toHaveTitle(/Mark Studio|馬克健身/);
  });

  test('header gradient renders with brand colors', async ({ page }) => {
    await page.goto(BASE);
    const hdr = page.locator('.hdr');
    await expect(hdr).toBeVisible();
    const bg = await hdr.evaluate(el => getComputedStyle(el).backgroundImage);
    // linear-gradient includes brand primary #B8956A
    expect(bg).toContain('rgb(184, 149, 106)');
  });

  test('renders 6 cards with correct labels', async ({ page }) => {
    await page.goto(BASE);
    const cards = page.locator('.card');
    await expect(cards).toHaveCount(6);

    const expectedLabels = ['立即預約', '我的預約', '個人資料', '最新消息', '店家位置', '聯絡我們'];
    for (let i = 0; i < 6; i++) {
      const label = cards.nth(i).locator('.card-label');
      await expect(label).toHaveText(expectedLabels[i]);
    }
  });

  test('each card has an SVG icon', async ({ page }) => {
    await page.goto(BASE);
    const icons = page.locator('.card .card-icon svg');
    await expect(icons).toHaveCount(6);
  });

  test('avatar SVG placeholder renders when no LIFF profile', async ({ page }) => {
    await page.goto(BASE);
    const avatar = page.locator('#liff-user-avatar');
    await expect(avatar).toBeVisible();
    // Should contain SVG (no img since we're not in LINE)
    const svg = avatar.locator('svg');
    await expect(svg).toBeVisible();
  });

  test('greeting text shows default welcome', async ({ page }) => {
    await page.goto(BASE);
    const greeting = page.locator('#liff-user-greeting');
    await expect(greeting).toHaveText('歡迎光臨');
  });

  test('LIFF SDK script tag is loaded', async ({ page }) => {
    await page.goto(BASE);
    const sdk = page.locator('script[src*="line-scdn.net/liff"]');
    // Page may include SDK via both inline and asset bundle
    const count = await sdk.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('error state: ?error=no_token shows error message', async ({ page }) => {
    await page.goto(`${BASE}?error=no_token`);
    // Error div should be visible with the error message
    const errDiv = page.locator('.err, .liff-member-error');
    await expect(errDiv).toBeVisible();
    await expect(errDiv).toContainText('登入失敗');
  });

});
