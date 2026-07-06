// tests/pre-launch/30-appointment-slots.spec.mjs
// Appointment scheduling configuration tests for O.G老地方身體修復
//
// Verifies:
//   - Appointment schedule page loads correctly
//   - Appointment type name is "O.G 身體修復體驗"
//   - Slot duration is 60 minutes
//   - Weekdays (Mon-Fri): 6 slots — 10:00, 11:00, 14:00, 15:00, 16:00, 17:00
//   - Weekends (Sat-Sun): 6 slots — 12:00, 13:00, 14:00, 15:00, 16:00, 17:00
//   - No slots during weekday lunch break (12:00-14:00)
//   - Booking form accessible after clicking a slot

import { test, expect } from '@playwright/test';

const BASE = process.env.ODOO_BASE_URL || 'https://markstudio-odoo.woowtech.io';

// ---------------------------------------------------------------------------
// Date helpers
// ---------------------------------------------------------------------------

/**
 * Find the next date that falls on the given day-of-week (0=Sun, 1=Mon, ..., 6=Sat).
 * Starts searching from tomorrow so we always get a future date.
 * Returns { dateStr: 'YYYY-MM-DD', dayNum: N, label: 'D 月份 YYYY' }
 */
function nextDayOfWeek(targetDow) {
  const now = new Date();
  // Start from tomorrow (UTC) to avoid "today" edge cases
  const start = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1));
  for (let i = 0; i < 60; i++) {
    const d = new Date(start.getTime() + i * 86400000);
    if (d.getUTCDay() === targetDow) {
      const yyyy = d.getUTCFullYear();
      const mm = String(d.getUTCMonth() + 1).padStart(2, '0');
      const dd = String(d.getUTCDate()).padStart(2, '0');
      return {
        dateStr: `${yyyy}-${mm}-${dd}`,
        dayNum: d.getUTCDate(),
        year: yyyy,
        month: d.getUTCMonth(), // 0-indexed
      };
    }
  }
  throw new Error(`Could not find a future ${targetDow} within 60 days`);
}

/** Chinese month names used in Odoo's zh_TW calendar */
const ZH_MONTHS = [
  '一月', '二月', '三月', '四月', '五月', '六月',
  '七月', '八月', '九月', '十月', '十一月', '十二月',
];

/**
 * Navigate the calendar to the correct month (if needed) and click the target date.
 * Waits for slots to fully load (AJAX) before returning.
 */
async function navigateToDate(page, dateInfo) {
  // The calendar heading shows e.g. "七月 2026"
  const targetHeading = `${ZH_MONTHS[dateInfo.month]} ${dateInfo.year}`;

  // Navigate forward/backward until we reach the correct month
  for (let attempts = 0; attempts < 12; attempts++) {
    const currentHeading = await page.locator('[role="application"] h5').textContent();
    if (currentHeading.trim() === targetHeading) break;
    // Click "下月" (next month) button
    await page.getByRole('button', { name: '下月' }).click();
    await page.waitForTimeout(500);
  }

  // Click the target date button. Odoo uses accessible names like "7 七月 2026"
  const dateButtonName = `${dateInfo.dayNum} ${ZH_MONTHS[dateInfo.month]} ${dateInfo.year}`;
  const dateButton = page.getByRole('button', { name: dateButtonName, exact: true });
  await expect(dateButton).toBeVisible({ timeout: 10000 });
  await dateButton.click();

  // Wait for the slot panel heading to appear
  const slotHeading = page.getByRole('heading', { name: /可用時段/ });
  await expect(slotHeading).toBeVisible({ timeout: 15000 });

  // Wait for slots to finish loading (the "Loading available times..." text disappears)
  // Slots are links with href containing "/appointment/1/book"
  await page.waitForFunction(() => {
    // Loading is done when either:
    // 1. Slot links are present, or
    // 2. A "no availability" message appears
    const slotLinks = document.querySelectorAll('a[href*="/appointment/1/book"]');
    const loading = document.querySelector('p');
    const hasLoadingText = loading && loading.textContent.includes('Loading');
    return slotLinks.length > 0 || !hasLoadingText;
  }, { timeout: 20000 });

  // Small additional wait to ensure DOM is stable
  await page.waitForTimeout(500);
}

/**
 * Extract all slot links from the currently visible slot panel.
 * Uses href-based selector since slots link to /appointment/1/book with query params.
 * Returns an array of { start: 'HH:MM', end: 'HH:MM', href: string }.
 */
