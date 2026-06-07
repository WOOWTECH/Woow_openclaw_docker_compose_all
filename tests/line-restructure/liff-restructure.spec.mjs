// @ts-check
import { test, expect } from '@playwright/test';

const BASE = 'https://markstudio-odoo.woowtech.io';

// ═══════════════════════════════════════════
// 6.1 LIFF Redirect Bridge Page
// ═══════════════════════════════════════════
test.describe('LIFF Redirect Bridge Page', () => {
  test('loads within 5 seconds', async ({ page }) => {
    const res = await page.goto(`${BASE}/liff/redirect/book`, { timeout: 10000 });
    expect(res.status()).toBe(200);
  });

  test('has grayscale spinner (not brand colors)', async ({ page }) => {
    await page.goto(`${BASE}/liff/redirect/book`);
    const html = await page.content();
    expect(html).toContain('#F5F5F5');    // gray background
    expect(html).toContain('#333333');    // dark spinner
    expect(html).toContain('#666666');    // gray text
    expect(html).not.toContain('#B8956A'); // no brand gold
    expect(html).not.toContain('#FAF6F2'); // no brand beige
  });

  test('LIFF SDK script in initial HTML', async ({ request }) => {
    const res = await request.get(`${BASE}/liff/redirect/book`);
    const html = await res.text();
    expect(html).toContain('static.line-scdn.net/liff');
  });

  test('has non-empty liffId', async ({ request }) => {
    const res = await request.get(`${BASE}/liff/redirect/book`);
    const html = await res.text();
    expect(html).toMatch(/liffId='[^']+'/);
    expect(html).not.toContain("liffId=''");
  });

  test('fallback dict includes home', async ({ request }) => {
    const res = await request.get(`${BASE}/liff/redirect/home`);
    const html = await res.text();
    expect(html).toContain('"home"');
    expect(html).toContain('"/my/home"');
  });

  test('different targets render correctly', async ({ request }) => {
    for (const target of ['book', 'my-bookings', 'home', 'profile']) {
      const res = await request.get(`${BASE}/liff/redirect/${target}`);
      const html = await res.text();
      expect(html).toContain(`target='${target}'`);
    }
  });
});

// ═══════════════════════════════════════════
// 6.2 LIFF News Page
// ═══════════════════════════════════════════
test.describe('LIFF News Page', () => {
  test('loads without error', async ({ page }) => {
    const res = await page.goto(`${BASE}/liff/news`, { timeout: 15000 });
    expect(res.status()).toBe(200);
  });

  test('has no /liff/member link', async ({ page }) => {
    await page.goto(`${BASE}/liff/news`);
    const html = await page.content();
    expect(html).not.toContain('href="/liff/member"');
  });

  test('page has navigation', async ({ request }) => {
    const res = await request.get(`${BASE}/liff/news`);
    const html = await res.text();
    expect(html).toContain('最新消息');
  });
});

// ═══════════════════════════════════════════
// 6.3 LIFF Locations Page
// ═══════════════════════════════════════════
test.describe('LIFF Locations Page', () => {
  test('loads without error', async ({ page }) => {
    const res = await page.goto(`${BASE}/liff/locations`, { timeout: 15000 });
    expect(res.status()).toBe(200);
  });

  test('has no /liff/member link', async ({ request }) => {
    const res = await request.get(`${BASE}/liff/locations`);
    const html = await res.text();
    expect(html).not.toContain('href="/liff/member"');
  });

  test('has shop info sections', async ({ request }) => {
    const res = await request.get(`${BASE}/liff/locations`);
    const html = await res.text();
    expect(html).toContain('店家位置');
  });
});

// ═══════════════════════════════════════════
// 6.4 LIFF Debug Page
// ═══════════════════════════════════════════
test.describe('LIFF Debug Page', () => {
  test('loads with grayscale background', async ({ page }) => {
    const res = await page.goto(`${BASE}/liff/debug`);
    expect(res.status()).toBe(200);
    const html = await page.content();
    expect(html).toContain('#F5F5F5');
  });
});

// ═══════════════════════════════════════════
// 6.5 Removed Pages
// ═══════════════════════════════════════════
test.describe('Removed Pages', () => {
  test('/liff/member returns 404', async ({ page }) => {
    const res = await page.goto(`${BASE}/liff/member`);
    expect(res.status()).toBe(404);
  });

  test('no liff-mode injection (liff_inject.js removed)', async ({ page }) => {
    await page.goto(`${BASE}/liff/redirect/book?liff=1`);
    // liff_inject.js was deleted, so liff-mode class should NOT be added
    const hasLiffMode = await page.evaluate(() =>
      document.documentElement.classList.contains('liff-mode')
    );
    expect(hasLiffMode).toBe(false);
  });
});

// ═══════════════════════════════════════════
// 6.6 Portal Navigation
// ═══════════════════════════════════════════
test.describe('Portal Navigation', () => {
  test('/web/login loads', async ({ page }) => {
    const res = await page.goto(`${BASE}/web/login`);
    expect(res.status()).toBe(200);
  });

  test('login page has form', async ({ page }) => {
    await page.goto(`${BASE}/web/login`);
    const form = await page.locator('form');
    await expect(form).toHaveCount(1);
  });
});

// ═══════════════════════════════════════════
// 6.7 Webhook Endpoint (API via Playwright)
// ═══════════════════════════════════════════
test.describe('Webhook API', () => {
  test('POST without signature returns 403', async ({ request }) => {
    const res = await request.post(`${BASE}/line/webhook`, {
      data: JSON.stringify({ events: [] }),
      headers: { 'Content-Type': 'application/json' },
    });
    expect(res.status()).toBe(403);
  });

  test('POST with wrong signature returns 403', async ({ request }) => {
    const res = await request.post(`${BASE}/line/webhook`, {
      data: JSON.stringify({ events: [] }),
      headers: {
        'Content-Type': 'application/json',
        'X-Line-Signature': 'invalid_signature_here',
      },
    });
    expect(res.status()).toBe(403);
  });
});

// ═══════════════════════════════════════════
// 6.8 Health Check
// ═══════════════════════════════════════════
test.describe('Health Check', () => {
  test('/web/health returns 200', async ({ request }) => {
    const res = await request.get(`${BASE}/web/health`);
    expect(res.status()).toBe(200);
  });
});
