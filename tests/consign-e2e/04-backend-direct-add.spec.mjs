// 04 — Backend direct add: admin adds items to card
import { test, expect } from '@playwright/test';
import { loginAsAdmin, searchRead, read, write, BASE } from './helpers/odoo-rpc.mjs';
import {
  createPartner, createProducts, createConsignProgram,
  createCardDirect, addConsignLine, cleanup,
} from './helpers/test-data-factory.mjs';

test.describe('Backend direct add lines', () => {
  let page;
  const toClean = [];
  let partner, products, program, cardId;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'add');
    products = await createProducts(page, 2, '-add');
    program = await createConsignProgram(page, [products.triggerId], '-add');

    const card = await createCardDirect(page, program.id, partner.id);
    cardId = card.id;

    toClean.push(
      { model: 'loyalty.program', id: program.id },
      { model: 'product.product', id: products.allIds },
      { model: 'res.partner', id: partner.id },
    );
  });

  test.afterAll(async () => {
    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]], ['id']);
    if (lines.length) toClean.unshift({ model: 'loyalty.consign.line', id: lines.map(l => l.id) });
    toClean.unshift({ model: 'loyalty.card', id: [cardId] });
    await cleanup(page, toClean);
    await page.close();
  });

  test('consign_add_line creates new line', async () => {
    await addConsignLine(page, cardId, products.itemIds[0], 5, 200);

    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]],
      ['product_id', 'qty_deposited', 'unit_price', 'state'],
    );
    expect(lines.length).toBe(1);
    expect(lines[0].qty_deposited).toBe(5);
    expect(lines[0].unit_price).toBe(200);
    expect(lines[0].state).toBe('active');
    console.log('[OK] Line created: qty=5, price=200');
  });

  test('same product same price accumulates qty', async () => {
    await addConsignLine(page, cardId, products.itemIds[0], 3, 200);

    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]],
      ['qty_deposited'],
    );
    expect(lines.length).toBe(1); // Still just 1 line
    expect(lines[0].qty_deposited).toBe(8); // 5 + 3
    console.log('[OK] Accumulated: qty=8, still 1 line');
  });

  test('different price creates new line', async () => {
    await addConsignLine(page, cardId, products.itemIds[0], 2, 300);

    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]],
      ['qty_deposited', 'unit_price'],
    );
    expect(lines.length).toBe(2);
    const p200 = lines.find(l => l.unit_price === 200);
    const p300 = lines.find(l => l.unit_price === 300);
    expect(p200.qty_deposited).toBe(8);
    expect(p300.qty_deposited).toBe(2);
    console.log('[OK] New line for different price');
  });

  test('different product creates new line', async () => {
    await addConsignLine(page, cardId, products.itemIds[1], 1, 400);

    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]],
      ['product_id', 'qty_deposited'],
    );
    expect(lines.length).toBe(3);
    console.log('[OK] 3 lines total for different product');
  });

  test('protected fields cannot be modified via write', async () => {
    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]], ['id'], 1);
    const lineId = lines[0].id;

    let err;
    try {
      await write(page, 'loyalty.consign.line', [lineId], { qty_deposited: 999 });
    } catch (e) {
      err = e;
    }
    expect(err).toBeDefined();
    console.log('[OK] Protected field write rejected');
  });

  test('card form shows consign lines tab (UI)', async () => {
    await page.goto(`${BASE}/odoo/action-woow_loyalty_consign.loyalty_card_consign_action`);
    await page.waitForSelector('.o_list_view', { timeout: 30000 });

    const row = page.locator(`.o_data_row:has-text("${partner.name}")`).first();
    await row.click();
    await page.waitForSelector('.o_form_view', { timeout: 15000 });

    // Click 寄品明細 tab
    const tab = page.locator('.nav-link:has-text("寄品明細")');
    if (await tab.isVisible().catch(() => false)) {
      await tab.click();
      await page.waitForTimeout(1000);
    }

    // Verify lines are shown
    const listRows = page.locator('.o_field_widget[name="consign_line_ids"] .o_data_row');
    const count = await listRows.count();
    expect(count).toBeGreaterThanOrEqual(3);
    console.log(`[OK] Card form shows ${count} consign lines`);
    await page.screenshot({ path: '/tmp/consign-card-form.png', fullPage: true });
  });
});
