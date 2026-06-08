// 02 — Card creation via Sale Order confirmation
import { test, expect } from '@playwright/test';
import { loginAsAdmin, searchRead, read, BASE } from './helpers/odoo-rpc.mjs';
import {
  createPartner, createProducts, createConsignProgram,
  createAndConfirmSO, findConsignCard, cleanup,
} from './helpers/test-data-factory.mjs';

test.describe('Consign card creation via sale order', () => {
  let page;
  const toClean = [];
  let partner, products, program;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'sale');
    toClean.push({ model: 'res.partner', id: partner.id });

    products = await createProducts(page, 2, '-sale');
    toClean.push({ model: 'product.product', id: products.allIds });

    program = await createConsignProgram(page, [products.triggerId], '-sale');
    toClean.push({ model: 'loyalty.program', id: program.id });
  });

  test.afterAll(async () => {
    // Clean cards first (they depend on program)
    const cards = await searchRead(page, 'loyalty.card', [['program_id', '=', program.id]], ['id']);
    if (cards.length) {
      // Clean redemptions
      const reds = await searchRead(page, 'loyalty.consign.redemption',
        [['card_id', 'in', cards.map(c => c.id)]], ['id']);
      if (reds.length) toClean.unshift({ model: 'loyalty.consign.redemption', id: reds.map(r => r.id) });
      // Clean lines
      const lines = await searchRead(page, 'loyalty.consign.line',
        [['card_id', 'in', cards.map(c => c.id)]], ['id']);
      if (lines.length) toClean.unshift({ model: 'loyalty.consign.line', id: lines.map(l => l.id) });
      toClean.unshift({ model: 'loyalty.card', id: cards.map(c => c.id) });
    }
    await cleanup(page, toClean);
    await page.close();
  });

  let soId, cardId;

  test('confirm SO creates consign card', async () => {
    // Debug: verify program setup
    const [prog] = await read(page, 'loyalty.program', [program.id],
      ['trigger_product_ids', 'program_type', 'active']);
    console.log(`Program: type=${prog.program_type}, active=${prog.active}, triggers=${JSON.stringify(prog.trigger_product_ids)}`);
    console.log(`Products: trigger=${products.triggerId}, items=${JSON.stringify(products.itemIds)}`);

    const so = await createAndConfirmSO(page, partner.id, [
      { product_id: products.triggerId, product_uom_qty: 1 },
      { product_id: products.itemIds[0], product_uom_qty: 3 },
      { product_id: products.itemIds[1], product_uom_qty: 2 },
    ]);
    soId = so.id;
    toClean.push({ model: 'sale.order', id: soId });

    // Debug: check SO state and lines
    const [soRec] = await read(page, 'sale.order', [soId], ['state']);
    console.log(`SO state after confirm: ${soRec.state}`);

    const card = await findConsignCard(page, program.id, partner.id);
    console.log(`Card found: ${JSON.stringify(card)}`);
    expect(card).not.toBeNull();
    cardId = card.id;
    console.log(`[OK] Card created: id=${cardId}, code=${card.code}`);
  });

  test('card has correct consign lines', async () => {
    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]],
      ['product_id', 'qty_deposited', 'qty_remaining', 'unit_price', 'state'],
    );
    // Should have 2 lines (item products only, not the trigger)
    expect(lines.length).toBe(2);

    const lineA = lines.find(l => l.qty_deposited === 3);
    const lineB = lines.find(l => l.qty_deposited === 2);
    expect(lineA).toBeTruthy();
    expect(lineB).toBeTruthy();
    expect(lineA.state).toBe('active');
    expect(lineB.state).toBe('active');
    expect(lineA.qty_remaining).toBe(3);
    expect(lineB.qty_remaining).toBe(2);
    console.log('[OK] 2 consign lines with correct qty');
  });

  test('trigger product line is marked is_consigned on SO', async () => {
    const soLines = await searchRead(page, 'sale.order.line',
      [['order_id', '=', soId]],
      ['product_id', 'is_consigned'],
    );
    const triggerLine = soLines.find(l => l.product_id[0] === products.triggerId);
    expect(triggerLine).toBeTruthy();
    expect(triggerLine.is_consigned).toBe(true);
    console.log('[OK] Trigger product is_consigned=true');
  });

  test('card computed totals are correct', async () => {
    const card = await findConsignCard(page, program.id, partner.id);
    expect(card.consign_total_remaining_qty).toBe(5); // 3 + 2
    expect(card.consign_active_lines).toBe(2);
    // Value depends on actual price (might differ from list_price after SO logic)
    expect(card.consign_total_remaining_value).toBeGreaterThan(0);
    console.log(`[OK] Totals: qty=${card.consign_total_remaining_qty}, value=${card.consign_total_remaining_value}, lines=${card.consign_active_lines}`);
  });

  test('second SO for same partner adds new line to existing card', async () => {
    // Use a different item product to avoid write protection on existing line
    const extraProd = await createProducts(page, 1, '-extra');
    toClean.push({ model: 'product.product', id: extraProd.allIds });

    const so2 = await createAndConfirmSO(page, partner.id, [
      { product_id: products.triggerId, product_uom_qty: 1 },
      { product_id: extraProd.itemIds[0], product_uom_qty: 1 },
    ]);
    toClean.push({ model: 'sale.order', id: so2.id });

    // Still only 1 card
    const cards = await searchRead(page, 'loyalty.card',
      [['program_id', '=', program.id], ['partner_id', '=', partner.id]],
      ['id'],
    );
    expect(cards.length).toBe(1);

    // Total qty increased (5 + 1 = 6), active lines increased (2 + 1 = 3)
    const card = await findConsignCard(page, program.id, partner.id);
    expect(card.consign_total_remaining_qty).toBe(6);
    expect(card.consign_active_lines).toBe(3);
    console.log('[OK] Second SO added new line to same card');
  });

  test('card visible in backend list view (UI)', async () => {
    // Read card code for reliable search
    const card = await findConsignCard(page, program.id, partner.id);
    const cardCode = card.code;

    await page.goto(`${BASE}/odoo/action-woow_loyalty_consign.loyalty_card_consign_action`);
    await page.waitForSelector('.o_list_view', { timeout: 30000 });

    // Search for the card code
    const searchInput = page.locator('.o_searchview_input');
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.fill(cardCode);
      await searchInput.press('Enter');
      await page.waitForTimeout(2000);
    }

    const row = page.locator('.o_data_row').first();
    await expect(row).toBeVisible({ timeout: 10000 });
    console.log('[OK] Card visible in backend list');
  });
});
