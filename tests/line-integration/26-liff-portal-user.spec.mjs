// tests/line-integration/26-liff-portal-user.spec.mjs
// L1-L8: LIFF portal user creation flow — server-side RPC simulation
//
// Simulates the exact code path of liff_redirect.py _ensure_portal_user +
// _create_portal_user WITHOUT needing a real LINE token. Each step mirrors
// the real LIFF login sequence:
//   LINE token verify -> line.user create -> partner create -> bind ->
//   portal user create -> group switch -> session authenticate
import { test, expect } from '@playwright/test';
import {
  loginAsAdmin, loginAs, rpcCall, searchRead, create, read, write,
  safeUnlink, BASE,
} from './helpers/odoo-rpc.mjs';

test.describe('L: LIFF Portal User Creation Flow', () => {

  // Unique suffix to avoid collisions across parallel runs
  const TS = Date.now();
  const LINE_UID = `U_PW_LIFF_TEST_${TS}`;
  const LOGIN_EMAIL = `line_${LINE_UID}@line.placeholder`;
  const DISPLAY_NAME = `PW LIFF Test User ${TS}`;
  const TEMP_PASSWORD = 'test_temp_password_Liff_26';

  // IDs to track for cleanup
  let lineUserId = null;
  let partnerId = null;
  let portalUserId = null;

  // Group IDs resolved once and reused
  let portalGroupId = null;
  let internalGroupId = null;

  // ---------------------------------------------------------------
  // Helper: resolve an XML ID (e.g. 'base.group_portal') to res_id
  // ---------------------------------------------------------------
  async function resolveXmlId(page, xmlid) {
    const [module, name] = xmlid.split('.');
    const recs = await searchRead(
      page,
      'ir.model.data',
      [['module', '=', module], ['name', '=', name]],
      ['res_id'],
      1,
    );
    if (!recs.length) throw new Error(`XML ID ${xmlid} not found`);
    return recs[0].res_id;
  }

  // ---------------------------------------------------------------
  // beforeAll: login and resolve group IDs once
  // ---------------------------------------------------------------
  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    try {
      await loginAsAdmin(page);
      portalGroupId = await resolveXmlId(page, 'base.group_portal');
      internalGroupId = await resolveXmlId(page, 'base.group_user');
      expect(portalGroupId).toBeTruthy();
      expect(internalGroupId).toBeTruthy();
      console.log(`[SETUP] portal group id=${portalGroupId}, internal group id=${internalGroupId}`);
    } finally {
      await page.close();
    }
  });

  // ---------------------------------------------------------------
  // afterAll: cleanup test data (reverse creation order)
  // ---------------------------------------------------------------
  test.afterAll(async ({ browser }) => {
    const page = await browser.newPage();
    try {
      await loginAsAdmin(page);
      // Delete portal user first (depends on partner)
      if (portalUserId) await safeUnlink(page, 'res.users', [portalUserId]);
      // Delete partner
      if (partnerId) await safeUnlink(page, 'res.partner', [partnerId]);
      // Delete line.user
      if (lineUserId) await safeUnlink(page, 'line.user', [lineUserId]);
      console.log('[CLEANUP] Removed test user/partner/line.user');
    } finally {
      await page.close();
    }
  });

  // =================================================================
  // L1: Create line.user record (simulates create_or_update_from_liff)
  // =================================================================
  test('L1: Create line.user record with unique LINE UID', async ({ page }) => {
    await loginAsAdmin(page);

    // Ensure no leftover from a previous run
    const existing = await searchRead(
      page,
      'line.user',
      [['line_user_id', '=', LINE_UID]],
      ['id'],
      1,
    );
    if (existing.length) {
      await safeUnlink(page, 'line.user', [existing[0].id]);
    }

    // Create — mirrors LineUser.create_or_update_from_liff(payload) for a new user
    const id = await create(page, 'line.user', {
      line_user_id: LINE_UID,
      display_name: DISPLAY_NAME,
    });
    lineUserId = Array.isArray(id) ? id[0] : id;
    expect(lineUserId).toBeTruthy();

    // Verify
    const [rec] = await read(page, 'line.user', [lineUserId], [
      'line_user_id', 'display_name',
    ]);
    expect(rec.line_user_id).toBe(LINE_UID);
    expect(rec.display_name).toBe(DISPLAY_NAME);

    console.log(`[OK] L1: line.user created id=${lineUserId}, uid=${LINE_UID}`);
  });

  // =================================================================
  // L2: Create partner and bind to line.user
  //     (simulates _ensure_portal_user case 3: new partner + bind)
  // =================================================================
  test('L2: Create res.partner and bind to line.user', async ({ page }) => {
    await loginAsAdmin(page);
    expect(lineUserId).toBeTruthy(); // L1 must have passed

    // Create partner — mirrors Partner.create({...}) in _ensure_portal_user
    const pid = await create(page, 'res.partner', {
      name: DISPLAY_NAME,
      email: LOGIN_EMAIL,
      image_1920: false,
    });
    partnerId = Array.isArray(pid) ? pid[0] : pid;
    expect(partnerId).toBeTruthy();

    // Bind — mirrors line_user.bind_partner(partner.id)
    await rpcCall(page, 'line.user', 'bind_partner', [[lineUserId], partnerId]);

    // Verify binding
    const [lu] = await read(page, 'line.user', [lineUserId], ['partner_id']);
    expect(lu.partner_id).toBeTruthy();
    // partner_id is returned as [id, name] tuple
    const boundPartnerId = Array.isArray(lu.partner_id) ? lu.partner_id[0] : lu.partner_id;
    expect(boundPartnerId).toBe(partnerId);

    console.log(`[OK] L2: partner id=${partnerId} bound to line.user id=${lineUserId}`);
  });

  // =================================================================
  // L3: Create portal user via RPC (mirrors _create_portal_user)
  //
  // The real code:
  //   1. Users.with_context(no_reset_password=True).create({...})
  //   2. user.write({'groups_id': [(3, internal), (4, portal)]})
  //
  // Via RPC we replicate this in two steps:
  //   Step A: create with no_reset_password context
  //   Step B: write groups_id to switch from internal to portal
  // =================================================================
  test('L3: Create portal user via two-step RPC (create + group switch)', async ({ page }) => {
    await loginAsAdmin(page);
    expect(partnerId).toBeTruthy();  // L2 must have passed

    // Resolve main company (same as _create_portal_user)
    const companies = await searchRead(
      page,
      'res.company',
      [],
      ['id', 'name'],
      1,
    );
    expect(companies.length).toBeGreaterThanOrEqual(1);
    const mainCompanyId = companies[0].id;

    // Step A: create user — no_reset_password via context
    const uid = await rpcCall(
      page,
      'res.users',
      'create',
      [{
        name: DISPLAY_NAME,
        login: LOGIN_EMAIL,
        password: TEMP_PASSWORD,
        partner_id: partnerId,
        company_id: mainCompanyId,
        company_ids: [[6, 0, [mainCompanyId]]],
      }],
      { context: { no_reset_password: true } },
    );
    portalUserId = Array.isArray(uid) ? uid[0] : uid;
    expect(portalUserId).toBeTruthy();

    // Step B: switch groups — remove internal, add portal
    // Mirrors: user.write({'groups_id': [(3, internal_group.id), (4, portal_group.id)]})
    await write(page, 'res.users', [portalUserId], {
      groups_id: [
        [3, internalGroupId],   // remove internal
        [4, portalGroupId],     // add portal
      ],
    });

    console.log(`[OK] L3: portal user created id=${portalUserId}, login=${LOGIN_EMAIL}`);
  });

  // =================================================================
  // L4: Verify user is PORTAL not INTERNAL (CRITICAL assertion)
  // =================================================================
  test('L4: User has portal group and NOT internal group', async ({ page }) => {
    await loginAsAdmin(page);
    expect(portalUserId).toBeTruthy(); // L3 must have passed

    // Read the user's groups_id (many2many returns array of IDs)
    const [user] = await read(page, 'res.users', [portalUserId], ['groups_id']);
    const groupIds = user.groups_id;

    expect(Array.isArray(groupIds)).toBe(true);

    // CRITICAL: portal group MUST be present
    expect(groupIds).toContain(portalGroupId);

    // CRITICAL: internal user group MUST NOT be present
    expect(groupIds).not.toContain(internalGroupId);

    console.log(
      `[OK] L4: user ${portalUserId} groups include portal(${portalGroupId}), ` +
      `exclude internal(${internalGroupId}). Total groups: ${groupIds.length}`,
    );
  });

  // =================================================================
  // L5: Verify user can authenticate (simulates session.authenticate)
  //     Use admin to set a known password, then login via form
  // =================================================================
  test('L5: Portal user can authenticate via login form', async ({ page }) => {
    expect(portalUserId).toBeTruthy(); // L3 must have passed

    // First, admin sets a known password on the portal user
    await loginAsAdmin(page);
    await write(page, 'res.users', [portalUserId], { password: TEMP_PASSWORD });

    // Now try logging in as the portal user via form
    await page.goto(`${BASE}/web/login`);
    await page.fill('input[name="login"]', LOGIN_EMAIL);
    await page.fill('input[name="password"]', TEMP_PASSWORD);
    await page.click('button[type="submit"]');

    // Wait for navigation away from login page (portal lands on /my or /my/home)
    try {
      await page.waitForURL(url => !url.href.includes('/web/login'), { timeout: 15000 });
    } catch {
      // Check if there's an error message on the login page
      const errorEl = page.locator('.alert-danger, .o_login_error, [role="alert"]');
      const errorText = await errorEl.textContent().catch(() => '');
      throw new Error(`Portal login failed. URL: ${page.url()}, Error: ${errorText || 'timeout'}`);
    }

    const url = page.url();
    expect(url).not.toContain('/web/login');

    console.log(`[OK] L5: Portal user authenticated, landed at ${url}`);
  });

  // =================================================================
  // L6: Verify user has correct company
  // =================================================================
  test('L6: Portal user has company_id and company_ids set', async ({ page }) => {
    await loginAsAdmin(page);
    expect(portalUserId).toBeTruthy();

    const [user] = await read(page, 'res.users', [portalUserId], [
      'company_id', 'company_ids',
    ]);

    // company_id is a many2one → [id, name] tuple
    expect(user.company_id).toBeTruthy();
    const companyId = Array.isArray(user.company_id) ? user.company_id[0] : user.company_id;
    expect(companyId).toBeGreaterThan(0);

    // company_ids is a many2many → array of IDs
    expect(Array.isArray(user.company_ids)).toBe(true);
    expect(user.company_ids.length).toBeGreaterThanOrEqual(1);
    expect(user.company_ids).toContain(companyId);

    console.log(
      `[OK] L6: user company_id=${companyId}, company_ids=${JSON.stringify(user.company_ids)}`,
    );
  });

  // =================================================================
  // L7: Second attempt finds existing user (idempotency check)
  //     Mirrors _create_portal_user's "existing = Users.search(...)" guard
  // =================================================================
  test('L7: Searching for same login returns the existing user (idempotent)', async ({ page }) => {
    await loginAsAdmin(page);
    expect(portalUserId).toBeTruthy();

    // Search by login — same as _create_portal_user does before creating
    const users = await searchRead(
      page,
      'res.users',
      [['login', '=', LOGIN_EMAIL]],
      ['id', 'login', 'partner_id'],
      2,  // limit=2 to detect duplicates
    );

    // Exactly one user with this login must exist
    expect(users.length).toBe(1);
    expect(users[0].id).toBe(portalUserId);
    expect(users[0].login).toBe(LOGIN_EMAIL);

    // Partner link is intact
    const linkedPartnerId = Array.isArray(users[0].partner_id)
      ? users[0].partner_id[0]
      : users[0].partner_id;
    expect(linkedPartnerId).toBe(partnerId);

    console.log(
      `[OK] L7: search for login=${LOGIN_EMAIL} returns exactly 1 user id=${portalUserId}`,
    );
  });

  // =================================================================
  // L8: Full chain integrity — line.user -> partner -> user linked
  // =================================================================
  test('L8: Full chain integrity: line.user -> partner -> portal user', async ({ page }) => {
    await loginAsAdmin(page);
    expect(lineUserId).toBeTruthy();
    expect(partnerId).toBeTruthy();
    expect(portalUserId).toBeTruthy();

    // Read line.user -> partner_id
    const [lu] = await read(page, 'line.user', [lineUserId], ['partner_id', 'line_user_id']);
    const luPartnerId = Array.isArray(lu.partner_id) ? lu.partner_id[0] : lu.partner_id;
    expect(luPartnerId).toBe(partnerId);

    // Read partner -> user (via res.users search)
    const users = await searchRead(
      page,
      'res.users',
      [['partner_id', '=', partnerId]],
      ['id', 'login'],
      1,
    );
    expect(users.length).toBe(1);
    expect(users[0].id).toBe(portalUserId);
    expect(users[0].login).toBe(LOGIN_EMAIL);

    // Read user -> partner_id (reverse check)
    const [usr] = await read(page, 'res.users', [portalUserId], ['partner_id']);
    const usrPartnerId = Array.isArray(usr.partner_id) ? usr.partner_id[0] : usr.partner_id;
    expect(usrPartnerId).toBe(partnerId);

    console.log(
      `[OK] L8: Chain verified: line.user(${lineUserId}) -> partner(${partnerId}) -> user(${portalUserId})`,
    );
  });

});
