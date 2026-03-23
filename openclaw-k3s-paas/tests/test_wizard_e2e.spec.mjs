import { test, expect } from '@playwright/test';
import { createServer } from 'http';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const TEMPLATE_PATH = join(__dirname, '..', 'setup-wizard', 'templates', 'index.html');
const PORT = 18799; // Test port to avoid conflict

let server;
let setupCalled = false;
let setupBody = {};
let statusStep = 0;
let statusDone = false;
let statusSuccess = false;
let statusMessage = '';

test.beforeAll(async () => {
  const html = readFileSync(TEMPLATE_PATH, 'utf-8');

  server = createServer((req, res) => {
    if (req.method === 'GET' && req.url === '/') {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(html);
    } else if (req.method === 'POST' && req.url === '/setup') {
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        setupCalled = true;
        // Parse multipart/form-data
        const ct = req.headers['content-type'] || '';
        if (ct.includes('multipart/form-data')) {
          const boundary = ct.split('boundary=')[1];
          const parts = body.split('--' + boundary).slice(1, -1);
          for (const part of parts) {
            const match = part.match(/name="([^"]+)"\r\n\r\n([\s\S]*?)\r\n/);
            if (match) setupBody[match[1]] = match[2];
          }
        } else {
          setupBody = Object.fromEntries(new URLSearchParams(body));
        }
        // Simulate async progress
        statusStep = 1;
        setTimeout(() => { statusStep = 4; }, 500);
        setTimeout(() => { statusStep = 7; statusDone = true; statusSuccess = true; statusMessage = 'https://test.example.com/#token=woowtech'; }, 1000);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, message: 'Setup started.' }));
      });
    } else if (req.method === 'GET' && req.url === '/setup/status') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        running: !statusDone,
        step: statusStep,
        step_label: `Step ${statusStep}`,
        done: statusDone,
        success: statusSuccess,
        error: '',
        message: statusMessage,
      }));
    } else {
      res.writeHead(404);
      res.end('Not Found');
    }
  });

  await new Promise(resolve => server.listen(PORT, resolve));
});

test.afterAll(async () => {
  if (server) server.close();
});

test.beforeEach(() => {
  setupCalled = false;
  setupBody = {};
  statusStep = 0;
  statusDone = false;
  statusSuccess = false;
  statusMessage = '';
});

// ─── TEST 1: Page renders correctly ───
test('homepage renders with all three form sections', async ({ page }) => {
  await page.goto(`http://localhost:${PORT}/`);

  // Brand
  await expect(page.locator('.brand-bar')).toBeVisible();
  await expect(page.locator('text=OpenClaw Setup')).toBeVisible();

  // Core Credentials section
  await expect(page.locator('#gateway_token')).toBeVisible();
  await expect(page.locator('#db_password')).toBeVisible();

  // AI Engine section
  await expect(page.locator('#ai_provider')).toBeVisible();
  await expect(page.locator('.section-title').first()).toBeVisible();

  // Chat Platform info section
  await expect(page.locator('.chat-info-box')).toBeVisible();

  // Submit button
  await expect(page.locator('#submit-btn')).toBeVisible();
  await expect(page.locator('#submit-btn')).toHaveText('Deploy Instance');
});

// ─── TEST 2: AI provider dynamic fields ───
test('AI provider dropdown shows dynamic fields', async ({ page }) => {
  await page.goto(`http://localhost:${PORT}/`);

  // Initially hidden
  const aiKeyField = page.locator('#field-ai-key');
  await expect(aiKeyField).not.toBeVisible();

  // Select OpenAI
  await page.selectOption('#ai_provider', 'openai');
  await expect(aiKeyField).toBeVisible();
  await expect(page.locator('#ai-key-label')).toHaveText('OpenAI API Key');
  await expect(page.locator('#ai_api_key')).toHaveAttribute('placeholder', 'sk-proj-...');

  // Switch to Anthropic
  await page.selectOption('#ai_provider', 'anthropic');
  await expect(page.locator('#ai-key-label')).toHaveText('Anthropic API Key');
  await expect(page.locator('#ai_api_key')).toHaveAttribute('placeholder', 'sk-ant-api03-...');

  // Switch to Google
  await page.selectOption('#ai_provider', 'google');
  await expect(page.locator('#ai-key-label')).toHaveText('Gemini API Key');

  // Switch to Ollama
  await page.selectOption('#ai_provider', 'ollama');
  await expect(page.locator('#ai-key-label')).toHaveText('Ollama Host');

  // Back to empty hides fields
  await page.selectOption('#ai_provider', '');
  await expect(aiKeyField).not.toBeVisible();
});

