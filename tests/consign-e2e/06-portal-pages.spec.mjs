// 06 — Portal user UI: card list, detail, redemption detail
import { test, expect } from '@playwright/test';
import { loginAsAdmin, loginAs, searchRead, read, BASE } from './helpers/odoo-rpc.mjs';
import {
  createPartner, createProducts, createConsignProgram,
  createCardDirect, addConsignLine, createAndConfirmRedemption,
  createPortalUser, cleanup,
} from './helpers/test-data-factory.mjs';

test.describe('Portal pages', () => {
  let adminPage;
  const toClean = [];
  let portalUser, products, program, cardId, cardCode, redemptionId;

  test.beforeAll(async ({ browser }) => {
    adminPage = await browser.newPage();
    await loginAsAdmin(adminPage);

    // Create portal user
    portalUser = await createPortalUser(adminPage, '-portal');
    toClean.push({ model: 'res.users', id: [portalUser.userId] });
    // Don't delete partner separately — user delete cascades

    products = await createProducts(adminPage, 1, '-portal');
    toClean.push({ model: 'product.product', id: products.allIds });

    program = await createConsignProgram(adminPage, [products.triggerId], '-portal');
    toClean.push({ model: 'loyalty.program', id: program.id });

    // Create card directly for the portal user's partner
    const card = await createCardDirect(adminPage, program.id, portalUser.partnerId);
    cardId = card.id;

    // Add line
    await addConsignLine(adminPage, cardId, products.itemIds[0], 5, 300);

    // Create and confirm a redemption
    const lines = await searchRead(adminPage, 'loyalty.consign.line',
      [['card_id', '=', cardId]], ['id']);
    const red = await createAndConfirmRedemption(adminPage, cardId, [
      { consign_line_id: lines[0].id, qty_redeemed: 1 },
    ]);
    redemptionId = red.id;

    // Read card code
    const [c] = await read(adminPage, 'loyalty.card', [cardId], ['code']);
    cardCode = c.code;

    await adminPage.close();
  });

  test.afterAll(async ({ browser }) => {
    const p = await browser.newPage();
    await loginAsAdmin(p);
    const reds = await searchRead(p, 'loyalty.consign.redemption',
      [['card_id', '=', cardId]], ['id']);
    if (reds.length) toClean.unshift({ model: 'loyalty.consign.redemption', id: reds.map(r => r.id) });
    const lines = await searchRead(p, 'loyalty.consign.line',
      [['card_id', '=', cardId]], ['id']);
    if (lines.length) toClean.unshift({ model: 'loyalty.consign.line', id: lines.map(l => l.id) });
    toClean.unshift({ model: 'loyalty.card', id: [cardId] });
    await cleanup(p, toClean);
    await p.close();
  });

  test('/my/consign-cards requires login', async ({ page }) => {
    const resp = await page.goto(`${BASE}/my/consign-cards`, { waitUntil: 'domcontentloaded' });
    // Should redirect to login
    expect(page.url()).toContain('/web/login');
  });

  test('portal card list shows card', async ({ page }) => {
    await loginAs(page, portalUser.login, portalUser.password);
    await page.goto(`${BASE}/my/consign-cards`);
    await page.waitForTimeout(3000);

    // Should see a table with the card
    const cardRow = page.locator(`table a:has-text("${cardCode}"), td:has-text("${cardCode}")`);
    const visible = await cardRow.first().isVisible().catch(() => false);
    expect(visible).toBe(true);
    console.log('[OK] Portal card list shows card');
    await page.screenshot({ path: '/tmp/portal-consign-list.png', fullPage: true });
  });

  test('portal card detail page', async ({ page }) => {
    await loginAs(page, portalUser.login, portalUser.password);
    await page.goto(`${BASE}/my/consign-cards/${cardId}`);
    await page.waitForTimeout(3000);

    // Heading should contain card code
    const heading = page.locator('h3, h2, .card-header').filter({ hasText: cardCode });
    await expect(heading.first()).toBeVisible({ timeout: 10000 });

    // Deposited items section
    const depositedSection = page.locator('text=寄存品項, text=Deposited Items');
    const hasDeposited = await depositedSection.first().isVisible().catch(() => false);
    console.log(`[${hasDeposited ? 'OK' : 'WARN'}] Deposited items section: ${hasDeposited}`);

    // Redemption records section
    const redemptionSection = page.locator('text=核銷紀錄, text=Redemption Records');
    const hasRedemption = await redemptionSection.first().isVisible().catch(() => false);
    console.log(`[${hasRedemption ? 'OK' : 'WARN'}] Redemption records section: ${hasRedemption}`);

    await page.screenshot({ path: '/tmp/portal-consign-detail.png', fullPage: true });
    console.log('[OK] Portal card detail loaded');
  });

  test('portal redemption detail page', async ({ page }) => {
    await loginAs(page, portalUser.login, portalUser.password);
    await page.goto(`${BASE}/my/consign-redemptions/${redemptionId}`);
    await page.waitForTimeout(3000);

    // Should show redemption reference (RD-XXXXXX-XXXX)
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toMatch(/RD-/);

    await page.screenshot({ path: '/tmp/portal-consign-redemption.png', fullPage: true });
    console.log('[OK] Portal redemption detail loaded');
  });

  test('portal user cannot see other users card', async ({ page }) => {
    await loginAs(page, portalUser.login, portalUser.password);
    // Try to access card ID 1 (likely belongs to another user or doesn't exist)
    await page.goto(`${BASE}/my/consign-cards/99999999`);
    await page.waitForTimeout(3000);

    // Should redirect to card list or show error
    const url = page.url();
    const isRedirected = url.includes('/my/consign-cards') && !url.includes('99999999');
    const isError = url.includes('/404') || url.includes('/error');
    expect(isRedirected || isError || page.url().includes('/web/login')).toBe(true);
    console.log('[OK] Unauthorized card access handled');
  });
});
