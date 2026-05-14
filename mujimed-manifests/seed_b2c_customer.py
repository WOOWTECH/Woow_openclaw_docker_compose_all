#!/usr/bin/env python3
"""
Mujimed B2C Customer Seeder
Seeds a portal customer (portal/portal) with loyalty cards, appointment
bookings, sale orders, and invoices for the B2C consumer website.

Usage:
    python3 seed_b2c_customer.py [--url URL] [--db DB] [--user USER] [--password PASSWORD]

Requires: Odoo 18 with reservation_module, woow_loyalty_consign,
          woow_member_center, woow_portal_ui installed.
          Run seed_clinic_data.py first (creates appointment types + staff).
Idempotent: safe to run multiple times.
"""
import xmlrpc.client
import sys
import argparse
from datetime import datetime

# ─── Configuration ──────────────────────────────────────────────
ODOO_URL = "https://mujimed-odoo.woowtech.io"
ODOO_DB = "mujimed"
ADMIN_USER = "admin"
ADMIN_PASS = "admin"

PORTAL_LOGIN = "portal"
PORTAL_PASSWORD = "portal"
PORTAL_NAME = "王小美"
PORTAL_EMAIL = "portal@mujimed.com"
PORTAL_PHONE = "0912-345-678"


# ─── Connection ─────────────────────────────────────────────────
def connect(url, db, user, password):
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, user, password, {})
    if not uid:
        print("[ERROR] Authentication failed.")
        sys.exit(1)
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    print(f"[ok] Connected as uid={uid}")
    return uid, models


def x(models, db, uid, pw, model, method, *args, **kwargs):
    return models.execute_kw(db, uid, pw, model, method, *args, **kwargs)


def find_or_create(models, db, uid, pw, model, domain, vals):
    ids = x(models, db, uid, pw, model, 'search', [domain], {'limit': 1})
    if ids:
        return ids[0]
    return x(models, db, uid, pw, model, 'create', [vals])


# ─── Portal User ────────────────────────────────────────────────
def seed_portal_user(models, db, uid, pw):
    """Create B2C portal customer."""
    print("\n── Seeding portal user ──")

    # Check if exists
    existing = x(models, db, uid, pw, 'res.users', 'search',
                 [[('login', '=', PORTAL_LOGIN)]], {'limit': 1})
    if existing:
        user_id = existing[0]
        partner = x(models, db, uid, pw, 'res.users', 'read',
                     [user_id], {'fields': ['partner_id']})
        partner_id = partner[0]['partner_id'][0]
        print(f"  [ok] Portal user already exists (uid={user_id}, partner={partner_id})")
        return user_id, partner_id

    # Find portal group
    portal_groups = x(models, db, uid, pw, 'res.groups', 'search',
                      [[('category_id.name', 'ilike', 'User types'),
                        ('name', 'ilike', 'Portal')]], {'limit': 1})
    if not portal_groups:
        print("  [ERROR] Portal group not found")
        sys.exit(1)

    user_id = x(models, db, uid, pw, 'res.users', 'create', [{
        'name': PORTAL_NAME,
        'login': PORTAL_LOGIN,
        'password': PORTAL_PASSWORD,
        'email': PORTAL_EMAIL,
        'phone': PORTAL_PHONE,
        'lang': 'zh_TW',
        'tz': 'Asia/Taipei',
        'groups_id': [(6, 0, portal_groups)],
    }])

    partner = x(models, db, uid, pw, 'res.users', 'read',
                 [user_id], {'fields': ['partner_id']})
    partner_id = partner[0]['partner_id'][0]
    print(f"  [ok] Created {PORTAL_NAME} (uid={user_id}, partner={partner_id})")
    return user_id, partner_id


# ─── Loyalty Programs & Cards ───────────────────────────────────
LOYALTY_PROGRAMS = [
    {
        "name": "Mujimed 電子錢包",
        "program_type": "ewallet",
        "points": 5000,
        "code": "EWALLET-PORTAL",
    },
    {
        "name": "Mujimed 忠誠點數",
        "program_type": "loyalty",
        "points": 1200,
        "code": "LOYALTY-PORTAL",
    },
    {
        "name": "Mujimed 禮品卡",
        "program_type": "gift_card",
        "points": 3000,
        "code": "GIFT-PORTAL",
    },
    {
        "name": "Mujimed 新客優惠券",
        "program_type": "promotion",
        "points": 1,
        "code": "COUPON-PORTAL",
    },
]


