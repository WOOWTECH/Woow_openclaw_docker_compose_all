// 08 — Multichannel card creation: scenarios A1, A3, A4, A5, A6
import { test, expect } from '@playwright/test';
import { loginAsAdmin, searchRead, read } from './helpers/odoo-rpc.mjs';
import {
  createPartner, createProducts, createConsignProgram,
  createAndConfirmSO, findConsignCard, cleanup,
} from './helpers/test-data-factory.mjs';

test.describe('A1: Backend SO with trigger + items creates card (varied combos)', () => {
  let page;
  const toClean = [];
  let partner, products, program;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'a1');
    products = await createProducts(page, 3, '-a1');
    program = await createConsignProgram(page, [products.triggerId], '-a1');

    toClean.push(
      { model: 'loyalty.program', id: program.id },
      { model: 'product.product', id: products.allIds },
      { model: 'res.partner', id: partner.id },
    );
  });

  test.afterAll(async () => {
    const cards = await searchRead(page, 'loyalty.card',
      [['program_id', '=', program.id]], ['id']);
    if (cards.length) {
      const cardIds = cards.map(c => c.id);
      const lines = await searchRead(page, 'loyalty.consign.line',
        [['card_id', 'in', cardIds]], ['id']);
      if (lines.length) toClean.unshift({ model: 'loyalty.consign.line', id: lines.map(l => l.id) });
      toClean.unshift({ model: 'loyalty.card', id: cardIds });
    }
    await cleanup(page, toClean);
    await page.close();
  });

  test('SO with trigger + 3 item products creates card with 3 lines', async () => {
    const so = await createAndConfirmSO(page, partner.id, [
      { product_id: products.triggerId, product_uom_qty: 1 },
      { product_id: products.itemIds[0], product_uom_qty: 4 },
      { product_id: products.itemIds[1], product_uom_qty: 2 },
      { product_id: products.itemIds[2], product_uom_qty: 1 },
    ]);
    toClean.push({ model: 'sale.order', id: so.id });

    const card = await findConsignCard(page, program.id, partner.id);
    expect(card).not.toBeNull();
    console.log(`[OK] Card created: id=${card.id}`);

    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', card.id]],
      ['product_id', 'qty_deposited', 'state'],
    );
    expect(lines.length).toBe(3);
    expect(lines.every(l => l.state === 'active')).toBe(true);

    const totalQty = lines.reduce((sum, l) => sum + l.qty_deposited, 0);
    expect(totalQty).toBe(7); // 4 + 2 + 1
    console.log(`[OK] 3 consign lines created, total qty=${totalQty}`);
  });
});

test.describe('A3: Program with multiple trigger products', () => {
  let page;
  const toClean = [];
  let partner1, partner2, products, extraTrigger, program;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner1 = await createPartner(page, 'a3-p1');
    partner2 = await createPartner(page, 'a3-p2');
    products = await createProducts(page, 1, '-a3');

    // Create a second trigger product
    const { create } = await import('./helpers/odoo-rpc.mjs');
    const triggerIds = await create(page, 'product.product', {
      name: `E2E-Trigger2-${Date.now()}-a3`,
      list_price: 800,
      type: 'service',
      sale_ok: true,
    });
    extraTrigger = triggerIds[0] || triggerIds;

    // Program has TWO trigger products
    program = await createConsignProgram(page, [products.triggerId, extraTrigger], '-a3');

    toClean.push(
      { model: 'loyalty.program', id: program.id },
      { model: 'product.product', id: [...products.allIds, extraTrigger] },
      { model: 'res.partner', id: partner1.id },
      { model: 'res.partner', id: partner2.id },
    );
  });

  test.afterAll(async () => {
    const cards = await searchRead(page, 'loyalty.card',
      [['program_id', '=', program.id]], ['id']);
    if (cards.length) {
      const cardIds = cards.map(c => c.id);
      const lines = await searchRead(page, 'loyalty.consign.line',
        [['card_id', 'in', cardIds]], ['id']);
      if (lines.length) toClean.unshift({ model: 'loyalty.consign.line', id: lines.map(l => l.id) });
      toClean.unshift({ model: 'loyalty.card', id: cardIds });
    }
    await cleanup(page, toClean);
    await page.close();
  });

  test('first trigger product creates card', async () => {
    const so = await createAndConfirmSO(page, partner1.id, [
      { product_id: products.triggerId, product_uom_qty: 1 },
      { product_id: products.itemIds[0], product_uom_qty: 2 },
    ]);
    toClean.push({ model: 'sale.order', id: so.id });

    const card = await findConsignCard(page, program.id, partner1.id);
    expect(card).not.toBeNull();
    console.log(`[OK] First trigger product created card: id=${card.id}`);
  });

  test('second trigger product also creates card', async () => {
    const so = await createAndConfirmSO(page, partner2.id, [
      { product_id: extraTrigger, product_uom_qty: 1 },
      { product_id: products.itemIds[0], product_uom_qty: 3 },
    ]);
    toClean.push({ model: 'sale.order', id: so.id });

    const card = await findConsignCard(page, program.id, partner2.id);
    expect(card).not.toBeNull();
    console.log(`[OK] Second trigger product created card: id=${card.id}`);
  });
});

