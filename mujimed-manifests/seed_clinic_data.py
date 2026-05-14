#!/usr/bin/env python3
"""
Mujimed Clinic Data Seeder
Seeds medical aesthetics clinic data: staff, products, appointment types.

Usage:
    python3 seed_clinic_data.py [--url URL] [--db DB] [--user USER] [--password PASSWORD]

Requires: Odoo 18 with reservation_module installed.
Idempotent: safe to run multiple times.
"""
import xmlrpc.client
import sys
import argparse

# ─── Configuration ──────────────────────────────────────────────
ODOO_URL = "https://mujimed-odoo.woowtech.io"
ODOO_DB = "mujimed"
ADMIN_USER = "admin"
ADMIN_PASS = "admin"


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


# ─── Staff Data ─────────────────────────────────────────────────
DOCTORS = [
    {"name": "陳志明醫師", "login": "dr.chen", "job": "微整形注射專科"},
    {"name": "林雅婷醫師", "login": "dr.lin", "job": "雷射光電專科"},
    {"name": "王建國醫師", "login": "dr.wang", "job": "體雕抗老專科"},
]

NURSES = [
    {"name": "張美玲護理師", "login": "nurse.zhang", "job": "注射助理"},
    {"name": "李佳蓉護理師", "login": "nurse.li", "job": "雷射操作"},
    {"name": "黃心怡護理師", "login": "nurse.huang", "job": "保養療程"},
]

# ─── Appointment Types ──────────────────────────────────────────
# (name, duration_minutes, price_twd, doctor_logins, nurse_logins)
APPOINTMENTS = [
    # 微整形注射
    ("玻尿酸填充", 30, 8000, ["dr.chen"], ["nurse.zhang"]),
    ("肉毒桿菌注射", 20, 6000, ["dr.chen"], ["nurse.zhang"]),
    ("膠原蛋白增生劑 (Sculptra)", 45, 15000, ["dr.chen"], ["nurse.zhang"]),
    ("消脂針", 30, 5000, ["dr.chen"], ["nurse.zhang"]),
    # 光電雷射
    ("皮秒雷射", 30, 5000, ["dr.lin"], ["nurse.li"]),
    ("飛梭雷射", 45, 6000, ["dr.lin"], ["nurse.li"]),
    ("淨膚雷射", 30, 3000, ["dr.lin"], ["nurse.li"]),
    ("脈衝光 (IPL)", 30, 3500, ["dr.lin"], ["nurse.li"]),
    ("除毛雷射", 30, 2500, ["dr.lin"], ["nurse.li"]),
    # 體雕療程
    ("冷凍溶脂", 60, 25000, ["dr.wang"], ["nurse.zhang"]),
    ("電波拉皮 (Thermage)", 60, 35000, ["dr.wang"], ["nurse.zhang"]),
    ("音波拉提 (HIFU)", 60, 30000, ["dr.wang"], ["nurse.zhang"]),
    # 臉部保養
    ("水光注射", 30, 4500, ["dr.chen", "dr.lin"], ["nurse.huang"]),
    ("導入保養", 45, 2000, ["dr.chen", "dr.lin"], ["nurse.huang"]),
    ("化學煥膚", 30, 2500, ["dr.chen", "dr.lin"], ["nurse.huang"]),
    ("杏仁酸煥膚", 30, 1800, ["dr.chen", "dr.lin"], ["nurse.huang"]),
    # 特殊療程
    ("PRP 自體血小板", 45, 12000, ["dr.chen", "dr.lin", "dr.wang"], ["nurse.zhang", "nurse.li"]),
    ("雷射除斑", 30, 6000, ["dr.lin", "dr.wang"], ["nurse.li"]),
    ("痘疤治療", 45, 5000, ["dr.lin", "dr.chen"], ["nurse.li", "nurse.huang"]),
    ("初次諮詢", 30, 500, ["dr.chen", "dr.lin", "dr.wang"], ["nurse.zhang", "nurse.li", "nurse.huang"]),
]

# Mon-Fri 09:00-12:00, 14:00-18:00; Sat 09:00-12:00
AVAILABILITY = [
    # (dayofweek, hour_from, hour_to) — 0=Mon .. 6=Sun
    ("0", 9.0, 12.0), ("0", 14.0, 18.0),
    ("1", 9.0, 12.0), ("1", 14.0, 18.0),
    ("2", 9.0, 12.0), ("2", 14.0, 18.0),
    ("3", 9.0, 12.0), ("3", 14.0, 18.0),
    ("4", 9.0, 12.0), ("4", 14.0, 18.0),
    ("5", 9.0, 12.0),  # Saturday morning only
]


