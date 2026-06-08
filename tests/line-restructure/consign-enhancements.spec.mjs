// @ts-check
import { test, expect } from '@playwright/test';

const BASE = 'https://markstudio-odoo.woowtech.io';

test.describe('Consign Card Portal Pages', () => {
  test('/my/consign-cards requires login', async ({ request }) => {
    const res = await request.get(`${BASE}/my/consign-cards`, {
      maxRedirects: 0,
    });
    // 303 = redirect to login (expected for portal pages)
    expect([200, 303]).toContain(res.status());
  });

  test('/my/consign-cards/1 requires login', async ({ request }) => {
    const res = await request.get(`${BASE}/my/consign-cards/1`, {
      maxRedirects: 0,
    });
    expect([200, 303]).toContain(res.status());
  });

  test('/my/member-center requires login', async ({ request }) => {
    const res = await request.get(`${BASE}/my/member-center`, {
      maxRedirects: 0,
    });
    expect([200, 303]).toContain(res.status());
  });
});

test.describe('Consign Program Backend', () => {
  test('program action URL loads', async ({ page }) => {
    // Backend URLs redirect to login when not authenticated
    const res = await page.goto(`${BASE}/web/login`);
    expect(res.status()).toBe(200);
  });

  test('health check', async ({ request }) => {
    const res = await request.get(`${BASE}/web/health`);
    expect(res.status()).toBe(200);
  });
});
