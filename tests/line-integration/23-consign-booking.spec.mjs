// tests/line-integration/23-consign-booking.spec.mjs
// J1-J15: Consign Booking Bridge — appointment + loyalty consign integration
import { test, expect } from '@playwright/test';
import {
  loginAsAdmin, rpcCall, searchRead, create, read, write, safeUnlink, BASE,
} from './helpers/odoo-rpc.mjs';

test.describe('J: Consign Booking Bridge — Reservation + Consign Card Integration', () => {

  // ── Shared test data IDs for cleanup ──
  const createdRedemptionIds = [];
  const createdBookingIds = [];
  const createdConsignLineIds = [];
  const createdCardIds = [];
  const createdProductIds = [];
  const createdProgramIds = [];
  const createdTypeIds = [];
  const createdPartnerIds = [];

  // ── Shared references set during setup ──
  let programId;
  let triggerProductId;
  let consignProductId;
  let partnerId;
  let cardId;
  let consignLineId;
  let appointmentTypeId;

  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    try {
      await loginAsAdmin(page);

      // 1. Create a consign loyalty.program
      programId = await create(page, 'loyalty.program', {
        name: 'PW Consign Program J',
        program_type: 'consign',
      });
      createdProgramIds.push(programId);

      // 2. Create a trigger product and a consign product
      triggerProductId = await create(page, 'product.product', {
        name: 'PW Trigger Product J',
        type: 'service',
        list_price: 1000.0,
      });
      createdProductIds.push(triggerProductId);

      consignProductId = await create(page, 'product.product', {
        name: 'PW Consign Service J',
        type: 'service',
        list_price: 500.0,
      });
      createdProductIds.push(consignProductId);

      // 3. Create a test partner
      partnerId = await create(page, 'res.partner', {
        name: 'PW Test Customer J',
        email: 'pw-consign-j@test.example',
      });
      createdPartnerIds.push(partnerId);

      // 4. Create a loyalty.card for that partner (consign card)
      cardId = await create(page, 'loyalty.card', {
        program_id: programId,
        partner_id: partnerId,
      });
      createdCardIds.push(cardId);

      // 5. Add consign lines: 5 units of consign product
      consignLineId = await create(page, 'loyalty.consign.line', {
        card_id: cardId,
        product_id: consignProductId,
        product_desc: 'PW Consign Service J',
        qty_deposited: 5.0,
        unit_price: 500.0,
      });
      createdConsignLineIds.push(consignLineId);

      // 6. Create an appointment.type with consign_enabled=True
      appointmentTypeId = await create(page, 'appointment.type', {
        name: 'PW Consign Appointment J',
        consign_enabled: true,
        consign_program_id: programId,
        consign_product_id: consignProductId,
        consign_qty: 1.0,
      });
      createdTypeIds.push(appointmentTypeId);

      console.log('[SETUP] Created program=%d, products=[%d,%d], partner=%d, card=%d, line=%d, type=%d',
        programId, triggerProductId, consignProductId, partnerId, cardId, consignLineId, appointmentTypeId);
    } finally {
      await page.close();
    }
  });

  test.afterAll(async ({ browser }) => {
    const page = await browser.newPage();
    try {
      await loginAsAdmin(page);

      // Cleanup in dependency order: redemptions -> bookings -> consign lines -> cards -> products -> programs -> types -> partners
      // First, reset any bookings to draft so they can be deleted
      for (const bId of createdBookingIds) {
        try {
          const [b] = await read(page, 'appointment.booking', [bId], ['state', 'consign_redemption_id']);
          // Clear consign fields first to avoid blocking
          if (b.consign_redemption_id) {
            // Force-clear the link so deletion is not blocked
            await write(page, 'appointment.booking', [bId], {
              consign_redemption_id: false,
              consign_line_id: false,
              consign_reserved_qty: 0,
            });
          }
        } catch { /* ignore */ }
      }

      await safeUnlink(page, 'loyalty.consign.redemption', createdRedemptionIds);
      await safeUnlink(page, 'appointment.booking', createdBookingIds);
      await safeUnlink(page, 'loyalty.consign.line', createdConsignLineIds);
      await safeUnlink(page, 'loyalty.card', createdCardIds);
      await safeUnlink(page, 'appointment.type', createdTypeIds);
      await safeUnlink(page, 'product.product', createdProductIds);
      await safeUnlink(page, 'loyalty.program', createdProgramIds);
      await safeUnlink(page, 'res.partner', createdPartnerIds);

      console.log(
        '[CLEANUP] Removed %d redemptions, %d bookings, %d consign lines, %d cards, %d products, %d programs, %d types, %d partners',
        createdRedemptionIds.length, createdBookingIds.length, createdConsignLineIds.length,
        createdCardIds.length, createdProductIds.length, createdProgramIds.length,
        createdTypeIds.length, createdPartnerIds.length,
      );
    } finally {
      await page.close();
    }
  });

  // ── J1: Verify consign fields exist on appointment.type ──
  test('J1: appointment.type has consign_enabled, consign_program_id, consign_product_id, consign_qty fields', async ({ page }) => {
    await loginAsAdmin(page);

    const fields = await rpcCall(page, 'appointment.type', 'fields_get', [], {
      attributes: ['type', 'relation', 'string'],
    });

    expect(fields).toHaveProperty('consign_enabled');
    expect(fields.consign_enabled.type).toBe('boolean');

    expect(fields).toHaveProperty('consign_program_id');
    expect(fields.consign_program_id.type).toBe('many2one');
    expect(fields.consign_program_id.relation).toBe('loyalty.program');

    expect(fields).toHaveProperty('consign_product_id');
    expect(fields.consign_product_id.type).toBe('many2one');
    expect(fields.consign_product_id.relation).toBe('product.product');

    expect(fields).toHaveProperty('consign_qty');
    expect(fields.consign_qty.type).toBe('float');

    console.log('[OK] J1: appointment.type has all 4 consign fields');
  });

  // ── J2: Verify consign fields exist on appointment.booking ──
  test('J2: appointment.booking has consign_line_id, consign_reserved_qty, consign_redemption_id, consign_enabled fields', async ({ page }) => {
    await loginAsAdmin(page);

    const fields = await rpcCall(page, 'appointment.booking', 'fields_get', [], {
      attributes: ['type', 'relation', 'string'],
    });

    expect(fields).toHaveProperty('consign_line_id');
    expect(fields.consign_line_id.type).toBe('many2one');
    expect(fields.consign_line_id.relation).toBe('loyalty.consign.line');

    expect(fields).toHaveProperty('consign_reserved_qty');
    expect(fields.consign_reserved_qty.type).toBe('float');

    expect(fields).toHaveProperty('consign_redemption_id');
    expect(fields.consign_redemption_id.type).toBe('many2one');
    expect(fields.consign_redemption_id.relation).toBe('loyalty.consign.redemption');

    expect(fields).toHaveProperty('consign_enabled');
    expect(fields.consign_enabled.type).toBe('boolean');

    console.log('[OK] J2: appointment.booking has all 4 consign fields');
  });

  // ── J3: Verify reserved_qty and qty_available fields on loyalty.consign.line ──
  test('J3: loyalty.consign.line has reserved_qty and qty_available fields', async ({ page }) => {
    await loginAsAdmin(page);

    const fields = await rpcCall(page, 'loyalty.consign.line', 'fields_get', [], {
      attributes: ['type', 'string'],
    });

    expect(fields).toHaveProperty('reserved_qty');
    expect(fields.reserved_qty.type).toBe('float');

    expect(fields).toHaveProperty('qty_available');
    expect(fields.qty_available.type).toBe('float');

    // Verify initial state of our test line
    const [line] = await read(page, 'loyalty.consign.line', [consignLineId], [
      'qty_deposited', 'qty_remaining', 'reserved_qty', 'qty_available', 'state',
    ]);
    expect(line.qty_deposited).toBe(5.0);
    expect(line.qty_remaining).toBe(5.0);
    expect(line.state).toBe('active');

    console.log('[OK] J3: loyalty.consign.line has reserved_qty (%.1f) and qty_available (%.1f)',
      line.reserved_qty, line.qty_available);
  });

  // ── J4: Create booking -> reserved_qty increases by consign_qty ──
  test('J4: Creating consign booking reserves qty on consign line', async ({ page }) => {
    await loginAsAdmin(page);

    // Read reserved_qty before
    const [lineBefore] = await read(page, 'loyalty.consign.line', [consignLineId], ['reserved_qty']);
    const reservedBefore = lineBefore.reserved_qty;

    // Create a booking with consign-enabled appointment type
    const bookingId = await create(page, 'appointment.booking', {
      appointment_type_id: appointmentTypeId,
      partner_id: partnerId,
      guest_name: 'PW Guest J4',
      guest_email: 'pw-j4@test.example',
      guest_count: 1,
      start_datetime: '2026-12-25 10:00:00',
      end_datetime: '2026-12-25 11:00:00',
    });
    expect(bookingId).toBeTruthy();
    createdBookingIds.push(bookingId);

    // Verify booking has consign fields populated
    const [booking] = await read(page, 'appointment.booking', [bookingId], [
      'consign_line_id', 'consign_reserved_qty', 'consign_enabled',
    ]);
    expect(booking.consign_line_id[0]).toBe(consignLineId);
    expect(booking.consign_reserved_qty).toBe(1.0);
    expect(booking.consign_enabled).toBe(true);

    // Verify reserved_qty increased on consign line
    const [lineAfter] = await read(page, 'loyalty.consign.line', [consignLineId], ['reserved_qty']);
    expect(lineAfter.reserved_qty).toBe(reservedBefore + 1.0);

    console.log('[OK] J4: Booking %d created, reserved_qty increased from %.1f to %.1f',
      bookingId, reservedBefore, lineAfter.reserved_qty);
  });

  // ── J5: Create second booking -> reserved_qty increases to 2 ──
  test('J5: Second consign booking further increases reserved_qty', async ({ page }) => {
    await loginAsAdmin(page);

    const [lineBefore] = await read(page, 'loyalty.consign.line', [consignLineId], ['reserved_qty']);
    const reservedBefore = lineBefore.reserved_qty;

    const bookingId = await create(page, 'appointment.booking', {
      appointment_type_id: appointmentTypeId,
      partner_id: partnerId,
      guest_name: 'PW Guest J5',
      guest_email: 'pw-j5@test.example',
      guest_count: 1,
      start_datetime: '2026-12-26 10:00:00',
      end_datetime: '2026-12-26 11:00:00',
    });
    expect(bookingId).toBeTruthy();
    createdBookingIds.push(bookingId);

    const [lineAfter] = await read(page, 'loyalty.consign.line', [consignLineId], ['reserved_qty']);
    expect(lineAfter.reserved_qty).toBe(reservedBefore + 1.0);

    console.log('[OK] J5: Second booking %d created, reserved_qty now %.1f',
      bookingId, lineAfter.reserved_qty);
  });

  // ── J6: Confirm first booking -> consign_redemption_id set, reserved_qty decreases ──
  test('J6: Confirming booking creates redemption and decreases reserved_qty', async ({ page }) => {
    await loginAsAdmin(page);

    // The first booking created in J4
    const firstBookingId = createdBookingIds[0];

    const [lineBefore] = await read(page, 'loyalty.consign.line', [consignLineId], ['reserved_qty']);
    const reservedBefore = lineBefore.reserved_qty;

    // Confirm the booking
    await rpcCall(page, 'appointment.booking', 'action_confirm', [firstBookingId]);

    // Verify booking now has a redemption
    const [booking] = await read(page, 'appointment.booking', [firstBookingId], [
      'consign_redemption_id', 'consign_reserved_qty', 'state',
    ]);
    expect(booking.consign_redemption_id).toBeTruthy();
    expect(booking.consign_reserved_qty).toBe(0);

    // Track the redemption for cleanup
    const redemptionId = booking.consign_redemption_id[0];
    createdRedemptionIds.push(redemptionId);

    // Verify reserved_qty decreased
    const [lineAfter] = await read(page, 'loyalty.consign.line', [consignLineId], ['reserved_qty']);
    expect(lineAfter.reserved_qty).toBe(reservedBefore - 1.0);

    console.log('[OK] J6: Booking %d confirmed, redemption %d created, reserved_qty %.1f -> %.1f',
      firstBookingId, redemptionId, reservedBefore, lineAfter.reserved_qty);
  });

  // ── J7: Verify redemption record: state=done, correct qty, booking_id set ──
  test('J7: Redemption record has state=done, correct qty, and booking_id', async ({ page }) => {
    await loginAsAdmin(page);

    const firstBookingId = createdBookingIds[0];

    // Get the redemption from the booking
    const [booking] = await read(page, 'appointment.booking', [firstBookingId], [
      'consign_redemption_id',
    ]);
    const redemptionId = booking.consign_redemption_id[0];

    // Read redemption details
    const [redemption] = await read(page, 'loyalty.consign.redemption', [redemptionId], [
      'state', 'booking_id', 'card_id', 'line_ids',
    ]);

    expect(redemption.state).toBe('done');
    expect(redemption.booking_id[0]).toBe(firstBookingId);
    expect(redemption.card_id[0]).toBe(cardId);
    expect(redemption.line_ids.length).toBeGreaterThanOrEqual(1);

    // Check the redemption line has correct qty
    const [redemptionLine] = await read(page, 'loyalty.consign.redemption.line', [redemption.line_ids[0]], [
      'qty_redeemed', 'consign_line_id',
    ]);
    expect(redemptionLine.qty_redeemed).toBe(1.0);
    expect(redemptionLine.consign_line_id[0]).toBe(consignLineId);

    console.log('[OK] J7: Redemption %d: state=done, qty=1.0, booking_id=%d',
      redemptionId, firstBookingId);
  });

  // ── J8: Cancel confirmed booking -> BLOCKED (UserError about done redemption) ──
  test('J8: Cancelling confirmed booking with done redemption raises UserError', async ({ page }) => {
    await loginAsAdmin(page);

    const firstBookingId = createdBookingIds[0];

    let cancelError = false;
    let errorMessage = '';
    try {
      await rpcCall(page, 'appointment.booking', 'action_cancel', [firstBookingId]);
    } catch (e) {
      cancelError = true;
      errorMessage = e.message || '';
    }

    expect(cancelError).toBe(true);
    // Error should mention the redemption is done / cannot cancel
    expect(errorMessage).toMatch(/核銷|cancel|無法取消/i);

    console.log('[OK] J8: Cancel of confirmed booking blocked with error: %s',
      errorMessage.substring(0, 80));
  });

  // ── J9: Cancel draft booking -> reserved_qty decreases, consign fields cleared ──
  test('J9: Cancelling draft booking releases reservation and clears consign fields', async ({ page }) => {
    await loginAsAdmin(page);

    // The second booking from J5 is still in draft
    const secondBookingId = createdBookingIds[1];

    // Verify it still has reservation
    const [bookingBefore] = await read(page, 'appointment.booking', [secondBookingId], [
      'consign_line_id', 'consign_reserved_qty', 'state',
    ]);
    expect(bookingBefore.consign_reserved_qty).toBe(1.0);

    const [lineBefore] = await read(page, 'loyalty.consign.line', [consignLineId], ['reserved_qty']);
    const reservedBefore = lineBefore.reserved_qty;

    // Cancel the draft booking
    await rpcCall(page, 'appointment.booking', 'action_cancel', [secondBookingId]);

    // Verify consign fields cleared on booking
    const [bookingAfter] = await read(page, 'appointment.booking', [secondBookingId], [
      'consign_line_id', 'consign_reserved_qty', 'consign_redemption_id',
    ]);
    expect(bookingAfter.consign_line_id).toBeFalsy();
    expect(bookingAfter.consign_reserved_qty).toBe(0);
    expect(bookingAfter.consign_redemption_id).toBeFalsy();

    // Verify reserved_qty decreased on consign line
    const [lineAfter] = await read(page, 'loyalty.consign.line', [consignLineId], ['reserved_qty']);
    expect(lineAfter.reserved_qty).toBe(reservedBefore - 1.0);

    console.log('[OK] J9: Draft booking %d cancelled, reserved_qty %.1f -> %.1f, consign fields cleared',
      secondBookingId, reservedBefore, lineAfter.reserved_qty);
  });

  // ── J10: Booking with insufficient balance -> UserError ──
  test('J10: Booking with insufficient consign balance raises UserError', async ({ page }) => {
    await loginAsAdmin(page);

    // Create an appointment type that requires 100 units (more than our 5)
    const bigTypeId = await create(page, 'appointment.type', {
      name: 'PW Big Consign J10',
      consign_enabled: true,
      consign_program_id: programId,
      consign_product_id: consignProductId,
      consign_qty: 100.0,
    });
    createdTypeIds.push(bigTypeId);

    let insufficientError = false;
    let errorMessage = '';
    try {
      const bookingId = await create(page, 'appointment.booking', {
        appointment_type_id: bigTypeId,
        partner_id: partnerId,
        guest_name: 'PW Guest J10',
        guest_email: 'pw-j10@test.example',
        guest_count: 1,
        start_datetime: '2026-12-27 10:00:00',
        end_datetime: '2026-12-27 11:00:00',
      });
      // If somehow created, track for cleanup
      createdBookingIds.push(bookingId);
    } catch (e) {
      insufficientError = true;
      errorMessage = e.message || '';
    }

    expect(insufficientError).toBe(true);
    // Error should mention insufficient balance
    expect(errorMessage).toMatch(/餘額不足|不足|insufficient/i);

    console.log('[OK] J10: Insufficient balance error: %s', errorMessage.substring(0, 80));
  });

  // ── J11: Booking with no consign card for customer -> UserError ──
  test('J11: Booking for customer without consign card raises UserError', async ({ page }) => {
    await loginAsAdmin(page);

    // Create a partner with no consign card
    const noCardPartnerId = await create(page, 'res.partner', {
      name: 'PW No Card Customer J11',
      email: 'pw-nocard-j11@test.example',
    });
    createdPartnerIds.push(noCardPartnerId);

    let noCardError = false;
    let errorMessage = '';
    try {
      const bookingId = await create(page, 'appointment.booking', {
        appointment_type_id: appointmentTypeId,
        partner_id: noCardPartnerId,
        guest_name: 'PW Guest J11',
        guest_email: 'pw-j11@test.example',
        guest_count: 1,
        start_datetime: '2026-12-28 10:00:00',
        end_datetime: '2026-12-28 11:00:00',
      });
      // If somehow created, track for cleanup
      createdBookingIds.push(bookingId);
    } catch (e) {
      noCardError = true;
      errorMessage = e.message || '';
    }

    expect(noCardError).toBe(true);
    // Error should mention no consign card
    expect(errorMessage).toMatch(/沒有.*寄品卡|no.*card/i);

    console.log('[OK] J11: No consign card error: %s', errorMessage.substring(0, 80));
  });

  // ── J12: Mutual exclusion: require_payment + consign_enabled -> ValidationError ──
  test('J12: require_payment and consign_enabled cannot both be true', async ({ page }) => {
    await loginAsAdmin(page);

    let exclusionError = false;
    let errorMessage = '';
    try {
      const typeId = await create(page, 'appointment.type', {
        name: 'PW Exclusive J12',
        require_payment: true,
        consign_enabled: true,
        consign_program_id: programId,
        consign_product_id: consignProductId,
        consign_qty: 1.0,
      });
      // If somehow created, track for cleanup
      createdTypeIds.push(typeId);
    } catch (e) {
      exclusionError = true;
      errorMessage = e.message || '';
    }

    expect(exclusionError).toBe(true);
    // Error should mention mutual exclusion
    expect(errorMessage).toMatch(/不可同時|付款|payment|exclusive/i);

    console.log('[OK] J12: Mutual exclusion enforced: %s', errorMessage.substring(0, 80));
  });

  // ── J13: Non-consign booking -> no consign fields populated ──
  test('J13: Non-consign booking does not populate consign fields', async ({ page }) => {
    await loginAsAdmin(page);

    // Create a plain appointment type without consign
    const plainTypeId = await create(page, 'appointment.type', {
      name: 'PW Plain Appointment J13',
      consign_enabled: false,
    });
    createdTypeIds.push(plainTypeId);

    const bookingId = await create(page, 'appointment.booking', {
      appointment_type_id: plainTypeId,
      partner_id: partnerId,
      guest_name: 'PW Guest J13',
      guest_email: 'pw-j13@test.example',
      guest_count: 1,
      start_datetime: '2026-12-29 10:00:00',
      end_datetime: '2026-12-29 11:00:00',
    });
    expect(bookingId).toBeTruthy();
    createdBookingIds.push(bookingId);

    const [booking] = await read(page, 'appointment.booking', [bookingId], [
      'consign_line_id', 'consign_reserved_qty', 'consign_redemption_id', 'consign_enabled',
    ]);

    expect(booking.consign_line_id).toBeFalsy();
    expect(booking.consign_reserved_qty).toBe(0);
    expect(booking.consign_redemption_id).toBeFalsy();
    expect(booking.consign_enabled).toBe(false);

    console.log('[OK] J13: Non-consign booking %d has no consign fields populated', bookingId);
  });

  // ── J14: Verify redemption.booking_id cross-reference ──
  test('J14: Redemption booking_id field exists and links back to appointment.booking', async ({ page }) => {
    await loginAsAdmin(page);

    // Verify the field exists on the model
    const fields = await rpcCall(page, 'loyalty.consign.redemption', 'fields_get', [], {
      attributes: ['type', 'relation', 'string'],
    });

    expect(fields).toHaveProperty('booking_id');
    expect(fields.booking_id.type).toBe('many2one');
    expect(fields.booking_id.relation).toBe('appointment.booking');

    // Cross-check using the confirmed booking from J6
    const firstBookingId = createdBookingIds[0];
    const [booking] = await read(page, 'appointment.booking', [firstBookingId], [
      'consign_redemption_id',
    ]);

    if (booking.consign_redemption_id) {
      const redemptionId = booking.consign_redemption_id[0];
      const [redemption] = await read(page, 'loyalty.consign.redemption', [redemptionId], [
        'booking_id',
      ]);
      expect(redemption.booking_id[0]).toBe(firstBookingId);

      console.log('[OK] J14: Redemption %d.booking_id = %d (cross-reference verified)',
        redemptionId, firstBookingId);
    } else {
      // If J6 did not run, just verify the field schema
      console.log('[OK] J14: booking_id field exists on loyalty.consign.redemption (Many2one -> appointment.booking)');
    }
  });

  // ── J15: Portal endpoints return 200 ──
  test('J15: Portal endpoints /liff/redirect/home and /liff/redirect/orders return 200', async ({ page }) => {
    // /liff/redirect/home
    const respHome = await page.goto(`${BASE}/liff/redirect/home`, { waitUntil: 'commit' });
    expect(respHome.status()).toBe(200);

    // /liff/redirect/orders
    const respOrders = await page.goto(`${BASE}/liff/redirect/orders`, { waitUntil: 'commit' });
    expect(respOrders.status()).toBe(200);

    console.log('[OK] J15: /liff/redirect/home (status=%d) and /liff/redirect/orders (status=%d) both return 200',
      respHome.status(), respOrders.status());
  });

});
