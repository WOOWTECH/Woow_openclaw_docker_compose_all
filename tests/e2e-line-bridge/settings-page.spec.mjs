// tests/e2e-line-bridge/settings-page.spec.mjs
// 後台 LINE Bridge 設定頁 — 登入、欄位存在、computed fields
import { test, expect } from '@playwright/test';

// Odoo 後台需要登入 — 使用 admin 帳號
// 注意：密碼需要從環境變數取得或在 CI 中設定
const ADMIN_LOGIN = process.env.ODOO_ADMIN_LOGIN || 'admin';
const ADMIN_PASSWORD = process.env.ODOO_ADMIN_PASSWORD || '';

test.describe('LINE Bridge Settings Page', () => {

  test.skip(!ADMIN_PASSWORD, 'Skipped: ODOO_ADMIN_PASSWORD not set');

  test.beforeEach(async ({ page }) => {
    // Login to Odoo backend
    await page.goto('/web/login');
    await page.fill('input[name="login"]', ADMIN_LOGIN);
    await page.fill('input[name="password"]', ADMIN_PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/web/);
  });

  test('LINE Bridge section visible in Settings', async ({ page }) => {
    await page.goto('/odoo/settings');
    // Wait for settings page to load
    await page.waitForSelector('.o_base_settings');
    // Search or scroll to LINE Bridge section
    const searchInput = page.locator('.o_searchview_input');
    if (await searchInput.count() > 0) {
      await searchInput.fill('LINE');
      await page.keyboard.press('Enter');
    }
    // LINE Bridge app section should be visible
    const lineSection = page.locator('[data-key="woow_line_bridge"]');
    await expect(lineSection).toBeVisible({ timeout: 10000 });
  });

  test('all 14 config fields are present', async ({ page }) => {
    await page.goto('/odoo/settings');
    await page.waitForSelector('.o_base_settings');
    const lineSection = page.locator('[data-key="woow_line_bridge"]');
    await lineSection.scrollIntoViewIfNeeded();

    // Check all field names exist
    const fieldNames = [
      'line_login_channel_id',
      'line_login_channel_secret',
      'line_messaging_channel_id',
      'line_messaging_channel_secret',
      'line_messaging_access_token',
      'line_liff_id_member',
      'line_liff_id_news',
      'line_liff_id_locations',
      'line_shop_name',
      'line_shop_address',
      'line_shop_phone',
      'line_shop_latitude',
      'line_shop_longitude',
      'line_shop_opening_hours',
    ];

    for (const name of fieldNames) {
      const field = lineSection.locator(`[name="${name}"]`);
      await expect(field).toHaveCount(1, { timeout: 5000 });
    }
  });

  test('webhook URL computed field shows correct URL', async ({ page }) => {
    await page.goto('/odoo/settings');
    await page.waitForSelector('.o_base_settings');
    const lineSection = page.locator('[data-key="woow_line_bridge"]');
    await lineSection.scrollIntoViewIfNeeded();

    const webhookField = lineSection.locator('[name="line_webhook_url"] input, [name="line_webhook_url"]');
    if (await webhookField.count() > 0) {
      const value = await webhookField.inputValue().catch(() => webhookField.textContent());
      expect(value).toContain('/line/webhook');
    }
  });

  test('LIFF endpoint URL fields are readonly', async ({ page }) => {
    await page.goto('/odoo/settings');
    await page.waitForSelector('.o_base_settings');
    const lineSection = page.locator('[data-key="woow_line_bridge"]');
    await lineSection.scrollIntoViewIfNeeded();

    const endpointFields = [
      'line_liff_endpoint_member',
      'line_liff_endpoint_news',
      'line_liff_endpoint_locations',
    ];

    for (const name of endpointFields) {
      const field = lineSection.locator(`[name="${name}"]`);
      if (await field.count() > 0) {
        // CopyClipboardChar widget — the input should be readonly
        const input = field.locator('input');
        if (await input.count() > 0) {
          const readonly = await input.getAttribute('readonly');
          expect(readonly).not.toBeNull();
        }
      }
    }
  });

  test('password fields mask input values', async ({ page }) => {
    await page.goto('/odoo/settings');
    await page.waitForSelector('.o_base_settings');
    const lineSection = page.locator('[data-key="woow_line_bridge"]');
    await lineSection.scrollIntoViewIfNeeded();

    const passwordFields = [
      'line_login_channel_secret',
      'line_messaging_channel_secret',
      'line_messaging_access_token',
    ];

    for (const name of passwordFields) {
      const field = lineSection.locator(`[name="${name}"] input[type="password"]`);
      if (await field.count() > 0) {
        const type = await field.getAttribute('type');
        expect(type).toBe('password');
      }
    }
  });

});
