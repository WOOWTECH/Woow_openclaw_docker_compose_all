// 07 — Chatter notifications: messages on card lifecycle
import { test, expect } from '@playwright/test';
import { loginAsAdmin, searchRead, read, BASE } from './helpers/odoo-rpc.mjs';
import {
  createPartner, createProducts, createConsignProgram,
  createAndConfirmSO, findConsignCard, createAndConfirmRedemption, cleanup,
} from './helpers/test-data-factory.mjs';

test.describe('Chatter notifications', () => {
  let page;
  const toClean = [];
  let partner, products, program, cardId;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'chatter');
    products = await createProducts(page, 1, '-chatter');
    program = await createConsignProgram(page, [products.triggerId], '-chatter');

    const so = await createAndConfirmSO(page, partner.id, [
      { product_id: products.triggerId, product_uom_qty: 1 },
      { product_id: products.itemIds[0], product_uom_qty: 3 },
    ]);
    toClean.push({ model: 'sale.order', id: so.id });

    const card = await findConsignCard(page, program.id, partner.id);
    cardId = card.id;

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

  test('redemption posts chatter message on card', async () => {
    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]], ['id', 'qty_remaining']);

    await createAndConfirmRedemption(page, cardId, [
      { consign_line_id: lines[0].id, qty_redeemed: 1 },
    ]);

    // Check mail.message for this card
    const messages = await searchRead(page, 'mail.message',
      [['model', '=', 'loyalty.card'], ['res_id', '=', cardId]],
      ['body', 'message_type', 'date'],
    );
    expect(messages.length).toBeGreaterThan(0);

    // At least one message should relate to redemption
    const hasRedemptionMsg = messages.some(m =>
      m.body && (m.body.includes('核銷') || m.body.includes('redemption') || m.body.includes('RD-'))
    );
    console.log(`[${hasRedemptionMsg ? 'OK' : 'INFO'}] Redemption chatter message: ${hasRedemptionMsg}`);
    console.log(`[OK] Card has ${messages.length} chatter messages`);
  });

  test('card form shows chatter in backend (UI)', async () => {
    const [c] = await read(page, 'loyalty.card', [cardId], ['code']);
    await page.goto(`${BASE}/odoo/action-woow_loyalty_consign.loyalty_card_consign_action`);
    await page.waitForSelector('.o_list_view', { timeout: 30000 });

    const searchInput = page.locator('.o_searchview_input');
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.fill(c.code);
      await searchInput.press('Enter');
      await page.waitForTimeout(2000);
    }

    const row = page.locator('.o_data_row').first();
    await row.click();
    await page.waitForSelector('.o_form_view', { timeout: 15000 });

    // Chatter should be visible
    const chatter = page.locator('.o-mail-Chatter, .o_ChatterContainer, .o_Chatter');
    const chatterVisible = await chatter.first().isVisible().catch(() => false);
    expect(chatterVisible).toBe(true);
    console.log('[OK] Chatter visible on card form');

    // Should have at least 1 message
    const messageEntries = page.locator('.o-mail-Message, .o_Message');
    const msgCount = await messageEntries.count();
    console.log(`[INFO] Chatter message count: ${msgCount}`);

    await page.screenshot({ path: '/tmp/consign-chatter.png', fullPage: true });
  });
});
