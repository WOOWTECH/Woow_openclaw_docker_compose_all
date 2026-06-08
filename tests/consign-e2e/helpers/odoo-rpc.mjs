// Odoo 18 JSON-RPC helper for Playwright tests
const BASE = process.env.ODOO_BASE_URL || 'https://markstudio-odoo.woowtech.io';
const ADMIN_LOGIN = process.env.ODOO_ADMIN_LOGIN || 'admin';
const ADMIN_PASSWORD = process.env.ODOO_ADMIN_PASSWORD || 'admin';

export { BASE, ADMIN_LOGIN, ADMIN_PASSWORD };

/** Login as admin, navigate to backend */
export async function loginAsAdmin(page) {
  await page.goto(`${BASE}/web/login`);
  await page.fill('input[name="login"]', ADMIN_LOGIN);
  await page.fill('input[name="password"]', ADMIN_PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForURL(url => !url.href.includes('/web/login'), { timeout: 30000 });
  // Ensure we are in the backend
  if (!page.url().includes('/odoo')) {
    await page.goto(`${BASE}/odoo`);
    await page.waitForSelector('.o_web_client, .o_action_manager', { timeout: 15000 });
  }
}

/** Login as a specific user */
export async function loginAs(page, login, password) {
  await page.goto(`${BASE}/web/login`);
  await page.fill('input[name="login"]', login);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL(url => !url.href.includes('/web/login'), { timeout: 30000 });
}

/** Generic JSON-RPC call via page.evaluate */
export async function rpcCall(page, model, method, args = [], kwargs = {}) {
  const result = await page.evaluate(
    async ({ model, method, args, kwargs }) => {
      const res = await fetch(`/web/dataset/call_kw/${model}/${method}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: Math.floor(Math.random() * 1e8),
          method: 'call',
          params: { model, method, args, kwargs },
        }),
      });
      const json = await res.json();
      if (json.error) return { __rpc_error__: true, error: json.error };
      return json.result;
    },
    { model, method, args, kwargs },
  );
  if (result && result.__rpc_error__) {
    const err = new Error(`RPC ${model}.${method} failed: ${result.error?.data?.message || result.error?.message || JSON.stringify(result.error)}`);
    err.rpcError = result.error;
    throw err;
  }
  return result;
}

/** Convenience: search_read */
export async function searchRead(page, model, domain, fields, limit = 100) {
  return rpcCall(page, model, 'search_read', [domain], { fields, limit });
}

/** Convenience: create (returns array of IDs) */
export async function create(page, model, vals) {
  return rpcCall(page, model, 'create', [vals]);
}

/** Convenience: write */
export async function write(page, model, ids, vals) {
  return rpcCall(page, model, 'write', [ids, vals]);
}

/** Convenience: unlink */
export async function unlink(page, model, ids) {
  return rpcCall(page, model, 'unlink', [ids]);
}

/** Convenience: read */
export async function read(page, model, ids, fields) {
  return rpcCall(page, model, 'read', [ids], { fields });
}

/** Call a button/action method on records */
export async function callButton(page, model, method, ids) {
  return rpcCall(page, model, method, [ids]);
}

/** Try to unlink, ignore errors */
export async function safeUnlink(page, model, ids) {
  try {
    if (ids && ids.length) await unlink(page, model, ids);
  } catch { /* ignore cleanup errors */ }
}