def seed_staff(models, db, uid, pw):
    """Create doctor and nurse users."""
    print("\n── Seeding staff ──")
    # Get internal user group
    internal_group = x(models, db, uid, pw, 'ir.model.data', 'search_read',
                       [[('module', '=', 'base'), ('name', '=', 'group_user')]],
                       {'fields': ['res_id'], 'limit': 1})
    internal_gid = internal_group[0]['res_id'] if internal_group else False

    user_map = {}  # login -> user_id
    for staff in DOCTORS + NURSES:
        user_id = find_or_create(
            models, db, uid, pw, 'res.users',
            [('login', '=', staff['login'])],
            {
                'name': staff['name'],
                'login': staff['login'],
                'password': staff['login'],
                'lang': 'zh_TW',
                'tz': 'Asia/Taipei',
                'groups_id': [(4, internal_gid)] if internal_gid else [],
            }
        )
        user_map[staff['login']] = user_id
        print(f"  [ok] {staff['name']} (login={staff['login']}, id={user_id})")

    return user_map


def seed_products(models, db, uid, pw):
    """Create service products for each appointment type."""
    print("\n── Seeding products ──")
    # Get TWD currency
    twd_ids = x(models, db, uid, pw, 'res.currency', 'search',
                [[('name', '=', 'TWD')]], {'limit': 1})

    product_map = {}  # appointment_name -> product_id
    for name, _dur, price, _docs, _nurses in APPOINTMENTS:
        product_name = f"療程 - {name}"
        product_id = find_or_create(
            models, db, uid, pw, 'product.product',
            [('name', '=', product_name)],
            {
                'name': product_name,
                'type': 'service',
                'list_price': price,
                'sale_ok': True,
                'purchase_ok': False,
            }
        )
        product_map[name] = product_id
        print(f"  [ok] {product_name} — TWD {price:,} (id={product_id})")

    return product_map


def seed_appointment_types(models, db, uid, pw, user_map, product_map):
    """Create appointment types with staff, products, and availability."""
    print("\n── Seeding appointment types ──")

    for name, dur_min, _price, doc_logins, nurse_logins in APPOINTMENTS:
        # Collect staff user IDs
        staff_ids = []
        for login in doc_logins + nurse_logins:
            if login in user_map:
                staff_ids.append(user_map[login])

        product_id = product_map.get(name)
        duration_hours = dur_min / 60.0

        apt_id = find_or_create(
            models, db, uid, pw, 'appointment.type',
            [('name', '=', name)],
            {
                'name': name,
                'slot_duration': duration_hours,
                'slot_interval': duration_hours,
                'is_scheduled': True,
                'location_type': 'physical',
                'timezone': 'Asia/Taipei',
                'require_payment': True,
                'auto_confirm': True,
                'is_published': True,
                'assign_staff': True,
                'allow_customer_choose_staff': True,
                'staff_user_ids': [(6, 0, staff_ids)],
                'payment_product_ids': [(6, 0, [product_id])] if product_id else [],
            }
        )
        print(f"  [ok] {name} ({dur_min}min, staff={len(staff_ids)}, id={apt_id})")

        # Seed availability schedule
        existing_avail = x(models, db, uid, pw, 'appointment.availability', 'search',
                           [[('appointment_type_id', '=', apt_id)]], {})
        if not existing_avail:
            for dow, h_from, h_to in AVAILABILITY:
                x(models, db, uid, pw, 'appointment.availability', 'create', [{
                    'appointment_type_id': apt_id,
                    'dayofweek': dow,
                    'hour_from': h_from,
                    'hour_to': h_to,
                }])
            print(f"        availability: Mon-Fri 09-12/14-18, Sat 09-12")
        else:
            print(f"        availability: already set ({len(existing_avail)} slots)")


def main():
    parser = argparse.ArgumentParser(description="Seed Mujimed clinic data")
    parser.add_argument('--url', default=ODOO_URL)
    parser.add_argument('--db', default=ODOO_DB)
    parser.add_argument('--user', default=ADMIN_USER)
    parser.add_argument('--password', default=ADMIN_PASS)
    args = parser.parse_args()

    uid, models = connect(args.url, args.db, args.user, args.password)
    db, pw = args.db, args.password

    user_map = seed_staff(models, db, uid, pw)
    product_map = seed_products(models, db, uid, pw)
    seed_appointment_types(models, db, uid, pw, user_map, product_map)

    print("\n══════════════════════════════════════")
    print(f" Seeded: {len(DOCTORS)} doctors, {len(NURSES)} nurses")
    print(f" Seeded: {len(APPOINTMENTS)} products")
    print(f" Seeded: {len(APPOINTMENTS)} appointment types")
    print("══════════════════════════════════════")


if __name__ == '__main__':
    main()