test.describe('A4: SO with ONLY trigger product (no other items)', () => {
  let page;
  const toClean = [];
  let partner, products, program;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'a4');
    products = await createProducts(page, 1, '-a4');
    program = await createConsignProgram(page, [products.triggerId], '-a4');

    toClean.push(
      { model: 'loyalty.program', id: program.id },
      { model: 'product.product', id: products.allIds },
      { model: 'res.partner', id: partner.id },
    );
  });

  test.afterAll(async () => {
    const cards = await searchRead(page, 'loyalty.card',
      [['program_id', '=', program.id]], ['id']);
    if (cards.length) {
      const cardIds = cards.map(c => c.id);
      const lines = await searchRead(page, 'loyalty.consign.line',
        [['card_id', 'in', cardIds]], ['id']);
      if (lines.length) toClean.unshift({ model: 'loyalty.consign.line', id: lines.map(l => l.id) });
      toClean.unshift({ model: 'loyalty.card', id: cardIds });
    }
    await cleanup(page, toClean);
    await page.close();
  });

  test('SO with only trigger product creates card with 0 consign lines', async () => {
    const so = await createAndConfirmSO(page, partner.id, [
      { product_id: products.triggerId, product_uom_qty: 1 },
    ]);
    toClean.push({ model: 'sale.order', id: so.id });

    const card = await findConsignCard(page, program.id, partner.id);
    expect(card).not.toBeNull();
    console.log(`[OK] Card created with only trigger product: id=${card.id}`);

    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', card.id]], ['id']);
    expect(lines.length).toBe(0);
    console.log('[OK] Card has 0 consign lines as expected');

    // Computed fields should reflect empty state
    expect(card.consign_total_remaining_qty).toBe(0);
    expect(card.consign_active_lines).toBe(0);
    console.log('[OK] Computed totals are 0');
  });
});

test.describe('A5: SO without any trigger product — no card created', () => {
  let page;
  const toClean = [];
  let partner, products, program;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'a5');
    products = await createProducts(page, 2, '-a5');
    program = await createConsignProgram(page, [products.triggerId], '-a5');

    toClean.push(
      { model: 'loyalty.program', id: program.id },
      { model: 'product.product', id: products.allIds },
      { model: 'res.partner', id: partner.id },
    );
  });

  test.afterAll(async () => {
    const cards = await searchRead(page, 'loyalty.card',
      [['program_id', '=', program.id]], ['id']);
    if (cards.length) {
      const cardIds = cards.map(c => c.id);
      toClean.unshift({ model: 'loyalty.card', id: cardIds });
    }
    await cleanup(page, toClean);
    await page.close();
  });

  test('SO with only non-trigger items does NOT create card', async () => {
    // Create SO with only item products (no trigger)
    const so = await createAndConfirmSO(page, partner.id, [
      { product_id: products.itemIds[0], product_uom_qty: 3 },
      { product_id: products.itemIds[1], product_uom_qty: 2 },
    ]);
    toClean.push({ model: 'sale.order', id: so.id });

    const card = await findConsignCard(page, program.id, partner.id);
    expect(card).toBeNull();
    console.log('[OK] No card created when SO has no trigger product');
  });
});

