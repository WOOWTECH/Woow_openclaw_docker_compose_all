// tests/e2e-line-bridge/liff-api.spec.mjs
// LIFF JSON API 端點 — token 驗證、回應格式
import { test, expect } from '@playwright/test';

test.describe('LIFF API Endpoints', () => {

  test('POST /api/line/me without token returns 401', async ({ request }) => {
    const resp = await request.post('/api/line/me', {
      data: {},
      headers: { 'Content-Type': 'application/json' },
    });
    // Should be 401 or error response
    const status = resp.status();
    expect([400, 401]).toContain(status);
    const body = await resp.json();
    expect(body).toHaveProperty('error');
  });

  test('POST /api/line/bind without token returns error', async ({ request }) => {
    const resp = await request.post('/api/line/bind', {
      data: {},
      headers: { 'Content-Type': 'application/json' },
    });
    const status = resp.status();
    expect([400, 401]).toContain(status);
    const body = await resp.json();
    expect(body).toHaveProperty('error');
  });

  test('POST /api/line/notification/toggle without token returns error', async ({ request }) => {
    const resp = await request.post('/api/line/notification/toggle', {
      data: { enabled: true },
      headers: { 'Content-Type': 'application/json' },
    });
    const status = resp.status();
    expect([400, 401]).toContain(status);
    const body = await resp.json();
    expect(body).toHaveProperty('error');
  });

  test('API responses have application/json content-type', async ({ request }) => {
    const resp = await request.post('/api/line/me', {
      data: {},
      headers: { 'Content-Type': 'application/json' },
    });
    const contentType = resp.headers()['content-type'] || '';
    expect(contentType).toContain('application/json');
  });

});
