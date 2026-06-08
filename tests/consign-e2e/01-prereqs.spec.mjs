// 01 — Health checks: modules installed, action URLs load
import { test, expect } from '@playwright/test';
import { loginAsAdmin, searchRead, BASE } from './helpers/odoo-rpc.mjs';

test.describe('Consign module prerequisites', () => {
  test.beforeEach(async ({ page }) => { await loginAsAdmin(page); });

  test('admin login reaches backend', async ({ page }) => {
    expect(page.url()).toContain('/odoo');
  });

  test('consign program action URL loads', async ({ page }) => {
    await page.goto(`${BASE}/odoo/action-woow_loyalty_consign.loyalty_program_consign_action`);
    const view = page.locator('.o_list_view, .o_nocontent_help');
    await expect(view).toBeVisible({ timeout: 30000 });
  });

  test('consign card action URL loads', async ({ page }) => {
    await page.goto(`${BASE}/odoo/action-woow_loyalty_consign.loyalty_card_consign_action`);
    const view = page.locator('.o_list_view, .o_nocontent_help');
    await expect(view).toBeVisible({ timeout: 30000 });
  });

  test('consign models are queryable via RPC', async ({ page }) => {
    for (const model of [
      'loyalty.consign.line',
      'loyalty.consign.redemption',
      'loyalty.consign.redemption.line',
    ]) {
      const result = await searchRead(page, model, [], ['id'], 1);
      expect(Array.isArray(result)).toBe(true);
    }
  });

  test('loyalty.program has consign type', async ({ page }) => {
    // Just verify no error when searching for consign programs
    const result = await searchRead(page, 'loyalty.program', [['program_type', '=', 'consign']], ['id', 'name'], 5);
    expect(Array.isArray(result)).toBe(true);
  });
});
