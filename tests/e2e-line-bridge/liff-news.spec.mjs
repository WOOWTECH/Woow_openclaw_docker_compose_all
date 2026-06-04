// tests/e2e-line-bridge/liff-news.spec.mjs
// 最新消息頁面 — 列表渲染、空狀態、詳情頁、導覽
import { test, expect } from '@playwright/test';

const BASE = '/liff/news';

test.describe('LIFF News Page — /liff/news', () => {

  test('loads with 200 and correct page title', async ({ page }) => {
    const resp = await page.goto(BASE);
    expect(resp.status()).toBe(200);
    const title = page.locator('.liff-page-title');
    await expect(title).toHaveText('最新消息');
  });

  test('back button links to /liff/member', async ({ page }) => {
    await page.goto(BASE);
    const backBtn = page.locator('.liff-back-btn');
    await expect(backBtn).toHaveAttribute('href', '/liff/member');
  });

  test('shows empty state or article cards', async ({ page }) => {
    await page.goto(BASE);
    // Either shows empty state OR news cards — both are valid
    const empty = page.locator('.liff-news-empty');
    const cards = page.locator('.liff-news-card');
    const emptyCount = await empty.count();
    const cardCount = await cards.count();
    // At least one of these should be present
    expect(emptyCount + cardCount).toBeGreaterThan(0);
  });

  test('empty state shows correct message and icon', async ({ page }) => {
    await page.goto(BASE);
    const empty = page.locator('.liff-news-empty');
    if (await empty.isVisible()) {
      await expect(empty).toContainText('目前沒有最新消息');
      await expect(empty).toContainText('稍後再來看看吧');
      // SVG bell icon
      const svg = empty.locator('svg');
      await expect(svg).toBeVisible();
    }
  });

  test('article cards have title and date', async ({ page }) => {
    await page.goto(BASE);
    const cards = page.locator('.liff-news-card');
    if (await cards.count() > 0) {
      const firstCard = cards.first();
      await expect(firstCard.locator('.liff-news-card-title')).toBeVisible();
      await expect(firstCard.locator('.liff-news-card-date')).toBeVisible();
      // Card should link to detail page with article_id
      const href = await firstCard.getAttribute('href');
      expect(href).toContain('article_id=');
    }
  });

  test('article detail page loads when article_id provided', async ({ page }) => {
    // First get an article ID from the list
    await page.goto(BASE);
    const firstCard = page.locator('.liff-news-card').first();
    if (await firstCard.count() > 0) {
      const href = await firstCard.getAttribute('href');
      const resp = await page.goto(href);
      expect(resp.status()).toBe(200);
      // Detail page should have title and back button to /liff/news
      const backBtn = page.locator('.liff-back-btn');
      await expect(backBtn).toHaveAttribute('href', '/liff/news');
      const detailTitle = page.locator('.liff-news-detail-title');
      await expect(detailTitle).toBeVisible();
    }
  });

});