def seed_loyalty(models, db, uid, pw, partner_id):
    """Create loyalty programs and cards for portal customer."""
    print("\n── Seeding loyalty programs & cards ──")

    for prog in LOYALTY_PROGRAMS:
        # Find or create program
        program_id = find_or_create(
            models, db, uid, pw, 'loyalty.program',
            [('name', '=', prog['name'])],
            {
                'name': prog['name'],
                'program_type': prog['program_type'],
                'active': True,
            }
        )
        print(f"  [ok] Program: {prog['name']} (id={program_id})")

        # Find or create card for this customer
        card_id = find_or_create(
            models, db, uid, pw, 'loyalty.card',
            [('program_id', '=', program_id), ('partner_id', '=', partner_id)],
            {
                'program_id': program_id,
                'partner_id': partner_id,
                'points': prog['points'],
                'code': prog['code'],
            }
        )
        print(f"        Card: {prog['code']} — {prog['points']} pts (id={card_id})")


# ─── Appointment Bookings ───────────────────────────────────────
BOOKINGS = [
    # (appointment_type_name, date_str, state, staff_login)
    ("初次諮詢", "2026-04-10 02:00:00", "2026-04-10 02:30:00", "done", "dr.chen"),
    ("玻尿酸填充", "2026-04-25 06:00:00", "2026-04-25 06:30:00", "done", "dr.chen"),
    ("皮秒雷射", "2026-05-08 02:00:00", "2026-05-08 02:30:00", "done", "dr.lin"),
    ("杏仁酸煥膚", "2026-05-20 07:00:00", "2026-05-20 07:30:00", "confirmed", "dr.lin"),
    ("電波拉皮 (Thermage)", "2026-06-05 02:00:00", "2026-06-05 03:00:00", "confirmed", "dr.wang"),
]


def seed_bookings(models, db, uid, pw, partner_id):
    """Create appointment bookings for portal customer."""
    print("\n── Seeding appointment bookings ──")

    for apt_name, start_dt, end_dt, state, staff_login in BOOKINGS:
        # Find appointment type
        apt_ids = x(models, db, uid, pw, 'appointment.type', 'search',
                    [[('name', '=', apt_name)]], {'limit': 1})
        if not apt_ids:
            print(f"  [SKIP] Appointment type '{apt_name}' not found")
            continue

        # Find staff
        staff_ids = x(models, db, uid, pw, 'res.users', 'search',
                      [[('login', '=', staff_login)]], {'limit': 1})
        staff_id = staff_ids[0] if staff_ids else False

        # Check if booking already exists
        existing = x(models, db, uid, pw, 'appointment.booking', 'search',
                     [[('partner_id', '=', partner_id),
                       ('appointment_type_id', '=', apt_ids[0]),
                       ('start_datetime', '=', start_dt)]], {'limit': 1})
        if existing:
            print(f"  [ok] {apt_name} — already exists (id={existing[0]})")
            continue

        booking_id = x(models, db, uid, pw, 'appointment.booking', 'create', [{
            'appointment_type_id': apt_ids[0],
            'partner_id': partner_id,
            'guest_name': PORTAL_NAME,
            'guest_email': PORTAL_EMAIL,
            'guest_phone': PORTAL_PHONE,
            'guest_count': 1,
            'start_datetime': start_dt,
            'end_datetime': end_dt,
            'staff_user_id': staff_id,
            'state': 'draft',
        }])

        # Transition to target state
        if state == 'confirmed':
            try:
                x(models, db, uid, pw, 'appointment.booking', 'action_confirm', [[booking_id]])
            except Exception:
                x(models, db, uid, pw, 'appointment.booking', 'write',
                  [[booking_id], {'state': 'confirmed'}])
        elif state == 'done':
            try:
                x(models, db, uid, pw, 'appointment.booking', 'action_confirm', [[booking_id]])
                x(models, db, uid, pw, 'appointment.booking', 'action_done', [[booking_id]])
            except Exception:
                x(models, db, uid, pw, 'appointment.booking', 'write',
                  [[booking_id], {'state': 'done'}])

        print(f"  [ok] {apt_name} — {state} (id={booking_id})")


# ─── Sale Orders ────────────────────────────────────────────────
SALE_ORDERS = [
    # (product_name_partial, qty, price, date, confirmed)
    ("療程 - 初次諮詢", 1, 500, "2026-04-10", True),
    ("療程 - 玻尿酸填充", 1, 8000, "2026-04-25", True),
    ("療程 - 皮秒雷射", 1, 5000, "2026-05-08", True),
]


