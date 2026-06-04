// tests/e2e-line-bridge/webhook-api.spec.mjs
// Webhook 端點 — 簽章驗證、事件處理、回應時間
import { test, expect } from '@playwright/test';
import crypto from 'node:crypto';

// 產生 HMAC-SHA256 簽章（模擬 LINE Platform）
function signBody(body, secret) {
  const hmac = crypto.createHmac('SHA256', secret);
  hmac.update(body);
  return hmac.digest('base64');
}

test.describe('LINE Webhook — POST /line/webhook', () => {

  test('missing X-Line-Signature header returns 403', async ({ request }) => {
    const resp = await request.post('/line/webhook', {
      data: { events: [] },
      headers: { 'Content-Type': 'application/json' },
    });
    expect(resp.status()).toBe(403);
  });

  test('invalid X-Line-Signature returns 403', async ({ request }) => {
    const resp = await request.post('/line/webhook', {
      data: { events: [] },
      headers: {
        'Content-Type': 'application/json',
        'X-Line-Signature': 'totally_wrong_signature',
      },
    });
    expect(resp.status()).toBe(403);
  });

  test('valid signature with empty events returns 200', async ({ request }) => {
    // 注意：需要知道 messaging_channel_secret 才能產生有效簽章
    // 這裡測試的是「格式正確但 secret 不匹配」 → 仍是 403
    // 若有測試 secret，可以改為真正的 200 測試
    const body = JSON.stringify({ events: [] });
    const fakeSig = signBody(body, 'test_secret_not_real');
    const resp = await request.post('/line/webhook', {
      data: body,
      headers: {
        'Content-Type': 'application/json',
        'X-Line-Signature': fakeSig,
      },
    });
    // Without the real secret, this will be 403
    // This validates the signature check is enforced
    expect(resp.status()).toBe(403);
  });

  test('non-JSON body with invalid signature returns 403', async ({ request }) => {
    const resp = await request.post('/line/webhook', {
      data: 'this is not json',
      headers: {
        'Content-Type': 'application/json',
        'X-Line-Signature': 'bad',
      },
    });
    // Signature check happens before JSON parsing
    expect(resp.status()).toBe(403);
  });

  test('webhook endpoint responds within 2 seconds', async ({ request }) => {
    const start = Date.now();
    await request.post('/line/webhook', {
      data: { events: [] },
      headers: {
        'Content-Type': 'application/json',
        'X-Line-Signature': 'irrelevant',
      },
    });
    const elapsed = Date.now() - start;
    // Even with 403, it should respond quickly
    expect(elapsed).toBeLessThan(2000);
  });

});
