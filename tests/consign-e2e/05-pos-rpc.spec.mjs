// 05 — POS RPC endpoints: card lookup, redemption
import { test, expect } from '@playwright/test';
import { loginAsAdmin, searchRead, read, rpcCall } from './helpers/odoo-rpc.mjs';
import {
  createPartner, createProducts, createConsignProgram,
  createCardDirect, addConsignLine, cleanup,
} from './helpers/test-data-factory.mjs';

test.describe('POS RPC endpoints', () => {
  let page;
  const toClean = [];
  let partner, products, program, cardId, cardCode, posConfigId;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'pos');
    products = await createProducts(page, 1, '-pos');
    program = await createConsignProgram(page, [products.triggerId], '-pos');

    const card = await createCardDirect(page, program.id, partner.id);
    cardId = card.id;

    await addConsignLine(page, cardId, products.itemIds[0], 10, 100);

    // Read card code
    const [c] = await read(page, 'loyalty.card', [cardId], ['code']);
    cardCode = c.code;

    // Find a POS config
    const configs = await searchRead(page, 'pos.config', [], ['id'], 1);
    posConfigId = configs[0]?.id;

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

  test('use_consign_card_code with valid code', async () => {
    test.skip(!posConfigId, 'No POS config found');

    const result = await rpcCall(page, 'pos.config', 'use_consign_card_code',
      [[posConfigId], cardCode, partner.id]);

    expect(result.successful).toBe(true);
    expect(result.payload.card_id).toBe(cardId);
    expect(result.payload.lines.length).toBeGreaterThan(0);
    expect(result.payload.lines[0].qty_remaining).toBe(10);
    console.log(`[OK] Card lookup: ${result.payload.lines.length} lines`);
  });

  test('use_consign_card_code with invalid code', async () => {
    test.skip(!posConfigId, 'No POS config found');

    const result = await rpcCall(page, 'pos.config', 'use_consign_card_code',
      [[posConfigId], 'INVALID-XXXXX-99999', false]);

    expect(result.successful).toBe(false);
    expect(result.payload?.not_found).toBe(true);
    console.log('[OK] Invalid code returns not_found');
  });

  test('use_consign_card_code with wrong partner', async () => {
    test.skip(!posConfigId, 'No POS config found');

    // Use a different partner ID
    const wrongPartner = await createPartner(page, 'wrong');
    toClean.push({ model: 'res.partner', id: wrongPartner.id });

    const result = await rpcCall(page, 'pos.config', 'use_consign_card_code',
      [[posConfigId], cardCode, wrongPartner.id]);

    expect(result.successful).toBe(false);
    console.log('[OK] Wrong partner rejected');
  });

  test('get_partner_consign_cards returns cards', async () => {
    test.skip(!posConfigId, 'No POS config found');

    const result = await rpcCall(page, 'pos.config', 'get_partner_consign_cards',
      [[posConfigId], partner.id]);

    expect(result.successful).toBe(true);
    expect(result.payload.cards.length).toBeGreaterThanOrEqual(1);

    const ourCard = result.payload.cards.find(c => c.card_id === cardId);
    expect(ourCard).toBeTruthy();
    expect(ourCard.lines.length).toBeGreaterThan(0);
    console.log(`[OK] Partner has ${result.payload.cards.length} card(s)`);
  });

  test('confirm_consign_redemptions via POS', async () => {
    test.skip(!posConfigId, 'No POS config found');

    // Get consign line
    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId], ['state', '=', 'active']],
      ['id', 'qty_remaining'],
    );
    expect(lines.length).toBeGreaterThan(0);
    const line = lines[0];
    const qtyBefore = line.qty_remaining;

    // We need a pos.order to call confirm_consign_redemptions on
    // For testing, find any existing POS order or skip
    const orders = await searchRead(page, 'pos.order', [], ['id'], 1);
    test.skip(!orders.length, 'No POS orders found for RPC test');

    const orderId = orders[0].id;
    const consignData = {
      card_id: cardId,
      lines: [{ consign_line_id: line.id, qty_redeemed: 1 }],
    };

    const result = await rpcCall(page, 'pos.order', 'confirm_consign_redemptions',
      [[orderId], consignData]);

    expect(result.successful).toBe(true);
    expect(result.payload.redemption_id).toBeGreaterThan(0);

    // Verify qty decreased
    const [updated] = await read(page, 'loyalty.consign.line', [line.id], ['qty_remaining']);
    expect(updated.qty_remaining).toBe(qtyBefore - 1);
    console.log(`[OK] POS redemption: id=${result.payload.redemption_id}`);
  });
});
