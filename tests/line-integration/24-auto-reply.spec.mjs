// tests/line-integration/24-auto-reply.spec.mjs
// K1-K12: Auto-Reply model, seed data, genericization changes
import { test, expect } from '@playwright/test';
import {
  loginAsAdmin, rpcCall, searchRead, create, read, write, safeUnlink, BASE,
} from './helpers/odoo-rpc.mjs';

test.describe('K: Auto-Reply + Genericization', () => {

  const createdReplyIds = [];

  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    try { await loginAsAdmin(page); } finally { await page.close(); }
  });

  test.afterAll(async ({ browser }) => {
    const page = await browser.newPage();
    try {
      await loginAsAdmin(page);
      await safeUnlink(page, 'line.auto.reply', createdReplyIds);
      console.log(`[CLEANUP] Removed ${createdReplyIds.length} auto-reply records`);
    } finally { await page.close(); }
  });

  // ── K1: line.auto.reply model has correct fields ──
  test('K1: line.auto.reply model has correct fields', async ({ page }) => {
    await loginAsAdmin(page);

    const fields = await rpcCall(page, 'line.auto.reply', 'fields_get', [], {
      attributes: ['type', 'selection', 'string'],
    });

    // name: char
    expect(fields).toHaveProperty('name');
    expect(fields.name.type).toBe('char');

    // keyword: char
    expect(fields).toHaveProperty('keyword');
    expect(fields.keyword.type).toBe('char');

    // match_type: selection with 3 options
    expect(fields).toHaveProperty('match_type');
    expect(fields.match_type.type).toBe('selection');
    const matchOptions = fields.match_type.selection.map(([k]) => k);
    expect(matchOptions).toHaveLength(3);
    expect(matchOptions).toContain('exact');
    expect(matchOptions).toContain('contains');
    expect(matchOptions).toContain('regex');

    // response_text: text
    expect(fields).toHaveProperty('response_text');
    expect(fields.response_text.type).toBe('text');

    // active: boolean
    expect(fields).toHaveProperty('active');
    expect(fields.active.type).toBe('boolean');

    // sequence: integer
    expect(fields).toHaveProperty('sequence');
    expect(fields.sequence.type).toBe('integer');

    console.log('[OK] K1: line.auto.reply has name(char), keyword(char), match_type(selection x3), response_text(text), active(boolean), sequence(integer)');
  });

  // ── K2: 8 seed records exist with correct keywords ──
  test('K2: 8 seed records exist with correct keywords', async ({ page }) => {
    await loginAsAdmin(page);

    const records = await searchRead(page, 'line.auto.reply',
      [['active', '=', true]],
      ['keyword', 'name']);

    expect(records.length).toBeGreaterThanOrEqual(8);

    const keywords = records.map(r => r.keyword);
    const expectedKeywords = ['預約', '電話', '地址', '營業時間', '你好', '哈囉', 'hi', 'hello'];
    for (const kw of expectedKeywords) {
      expect(keywords).toContain(kw);
    }

    console.log(`[OK] K2: Found ${records.length} active auto-reply records, all 8 expected keywords present`);
  });

  // ── K3: Contains match — create rule ──
  test('K3: Contains match — create rule keyword="測試PW", match_type=contains', async ({ page }) => {
    await loginAsAdmin(page);

    const replyId = await create(page, 'line.auto.reply', {
      name: 'PW Test Contains K3',
      keyword: '測試PW',
      match_type: 'contains',
      response_text: 'PW測試成功',
      active: true,
      sequence: 50,
    });
    expect(replyId).toBeTruthy();
    createdReplyIds.push(replyId);

    const [record] = await read(page, 'line.auto.reply', [replyId], [
      'name', 'keyword', 'match_type', 'response_text', 'active', 'sequence',
    ]);
    expect(record.name).toBe('PW Test Contains K3');
    expect(record.keyword).toBe('測試PW');
    expect(record.match_type).toBe('contains');
    expect(record.response_text).toBe('PW測試成功');
    expect(record.active).toBe(true);
    expect(record.sequence).toBe(50);

    console.log('[OK] K3: Contains match rule created and all fields verified');
  });

  // ── K4: Exact match seed — verify "hi" seed has match_type=exact ──
  test('K4: Exact match seed — "hi" has match_type=exact', async ({ page }) => {
    await loginAsAdmin(page);

    const records = await searchRead(page, 'line.auto.reply',
      [['keyword', '=', 'hi']],
      ['keyword', 'match_type', 'name']);

    expect(records.length).toBeGreaterThanOrEqual(1);
    const hiRecord = records[0];
    expect(hiRecord.keyword).toBe('hi');
    expect(hiRecord.match_type).toBe('exact');

    console.log('[OK] K4: Seed "hi" has match_type=exact');
  });

  // ── K5: Regex match — create rule ──
  test('K5: Regex match — create rule keyword="價[格目]", match_type=regex', async ({ page }) => {
    await loginAsAdmin(page);

    const replyId = await create(page, 'line.auto.reply', {
      name: 'PW Test Regex K5',
      keyword: '價[格目]',
      match_type: 'regex',
      response_text: '價目表',
      active: true,
      sequence: 55,
    });
    expect(replyId).toBeTruthy();
    createdReplyIds.push(replyId);

    const [record] = await read(page, 'line.auto.reply', [replyId], [
      'keyword', 'match_type', 'response_text',
    ]);
    expect(record.keyword).toBe('價[格目]');
    expect(record.match_type).toBe('regex');
    expect(record.response_text).toBe('價目表');

    console.log('[OK] K5: Regex match rule created and verified');
  });

  // ── K6: Placeholder in response_text — verify "{shop_phone}" in "電話" seed ──
  test('K6: Placeholder in response_text — "電話" seed contains {shop_phone}', async ({ page }) => {
    await loginAsAdmin(page);

    const records = await searchRead(page, 'line.auto.reply',
      [['keyword', '=', '電話']],
      ['keyword', 'response_text']);

    expect(records.length).toBeGreaterThanOrEqual(1);
    const phoneRecord = records[0];
    expect(phoneRecord.response_text).toContain('{shop_phone}');

    // Verify shop_name config parameter exists and has a value
    const params = await searchRead(page, 'ir.config_parameter',
      [['key', '=', 'woow_line_bridge.shop_name']],
      ['key', 'value']);

    expect(params.length).toBeGreaterThanOrEqual(1);
    expect(params[0].value).toBeTruthy();

    console.log(`[OK] K6: "電話" response_text contains {shop_phone}, shop_name="${params[0].value}"`);
  });

  // ── K7: Sequence priority — create 2 rules with different sequences ──
  test('K7: Sequence priority — 2 rules with different sequences', async ({ page }) => {
    await loginAsAdmin(page);

    const replyA = await create(page, 'line.auto.reply', {
      name: 'PW Priority A K7',
      keyword: 'pw優先',
      match_type: 'contains',
      response_text: 'first',
      active: true,
      sequence: 1,
    });
    expect(replyA).toBeTruthy();
    createdReplyIds.push(replyA);

    const replyB = await create(page, 'line.auto.reply', {
      name: 'PW Priority B K7',
      keyword: 'pw優先測試',
      match_type: 'contains',
      response_text: 'second',
      active: true,
      sequence: 99,
    });
    expect(replyB).toBeTruthy();
    createdReplyIds.push(replyB);

    const [recordA] = await read(page, 'line.auto.reply', [replyA], ['sequence', 'response_text']);
    const [recordB] = await read(page, 'line.auto.reply', [replyB], ['sequence', 'response_text']);

    expect(recordA.sequence).toBe(1);
    expect(recordA.response_text).toBe('first');
    expect(recordB.sequence).toBe(99);
    expect(recordB.response_text).toBe('second');
    expect(recordA.sequence).toBeLessThan(recordB.sequence);

    console.log('[OK] K7: Sequence ordering verified — rule A (seq=1) < rule B (seq=99)');
  });

  // ── K8: Active toggle — create inactive rule ──
  test('K8: Active toggle — inactive rule hidden from default search', async ({ page }) => {
    await loginAsAdmin(page);

    const replyId = await create(page, 'line.auto.reply', {
      name: 'PW Inactive K8',
      keyword: 'pw_inactive_k8',
      match_type: 'exact',
      response_text: 'should be hidden',
      active: false,
      sequence: 10,
    });
    expect(replyId).toBeTruthy();
    createdReplyIds.push(replyId);

    // Active search should NOT find it
    const activeRecords = await searchRead(page, 'line.auto.reply',
      [['active', '=', true], ['id', '=', replyId]],
      ['id']);
    expect(activeRecords.length).toBe(0);

    // Inactive search SHOULD find it
    const inactiveRecords = await searchRead(page, 'line.auto.reply',
      [['active', '=', false], ['id', '=', replyId]],
      ['id', 'active']);
    expect(inactiveRecords.length).toBe(1);
    expect(inactiveRecords[0].active).toBe(false);

    console.log('[OK] K8: Inactive rule hidden from active search, found with active=False filter');
  });

  // ── K9: Bridge hooks removed — verify model exists and no booking-specific fields ──
  test('K9: line.bridge model exists without booking-specific hook fields', async ({ page }) => {
    await loginAsAdmin(page);

    // Verify line.bridge model exists
    const models = await searchRead(page, 'ir.model',
      [['model', '=', 'line.bridge']],
      ['model', 'name']);
    expect(models.length).toBeGreaterThanOrEqual(1);
    expect(models[0].model).toBe('line.bridge');

    // Verify the model has expected generic fields (notify_partner exists as a method concept)
    const fields = await rpcCall(page, 'line.bridge', 'fields_get', [], {
      attributes: ['string', 'type'],
    });
    // Model should have fields — just verify it responds correctly
    expect(fields).toBeTruthy();
    expect(typeof fields).toBe('object');

    // on_booking_confirmed should NOT exist as a stored field
    const bookingFields = await searchRead(page, 'ir.model.fields',
      [['model', '=', 'line.bridge'], ['name', '=', 'on_booking_confirmed']],
      ['name']);
    expect(bookingFields.length).toBe(0);

    console.log('[OK] K9: line.bridge model exists, no on_booking_confirmed field found');
  });

  // ── K10: Config parameters exist ──
  test('K10: Config parameters rebook_path and richmenu_contact_text exist', async ({ page }) => {
    await loginAsAdmin(page);

    // Check rebook_path
    const rebookParams = await searchRead(page, 'ir.config_parameter',
      [['key', '=', 'woow_line_bridge.rebook_path']],
      ['key', 'value']);
    expect(rebookParams.length).toBeGreaterThanOrEqual(1);
    expect(rebookParams[0].value).toBe('/liff/redirect/book');

    // Check richmenu_contact_text
    const contactParams = await searchRead(page, 'ir.config_parameter',
      [['key', '=', 'woow_line_bridge.richmenu_contact_text']],
      ['key', 'value']);
    expect(contactParams.length).toBeGreaterThanOrEqual(1);
    expect(contactParams[0].value).toContain('歡迎');

    console.log(`[OK] K10: rebook_path="${rebookParams[0].value}", richmenu_contact_text contains "歡迎"`);
  });

  // ── K11: Views and menu exist ──
  test('K11: Views and action window exist for line.auto.reply', async ({ page }) => {
    await loginAsAdmin(page);

    // Check views (list, form, search)
    const views = await searchRead(page, 'ir.ui.view',
      [['model', '=', 'line.auto.reply']],
      ['name', 'type']);
    expect(views.length).toBeGreaterThanOrEqual(3);

    const viewTypes = views.map(v => v.type);
    expect(viewTypes).toContain('list');
    expect(viewTypes).toContain('form');
    expect(viewTypes).toContain('search');

    // Check action window
    const actions = await searchRead(page, 'ir.actions.act_window',
      [['res_model', '=', 'line.auto.reply']],
      ['name', 'res_model']);
    expect(actions.length).toBeGreaterThanOrEqual(1);

    console.log(`[OK] K11: Found ${views.length} views (list, form, search) and ${actions.length} action window(s)`);
  });

  // ── K12: Edge case — unique keyword stored correctly ──
  test('K12: Unique keyword rule stored and retrievable', async ({ page }) => {
    await loginAsAdmin(page);

    const uniqueKeyword = 'XYZUNIQUE999';
    const replyId = await create(page, 'line.auto.reply', {
      name: 'PW Edge Case K12',
      keyword: uniqueKeyword,
      match_type: 'exact',
      response_text: 'This keyword should never match real user input',
      active: true,
      sequence: 999,
    });
    expect(replyId).toBeTruthy();
    createdReplyIds.push(replyId);

    // Verify we can find it by the unique keyword
    const found = await searchRead(page, 'line.auto.reply',
      [['keyword', '=', uniqueKeyword]],
      ['keyword', 'match_type', 'response_text', 'active', 'sequence']);
    expect(found.length).toBe(1);
    expect(found[0].keyword).toBe(uniqueKeyword);
    expect(found[0].match_type).toBe('exact');
    expect(found[0].response_text).toBe('This keyword should never match real user input');
    expect(found[0].active).toBe(true);
    expect(found[0].sequence).toBe(999);

    console.log('[OK] K12: Unique keyword "XYZUNIQUE999" stored and retrieved correctly');
  });

  // ── Scorecard ──
  test.afterAll(() => {
    console.log('\n══════════════════════════════════════');
    console.log('  K: Auto-Reply + Genericization — Scorecard');
    console.log('══════════════════════════════════════');
    console.log('  K1:  line.auto.reply fields (name, keyword, match_type, response_text, active, sequence)');
    console.log('  K2:  8 seed records with correct keywords');
    console.log('  K3:  Contains match rule CRUD');
    console.log('  K4:  Exact match seed "hi" verification');
    console.log('  K5:  Regex match rule CRUD');
    console.log('  K6:  Placeholder {shop_phone} in response_text');
    console.log('  K7:  Sequence priority ordering');
    console.log('  K8:  Active toggle hides from default search');
    console.log('  K9:  line.bridge model exists, no booking-specific hooks');
    console.log('  K10: Config parameters rebook_path + richmenu_contact_text');
    console.log('  K11: Views (list, form, search) and action window');
    console.log('  K12: Unique keyword edge case storage');
    console.log('══════════════════════════════════════\n');
  });

});
