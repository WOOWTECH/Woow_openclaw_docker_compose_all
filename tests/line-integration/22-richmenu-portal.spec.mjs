// tests/line-integration/22-richmenu-portal.spec.mjs
// I1-I12: Rich Menu liff_portal action type, alias integration, field visibility
import { test, expect } from '@playwright/test';
import {
  loginAsAdmin, rpcCall, searchRead, create, read, write, safeUnlink, BASE,
} from './helpers/odoo-rpc.mjs';

test.describe('I: Rich Menu — Portal Action, Alias, Field Validation', () => {

  const createdMenuIds = [];
  const createdAreaIds = [];
  const createdAliasIds = [];

  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    try { await loginAsAdmin(page); } finally { await page.close(); }
  });

  test.afterAll(async ({ browser }) => {
    const page = await browser.newPage();
    try {
      await loginAsAdmin(page);
      await safeUnlink(page, 'line.richmenu.alias', createdAliasIds);
      await safeUnlink(page, 'line.richmenu.area', createdAreaIds);
      await safeUnlink(page, 'line.richmenu', createdMenuIds);
      console.log(`[CLEANUP] Removed ${createdMenuIds.length} menus, ${createdAreaIds.length} areas, ${createdAliasIds.length} aliases`);
    } finally { await page.close(); }
  });

  // ── I1: liff_portal action_type exists in selection ──
  test('I1: action_type selection includes liff_portal', async ({ page }) => {
    await loginAsAdmin(page);

    const fields = await rpcCall(page, 'line.richmenu.area', 'fields_get', [], {
      attributes: ['selection', 'type'],
    });

    expect(fields).toHaveProperty('action_type');
    const options = fields.action_type.selection.map(([k]) => k);
    expect(options).toContain('uri');
    expect(options).toContain('liff_portal');
    expect(options).toContain('message');
    expect(options).toContain('postback');
    expect(options).toContain('datetimepicker');
    expect(options).toContain('richmenuswitch');
    expect(options).toContain('clipboard');

    console.log(`[OK] I1: action_type has 7 options including liff_portal`);
  });

  // ── I2: action_portal_path field exists as char ──
  test('I2: action_portal_path field exists and is char type', async ({ page }) => {
    await loginAsAdmin(page);

    const fields = await rpcCall(page, 'line.richmenu.area', 'fields_get', [], {
      attributes: ['type', 'string'],
    });

    expect(fields).toHaveProperty('action_portal_path');
    expect(fields.action_portal_path.type).toBe('char');

    console.log(`[OK] I2: action_portal_path is char field`);
  });

  // ── I3: Create area with liff_portal action type ──
  test('I3: Create area with liff_portal and /home path', async ({ page }) => {
    await loginAsAdmin(page);

    const menuId = await create(page, 'line.richmenu', {
      name: 'PW Test Portal I3',
      size: 'full',
    });
    createdMenuIds.push(menuId);

    const areaId = await create(page, 'line.richmenu.area', {
      richmenu_id: menuId,
      label: 'Portal Home',
      x: 0, y: 0, width: 833, height: 843,
      action_type: 'liff_portal',
      action_portal_path: '/home',
    });
    expect(areaId).toBeTruthy();
    createdAreaIds.push(areaId);

    const [area] = await read(page, 'line.richmenu.area', [areaId], [
      'action_type', 'action_portal_path', 'label',
    ]);
    expect(area.action_type).toBe('liff_portal');
    expect(area.action_portal_path).toBe('/home');

    console.log(`[OK] I3: liff_portal area created with /home path`);
  });

  // ── I4: Multiple portal paths work ──
  test('I4: Create areas with various portal paths (/book, /my-bookings, /profile)', async ({ page }) => {
    await loginAsAdmin(page);

    const menuId = await create(page, 'line.richmenu', {
      name: 'PW Test Paths I4',
      size: 'full',
    });
    createdMenuIds.push(menuId);

    const paths = ['/book', '/my-bookings', '/profile', '/home'];
    for (const path of paths) {
      const areaId = await create(page, 'line.richmenu.area', {
        richmenu_id: menuId,
        label: `Test ${path}`,
        x: 0, y: 0, width: 833, height: 843,
        action_type: 'liff_portal',
        action_portal_path: path,
      });
      expect(areaId).toBeTruthy();
      createdAreaIds.push(areaId);
    }

    const areas = await searchRead(page, 'line.richmenu.area',
      [['richmenu_id', '=', menuId]],
      ['action_type', 'action_portal_path']);
    expect(areas.length).toBe(4);
    expect(areas.every(a => a.action_type === 'liff_portal')).toBe(true);

    console.log(`[OK] I4: 4 portal areas created with different paths`);
  });

  // ── I5: liff_portal with leading slash stripped correctly ──
  test('I5: Portal path with or without leading slash both work', async ({ page }) => {
    await loginAsAdmin(page);

    const menuId = await create(page, 'line.richmenu', {
      name: 'PW Test Slash I5',
      size: 'full',
    });
    createdMenuIds.push(menuId);

    // With leading slash
    const a1 = await create(page, 'line.richmenu.area', {
      richmenu_id: menuId,
      label: 'Slash',
      x: 0, y: 0, width: 1250, height: 843,
      action_type: 'liff_portal',
      action_portal_path: '/book',
    });
    createdAreaIds.push(a1);

    // Without leading slash
    const a2 = await create(page, 'line.richmenu.area', {
      richmenu_id: menuId,
      label: 'NoSlash',
      x: 1250, y: 0, width: 1250, height: 843,
      action_type: 'liff_portal',
      action_portal_path: 'book',
    });
    createdAreaIds.push(a2);

    const areas = await read(page, 'line.richmenu.area', [a1, a2], ['action_portal_path']);
    expect(areas[0].action_portal_path).toBe('/book');
    expect(areas[1].action_portal_path).toBe('book');

    console.log(`[OK] I5: Both /book and book stored correctly`);
  });

  // ── I6: Empty portal path edge case ──
  test('I6: liff_portal with empty path stores correctly', async ({ page }) => {
    await loginAsAdmin(page);

    const menuId = await create(page, 'line.richmenu', {
      name: 'PW Test Empty I6',
      size: 'full',
    });
    createdMenuIds.push(menuId);

    const areaId = await create(page, 'line.richmenu.area', {
      richmenu_id: menuId,
      label: 'EmptyPath',
      x: 0, y: 0, width: 2500, height: 843,
      action_type: 'liff_portal',
      action_portal_path: '',
    });
    createdAreaIds.push(areaId);

    const [area] = await read(page, 'line.richmenu.area', [areaId], [
      'action_type', 'action_portal_path',
    ]);
    expect(area.action_type).toBe('liff_portal');
    expect(area.action_portal_path).toBeFalsy();

    console.log(`[OK] I6: Empty portal path handled without error`);
  });

  // ── I7: All 7 action types can coexist on same menu ──
  test('I7: Menu with all 7 action types on different areas', async ({ page }) => {
    await loginAsAdmin(page);

    const menuId = await create(page, 'line.richmenu', {
      name: 'PW Test AllTypes I7',
      size: 'full',
    });
    createdMenuIds.push(menuId);

    const types = [
      { action_type: 'uri', action_uri: 'https://example.com' },
      { action_type: 'liff_portal', action_portal_path: '/home' },
      { action_type: 'message', action_text: 'hello' },
      { action_type: 'postback', action_data: 'action=test' },
      { action_type: 'datetimepicker', action_data: 'pick', action_mode: 'date' },
      { action_type: 'richmenuswitch', action_richmenu_alias: 'test-alias', action_data: 'sw' },
      { action_type: 'clipboard', action_clipboard_text: 'COPY' },
    ];

    for (let i = 0; i < types.length; i++) {
      const areaId = await create(page, 'line.richmenu.area', {
        richmenu_id: menuId,
        label: `Type-${types[i].action_type}`,
        x: 0, y: i * 240, width: 2500, height: 240,
        ...types[i],
      });
      createdAreaIds.push(areaId);
    }

    const areas = await searchRead(page, 'line.richmenu.area',
      [['richmenu_id', '=', menuId]], ['action_type']);
    const foundTypes = areas.map(a => a.action_type).sort();
    expect(foundTypes).toEqual([
      'clipboard', 'datetimepicker', 'liff_portal', 'message',
      'postback', 'richmenuswitch', 'uri',
    ]);

    console.log(`[OK] I7: All 7 action types coexist on one menu`);
  });

  // ── I8: alias_ids One2many field exists on line.richmenu ──
  test('I8: line.richmenu has alias_ids One2many field', async ({ page }) => {
    await loginAsAdmin(page);

    const fields = await rpcCall(page, 'line.richmenu', 'fields_get', [], {
      attributes: ['type', 'relation'],
    });

    expect(fields).toHaveProperty('alias_ids');
    expect(fields.alias_ids.type).toBe('one2many');
    expect(fields.alias_ids.relation).toBe('line.richmenu.alias');

    console.log(`[OK] I8: alias_ids is One2many to line.richmenu.alias`);
  });

  // ── I9: Create alias via parent menu's alias_ids ──
  test('I9: Create alias linked to menu and verify reverse relation', async ({ page }) => {
    await loginAsAdmin(page);

    const menuId = await create(page, 'line.richmenu', {
      name: 'PW Test Alias I9',
      size: 'full',
    });
    createdMenuIds.push(menuId);

    const aliasId = await create(page, 'line.richmenu.alias', {
      alias_id: 'pw-test-i9-alias',
      richmenu_id: menuId,
    });
    createdAliasIds.push(aliasId);

    // Verify alias exists
    const [alias] = await read(page, 'line.richmenu.alias', [aliasId], [
      'alias_id', 'richmenu_id',
    ]);
    expect(alias.alias_id).toBe('pw-test-i9-alias');
    expect(alias.richmenu_id[0]).toBe(menuId);

    // Verify reverse relation via menu's alias_ids
    const [menu] = await read(page, 'line.richmenu', [menuId], ['alias_ids']);
    expect(menu.alias_ids).toContain(aliasId);

    console.log(`[OK] I9: Alias created and visible via menu's alias_ids`);
  });

  // ── I10: Unique constraint on alias_id ──
  test('I10: Duplicate alias_id triggers unique constraint error', async ({ page }) => {
    await loginAsAdmin(page);

    const menuId = await create(page, 'line.richmenu', {
      name: 'PW Test Unique I10',
      size: 'full',
    });
    createdMenuIds.push(menuId);

    const aliasId1 = await create(page, 'line.richmenu.alias', {
      alias_id: 'pw-unique-i10',
      richmenu_id: menuId,
    });
    createdAliasIds.push(aliasId1);

    let duplicateError = false;
    try {
      const aliasId2 = await create(page, 'line.richmenu.alias', {
        alias_id: 'pw-unique-i10',
        richmenu_id: menuId,
      });
      createdAliasIds.push(aliasId2);
    } catch (e) {
      duplicateError = true;
    }
    expect(duplicateError).toBe(true);

    console.log(`[OK] I10: Unique constraint on alias_id enforced`);
  });

  // ── I11: liff_portal does not affect action_uri field ──
  test('I11: liff_portal and uri action types use independent fields', async ({ page }) => {
    await loginAsAdmin(page);

    const menuId = await create(page, 'line.richmenu', {
      name: 'PW Test Independence I11',
      size: 'full',
    });
    createdMenuIds.push(menuId);

    // Create portal area — should NOT have action_uri
    const portalId = await create(page, 'line.richmenu.area', {
      richmenu_id: menuId,
      label: 'Portal',
      x: 0, y: 0, width: 1250, height: 843,
      action_type: 'liff_portal',
      action_portal_path: '/home',
    });
    createdAreaIds.push(portalId);

    // Create uri area — should NOT have action_portal_path
    const uriId = await create(page, 'line.richmenu.area', {
      richmenu_id: menuId,
      label: 'URL',
      x: 1250, y: 0, width: 1250, height: 843,
      action_type: 'uri',
      action_uri: 'https://example.com/news',
    });
    createdAreaIds.push(uriId);

    const [portal] = await read(page, 'line.richmenu.area', [portalId], [
      'action_type', 'action_portal_path', 'action_uri',
    ]);
    expect(portal.action_type).toBe('liff_portal');
    expect(portal.action_portal_path).toBe('/home');
    // action_uri may be false/empty for portal type
    expect(portal.action_uri).toBeFalsy();

    const [uri] = await read(page, 'line.richmenu.area', [uriId], [
      'action_type', 'action_portal_path', 'action_uri',
    ]);
    expect(uri.action_type).toBe('uri');
    expect(uri.action_uri).toBe('https://example.com/news');
    expect(uri.action_portal_path).toBeFalsy();

    console.log(`[OK] I11: liff_portal and uri fields are independent`);
  });

  // ── I12: LIFF endpoint /liff/news is still accessible (public page) ──
  test('I12: Public /liff/news endpoint returns 200', async ({ page }) => {
    const resp = await page.goto(`${BASE}/liff/news`, { waitUntil: 'commit' });
    expect(resp.status()).toBe(200);
    const html = await page.content();
    expect(html).toContain('最新消息');

    console.log(`[OK] I12: /liff/news returns 200 with expected content`);
  });

});
