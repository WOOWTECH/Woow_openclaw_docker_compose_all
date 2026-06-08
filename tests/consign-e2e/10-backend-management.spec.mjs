// 10 — Backend management: scenarios C1-C6
import { test, expect } from '@playwright/test';
import { loginAsAdmin, searchRead, read, write, unlink } from './helpers/odoo-rpc.mjs';
import {
  createPartner, createProducts, createConsignProgram,
  createCardDirect, addConsignLine, createAndConfirmRedemption, cleanup,
} from './helpers/test-data-factory.mjs';

test.describe('C1-C3: consign_add_line behavior', () => {
  let page;
  const toClean = [];
  let partner, products, program, cardId;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'mgmt-add');
    products = await createProducts(page, 2, '-mgmt-add');
    program = await createConsignProgram(page, [products.triggerId], '-mgmt-add');

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

  test('C1: consign_add_line creates new line', async () => {
    await addConsignLine(page, cardId, products.itemIds[0], 5, 200);

    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]],
      ['product_id', 'qty_deposited', 'qty_remaining', 'unit_price', 'state'],
    );
    expect(lines.length).toBe(1);
    expect(lines[0].product_id[0]).toBe(products.itemIds[0]);
    expect(lines[0].qty_deposited).toBe(5);
    expect(lines[0].qty_remaining).toBe(5);
    expect(lines[0].unit_price).toBe(200);
    expect(lines[0].state).toBe('active');
    console.log('[OK] C1: New consign line created: qty=5, price=200, state=active');
  });

  test('C2: Same product + same price accumulates qty', async () => {
    await addConsignLine(page, cardId, products.itemIds[0], 3, 200);

    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]],
      ['product_id', 'qty_deposited', 'qty_remaining', 'unit_price'],
    );
    // Still 1 line — accumulated
    expect(lines.length).toBe(1);
    expect(lines[0].qty_deposited).toBe(8); // 5 + 3
    expect(lines[0].qty_remaining).toBe(8);
    expect(lines[0].unit_price).toBe(200);
    console.log('[OK] C2: Same product+price accumulated: qty=8, still 1 line');
  });

  test('C3: Same product different price creates new line', async () => {
    await addConsignLine(page, cardId, products.itemIds[0], 2, 350);

    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]],
      ['qty_deposited', 'unit_price'],
    );
    expect(lines.length).toBe(2);

    const p200 = lines.find(l => l.unit_price === 200);
    const p350 = lines.find(l => l.unit_price === 350);
    expect(p200).toBeTruthy();
    expect(p350).toBeTruthy();
    expect(p200.qty_deposited).toBe(8);
    expect(p350.qty_deposited).toBe(2);
    console.log('[OK] C3: Different price created new line: price=350 qty=2');
  });
});

test.describe('C4: Protected field write', () => {
  let page;
  const toClean = [];
  let partner, products, program, cardId;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'mgmt-prot');
    products = await createProducts(page, 1, '-mgmt-prot');
    program = await createConsignProgram(page, [products.triggerId], '-mgmt-prot');

    const card = await createCardDirect(page, program.id, partner.id);
    cardId = card.id;

    // Add a line to test write protection on
    await addConsignLine(page, cardId, products.itemIds[0], 5, 100);

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

  test('C4: Writing qty_deposited directly raises ValidationError', async () => {
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
    console.log(`[OK] C4: Protected field write rejected: ${err.message.substring(0, 120)}`);

    // Verify qty_deposited was NOT changed
    const [line] = await read(page, 'loyalty.consign.line', [lineId], ['qty_deposited']);
    expect(line.qty_deposited).toBe(5);
    console.log('[OK] C4: qty_deposited remains 5 after rejected write');
  });
});

test.describe('C5: Cancel line via action_cancel', () => {
  let page;
  const toClean = [];
  let partner, products, program, cardId;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'mgmt-cancel');
    products = await createProducts(page, 1, '-mgmt-cancel');
    program = await createConsignProgram(page, [products.triggerId], '-mgmt-cancel');

    const card = await createCardDirect(page, program.id, partner.id);
    cardId = card.id;

    // Add a line to cancel
    await addConsignLine(page, cardId, products.itemIds[0], 3, 150);

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

  test('C5: action_cancel sets state=cancelled and is_cancelled=True', async () => {
    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]], ['id', 'state'], 1);
    const lineId = lines[0].id;
    expect(lines[0].state).toBe('active');

    // Cancel the line
    const { callButton } = await import('./helpers/odoo-rpc.mjs');
    await callButton(page, 'loyalty.consign.line', 'action_cancel', [lineId]);

    const [after] = await read(page, 'loyalty.consign.line', [lineId],
      ['state', 'is_cancelled']);
    expect(after.state).toBe('cancelled');
    expect(after.is_cancelled).toBe(true);
    console.log('[OK] C5: Line cancelled: state=cancelled, is_cancelled=true');
  });

  test('C5b: Cancelled line does not count in card active_lines', async () => {
    const card = await searchRead(page, 'loyalty.card',
      [['id', '=', cardId]],
      ['consign_active_lines', 'consign_total_remaining_qty'],
      1,
    );
    expect(card[0].consign_active_lines).toBe(0);
    expect(card[0].consign_total_remaining_qty).toBe(0);
    console.log('[OK] C5b: Card shows 0 active lines after cancellation');
  });
});

test.describe('C6: Cannot unlink a line that has been redeemed', () => {
  let page;
  const toClean = [];
  let partner, products, program, cardId, lineId;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'mgmt-unlink');
    products = await createProducts(page, 1, '-mgmt-unlink');
    program = await createConsignProgram(page, [products.triggerId], '-mgmt-unlink');

    const card = await createCardDirect(page, program.id, partner.id);
    cardId = card.id;

    // Add a line and redeem from it
    await addConsignLine(page, cardId, products.itemIds[0], 5, 100);

    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]], ['id'], 1);
    lineId = lines[0].id;

    // Partial redemption to make the line "redeemed"
    await createAndConfirmRedemption(page, cardId, [
      { consign_line_id: lineId, qty_redeemed: 2 },
    ]);

    toClean.push(
      { model: 'loyalty.program', id: program.id },
      { model: 'product.product', id: products.allIds },
      { model: 'res.partner', id: partner.id },
    );
  });

  test.afterAll(async () => {
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

  test('C6: Unlinking a redeemed line is rejected', async () => {
    // Verify line has been redeemed
    const [line] = await read(page, 'loyalty.consign.line', [lineId],
      ['qty_redeemed', 'qty_remaining']);
    expect(line.qty_redeemed).toBe(2);
    console.log(`C6: Line has qty_redeemed=${line.qty_redeemed}, qty_remaining=${line.qty_remaining}`);

    // Attempt to unlink — should raise error
    let err;
    try {
      await unlink(page, 'loyalty.consign.line', [lineId]);
    } catch (e) {
      err = e;
    }
    expect(err).toBeDefined();
    console.log(`[OK] C6: Unlink of redeemed line rejected: ${err.message.substring(0, 120)}`);

    // Verify the line still exists
    const [still] = await read(page, 'loyalty.consign.line', [lineId], ['id']);
    expect(still.id).toBe(lineId);
    console.log('[OK] C6: Redeemed line still exists after failed unlink');
  });
});