def seed_sale_orders(models, db, uid, pw, partner_id):
    """Create sale orders for completed appointments."""
    print("\n── Seeding sale orders ──")
    order_ids = []

    for product_name, qty, price, date_str, confirmed in SALE_ORDERS:
        # Find product
        prod_ids = x(models, db, uid, pw, 'product.product', 'search',
                     [[('name', '=', product_name)]], {'limit': 1})
        if not prod_ids:
            print(f"  [SKIP] Product '{product_name}' not found")
            continue

        # Check existing
        existing = x(models, db, uid, pw, 'sale.order', 'search',
                     [[('partner_id', '=', partner_id),
                       ('date_order', '>=', f"{date_str} 00:00:00"),
                       ('date_order', '<=', f"{date_str} 23:59:59"),
                       ('order_line.product_id', '=', prod_ids[0])]], {'limit': 1})
        if existing:
            order_ids.append(existing[0])
            print(f"  [ok] {product_name} — already exists (id={existing[0]})")
            continue

        order_id = x(models, db, uid, pw, 'sale.order', 'create', [{
            'partner_id': partner_id,
            'date_order': f"{date_str} 10:00:00",
            'order_line': [(0, 0, {
                'product_id': prod_ids[0],
                'product_uom_qty': qty,
                'price_unit': price,
            })],
        }])
        order_ids.append(order_id)

        if confirmed:
            try:
                x(models, db, uid, pw, 'sale.order', 'action_confirm', [[order_id]])
            except Exception as e:
                print(f"        [WARN] Could not confirm SO: {e}")

        print(f"  [ok] {product_name} — TWD {price:,} (id={order_id})")

    return order_ids


# ─── Invoices ───────────────────────────────────────────────────
def seed_invoices(models, db, uid, pw, partner_id, order_ids):
    """Create invoices from confirmed sale orders via wizard."""
    print("\n── Seeding invoices ──")

    for order_id in order_ids:
        order = x(models, db, uid, pw, 'sale.order', 'read',
                  [order_id], {'fields': ['state', 'name', 'invoice_ids']})
        if not order:
            continue
        order = order[0]

        if order.get('invoice_ids'):
            print(f"  [ok] {order['name']} — invoice already exists")
            continue

        if order['state'] != 'sale':
            print(f"  [SKIP] {order['name']} — not confirmed (state={order['state']})")
            continue

        try:
            # Use sale.advance.payment.inv wizard to create invoice
            ctx = {'active_ids': [order_id], 'active_model': 'sale.order'}
            wiz_id = x(models, db, uid, pw, 'sale.advance.payment.inv', 'create',
                       [{'advance_payment_method': 'delivered'}], {'context': ctx})
            x(models, db, uid, pw, 'sale.advance.payment.inv',
              'create_invoices', [[wiz_id]], {'context': ctx})
            print(f"  [ok] {order['name']} — invoice created via wizard")
        except Exception:
            try:
                # Fallback: create account.move directly
                so_lines = x(models, db, uid, pw, 'sale.order.line', 'search_read',
                             [[('order_id', '=', order_id)]],
                             {'fields': ['product_id', 'product_uom_qty', 'price_unit', 'name']})
                invoice_lines = []
                for line in so_lines:
                    invoice_lines.append((0, 0, {
                        'name': line['name'],
                        'product_id': line['product_id'][0] if line['product_id'] else False,
                        'quantity': line['product_uom_qty'],
                        'price_unit': line['price_unit'],
                    }))
                inv_id = x(models, db, uid, pw, 'account.move', 'create', [{
                    'partner_id': partner_id,
                    'move_type': 'out_invoice',
                    'invoice_line_ids': invoice_lines,
                }])
                print(f"  [ok] {order['name']} — invoice created directly (id={inv_id})")
            except Exception as e2:
                print(f"  [WARN] {order['name']} — could not create invoice: {e2}")


# ─── Main ───────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Seed Mujimed B2C customer data")
    parser.add_argument('--url', default=ODOO_URL)
    parser.add_argument('--db', default=ODOO_DB)
    parser.add_argument('--user', default=ADMIN_USER)
    parser.add_argument('--password', default=ADMIN_PASS)
    args = parser.parse_args()

    uid, models = connect(args.url, args.db, args.user, args.password)
    db, pw = args.db, args.password

    portal_uid, partner_id = seed_portal_user(models, db, uid, pw)
    seed_loyalty(models, db, uid, pw, partner_id)
    seed_bookings(models, db, uid, pw, partner_id)
    order_ids = seed_sale_orders(models, db, uid, pw, partner_id)
    seed_invoices(models, db, uid, pw, partner_id, order_ids)

    print(f"\n══════════════════════════════════════")
    print(f" Portal user: {PORTAL_LOGIN} / {PORTAL_PASSWORD}")
    print(f" Customer:    {PORTAL_NAME} ({PORTAL_EMAIL})")
    print(f" Loyalty:     {len(LOYALTY_PROGRAMS)} cards")
    print(f" Bookings:    {len(BOOKINGS)} appointments")
    print(f" Orders:      {len(SALE_ORDERS)} sale orders")
    print(f"══════════════════════════════════════")
    print(f" Login at B2C: https://b2cmujimed-odoo.woowtech.io")


if __name__ == '__main__':
    main()
