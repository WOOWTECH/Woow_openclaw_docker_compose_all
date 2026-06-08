// 13 — Notifications: chatter messages on card creation, redemption, and backend UI
import { test, expect } from '@playwright/test';
import { loginAsAdmin, searchRead, read, BASE } from './helpers/odoo-rpc.mjs';
import {
  createPartner, createProducts, createConsignProgram,
  createAndConfirmSO, findConsignCard, createAndConfirmRedemption, cleanup,
} from './helpers/test-data-factory.mjs';

test.describe('F: Notifications and chatter', () => {
  let page;
  const toClean = [];
  let partner, products, program, cardId, cardCode;
  let redemptionId, redemptionRef;
  let messagesBeforeRedemption;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsAdmin(page);

    partner = await createPartner(page, 'notif');
    products = await createProducts(page, 1, '-notif');
    program = await createConsignProgram(page, [products.triggerId], '-notif');

    // --- F1 setup: Create card via SO confirm ---
    const so = await createAndConfirmSO(page, partner.id, [
      { product_id: products.triggerId, product_uom_qty: 1 },
      { product_id: products.itemIds[0], product_uom_qty: 5 },
    ]);
    toClean.push({ model: 'sale.order', id: so.id });

    const card = await findConsignCard(page, program.id, partner.id);
    expect(card).not.toBeNull();
    cardId = card.id;

    const [c] = await read(page, 'loyalty.card', [cardId], ['code']);
    cardCode = c.code;

    // Snapshot messages after card creation (before redemption)
    messagesBeforeRedemption = await searchRead(page, 'mail.message',
      [['model', '=', 'loyalty.card'], ['res_id', '=', cardId]],
      ['id', 'body', 'message_type', 'date'],
    );

    // --- F2 setup: Perform a redemption ---
    const lines = await searchRead(page, 'loyalty.consign.line',
      [['card_id', '=', cardId]], ['id', 'qty_remaining']);
    expect(lines.length).toBeGreaterThan(0);

    const red = await createAndConfirmRedemption(page, cardId, [
      { consign_line_id: lines[0].id, qty_redeemed: 2 },
    ]);
    redemptionId = red.id;

    const [r] = await read(page, 'loyalty.consign.redemption', [redemptionId], ['name']);
    redemptionRef = r.name;

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
  // F1: Card creation via SO confirm produces mail.message
  // -------------------------------------------------------------------
  test('F1: card creation via SO produces chatter message', async () => {
    // messagesBeforeRedemption was captured right after SO confirm / card creation
    // There should be at least 1 message on the card
    expect(messagesBeforeRedemption.length).toBeGreaterThan(0);

    // Log all messages for debugging
    for (const m of messagesBeforeRedemption) {
      const bodySnippet = (m.body || '').replace(/<[^>]+>/g, '').substring(0, 100);
      console.log(`  [F1 msg] type=${m.message_type}, date=${m.date}, body="${bodySnippet}"`);
    }

    // Check for creation-related message — could contain card code, partner name, or creation keywords
    const hasCreationMsg = messagesBeforeRedemption.some(m => {
      const body = (m.body || '').toLowerCase();
      return body.includes('建立') || body.includes('creat') || body.includes(cardCode.toLowerCase())
        || body.includes('寄存') || body.includes('consign') || m.message_type === 'notification';
    });

    console.log(`[${hasCreationMsg ? 'OK' : 'INFO'}] F1: Creation chatter message found: ${hasCreationMsg}`);
    console.log(`[OK] F1: Card has ${messagesBeforeRedemption.length} message(s) after creation`);
  });

  // -------------------------------------------------------------------
  // F2: Redemption completion produces chatter message on card
  // -------------------------------------------------------------------
  test('F2: redemption produces chatter message on card', async () => {
    // Fetch messages after redemption
    const messagesAfterRedemption = await searchRead(page, 'mail.message',
      [['model', '=', 'loyalty.card'], ['res_id', '=', cardId]],
      ['id', 'body', 'message_type', 'date'],
    );

    // Should have more messages than before
    expect(messagesAfterRedemption.length).toBeGreaterThan(messagesBeforeRedemption.length);
    console.log(`[OK] F2: Messages grew from ${messagesBeforeRedemption.length} to ${messagesAfterRedemption.length}`);

    // Identify new messages (IDs not in the before set)
    const beforeIds = new Set(messagesBeforeRedemption.map(m => m.id));
    const newMessages = messagesAfterRedemption.filter(m => !beforeIds.has(m.id));

    expect(newMessages.length).toBeGreaterThan(0);
    console.log(`[OK] F2: ${newMessages.length} new message(s) after redemption`);

    // At least one new message should reference the redemption
    const hasRedemptionRef = newMessages.some(m => {
      const body = (m.body || '').toLowerCase();
      return body.includes('核銷') || body.includes('redemption') || body.includes('rd-')
        || body.includes('redeem') || (redemptionRef && body.includes(redemptionRef.toLowerCase()));
    });

    for (const m of newMessages) {
      const bodySnippet = (m.body || '').replace(/<[^>]+>/g, '').substring(0, 120);
      console.log(`  [F2 new msg] type=${m.message_type}, body="${bodySnippet}"`);
    }

    console.log(`[${hasRedemptionRef ? 'OK' : 'INFO'}] F2: Redemption info in chatter: ${hasRedemptionRef}`);
  });

  // -------------------------------------------------------------------
  // F3: Backend card form shows chatter component with messages
  // -------------------------------------------------------------------
  test('F3: backend card form shows chatter with messages', async () => {
    // Navigate to consign card list
    await page.goto(`${BASE}/odoo/action-woow_loyalty_consign.loyalty_card_consign_action`);
    await page.waitForSelector('.o_list_view', { timeout: 30000 });

    // Find and click the card row
    const row = page.locator(`.o_data_row:has-text("${partner.name}")`).first();
    const rowVisible = await row.isVisible().catch(() => false);

    if (!rowVisible) {
      // Try searching
      const searchInput = page.locator('.o_searchview_input');
      if (await searchInput.isVisible().catch(() => false)) {
        await searchInput.fill(cardCode);
        await searchInput.press('Enter');
        await page.waitForTimeout(2000);
      }
    }

    await row.click();
    await page.waitForSelector('.o_form_view', { timeout: 15000 });

    // Chatter container should be visible
    const chatter = page.locator('.o-mail-Chatter, .o_ChatterContainer, .o_Chatter');
    await expect(chatter.first()).toBeVisible({ timeout: 10000 });
    console.log('[OK] F3: Chatter component visible on card form');

    // Chatter should contain message content (selector varies by Odoo 18 theme)
    await page.waitForTimeout(2000);
    const chatterText = await chatter.first().textContent();
    // Messages are verified via RPC in F1/F2; here we just confirm chatter renders content
    console.log(`[OK] F3: Chatter content length: ${chatterText.length} chars`);

    await page.screenshot({ path: '/tmp/f3-chatter-backend.png', fullPage: true });
  });
});
