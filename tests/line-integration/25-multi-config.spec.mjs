// tests/line-integration/25-multi-config.spec.mjs
// N1-N15: Multi-LIFF-Config architecture + per-config routing
import { test, expect } from '@playwright/test';
import {
  loginAsAdmin, rpcCall, searchRead, create, read, write, safeUnlink, BASE,
} from './helpers/odoo-rpc.mjs';

test.describe('N: Multi-LIFF-Config Architecture', () => {

  const createdConfigIds = [];
  const createdUserIds = [];

  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    try { await loginAsAdmin(page); } finally { await page.close(); }
  });

  test.afterAll(async ({ browser }) => {
    const page = await browser.newPage();
    try {
      await loginAsAdmin(page);
      await safeUnlink(page, 'line.user', createdUserIds);
      await safeUnlink(page, 'line.liff.config', createdConfigIds);
    } finally { await page.close(); }
  });

  // ── N1: line.liff.config model exists with all expected fields ──
  test('N1: line.liff.config has all credential, LIFF, shop, and behavior fields', async ({ page }) => {
    await loginAsAdmin(page);
    const fields = await rpcCall(page, 'line.liff.config', 'fields_get', [], { attributes: ['type', 'string'] });

    // Credentials
    expect(fields).toHaveProperty('messaging_channel_id');
    expect(fields).toHaveProperty('messaging_channel_secret');
    expect(fields).toHaveProperty('messaging_access_token');
    expect(fields).toHaveProperty('login_channel_id');
    expect(fields).toHaveProperty('login_channel_secret');

    // LIFF
    expect(fields).toHaveProperty('liff_id_member');
    expect(fields).toHaveProperty('liff_id_news');
    expect(fields).toHaveProperty('liff_id_locations');

    // Shop
    expect(fields).toHaveProperty('shop_name');
    expect(fields).toHaveProperty('shop_address');
    expect(fields).toHaveProperty('shop_phone');
    expect(fields).toHaveProperty('shop_latitude');
    expect(fields).toHaveProperty('shop_longitude');
    expect(fields).toHaveProperty('shop_opening_hours');

    // Behavior
    expect(fields).toHaveProperty('auto_line_notify');
    expect(fields).toHaveProperty('admin_line_user_id');
    expect(fields).toHaveProperty('rebook_path');
    expect(fields).toHaveProperty('richmenu_contact_text');

    // Computed
    expect(fields).toHaveProperty('webhook_url');
    expect(fields.webhook_url.type).toBe('char');

    console.log(`[OK] N1: line.liff.config has ${Object.keys(fields).length} fields`);
  });

  // ── N2: Create config record ──
  test('N2: Create line.liff.config with all fields', async ({ page }) => {
    await loginAsAdmin(page);
    const cfgId = await create(page, 'line.liff.config', {
      name: 'PW Test Config N2',
      messaging_channel_id: 'CH_TEST_001',
      messaging_channel_secret: 'secret_test',
      messaging_access_token: 'token_test',
      login_channel_id: 'LOGIN_TEST_001',
      login_channel_secret: 'login_secret',
      liff_id_member: '9999-TESTLIFF',
      shop_name: 'PW Test Shop',
      shop_phone: '02-1234-5678',
      auto_line_notify: true,
      rebook_path: '/liff/redirect/book',
    });
    expect(cfgId).toBeTruthy();
    createdConfigIds.push(cfgId);

    const [cfg] = await read(page, 'line.liff.config', [cfgId], [
      'name', 'messaging_channel_id', 'liff_id_member', 'shop_name', 'auto_line_notify',
    ]);
    expect(cfg.name).toBe('PW Test Config N2');
    expect(cfg.messaging_channel_id).toBe('CH_TEST_001');
    expect(cfg.liff_id_member).toBe('9999-TESTLIFF');
    expect(cfg.shop_name).toBe('PW Test Shop');
    expect(cfg.auto_line_notify).toBe(true);

    console.log(`[OK] N2: Config created id=${cfgId}`);
  });

  // ── N3: Multiple configs can coexist ──
  test('N3: Create second config — both coexist', async ({ page }) => {
    await loginAsAdmin(page);
    const cfg2 = await create(page, 'line.liff.config', {
      name: 'PW Test Config N3 Second',
      messaging_channel_id: 'CH_TEST_002',
      shop_name: 'PW Second Shop',
    });
    createdConfigIds.push(cfg2);

    const allConfigs = await searchRead(page, 'line.liff.config',
      [['name', 'like', 'PW Test Config N']],
      ['name']);
    expect(allConfigs.length).toBe(2);

    console.log(`[OK] N3: Two configs coexist`);
  });

  // ── N4: line.user has messaging_channel_id field (from base) ──
  test('N4: line.user has messaging_channel_id and messaging_channel_name', async ({ page }) => {
    await loginAsAdmin(page);
    const fields = await rpcCall(page, 'line.user', 'fields_get', [], { attributes: ['type'] });
    expect(fields).toHaveProperty('messaging_channel_id');
    expect(fields.messaging_channel_id.type).toBe('char');
    expect(fields).toHaveProperty('messaging_channel_name');
    expect(fields.messaging_channel_name.type).toBe('char');

    console.log(`[OK] N4: line.user has messaging channel fields`);
  });

  // ── N5: line.user has liff_config_id field (from bridge) ──
  test('N5: line.user has liff_config_id many2one', async ({ page }) => {
    await loginAsAdmin(page);
    const fields = await rpcCall(page, 'line.user', 'fields_get', [], { attributes: ['type', 'relation'] });
    expect(fields).toHaveProperty('liff_config_id');
    expect(fields.liff_config_id.type).toBe('many2one');
    expect(fields.liff_config_id.relation).toBe('line.liff.config');

    console.log(`[OK] N5: line.user.liff_config_id → line.liff.config`);
  });

  // ── N6: line.richmenu has config_id ──
  test('N6: line.richmenu has config_id field', async ({ page }) => {
    await loginAsAdmin(page);
    const fields = await rpcCall(page, 'line.richmenu', 'fields_get', [], { attributes: ['type', 'relation'] });
    expect(fields).toHaveProperty('config_id');
    expect(fields.config_id.relation).toBe('line.liff.config');

    console.log(`[OK] N6: line.richmenu.config_id exists`);
  });

  // ── N7: line.news has config_id ──
  test('N7: line.news has config_id field', async ({ page }) => {
    await loginAsAdmin(page);
    const fields = await rpcCall(page, 'line.news', 'fields_get', [], { attributes: ['type'] });
    expect(fields).toHaveProperty('config_id');

    console.log(`[OK] N7: line.news.config_id exists`);
  });

  // ── N8: line.auto.reply has config_id (optional) ──
  test('N8: line.auto.reply has optional config_id', async ({ page }) => {
    await loginAsAdmin(page);
    const fields = await rpcCall(page, 'line.auto.reply', 'fields_get', [], { attributes: ['type', 'required'] });
    expect(fields).toHaveProperty('config_id');
    // auto.reply config_id is optional (not required)
    expect(fields.config_id.required).toBeFalsy();

    console.log(`[OK] N8: line.auto.reply.config_id exists (optional)`);
  });

  // ── N9: line.event.log has config_id ──
  test('N9: line.event.log has config_id field', async ({ page }) => {
    await loginAsAdmin(page);
    const fields = await rpcCall(page, 'line.event.log', 'fields_get', [], { attributes: ['type'] });
    expect(fields).toHaveProperty('config_id');

    console.log(`[OK] N9: line.event.log.config_id exists`);
  });

  // ── N10: line.push.log has config_id ──
  test('N10: line.push.log has config_id field', async ({ page }) => {
    await loginAsAdmin(page);
    const fields = await rpcCall(page, 'line.push.log', 'fields_get', [], { attributes: ['type'] });
    expect(fields).toHaveProperty('config_id');

    console.log(`[OK] N10: line.push.log.config_id exists`);
  });

  // ── N11: Webhook /line/webhook still returns 403 (backward compat) ──
  test('N11: Webhook /line/webhook (no config) returns 403 without signature', async ({ request }) => {
    const resp = await request.post(`${BASE}/line/webhook`, {
      data: JSON.stringify({ events: [] }),
      headers: { 'Content-Type': 'application/json' },
    });
    expect(resp.status()).toBe(403);

    console.log(`[OK] N11: /line/webhook returns 403 (no signature)`);
  });

  // ── N12: Webhook /line/webhook/999 fallbacks to default config (403 = sig check) ──
  test('N12: Webhook /line/webhook/999 fallbacks to default config (403 sig fail)', async ({ request }) => {
    const resp = await request.post(`${BASE}/line/webhook/999`, {
      data: JSON.stringify({ events: [] }),
      headers: { 'Content-Type': 'application/json' },
    });
    // Non-existent config_id now falls back to default config → signature verification → 403
    expect(resp.status()).toBe(403);

    console.log(`[OK] N12: /line/webhook/999 fallbacks to default → 403 (sig fail)`);
  });

  // ── N13: LIFF redirect endpoint still works ──
  test('N13: LIFF redirect /liff/redirect/home returns 200', async ({ page }) => {
    const resp = await page.goto(`${BASE}/liff/redirect/home`, { waitUntil: 'commit' });
    expect(resp.status()).toBe(200);

    console.log(`[OK] N13: /liff/redirect/home returns 200`);
  });

  // ── N14: Config views and menu exist ──
  test('N14: line.liff.config has list + form views and action', async ({ page }) => {
    await loginAsAdmin(page);

    const views = await searchRead(page, 'ir.ui.view',
      [['model', '=', 'line.liff.config']],
      ['name', 'type']);
    expect(views.length).toBeGreaterThanOrEqual(2); // list + form

    const actions = await searchRead(page, 'ir.actions.act_window',
      [['res_model', '=', 'line.liff.config']],
      ['name']);
    expect(actions.length).toBeGreaterThanOrEqual(1);

    console.log(`[OK] N14: ${views.length} views + ${actions.length} action(s) for line.liff.config`);
  });

  // ── N15: Create line.user with both messaging_channel and liff_config ──
  test('N15: line.user stores both messaging_channel and liff_config independently', async ({ page }) => {
    await loginAsAdmin(page);

    // Need a config for liff_config_id
    const cfgId = createdConfigIds[0];
    expect(cfgId).toBeTruthy();

    const userId = await create(page, 'line.user', {
      line_user_id: 'U_PW_TEST_N15_' + Date.now(),
      display_name: 'PW Test User N15',
      messaging_channel_id: 'CH_TEST_FROM_WEBHOOK',
      messaging_channel_name: 'Test Webhook Channel',
      liff_config_id: cfgId,
    });
    createdUserIds.push(userId);

    const [user] = await read(page, 'line.user', [userId], [
      'messaging_channel_id', 'messaging_channel_name', 'liff_config_id',
    ]);
    expect(user.messaging_channel_id).toBe('CH_TEST_FROM_WEBHOOK');
    expect(user.messaging_channel_name).toBe('Test Webhook Channel');
    expect(user.liff_config_id[0]).toBe(cfgId);

    console.log(`[OK] N15: line.user has messaging_channel=CH_TEST_FROM_WEBHOOK + liff_config_id=${cfgId}`);
  });
});
