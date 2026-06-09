// tests/line-integration/16-webhook.spec.mjs
// C1-C7: Webhook endpoint handling tests
import { test, expect } from '@playwright/test';
import crypto from 'node:crypto';
import {
  loginAsAdmin, rpcCall, searchRead, BASE,
} from './helpers/odoo-rpc.mjs';

/**
 * Generate HMAC-SHA256 signature (simulates LINE Platform signing).
 * @param {string} body - The raw request body
 * @param {string} secret - The channel secret
 * @returns {string} Base64-encoded signature
 */
function signBody(body, secret) {
  const hmac = crypto.createHmac('SHA256', secret);
  hmac.update(body);
  return hmac.digest('base64');
}

test.describe('C: LINE Webhook — POST /line/webhook', () => {

  // C1: POST /line/webhook with empty body returns 200 (graceful) or 403 (sig check)
  test('C1: POST /line/webhook with empty body returns graceful response (not 500)', async ({ request }) => {
    const resp = await request.post(`${BASE}/line/webhook`, {
      data: JSON.stringify({ events: [] }),
      headers: {
        'Content-Type': 'application/json',
      },
    });
    const status = resp.status();
    // Without X-Line-Signature, should get 403 (signature required)
    // The key thing is it does NOT crash with 500
    expect(status).not.toBe(500);
    expect([200, 400, 403]).toContain(status);
    console.log(`[OK] C1: POST /line/webhook with empty body returns ${status} (not 500)`);
  });

  // C2: POST /line/webhook with invalid X-Line-Signature returns 403
  test('C2: POST /line/webhook with invalid X-Line-Signature returns 403', async ({ request }) => {
    const body = JSON.stringify({ events: [] });
    const resp = await request.post(`${BASE}/line/webhook`, {
      data: body,
      headers: {
        'Content-Type': 'application/json',
        'X-Line-Signature': 'totally_invalid_signature_base64==',
      },
    });
    expect(resp.status()).toBe(403);
    console.log('[OK] C2: Invalid X-Line-Signature returns 403');
  });

  // C3: POST with fake but properly formatted signature still rejected (wrong secret)
  test('C3: POST with HMAC-signed body using wrong secret returns 403', async ({ request }) => {
    const body = JSON.stringify({ events: [] });
    const fakeSig = signBody(body, 'this_is_not_the_real_secret');
    const resp = await request.post(`${BASE}/line/webhook`, {
      data: body,
      headers: {
        'Content-Type': 'application/json',
        'X-Line-Signature': fakeSig,
      },
    });
    // Signature check should reject because the secret doesn't match
    expect(resp.status()).toBe(403);
    console.log('[OK] C3: HMAC with wrong secret correctly rejected (403)');
  });

  // C4: Webhook endpoint responds quickly (< 2 seconds)
  test('C4: Webhook endpoint responds within 2 seconds', async ({ request }) => {
    const start = Date.now();
    await request.post(`${BASE}/line/webhook`, {
      data: JSON.stringify({ events: [] }),
      headers: {
        'Content-Type': 'application/json',
        'X-Line-Signature': 'irrelevant',
      },
    });
    const elapsed = Date.now() - start;
    expect(elapsed).toBeLessThan(2000);
    console.log(`[OK] C4: Webhook responded in ${elapsed}ms (< 2000ms)`);
  });

  // C5: Non-JSON body with signature header returns 403 (signature checked first)
  test('C5: Non-JSON body with invalid signature returns 403', async ({ request }) => {
    const resp = await request.post(`${BASE}/line/webhook`, {
      data: 'this is not JSON at all',
      headers: {
        'Content-Type': 'application/json',
        'X-Line-Signature': 'bad_sig',
      },
    });
    // Signature check happens before JSON parsing
    expect(resp.status()).toBe(403);
    console.log('[OK] C5: Non-JSON body with bad signature returns 403 (sig check first)');
  });

  // C6: line.event.log model exists and is searchable (requires admin login)
  test('C6: line.event.log model exists and is queryable via RPC', async ({ page }) => {
    await loginAsAdmin(page);

    // Verify the model is accessible by attempting a search_read
    const logs = await searchRead(page, 'line.event.log', [], [
      'event_type', 'message_type', 'line_user_id', 'processed', 'create_date',
    ], 5);

    // The model should be queryable (even if no records exist yet)
    expect(Array.isArray(logs)).toBe(true);
    console.log(`[OK] C6: line.event.log is queryable, found ${logs.length} existing records`);
  });

  // C7: line.event.log has correct field definitions
  test('C7: line.event.log fields match expected schema', async ({ page }) => {
    await loginAsAdmin(page);

    const fields = await rpcCall(page, 'line.event.log', 'fields_get', [], {
      attributes: ['string', 'type'],
    });

    // Verify essential fields exist
    expect(fields).toHaveProperty('event_type');
    expect(fields.event_type.type).toBe('selection');

    expect(fields).toHaveProperty('message_type');
    expect(fields.message_type.type).toBe('selection');

    expect(fields).toHaveProperty('line_user_id');
    expect(fields.line_user_id.type).toBe('many2one');

    expect(fields).toHaveProperty('raw_payload');
    expect(fields.raw_payload.type).toBe('text');

    expect(fields).toHaveProperty('text_content');
    expect(fields.text_content.type).toBe('char');

    expect(fields).toHaveProperty('processed');
    expect(fields.processed.type).toBe('boolean');

    expect(fields).toHaveProperty('error_msg');
    expect(fields.error_msg.type).toBe('text');

    console.log('[OK] C7: line.event.log has all expected fields with correct types');
  });

});
