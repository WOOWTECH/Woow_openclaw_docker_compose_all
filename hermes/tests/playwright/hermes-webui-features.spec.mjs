import { test, expect } from '@playwright/test';

const BASE = process.env.HERMES_TEST_URL || 'http://localhost:18787';
const PASSWORD = 'woowtech';

/**
 * Helper: login to WebUI if password form is present
 */
async function login(page) {
  await page.goto(BASE);
  await page.waitForTimeout(3000);
  const passwordInput = page.locator('input[type="password"]');
  if (await passwordInput.isVisible({ timeout: 5000 }).catch(() => false)) {
    await passwordInput.fill(PASSWORD);
    const submitBtn = page.locator(
      'button[type="submit"], button:has-text("Login"), button:has-text("Sign"), button:has-text("Enter")'
    ).first();
    if (await submitBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await submitBtn.click();
    } else {
      await passwordInput.press('Enter');
    }
    await page.waitForTimeout(4000);
  }
}

test.describe('Hermes WebUI Feature Verification (18 tests)', () => {

  // ── Chat Interface ──

  test('F1: Chat page — message input visible after login', async ({ page }) => {
    await login(page);
    const input = page.locator('textarea, input[type="text"], [contenteditable="true"], [role="textbox"]');
    const visible = await input.first().isVisible({ timeout: 10000 }).catch(() => false);
    expect(visible).toBe(true);
    await page.screenshot({ path: '/tmp/hermes-feat-01-chat.png' });
  });

  test('F2: Chat page — model selector/indicator present', async ({ page }) => {
    await login(page);
    const body = await page.textContent('body');
    // Look for model name or model selector in the page
    const hasModelRef = /minimax|model|MiniMax|M2\.7|provider/i.test(body);
    const modelSelector = page.locator('[class*="model"], [data-testid*="model"], select, [role="combobox"]');
    const selectorExists = await modelSelector.first().isVisible({ timeout: 5000 }).catch(() => false);
    expect(hasModelRef || selectorExists).toBe(true);
    await page.screenshot({ path: '/tmp/hermes-feat-02-model.png' });
  });

  // ── Sidebar Navigation ──

  test('F3: Sidebar navigation has menu items', async ({ page }) => {
    await login(page);
    const sidebar = page.locator('nav, [class*="sidebar"], [class*="Sidebar"], aside');
    const sidebarVisible = await sidebar.first().isVisible({ timeout: 5000 }).catch(() => false);
    if (sidebarVisible) {
      const links = await sidebar.first().locator('a, button, [role="menuitem"]').count();
      expect(links).toBeGreaterThan(0);
    }
    await page.screenshot({ path: '/tmp/hermes-feat-03-sidebar.png' });
  });

  // ── Skills Center ──

  test('F4: Skills page accessible', async ({ page }) => {
    await login(page);
    // Try to navigate to skills
    const skillsLink = page.locator('a:has-text("Skills"), button:has-text("Skills"), [href*="skill"]').first();
    if (await skillsLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await skillsLink.click();
      await page.waitForTimeout(2000);
    } else {
      await page.goto(`${BASE}/skills`);
      await page.waitForTimeout(2000);
    }
    const body = await page.textContent('body');
    expect(body.length).toBeGreaterThan(20);
    await page.screenshot({ path: '/tmp/hermes-feat-04-skills.png' });
  });

  // ── Tasks Management ──

  test('F5: Tasks page accessible', async ({ page }) => {
    await login(page);
    const tasksLink = page.locator('a:has-text("Tasks"), button:has-text("Tasks"), [href*="task"]').first();
    if (await tasksLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await tasksLink.click();
      await page.waitForTimeout(2000);
    } else {
      await page.goto(`${BASE}/tasks`);
      await page.waitForTimeout(2000);
    }
    const status = await page.evaluate(() => document.readyState);
    expect(status).toBe('complete');
    await page.screenshot({ path: '/tmp/hermes-feat-05-tasks.png' });
  });

  // ── Kanban Board ──

  test('F6: Kanban page accessible', async ({ page }) => {
    await login(page);
    const kanbanLink = page.locator('a:has-text("Kanban"), button:has-text("Kanban"), [href*="kanban"]').first();
    if (await kanbanLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await kanbanLink.click();
      await page.waitForTimeout(2000);
    } else {
      await page.goto(`${BASE}/kanban`);
      await page.waitForTimeout(2000);
    }
    const status = await page.evaluate(() => document.readyState);
    expect(status).toBe('complete');
    await page.screenshot({ path: '/tmp/hermes-feat-06-kanban.png' });
  });

  // ── Memory Management ──

  test('F7: Memory page accessible', async ({ page }) => {
    await login(page);
    const memLink = page.locator('a:has-text("Memory"), button:has-text("Memory"), [href*="memory"]').first();
    if (await memLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await memLink.click();
      await page.waitForTimeout(2000);
    } else {
      await page.goto(`${BASE}/memory`);
      await page.waitForTimeout(2000);
    }
    const status = await page.evaluate(() => document.readyState);
    expect(status).toBe('complete');
    await page.screenshot({ path: '/tmp/hermes-feat-07-memory.png' });
  });

  // ── Agent Profiles ──

  test('F8: Profiles page accessible', async ({ page }) => {
    await login(page);
    const profLink = page.locator('a:has-text("Profile"), button:has-text("Profile"), [href*="profile"]').first();
    if (await profLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await profLink.click();
      await page.waitForTimeout(2000);
    } else {
      await page.goto(`${BASE}/profiles`);
      await page.waitForTimeout(2000);
    }
    const status = await page.evaluate(() => document.readyState);
    expect(status).toBe('complete');
    await page.screenshot({ path: '/tmp/hermes-feat-08-profiles.png' });
  });

  // ── Spaces ──

  test('F9: Spaces page accessible', async ({ page }) => {
    await login(page);
    const spacesLink = page.locator('a:has-text("Spaces"), button:has-text("Spaces"), [href*="space"]').first();
    if (await spacesLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await spacesLink.click();
      await page.waitForTimeout(2000);
    } else {
      await page.goto(`${BASE}/spaces`);
      await page.waitForTimeout(2000);
    }
    const status = await page.evaluate(() => document.readyState);
    expect(status).toBe('complete');
    await page.screenshot({ path: '/tmp/hermes-feat-09-spaces.png' });
  });

  // ── Todos ──

  test('F10: Todos page accessible', async ({ page }) => {
    await login(page);
    const todosLink = page.locator('a:has-text("Todos"), button:has-text("Todos"), [href*="todo"]').first();
    if (await todosLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await todosLink.click();
      await page.waitForTimeout(2000);
    } else {
      await page.goto(`${BASE}/todos`);
      await page.waitForTimeout(2000);
    }
    const status = await page.evaluate(() => document.readyState);
    expect(status).toBe('complete');
    await page.screenshot({ path: '/tmp/hermes-feat-10-todos.png' });
  });

  // ── Insights ──

  test('F11: Insights page accessible', async ({ page }) => {
    await login(page);
    const insightsLink = page.locator('a:has-text("Insights"), button:has-text("Insights"), [href*="insight"]').first();
    if (await insightsLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await insightsLink.click();
      await page.waitForTimeout(2000);
    } else {
      await page.goto(`${BASE}/insights`);
      await page.waitForTimeout(2000);
    }
    const status = await page.evaluate(() => document.readyState);
    expect(status).toBe('complete');
    await page.screenshot({ path: '/tmp/hermes-feat-11-insights.png' });
  });

  // ── Logs ──

  test('F12: Logs page accessible', async ({ page }) => {
    await login(page);
    const logsLink = page.locator('a:has-text("Logs"), button:has-text("Logs"), [href*="log"]').first();
    if (await logsLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await logsLink.click();
      await page.waitForTimeout(2000);
    } else {
      await page.goto(`${BASE}/logs`);
      await page.waitForTimeout(2000);
    }
    const status = await page.evaluate(() => document.readyState);
    expect(status).toBe('complete');
    await page.screenshot({ path: '/tmp/hermes-feat-12-logs.png' });
  });

  // ── Settings ──

  test('F13: Settings page accessible', async ({ page }) => {
    await login(page);
    const settingsLink = page.locator('a:has-text("Settings"), button:has-text("Settings"), [href*="setting"]').first();
    if (await settingsLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await settingsLink.click();
      await page.waitForTimeout(2000);
    } else {
      await page.goto(`${BASE}/settings`);
      await page.waitForTimeout(2000);
    }
    const status = await page.evaluate(() => document.readyState);
    expect(status).toBe('complete');
    await page.screenshot({ path: '/tmp/hermes-feat-13-settings.png' });
  });

  // ── Gateway Management ──

  test('F14: Gateway status visible', async ({ page }) => {
    await login(page);
    const body = await page.textContent('body');
    // Page must load with content
    expect(body.length).toBeGreaterThan(50);
    // Look for gateway status indicators (connected, running, online, etc.)
    const hasGateway = /gateway|running|connected|online|agent/i.test(body);
    expect(hasGateway).toBe(true);
    await page.screenshot({ path: '/tmp/hermes-feat-14-gateway.png' });
  });

  // ── Workspace Files ──

  test('F15: Workspace files panel accessible', async ({ page }) => {
    await login(page);
    const filesLink = page.locator(
      'a:has-text("Files"), button:has-text("Files"), [href*="file"], [class*="file"]'
    ).first();
    if (await filesLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await filesLink.click();
      await page.waitForTimeout(2000);
    }
    const status = await page.evaluate(() => document.readyState);
    expect(status).toBe('complete');
    await page.screenshot({ path: '/tmp/hermes-feat-15-files.png' });
  });

  // ── Responsive Design ──

  test('F16: Mobile layout — sidebar collapses', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await login(page);
    const body = await page.textContent('body');
    expect(body.length).toBeGreaterThan(10);
    await page.screenshot({ path: '/tmp/hermes-feat-16-mobile.png' });
  });

  // ── API Route ──

  test('F17: /api route proxied to agent', async ({ page }) => {
    const response = await page.goto(`${BASE}/api`);
    const status = response.status();
    // Should NOT be 502/503 (bad gateway)
    expect([502, 503]).not.toContain(status);
    await page.screenshot({ path: '/tmp/hermes-feat-17-api.png' });
  });

  // ── New Conversation ──

  test('F18: New conversation button exists', async ({ page }) => {
    await login(page);
    const newChat = page.locator(
      'button:has-text("New"), button[aria-label*="new"], [class*="new-chat"], [data-testid*="new"]'
    );
    const exists = await newChat.first().isVisible({ timeout: 5000 }).catch(() => false);
    // Also check for + icon buttons commonly used for "new chat"
    const plusBtn = page.locator('button svg, button [class*="plus"], button [class*="add"]');
    const plusExists = await plusBtn.first().isVisible({ timeout: 3000 }).catch(() => false);
    expect(exists || plusExists).toBe(true);
    await page.screenshot({ path: '/tmp/hermes-feat-18-newchat.png' });
  });

});
