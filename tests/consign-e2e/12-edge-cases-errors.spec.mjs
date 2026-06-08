// 12 — Edge cases and error handling: over-redemption, POS errors, depleted, zero qty, cancelled
import { test, expect } from '@playwright/test';
import { loginAsAdmin, searchRead, read, rpcCall, callButton } from './helpers/odoo-rpc.mjs';
import {
  createPartner, createProducts, createConsignProgram,
  createCardDirect, addConsignLine, createAndConfirmRedemption, cleanup,
} from './helpers/test-data-factory.mjs';

test.describe('E: Edge cases and error handling', () => {
  let page;
  const toClean = [];
  let partner, products, program, cardId, cardCode, posConfigId;
  let lineA, lineB, lineC; // consign lines with different purposes

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'edge');
    products = await createProducts(page, 2, '-edge');
    program = await createConsignProgram(page, [products.triggerId], '-edge');

    const card = await createCardDirect(page, program.id, partner.id);
    cardId = card.id;

    // Line A: 5 units — used for over-redemption (E1) and depletion (E4)
    await addConsignLine(page, cardId, products.itemIds[0], 5, 100, 'EdgeA');

    // Line B: 3 units — used for zero-qty test (E5)
    await addConsignLine(page, cardId, products.itemIds[1], 3, 200, 'EdgeB');

    // Line C: 2 units — will be cancelled (E6)
    await addConsignLine(page, cardId, products.itemIds[0], 2, 150, 'EdgeC-cancel');

    // Read line IDs
    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]],
      ['id', 'product_id', 'qty_deposited', 'unit_price', 'product_desc'],
    );
    // Identify lines by unique price + qty combination
    lineA = lines.find(l => l.unit_price === 100 && l.qty_deposited === 5);
    lineB = lines.find(l => l.unit_price === 200 && l.qty_deposited === 3);
    lineC = lines.find(l => l.unit_price === 150 && l.qty_deposited === 2);

    expect(lineA).toBeTruthy();
    expect(lineB).toBeTruthy();
    expect(lineC).toBeTruthy();

    // Read card code
    const [c] = await read(page, 'loyalty.card', [cardId], ['code']);
    cardCode = c.code;

    // Find a POS config for POS tests
    const configs = await searchRead(page, 'pos.config', [], ['id'], 1);
    posConfigId = configs[0]?.id;

    toClean.push(
      { model: 'loyalty.program', id: program.id },
      { model: 'product.product', id: products.allIds },
      { model: 'res.partner', id: partner.id },
    );
  });

  test.afterAll(async () => {
    // Clean redemptions
    const reds = await searchRead(page, 'loyalty.consign.redemption',
      [['card_id', '=', cardId]], ['id']);
    if (reds.length) toClean.unshift({ model: 'loyalty.consign.redemption', id: reds.map(r => r.id) });

    // Clean consign lines
    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]], ['id']);
    if (lines.length) toClean.unshift({ model: 'loyalty.consign.line', id: lines.map(l => l.id) });

    // Clean card
    toClean.unshift({ model: 'loyalty.card', id: [cardId] });

    await cleanup(page, toClean);
    await page.close();
  });

  // -------------------------------------------------------------------
  // E1: Over-redemption rejected (qty > remaining)
  // -------------------------------------------------------------------
  test('E1: over-redemption is rejected when qty exceeds remaining', async () => {
    let err;
    try {
      await createAndConfirmRedemption(page, cardId, [
        { consign_line_id: lineA.id, qty_redeemed: 999 },
      ]);
    } catch (e) {
      err = e;
    }
    expect(err).toBeDefined();
    const msg = err.message || err.rpcError?.data?.message || '';
    expect(msg).toMatch(/超過|exceed|Validation|insufficient|cannot|大於/i);
    console.log(`[OK] E1: Over-redemption rejected: ${msg.substring(0, 80)}`);
  });

  // -------------------------------------------------------------------
  // E2: POS invalid barcode returns not_found
  // -------------------------------------------------------------------
  test('E2: POS invalid barcode returns not_found', async () => {
    test.skip(!posConfigId, 'No POS config found');

    const result = await rpcCall(page, 'pos.config', 'use_consign_card_code',
      [[posConfigId], 'BOGUS-INVALID-99999', partner.id]);

    expect(result.successful).toBe(false);
    expect(result.payload?.not_found).toBe(true);
    console.log('[OK] E2: POS invalid barcode → not_found');
  });

  // -------------------------------------------------------------------
  // E3: POS wrong partner returns error
  // -------------------------------------------------------------------
  test('E3: POS wrong partner returns error', async () => {
    test.skip(!posConfigId, 'No POS config found');

    // Create a different partner
    const wrongPartner = await createPartner(page, 'wrong-edge');
    toClean.push({ model: 'res.partner', id: wrongPartner.id });

    const result = await rpcCall(page, 'pos.config', 'use_consign_card_code',
      [[posConfigId], cardCode, wrongPartner.id]);

    expect(result.successful).toBe(false);
    console.log(`[OK] E3: POS wrong partner rejected (payload: ${JSON.stringify(result.payload || {}).substring(0, 80)})`);
  });

  // -------------------------------------------------------------------
  // E4: Depleted line filtered from subsequent redemption
  // -------------------------------------------------------------------
  test('E4: depleted line cannot be redeemed again', async () => {
    // Read current remaining for lineA
    const [before] = await read(page, 'loyalty.consign.line', [lineA.id], ['qty_remaining']);

    // Fully redeem lineA
    await createAndConfirmRedemption(page, cardId, [
      { consign_line_id: lineA.id, qty_redeemed: before.qty_remaining },
    ]);

    // Verify line is depleted
    const [after] = await read(page, 'loyalty.consign.line', [lineA.id], ['state', 'qty_remaining']);
    expect(after.qty_remaining).toBe(0);
    expect(after.state).toBe('depleted');
    console.log('[OK] E4: LineA fully redeemed, state=depleted');

    // Try to redeem again — should fail
    let err;
    try {
      await createAndConfirmRedemption(page, cardId, [
        { consign_line_id: lineA.id, qty_redeemed: 1 },
      ]);
    } catch (e) {
      err = e;
    }
    expect(err).toBeDefined();
    console.log(`[OK] E4: Depleted line redemption rejected: ${(err.message || '').substring(0, 80)}`);
  });

  // -------------------------------------------------------------------
  // E5: Zero quantity redemption rejected or no-op
  // -------------------------------------------------------------------
  test('E5: zero quantity redemption is rejected', async () => {
    let err;
    let result;
    try {
      result = await createAndConfirmRedemption(page, cardId, [
        { consign_line_id: lineB.id, qty_redeemed: 0 },
      ]);
    } catch (e) {
      err = e;
    }

    // Either an error is thrown (validation) or qty_remaining unchanged
    if (err) {
      console.log(`[OK] E5: Zero-qty redemption rejected with error: ${(err.message || '').substring(0, 80)}`);
    } else {
      // If no error, verify qty was not affected (no-op)
      const [line] = await read(page, 'loyalty.consign.line', [lineB.id], ['qty_remaining']);
      expect(line.qty_remaining).toBe(3); // unchanged
      console.log('[OK] E5: Zero-qty redemption was a no-op (qty unchanged)');

      // Clean up the no-op redemption if it was created
      if (result?.id) {
        toClean.unshift({ model: 'loyalty.consign.redemption', id: [result.id] });
      }
    }
  });

  // -------------------------------------------------------------------
  // E6: Cancelled line cannot be redeemed
  // -------------------------------------------------------------------
  test('E6: cancelled line cannot be redeemed', async () => {
    // Cancel lineC via action_cancel
    await callButton(page, 'loyalty.consign.line', 'action_cancel', [lineC.id]);

    // Verify it is cancelled
    const [cancelled] = await read(page, 'loyalty.consign.line', [lineC.id], ['state', 'is_cancelled']);
    expect(cancelled.state).toBe('cancelled');
    console.log(`[OK] E6: LineC cancelled (state=${cancelled.state}, is_cancelled=${cancelled.is_cancelled})`);

    // Try to redeem the cancelled line
    let err;
    try {
      await createAndConfirmRedemption(page, cardId, [
        { consign_line_id: lineC.id, qty_redeemed: 1 },
      ]);
    } catch (e) {
      err = e;
    }
    expect(err).toBeDefined();
    console.log(`[OK] E6: Cancelled line redemption rejected: ${(err.message || '').substring(0, 80)}`);
  });
});
