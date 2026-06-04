// tests/e2e-line-bridge/liff-member.spec.mjs
// 會員中心頁面 — Retrodandy 黑白風格、UI 結構、錯誤狀態、LIFF SDK 載入
import { test, expect } from '@playwright/test';

const BASE = '/liff/member';

test.describe('LIFF Member Page — /liff/member', () => {

  test('loads with 200 and correct title containing shop name', async ({ page }) => {
    const resp = await page.goto(BASE);
    expect(resp.status()).toBe(200);
    await expect(page).toHaveTitle(/Mark Studio|馬克健身/);
  });

  test('dark theme: body background is black (#000)', async ({ page }) => {
    await page.goto(BASE);
    const bg = await page.locator('body').evaluate(el => getComputedStyle(el).backgroundColor);
    // rgb(0, 0, 0) = #000
    expect(bg).toBe('rgb(0, 0, 0)');
  });

  test('header uses serif font family', async ({ page }) => {
    await page.goto(BASE);
    const hdr = page.locator('.hdr h1');
    await expect(hdr).toBeVisible();
    const font = await hdr.evaluate(el => getComputedStyle(el).fontFamily);
    expect(font).toContain('Noto Serif TC');
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

  test('cards have dark background (#1a1a1a)', async ({ page }) => {
    await page.goto(BASE);
    const card = page.locator('.card').first();
    const bg = await card.evaluate(el => getComputedStyle(el).backgroundColor);
    expect(bg).toBe('rgb(26, 26, 26)');
  });

  test('card icons use white stroke', async ({ page }) => {
    await page.goto(BASE);
    const icons = page.locator('.card .card-icon svg');
    await expect(icons).toHaveCount(6);
    const stroke = await icons.first().getAttribute('stroke');
    expect(stroke).toBe('#fff');
  });

  test('news card links to /#news (website news section)', async ({ page }) => {
    await page.goto(BASE);
    // 4th card is 最新消息
    const newsCard = page.locator('.card').nth(3);
    const href = await newsCard.getAttribute('href');
    expect(href).toBe('/#news');
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
    const count = await sdk.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('error state: ?error=no_token shows error message', async ({ page }) => {
    await page.goto(`${BASE}?error=no_token`);
    const errDiv = page.locator('.liff-member-error');
    await expect(errDiv).toBeVisible();
    await expect(errDiv).toContainText('登入失敗');
  });

});