async function extractSlots(page) {
  // Slot links have hrefs like /appointment/1/book?start_datetime=...&end_datetime=...
  const slotLinks = page.locator('a[href*="/appointment/1/book"]');
  const count = await slotLinks.count();
  const slots = [];
  for (let i = 0; i < count; i++) {
    const link = slotLinks.nth(i);
    const text = await link.textContent();
    const href = await link.getAttribute('href');
    // Extract times from text like "10:00 - 11:001 available"
    const match = text.match(/(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})/);
    if (match) {
      slots.push({ start: match[1], end: match[2], href: href || '' });
    }
  }
  return slots;
}


// ===========================================================================
// Test Suite
// ===========================================================================

test.describe('Appointment Scheduling Configuration', () => {

  test.describe.configure({ timeout: 60000 });

  // -----------------------------------------------------------------------
  // S1: Appointment schedule page loads
  // -----------------------------------------------------------------------
  test('S1: Appointment schedule page loads', async ({ page }) => {
    const response = await page.goto(`${BASE}/appointment/1/schedule`, {
      waitUntil: 'domcontentloaded',
      timeout: 30000,
    });

    // HTTP 200
    expect(response.status()).toBe(200);

    // Page has the calendar widget (role="application" with name "預約行事曆")
    const calendar = page.getByRole('application', { name: /預約行事曆/ });
    await expect(calendar).toBeVisible({ timeout: 15000 });

    // Page has heading "選擇日期與時間"
    const heading = page.getByRole('heading', { name: /選擇日期與時間/ });
    await expect(heading).toBeVisible();

    console.log('  [S1] Schedule page loaded — HTTP 200, calendar visible');
  });


  // -----------------------------------------------------------------------
  // S2: Appointment type name is correct
  // -----------------------------------------------------------------------
  test('S2: Appointment type name is correct', async ({ page }) => {
    await page.goto(`${BASE}/appointment/1/schedule`, {
      waitUntil: 'domcontentloaded',
      timeout: 30000,
    });

    // Breadcrumb contains "O.G 身體修復體驗"
    const breadcrumb = page.getByRole('link', { name: 'O.G 身體修復體驗' });
    await expect(breadcrumb).toBeVisible({ timeout: 10000 });

    const text = await breadcrumb.textContent();
    expect(text.trim()).toBe('O.G 身體修復體驗');

    console.log('  [S2] Appointment type name confirmed: "O.G 身體修復體驗"');
  });


  // -----------------------------------------------------------------------
  // S3: Slot duration is 60 minutes
  // -----------------------------------------------------------------------
  test('S3: Slot duration is 60 minutes', async ({ page }) => {
    await page.goto(`${BASE}/appointment/1/schedule`, {
      waitUntil: 'domcontentloaded',
      timeout: 30000,
    });

    // Pick the next available Monday (weekday = 1)
    const monday = nextDayOfWeek(1);
    await navigateToDate(page, monday);
    const slots = await extractSlots(page);

    expect(slots.length).toBeGreaterThan(0);

    // Every slot should span exactly 60 minutes
    for (const slot of slots) {
      const [startH, startM] = slot.start.split(':').map(Number);
      const [endH, endM] = slot.end.split(':').map(Number);
      const durationMin = (endH * 60 + endM) - (startH * 60 + startM);
      expect(durationMin, `Slot ${slot.start}-${slot.end} should be 60 min, got ${durationMin}`).toBe(60);
    }

    console.log(`  [S3] All ${slots.length} slots are exactly 60 minutes`);
  });


  // -----------------------------------------------------------------------
  // S4: Weekday has exactly 6 slots
  // -----------------------------------------------------------------------
  test('S4: Weekday has exactly 6 slots (Mon-Fri)', async ({ page }) => {
    await page.goto(`${BASE}/appointment/1/schedule`, {
      waitUntil: 'domcontentloaded',
      timeout: 30000,
    });

    // Pick the next Wednesday (weekday = 3) for variety
    const wednesday = nextDayOfWeek(3);
    await navigateToDate(page, wednesday);
    const slots = await extractSlots(page);

    const startTimes = slots.map(s => s.start);
    console.log(`  [S4] Wednesday ${wednesday.dateStr} slots: ${startTimes.join(', ')}`);

    // Expect exactly 6 slots
    expect(slots.length, `Expected 6 weekday slots, got ${slots.length}`).toBe(6);

    // Verify exact start times: 10:00, 11:00, 14:00, 15:00, 16:00, 17:00
    const expectedStarts = ['10:00', '11:00', '14:00', '15:00', '16:00', '17:00'];
    expect(startTimes).toEqual(expectedStarts);

    console.log('  [S4] Weekday slots match expected: 10:00, 11:00, 14:00, 15:00, 16:00, 17:00');
  });


  // -----------------------------------------------------------------------
  // S5: Weekend has exactly 6 slots
  // -----------------------------------------------------------------------
  test('S5: Weekend has exactly 6 slots (Sat-Sun)', async ({ page }) => {
    await page.goto(`${BASE}/appointment/1/schedule`, {
      waitUntil: 'domcontentloaded',
      timeout: 30000,
    });

    // Pick the next Saturday (weekday = 6)
    const saturday = nextDayOfWeek(6);
    await navigateToDate(page, saturday);
    const slots = await extractSlots(page);

    const startTimes = slots.map(s => s.start);
    console.log(`  [S5] Saturday ${saturday.dateStr} slots: ${startTimes.join(', ')}`);

    // Expect exactly 6 slots
    expect(slots.length, `Expected 6 weekend slots, got ${slots.length}`).toBe(6);

    // Verify exact start times: 12:00, 13:00, 14:00, 15:00, 16:00, 17:00
    const expectedStarts = ['12:00', '13:00', '14:00', '15:00', '16:00', '17:00'];
    expect(startTimes).toEqual(expectedStarts);

    console.log('  [S5] Weekend slots match expected: 12:00, 13:00, 14:00, 15:00, 16:00, 17:00');
  });


  // -----------------------------------------------------------------------
  // S6: No slots during weekday lunch break (12:00-14:00)
  // -----------------------------------------------------------------------
  test('S6: No slots during weekday lunch break', async ({ page }) => {
    await page.goto(`${BASE}/appointment/1/schedule`, {
      waitUntil: 'domcontentloaded',
      timeout: 30000,
    });

    // Pick the next Thursday (weekday = 4)
    const thursday = nextDayOfWeek(4);
    await navigateToDate(page, thursday);
    const slots = await extractSlots(page);

    const startTimes = slots.map(s => s.start);
    console.log(`  [S6] Thursday ${thursday.dateStr} slots: ${startTimes.join(', ')}`);

    // No slot should start at 12:00 or 13:00 on a weekday
    const lunchSlots = startTimes.filter(t => t === '12:00' || t === '13:00');
    expect(
      lunchSlots.length,
      `Found lunch-break slots on weekday: ${lunchSlots.join(', ')}`
    ).toBe(0);

    // Double-check: no slot starts between 12:00 and 13:59
    for (const t of startTimes) {
      const hour = parseInt(t.split(':')[0], 10);
      expect(
        hour >= 12 && hour < 14,
        `Slot at ${t} falls within weekday lunch break 12:00-14:00`
      ).toBe(false);
    }

    console.log('  [S6] No lunch-break slots found on weekday (12:00-14:00 gap confirmed)');
  });


  // -----------------------------------------------------------------------
  // S7: Booking page accessible after clicking a slot
  // -----------------------------------------------------------------------
  test('S7: Booking page accessible after clicking a slot', async ({ page }) => {
    await page.goto(`${BASE}/appointment/1/schedule`, {
      waitUntil: 'domcontentloaded',
      timeout: 30000,
    });

    // Pick the next Tuesday (weekday = 2)
    const tuesday = nextDayOfWeek(2);
    await navigateToDate(page, tuesday);

    // Click the first available slot link
    const firstSlot = page.locator('a[href*="/appointment/1/book"]').first();
    await expect(firstSlot).toBeVisible({ timeout: 10000 });
    const slotText = await firstSlot.textContent();
    console.log(`  [S7] Clicking slot: ${slotText.trim()}`);
    await firstSlot.click();

    // Should navigate to /appointment/1/book
    await page.waitForURL(/\/appointment\/1\/book/, { timeout: 15000 });
    expect(page.url()).toContain('/appointment/1/book');

    // Booking form should have the heading "完成您的預約"
    const heading = page.getByRole('heading', { name: /完成您的預約/ });
    await expect(heading).toBeVisible({ timeout: 10000 });

    // Booking form should show the appointment type name
    const typeName = page.locator('strong').filter({ hasText: 'O.G 身體修復體驗' });
    await expect(typeName).toBeVisible();

    // Booking form should have the required fields
    await expect(page.getByRole('textbox', { name: /姓名/ })).toBeVisible();
    await expect(page.getByRole('textbox', { name: /電子郵件/ })).toBeVisible();
    await expect(page.getByRole('textbox', { name: /電話/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /確認預約/ })).toBeVisible();

    console.log('  [S7] Booking form loaded with all expected fields');
  });

});
