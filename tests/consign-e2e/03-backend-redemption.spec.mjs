// 03 — Backend redemption: wizard and direct form
import { test, expect } from '@playwright/test';
import { loginAsAdmin, searchRead, read, rpcCall, BASE } from './helpers/odoo-rpc.mjs';
import {
  createPartner, createProducts, createConsignProgram,
  createAndConfirmSO, findConsignCard, createAndConfirmRedemption, cleanup,
} from './helpers/test-data-factory.mjs';

test.describe('Backend redemption', () => {
  let page;
  const toClean = [];
  let partner, products, program, cardId, consignLines;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'redeem');
    products = await createProducts(page, 2, '-redeem');
    program = await createConsignProgram(page, [products.triggerId], '-redeem');

    const so = await createAndConfirmSO(page, partner.id, [
      { product_id: products.triggerId, product_uom_qty: 1 },
      { product_id: products.itemIds[0], product_uom_qty: 5 },
      { product_id: products.itemIds[1], product_uom_qty: 3 },
    ]);
    toClean.push({ model: 'sale.order', id: so.id });

    const card = await findConsignCard(page, program.id, partner.id);
    cardId = card.id;

    consignLines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]],
      ['id', 'product_id', 'qty_deposited', 'qty_remaining', 'unit_price'],
    );

    toClean.push(
      { model: 'loyalty.program', id: program.id },
      { model: 'product.product', id: products.allIds },
      { model: 'res.partner', id: partner.id },
    );
  });

  test.afterAll(async () => {
    // Clean redemptions and cards
    const reds = await searchRead(page, 'loyalty.consign.redemption',
      [['card_id', '=', cardId]], ['id']);
    if (reds.length) toClean.unshift({ model: 'loyalty.consign.redemption', id: reds.map(r => r.id) });
    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]], ['id']);
    if (lines.length) toClean.unshift({ model: 'loyalty.consign.line', id: lines.map(l => l.id) });
    toClean.unshift({ model: 'loyalty.card', id: [cardId] });
    await cleanup(page, toClean);
    await page.close();
  });

  test('create and confirm redemption via RPC', async () => {
    const lineA = consignLines[0];
    const red = await createAndConfirmRedemption(page, cardId, [
      { consign_line_id: lineA.id, qty_redeemed: 2 },
    ]);
    expect(red.id).toBeGreaterThan(0);

    const [rec] = await read(page, 'loyalty.consign.redemption', [red.id], ['state']);
    expect(rec.state).toBe('done');
    console.log(`[OK] Redemption ${red.id} confirmed`);
  });

  test('redemption updates consign line quantities', async () => {
    const lineA = consignLines[0];
    const [updated] = await read(page, 'loyalty.consign.line', [lineA.id],
      ['qty_redeemed', 'qty_remaining']);
    expect(updated.qty_redeemed).toBe(2);
    expect(updated.qty_remaining).toBe(lineA.qty_deposited - 2);
    console.log(`[OK] Line qty_redeemed=${updated.qty_redeemed}, qty_remaining=${updated.qty_remaining}`);
  });

  test('card totals update after redemption', async () => {
    const card = await findConsignCard(page, program.id, partner.id);
    // Was 8 (5+3), redeemed 2 → now 6
    expect(card.consign_total_remaining_qty).toBe(6);
    console.log(`[OK] Card remaining qty=${card.consign_total_remaining_qty}`);
  });

  test('over-redemption is rejected', async () => {
    const lineB = consignLines[1]; // has qty_deposited=3, qty_remaining=3
    let err;
    try {
      await createAndConfirmRedemption(page, cardId, [
        { consign_line_id: lineB.id, qty_redeemed: 999 },
      ]);
    } catch (e) {
      err = e;
    }
    expect(err).toBeDefined();
    expect(err.message || err.rpcError?.data?.message || '').toMatch(/超過|exceed|Validation/i);
    console.log('[OK] Over-redemption rejected');
  });

  test('full redemption sets line state to depleted', async () => {
    const lineB = consignLines[1];
    const [before] = await read(page, 'loyalty.consign.line', [lineB.id], ['qty_remaining']);

    await createAndConfirmRedemption(page, cardId, [
      { consign_line_id: lineB.id, qty_redeemed: before.qty_remaining },
    ]);

    const [after] = await read(page, 'loyalty.consign.line', [lineB.id], ['state', 'qty_remaining']);
    expect(after.qty_remaining).toBe(0);
    expect(after.state).toBe('depleted');
    console.log('[OK] Line depleted after full redemption');
  });

  test('card form shows redemption wizard button (UI)', async () => {
    // Read card code for search
    const [c] = await read(page, 'loyalty.card', [cardId], ['code']);
    await page.goto(`${BASE}/odoo/action-woow_loyalty_consign.loyalty_card_consign_action`);
    await page.waitForSelector('.o_list_view', { timeout: 30000 });

    // Search by card code to find quickly
    const searchInput = page.locator('.o_searchview_input');
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.fill(c.code);
      await searchInput.press('Enter');
      await page.waitForTimeout(2000);
    }

    const row = page.locator('.o_data_row').first();
    await row.click();
    await page.waitForSelector('.o_form_view', { timeout: 15000 });

    // Look for the 核銷 button
    const redeemBtn = page.locator('button:has-text("核銷")');
    await expect(redeemBtn).toBeVisible({ timeout: 5000 });

    // Click it to open wizard
    await redeemBtn.click();
    await page.waitForTimeout(2000);

    // Should see a dialog
    const dialog = page.locator('.o_dialog, [role="dialog"]');
    const dialogVisible = await dialog.isVisible().catch(() => false);
    console.log(`[${dialogVisible ? 'OK' : 'INFO'}] Wizard dialog visible: ${dialogVisible}`);

    await page.screenshot({ path: '/tmp/consign-wizard.png', fullPage: true });

    // Close without submitting
    const cancelBtn = page.locator('.o_dialog button:has-text("取消"), .o_dialog button:has-text("Cancel"), .o_dialog .btn-close');
    if (await cancelBtn.first().isVisible().catch(() => false)) {
      await cancelBtn.first().click();
    }
  });
});
