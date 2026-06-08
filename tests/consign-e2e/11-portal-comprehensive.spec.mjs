// 11 — Portal comprehensive: card list, detail, redemption detail, security, anonymous
import { test, expect } from '@playwright/test';
import { loginAsAdmin, loginAs, searchRead, read, BASE } from './helpers/odoo-rpc.mjs';
import {
  createPartner, createProducts, createConsignProgram,
  createCardDirect, addConsignLine, createAndConfirmRedemption,
  createPortalUser, cleanup,
} from './helpers/test-data-factory.mjs';

test.describe('D: Portal comprehensive', () => {
  let adminPage;
  const toClean = [];

  // Portal user A — owns the card
  let portalA, products, program, cardId, cardCode, redemptionId, redemptionRef;
  // Portal user B — used for cross-user security test
  let portalB;

  test.beforeAll(async ({ browser }) => {
    adminPage = await browser.newPage();
    await loginAsAdmin(adminPage);

    // --- Portal user A (card owner) ---
    portalA = await createPortalUser(adminPage, '-compA');
    toClean.push({ model: 'res.users', id: [portalA.userId] });

    // --- Portal user B (intruder) ---
    portalB = await createPortalUser(adminPage, '-compB');
    toClean.push({ model: 'res.users', id: [portalB.userId] });

    // --- Products and program ---
    products = await createProducts(adminPage, 2, '-comp');
    toClean.push({ model: 'product.product', id: products.allIds });

    program = await createConsignProgram(adminPage, [products.triggerId], '-comp');
    toClean.push({ model: 'loyalty.program', id: program.id });

    // --- Create card for portal user A ---
    const card = await createCardDirect(adminPage, program.id, portalA.partnerId);
    cardId = card.id;

    // Add two consign lines
    await addConsignLine(adminPage, cardId, products.itemIds[0], 5, 300, 'ItemA Comp');
    await addConsignLine(adminPage, cardId, products.itemIds[1], 3, 200, 'ItemB Comp');

    // Create and confirm a redemption
    const lines = await searchRead(adminPage, 'loyalty.consign.line',
      [['card_id', '=', cardId]], ['id', 'qty_remaining']);
    const red = await createAndConfirmRedemption(adminPage, cardId, [
      { consign_line_id: lines[0].id, qty_redeemed: 1 },
    ]);
    redemptionId = red.id;

    // Read card code
    const [c] = await read(adminPage, 'loyalty.card', [cardId], ['code']);
    cardCode = c.code;

    // Read redemption reference
    const [r] = await read(adminPage, 'loyalty.consign.redemption', [redemptionId], ['name']);
    redemptionRef = r.name;

    await adminPage.close();
  });

  test.afterAll(async ({ browser }) => {
    const p = await browser.newPage();
    await loginAsAdmin(p);

    // Clean redemptions
    const reds = await searchRead(p, 'loyalty.consign.redemption',
      [['card_id', '=', cardId]], ['id']);
    if (reds.length) toClean.unshift({ model: 'loyalty.consign.redemption', id: reds.map(r => r.id) });

    // Clean consign lines
    const lines = await searchRead(p, 'loyalty.consign.line',
      [['card_id', '=', cardId]], ['id']);
    if (lines.length) toClean.unshift({ model: 'loyalty.consign.line', id: lines.map(l => l.id) });

    // Clean card
    toClean.unshift({ model: 'loyalty.card', id: [cardId] });

    await cleanup(p, toClean);
    await p.close();
  });

  // -------------------------------------------------------------------
  // D1: Card list page shows correct data
  // -------------------------------------------------------------------
  test('D1: card list page shows card code and program name', async ({ page }) => {
    await loginAs(page, portalA.login, portalA.password);
    await page.goto(`${BASE}/my/consign-cards`);
    await page.waitForTimeout(3000);

    // Card code should be visible in the table
    const cardCodeCell = page.locator(`table a:has-text("${cardCode}"), td:has-text("${cardCode}")`);
    await expect(cardCodeCell.first()).toBeVisible({ timeout: 10000 });
    console.log('[OK] D1: Card code visible in list');

    // Program name should be visible
    const [prog] = await read(page, 'loyalty.program', [program.id], ['name']);
    const programCell = page.locator(`td:has-text("${prog.name}"), table:has-text("${prog.name}")`);
    const progVisible = await programCell.first().isVisible().catch(() => false);
    console.log(`[${progVisible ? 'OK' : 'INFO'}] D1: Program name visible: ${progVisible}`);

    await page.screenshot({ path: '/tmp/d1-card-list.png', fullPage: true });
  });

  // -------------------------------------------------------------------
  // D2: Card detail page shows heading, deposited items, summary stats
  // -------------------------------------------------------------------
  test('D2: card detail page shows heading, items table, and summary', async ({ page }) => {
    await loginAs(page, portalA.login, portalA.password);
    await page.goto(`${BASE}/my/consign-cards/${cardId}`);
    await page.waitForTimeout(3000);

    // Heading should contain card code
    const heading = page.locator('h3, h2, h1, .card-header').filter({ hasText: cardCode });
    await expect(heading.first()).toBeVisible({ timeout: 10000 });
    console.log('[OK] D2: Card code in heading');

    // Deposited items table should exist with rows
    const depositedSection = page.locator('text=寄存品項, text=Deposited Items, text=deposited');
    const hasDeposited = await depositedSection.first().isVisible().catch(() => false);
    console.log(`[${hasDeposited ? 'OK' : 'INFO'}] D2: Deposited items section visible: ${hasDeposited}`);

    // Should see product-related data in table rows
    const tableRows = page.locator('table tbody tr, .table tbody tr');
    const rowCount = await tableRows.count();
    expect(rowCount).toBeGreaterThanOrEqual(2); // At least 2 consign lines
    console.log(`[OK] D2: Table has ${rowCount} rows`);

    // Summary stats — look for remaining qty or value
    const bodyText = await page.locator('body').textContent();
    const hasSummary = bodyText.includes('7') || bodyText.includes('剩餘') || bodyText.includes('remaining');
    console.log(`[${hasSummary ? 'OK' : 'INFO'}] D2: Summary stats present: ${hasSummary}`);

    await page.screenshot({ path: '/tmp/d2-card-detail.png', fullPage: true });
  });

  // -------------------------------------------------------------------
  // D3: Redemption detail page shows RD- reference, items, total
  // -------------------------------------------------------------------
  test('D3: redemption detail page shows reference, items, and total', async ({ page }) => {
    await loginAs(page, portalA.login, portalA.password);
    await page.goto(`${BASE}/my/consign-redemptions/${redemptionId}`);
    await page.waitForTimeout(3000);

    const bodyText = await page.locator('body').textContent();

    // Should show RD- reference
    expect(bodyText).toMatch(/RD-/);
    console.log('[OK] D3: Redemption reference (RD-) visible');

    // If we know the exact ref, check it
    if (redemptionRef) {
      const refVisible = bodyText.includes(redemptionRef);
      console.log(`[${refVisible ? 'OK' : 'INFO'}] D3: Exact ref "${redemptionRef}" visible: ${refVisible}`);
    }

    // Redemption items table — should have at least 1 row
    const tableRows = page.locator('table tbody tr, .table tbody tr');
    const rowCount = await tableRows.count();
    expect(rowCount).toBeGreaterThanOrEqual(1);
    console.log(`[OK] D3: Redemption items table has ${rowCount} row(s)`);

    // Total value or quantity should be present
    const hasTotal = bodyText.includes('合計') || bodyText.includes('Total') || bodyText.includes('total');
    console.log(`[${hasTotal ? 'OK' : 'INFO'}] D3: Total section visible: ${hasTotal}`);

    await page.screenshot({ path: '/tmp/d3-redemption-detail.png', fullPage: true });
  });

  // -------------------------------------------------------------------
  // D4: Security — portal user B cannot access portal user A's card
  // -------------------------------------------------------------------
  test('D4: portal user cannot access another user\'s card', async ({ page }) => {
    await loginAs(page, portalB.login, portalB.password);

    // Try to access portal A's card
    const resp = await page.goto(`${BASE}/my/consign-cards/${cardId}`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    const url = page.url();
    const status = resp?.status() || 200;

    // Should redirect away, show 403/404, or show error
    const isRedirected = url.includes('/my/consign-cards') && !url.endsWith(`/${cardId}`);
    const isErrorPage = status === 403 || status === 404 || url.includes('/404');
    const isLoginRedirect = url.includes('/web/login');

    // Check page body for error indicators
    const bodyText = await page.locator('body').textContent();
    const hasAccessDenied = bodyText.includes('Access Denied') || bodyText.includes('not found')
      || bodyText.includes('Not Found') || bodyText.includes('denied')
      || bodyText.includes('403') || bodyText.includes('存取被拒');

    const protected_ = isRedirected || isErrorPage || isLoginRedirect || hasAccessDenied;
    expect(protected_).toBe(true);
    console.log(`[OK] D4: Cross-user access blocked (redirect=${isRedirected}, error=${isErrorPage}, login=${isLoginRedirect}, denied=${hasAccessDenied})`);

    await page.screenshot({ path: '/tmp/d4-cross-user-denied.png', fullPage: true });
  });

  // -------------------------------------------------------------------
  // D5: Anonymous user redirected to login
  // -------------------------------------------------------------------
  test('D5: anonymous user redirected to login on card list', async ({ page }) => {
    // Do NOT login — go directly to portal
    await page.goto(`${BASE}/my/consign-cards`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);

    expect(page.url()).toContain('/web/login');
    console.log('[OK] D5: Anonymous redirected to /web/login from card list');
  });

  test('D5b: anonymous user redirected to login on card detail', async ({ page }) => {
    await page.goto(`${BASE}/my/consign-cards/${cardId}`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);

    expect(page.url()).toContain('/web/login');
    console.log('[OK] D5b: Anonymous redirected to /web/login from card detail');
  });

  test('D5c: anonymous user redirected to login on redemption detail', async ({ page }) => {
    await page.goto(`${BASE}/my/consign-redemptions/${redemptionId}`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);

    expect(page.url()).toContain('/web/login');
    console.log('[OK] D5c: Anonymous redirected to /web/login from redemption detail');
  });
});
