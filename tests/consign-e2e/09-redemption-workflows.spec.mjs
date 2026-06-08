// 09 — Redemption workflows: scenarios B1, B5, B6, B7, B8
import { test, expect } from '@playwright/test';
import { loginAsAdmin, searchRead, read } from './helpers/odoo-rpc.mjs';
import {
  createPartner, createProducts, createConsignProgram,
  createAndConfirmSO, findConsignCard, createAndConfirmRedemption, cleanup,
} from './helpers/test-data-factory.mjs';

test.describe('Redemption workflows', () => {
  let page;
  const toClean = [];
  let partner, products, program, cardId, consignLines;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'redwf');
    // 3 item products for varied line testing
    products = await createProducts(page, 3, '-redwf');
    program = await createConsignProgram(page, [products.triggerId], '-redwf');

    // SO with trigger + 3 items with specific quantities
    // LineA: item0 qty=6 (for B1 partial, B5 active check, B8 sequential deplete)
    // LineB: item1 qty=3 (for B6 full redemption)
    // LineC: item2 qty=4 (for B7 multi-line redemption)
    const so = await createAndConfirmSO(page, partner.id, [
      { product_id: products.triggerId, product_uom_qty: 1 },
      { product_id: products.itemIds[0], product_uom_qty: 6, price_unit: 200 },
      { product_id: products.itemIds[1], product_uom_qty: 3, price_unit: 300 },
      { product_id: products.itemIds[2], product_uom_qty: 4, price_unit: 150 },
    ]);
    toClean.push({ model: 'sale.order', id: so.id });

    const card = await findConsignCard(page, program.id, partner.id);
    expect(card).not.toBeNull();
    cardId = card.id;

    consignLines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]],
      ['id', 'product_id', 'qty_deposited', 'qty_remaining', 'unit_price'],
    );
    // Sort by qty_deposited descending for predictable indexing
    consignLines.sort((a, b) => b.qty_deposited - a.qty_deposited);
    console.log(`Setup: card=${cardId}, lines=${consignLines.map(l => `id=${l.id} qty=${l.qty_deposited}`).join(', ')}`);

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

  // lineA = qty_deposited 6 (index 0 after sort)
  // lineC = qty_deposited 4 (index 1 after sort)
  // lineB = qty_deposited 3 (index 2 after sort)

  test('B1: Backend partial redemption via RPC', async () => {
    const lineA = consignLines[0]; // qty_deposited=6
    expect(lineA.qty_deposited).toBe(6);

    const red = await createAndConfirmRedemption(page, cardId, [
      { consign_line_id: lineA.id, qty_redeemed: 2 },
    ]);
    expect(red.id).toBeGreaterThan(0);

    // Verify redemption record
    const [rec] = await read(page, 'loyalty.consign.redemption', [red.id], ['state']);
    expect(rec.state).toBe('done');

    // Verify line quantities updated
    const [updated] = await read(page, 'loyalty.consign.line', [lineA.id],
      ['qty_redeemed', 'qty_remaining']);
    expect(updated.qty_redeemed).toBe(2);
    expect(updated.qty_remaining).toBe(4); // 6 - 2
    console.log(`[OK] B1: Partial redemption done, qty_redeemed=2, qty_remaining=4`);
  });

  test('B5: Partial redemption keeps state=active', async () => {
    const lineA = consignLines[0]; // after B1: remaining=4
    const [line] = await read(page, 'loyalty.consign.line', [lineA.id],
      ['state', 'qty_remaining']);
    expect(line.state).toBe('active');
    expect(line.qty_remaining).toBeGreaterThan(0);
    console.log(`[OK] B5: Line state=active after partial redemption, remaining=${line.qty_remaining}`);
  });

  test('B6: Full redemption sets state=depleted', async () => {
    const lineB = consignLines[2]; // qty_deposited=3, not yet redeemed
    expect(lineB.qty_deposited).toBe(3);

    // Read current remaining to be safe
    const [before] = await read(page, 'loyalty.consign.line', [lineB.id],
      ['qty_remaining']);
    expect(before.qty_remaining).toBe(3);

    // Redeem ALL remaining
    const red = await createAndConfirmRedemption(page, cardId, [
      { consign_line_id: lineB.id, qty_redeemed: before.qty_remaining },
    ]);
    expect(red.id).toBeGreaterThan(0);

    const [after] = await read(page, 'loyalty.consign.line', [lineB.id],
      ['state', 'qty_remaining', 'qty_redeemed']);
    expect(after.qty_remaining).toBe(0);
    expect(after.qty_redeemed).toBe(3);
    expect(after.state).toBe('depleted');
    console.log(`[OK] B6: Full redemption -> state=depleted, qty_remaining=0`);
  });

  test('B7: Multi-line redemption (redeem from 2 lines at once)', async () => {
    const lineA = consignLines[0]; // remaining=4 after B1
    const lineC = consignLines[1]; // qty_deposited=4, not yet redeemed

    const [beforeA] = await read(page, 'loyalty.consign.line', [lineA.id], ['qty_remaining']);
    const [beforeC] = await read(page, 'loyalty.consign.line', [lineC.id], ['qty_remaining']);
    console.log(`B7 before: lineA remaining=${beforeA.qty_remaining}, lineC remaining=${beforeC.qty_remaining}`);

    // Redeem from BOTH lines in a single redemption
    const red = await createAndConfirmRedemption(page, cardId, [
      { consign_line_id: lineA.id, qty_redeemed: 1 },
      { consign_line_id: lineC.id, qty_redeemed: 2 },
    ]);
    expect(red.id).toBeGreaterThan(0);

    const [recA] = await read(page, 'loyalty.consign.line', [lineA.id], ['qty_remaining']);
    const [recC] = await read(page, 'loyalty.consign.line', [lineC.id], ['qty_remaining']);
    expect(recA.qty_remaining).toBe(beforeA.qty_remaining - 1);
    expect(recC.qty_remaining).toBe(beforeC.qty_remaining - 2);
    console.log(`[OK] B7: Multi-line redemption: lineA remaining=${recA.qty_remaining}, lineC remaining=${recC.qty_remaining}`);

    // Verify the redemption has 2 lines
    const redLines = await searchRead(page, 'loyalty.consign.redemption.line',
      [['redemption_id', '=', red.id]], ['consign_line_id', 'qty_redeemed']);
    expect(redLines.length).toBe(2);
    console.log(`[OK] B7: Redemption has ${redLines.length} lines`);
  });

  test('B8: Sequential redemptions until depleted (3 rounds)', async () => {
    const lineC = consignLines[1]; // remaining after B7: 4 - 2 = 2

    const [start] = await read(page, 'loyalty.consign.line', [lineC.id],
      ['qty_remaining', 'state']);
    expect(start.qty_remaining).toBe(2);
    expect(start.state).toBe('active');
    console.log(`B8 start: lineC remaining=${start.qty_remaining}, state=${start.state}`);

    // Round 1: redeem 1
    const red1 = await createAndConfirmRedemption(page, cardId, [
      { consign_line_id: lineC.id, qty_redeemed: 1 },
    ]);
    expect(red1.id).toBeGreaterThan(0);
    const [after1] = await read(page, 'loyalty.consign.line', [lineC.id],
      ['qty_remaining', 'state']);
    expect(after1.qty_remaining).toBe(1);
    expect(after1.state).toBe('active');
    console.log(`[OK] B8 round 1: remaining=1, state=active`);

    // Round 2: redeem remaining 1 to deplete
    const red2 = await createAndConfirmRedemption(page, cardId, [
      { consign_line_id: lineC.id, qty_redeemed: 1 },
    ]);
    expect(red2.id).toBeGreaterThan(0);
    const [after2] = await read(page, 'loyalty.consign.line', [lineC.id],
      ['qty_remaining', 'state']);
    expect(after2.qty_remaining).toBe(0);
    expect(after2.state).toBe('depleted');
    console.log(`[OK] B8 round 2: remaining=0, state=depleted`);

    // Round 3: attempt to redeem from depleted line should fail
    let err;
    try {
      await createAndConfirmRedemption(page, cardId, [
        { consign_line_id: lineC.id, qty_redeemed: 1 },
      ]);
    } catch (e) {
      err = e;
    }
    expect(err).toBeDefined();
    console.log(`[OK] B8 round 3: Redemption on depleted line rejected: ${err.message.substring(0, 100)}`);
  });
});