test.describe('A6: Card computed fields after creation', () => {
  let page;
  const toClean = [];
  let partner, products, program;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'a6');
    products = await createProducts(page, 2, '-a6');
    program = await createConsignProgram(page, [products.triggerId], '-a6');

    toClean.push(
      { model: 'loyalty.program', id: program.id },
      { model: 'product.product', id: products.allIds },
      { model: 'res.partner', id: partner.id },
    );
  });

  test.afterAll(async () => {
    const cards = await searchRead(page, 'loyalty.card',
      [['program_id', '=', program.id]], ['id']);
    if (cards.length) {
      const cardIds = cards.map(c => c.id);
      const reds = await searchRead(page, 'loyalty.consign.redemption',
        [['card_id', 'in', cardIds]], ['id']);
      if (reds.length) toClean.unshift({ model: 'loyalty.consign.redemption', id: reds.map(r => r.id) });
      const lines = await searchRead(page, 'loyalty.consign.line',
        [['card_id', 'in', cardIds]], ['id']);
      if (lines.length) toClean.unshift({ model: 'loyalty.consign.line', id: lines.map(l => l.id) });
      toClean.unshift({ model: 'loyalty.card', id: cardIds });
    }
    await cleanup(page, toClean);
    await page.close();
  });

  test('card computed fields are correct after SO confirm', async () => {
    const so = await createAndConfirmSO(page, partner.id, [
      { product_id: products.triggerId, product_uom_qty: 1 },
      { product_id: products.itemIds[0], product_uom_qty: 5, price_unit: 100 },
      { product_id: products.itemIds[1], product_uom_qty: 3, price_unit: 250 },
    ]);
    toClean.push({ model: 'sale.order', id: so.id });

    const card = await findConsignCard(page, program.id, partner.id);
    expect(card).not.toBeNull();

    // consign_total_remaining_qty = sum of qty_deposited across active lines
    expect(card.consign_total_remaining_qty).toBe(8); // 5 + 3
    // consign_active_lines = count of lines with state=active
    expect(card.consign_active_lines).toBe(2);
    console.log(`[OK] consign_total_remaining_qty=${card.consign_total_remaining_qty}`);
    console.log(`[OK] consign_active_lines=${card.consign_active_lines}`);
  });

  test('card consign_total_remaining_value reflects line prices', async () => {
    const card = await findConsignCard(page, program.id, partner.id);
    // Value = sum(qty_remaining * unit_price) for active lines
    // Lines: 5 * 100 = 500, 3 * 250 = 750 => total 1250
    // Note: price_unit on SO lines might be overridden by product list_price
    // so we just check it is > 0 and read the actual lines for precise math
    expect(card.consign_total_remaining_value).toBeGreaterThan(0);

    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', card.id]],
      ['qty_remaining', 'unit_price', 'state'],
    );
    const expectedValue = lines
      .filter(l => l.state === 'active')
      .reduce((sum, l) => sum + l.qty_remaining * l.unit_price, 0);
    expect(card.consign_total_remaining_value).toBe(expectedValue);
    console.log(`[OK] consign_total_remaining_value=${card.consign_total_remaining_value} matches line computation (${expectedValue})`);
  });

  test('card code is non-empty', async () => {
    const card = await findConsignCard(page, program.id, partner.id);
    expect(card.code).toBeTruthy();
    expect(typeof card.code).toBe('string');
    expect(card.code.length).toBeGreaterThan(0);
    console.log(`[OK] Card code=${card.code}`);
  });
});
