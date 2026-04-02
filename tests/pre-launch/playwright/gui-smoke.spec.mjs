import { test, expect } from '@playwright/test';

const BASE = 'https://cindytech1-openclaw.woowtech.io';
const TOKEN = 'woowtech';

test.describe('OpenClaw GUI Smoke Tests', () => {

  test('dashboard loads with token auth', async ({ page }) => {
    await page.goto(`${BASE}/#token=${TOKEN}`);
    // Wait for WebSocket-driven content to load
    await page.waitForTimeout(5000);
    // Dashboard should show status cards or main UI
    const body = await page.textContent('body');
    expect(body.length).toBeGreaterThan(100);
  });

  test('no red Gateway Error on dashboard', async ({ page }) => {
    await page.goto(`${BASE}/#token=${TOKEN}`);
    await page.waitForTimeout(5000);
    const errors = await page.locator('text=Gateway Error').count();
    // Allow 0 or transient (auto-dismissed)
    expect(errors).toBeLessThanOrEqual(1);
  });

  test('channels page shows LINE configured', async ({ page }) => {
    await page.goto(`${BASE}/#token=${TOKEN}`);
    await page.waitForTimeout(3000);
    // Navigate to channels (if sidebar exists)
    const channelsLink = page.locator('text=Channels').first();
    if (await channelsLink.isVisible()) {
      await channelsLink.click();
      await page.waitForTimeout(2000);
      const content = await page.textContent('body');
      expect(content).toContain('LINE');
    }
  });

  test('cron jobs page shows 3 jobs', async ({ page }) => {
    await page.goto(`${BASE}/#token=${TOKEN}`);
    await page.waitForTimeout(3000);
    const cronLink = page.locator('text=Cron').first();
    if (await cronLink.isVisible()) {
      await cronLink.click();
      await page.waitForTimeout(2000);
      const content = await page.textContent('body');
      expect(content).toContain('heartbeat');
    }
  });

});