// ─── TEST 3: Chat platform info box ───
test('Chat platform info box shows supported platforms', async ({ page }) => {
  await page.goto(`http://localhost:${PORT}/`);

  const infoBox = page.locator('.chat-info-box');
  await expect(infoBox).toBeVisible();
  await expect(infoBox).toContainText('WhatsApp');
  await expect(infoBox).toContainText('Telegram');
  await expect(infoBox).toContainText('Discord');
});

// ─── TEST 4: Form validation (empty required fields) ───
test('form requires gateway_token and db_password', async ({ page }) => {
  await page.goto(`http://localhost:${PORT}/`);

  // HTML5 required attribute prevents submission
  const gatewayInput = page.locator('#gateway_token');
  await expect(gatewayInput).toHaveAttribute('required', '');

  const dbInput = page.locator('#db_password');
  await expect(dbInput).toHaveAttribute('required', '');
});

// ─── TEST 5: Full form submission with all fields ───
test('submitting form shows progress then success', async ({ page }) => {
  await page.goto(`http://localhost:${PORT}/`);

  // Fill core credentials
  await page.fill('#gateway_token', 'woowtech');
  await page.fill('#db_password', 'woowtech');

  // Select AI Engine and pick model from dropdown
  await page.selectOption('#ai_provider', 'openai');
  await page.fill('#ai_api_key', 'sk-test-key-12345');
  await page.selectOption('#ai_model_select', 'gpt-4o');

  // Submit
  await page.click('#submit-btn');

  // Form should disappear, progress should show
  await expect(page.locator('#setup-form')).not.toBeVisible();
  await expect(page.locator('#progress-section')).toBeVisible();

  // Wait for success (mock resolves in ~1s)
  await expect(page.locator('#result-success')).toBeVisible({ timeout: 10000 });
  await expect(page.locator('#progress-section')).not.toBeVisible();

  // Dashboard link should be set
  const link = page.locator('#dashboard-link');
  await expect(link).toHaveAttribute('href', 'https://test.example.com/#token=woowtech');

  // Channels link should be set
  const chLink = page.locator('#channels-link');
  await expect(chLink).toHaveAttribute('href', 'https://test.example.com/#channels');

  // Status badges should be visible
  await expect(page.locator('.status-badge.ok').first()).toBeVisible();

  // Verify backend received fields
  expect(setupCalled).toBe(true);
  expect(setupBody.gateway_token).toBe('woowtech');
  expect(setupBody.db_password).toBe('woowtech');
  expect(setupBody.ai_provider).toBe('openai');
  expect(setupBody.ai_api_key).toBe('sk-test-key-12345');
  expect(setupBody.ai_model).toBe('gpt-4o');
});

// ─── TEST 6: Submit button disabled during setup ───
test('submit button is disabled after click', async ({ page }) => {
  await page.goto(`http://localhost:${PORT}/`);

  await page.fill('#gateway_token', 'test');
  await page.fill('#db_password', 'test');
  await page.click('#submit-btn');

  // Button should be disabled
  await expect(page.locator('#submit-btn')).toBeDisabled();
});

// ─── TEST 7: Progress steps render correctly ───
test('progress section shows 7 steps', async ({ page }) => {
  await page.goto(`http://localhost:${PORT}/`);

  const steps = page.locator('.progress-step');
  await expect(steps).toHaveCount(7);

  // Verify step labels
  await expect(steps.nth(0)).toContainText('Creating encryption keys');
  await expect(steps.nth(1)).toContainText('Starting database engine');
  await expect(steps.nth(2)).toContainText('Launching AI gateway');
  await expect(steps.nth(3)).toContainText('Waiting for system readiness');
  await expect(steps.nth(4)).toContainText('Configuring AI');
  await expect(steps.nth(5)).toContainText('Switching network routes');
  await expect(steps.nth(6)).toContainText('Finalizing deployment');
});

// ─── TEST 8: Core-only submission (no AI, no chat) ───
test('form submits with only core credentials', async ({ page }) => {
  await page.goto(`http://localhost:${PORT}/`);

  await page.fill('#gateway_token', 'woowtech');
  await page.fill('#db_password', 'woowtech');

  // Don't select AI or Chat - submit core only
  await page.click('#submit-btn');

  await expect(page.locator('#result-success')).toBeVisible({ timeout: 10000 });

  expect(setupCalled).toBe(true);
  expect(setupBody.gateway_token).toBe('woowtech');
  expect(setupBody.ai_provider).toBe('');
});
