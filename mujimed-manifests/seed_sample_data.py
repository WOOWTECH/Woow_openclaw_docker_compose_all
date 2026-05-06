#!/usr/bin/env python3
"""
Mujimed Staff Sample Data Seeder
Seeds realistic employee data for staff/staff (陳美玲 / 行政助理)
to demonstrate the woow_hr_portal (Office Assistant) module.

Usage:
    python3 seed_sample_data.py [--url URL] [--db DB]

Requires: Odoo 18 instance running with all WOOWTECH addons installed.
Idempotent: safe to run multiple times.
"""
import xmlrpc.client
import random
import sys
import argparse
from datetime import datetime, date

# ─── Configuration ──────────────────────────────────────────────
ODOO_URL = "https://mujimed-odoo.woowtech.io"
ODOO_DB = "mujimed"
ADMIN_USER = "admin"
ADMIN_PASS = "admin"


# ─── Connection ─────────────────────────────────────────────────
def connect(url=ODOO_URL, db=ODOO_DB, user=ADMIN_USER, password=ADMIN_PASS):
    """Authenticate and return (uid, models proxy)."""
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, user, password, {})
    if not uid:
        print("[ERROR] Authentication failed. Check credentials.")
        sys.exit(1)
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    print(f"[ok] Connected as uid={uid}")
    return uid, models, db, password


def search(models, db, uid, pw, model, domain, limit=0):
    """Search helper."""
    return models.execute_kw(db, uid, pw, model, 'search', [domain], {'limit': limit})


def search_read(models, db, uid, pw, model, domain, fields, limit=0):
    """Search + read helper."""
    return models.execute_kw(db, uid, pw, model, 'search_read', [domain], {'fields': fields, 'limit': limit})


def create(models, db, uid, pw, model, vals):
    """Create record helper."""
    return models.execute_kw(db, uid, pw, model, 'create', [vals])


def write(models, db, uid, pw, model, ids, vals):
    """Write record helper."""
    return models.execute_kw(db, uid, pw, model, 'write', [ids, vals])


# ─── Task 2: Staff User + Employee ─────────────────────────────
def seed_staff_user(models, db, uid, pw):
    """Create staff/staff portal user and linked employee."""
    # Check if user already exists
    existing = search(models, db, uid, pw, 'res.users', [('login', '=', 'staff')])
    if existing:
        print("[ok] staff user already exists")
        staff_uid = existing[0]
    else:
        # Get portal group id
        portal_group = search(models, db, uid, pw, 'res.groups',
                              [('category_id.name', '=', 'User types'),
                               ('name', 'ilike', 'Portal')])
        if not portal_group:
            print("[ERROR] Portal group not found")
            return None, None

        staff_uid = create(models, db, uid, pw, 'res.users', {
            'name': '陳美玲',
            'login': 'staff',
            'password': 'staff',
            'lang': 'zh_TW',
            'tz': 'Asia/Taipei',
            'active': True,
            'groups_id': [(6, 0, portal_group)],
        })
        print(f"[ok] Created staff user (uid={staff_uid})")

    # Ensure password is set (also handles pre-existing users)
    write(models, db, uid, pw, 'res.users', [staff_uid], {'password': 'staff'})

    # Get or create department
    dept_ids = search(models, db, uid, pw, 'hr.department', [('name', '=', '行政部')])
    if dept_ids:
        dept_id = dept_ids[0]
    else:
        dept_id = create(models, db, uid, pw, 'hr.department', {
            'name': '行政部',
        })
        print(f"[ok] Created department 行政部 (id={dept_id})")

    # Check if employee exists
    emp_ids = search(models, db, uid, pw, 'hr.employee', [('user_id', '=', staff_uid)])
    if emp_ids:
        print(f"[ok] Employee already exists (id={emp_ids[0]})")
        return staff_uid, emp_ids[0]

    emp_id = create(models, db, uid, pw, 'hr.employee', {
        'name': '陳美玲',
        'user_id': staff_uid,
        'job_title': '行政助理',
        'department_id': dept_id,
        'work_email': 'staff@mujimed.com',
    })
    print(f"[ok] Created employee 陳美玲 (id={emp_id})")
    return staff_uid, emp_id


# ─── Task 3: Attendance Records ─────────────────────────────────
def seed_attendance(models, db, uid, pw, emp_id):
    """Create ~20 attendance records for April 2026."""
    # Check if attendance already seeded
    existing = search(models, db, uid, pw, 'hr.attendance', [
        ('employee_id', '=', emp_id),
        ('check_in', '>=', '2026-04-01 00:00:00'),
        ('check_in', '<=', '2026-04-30 23:59:59'),
    ])
    if existing:
        print(f"[ok] Attendance already seeded ({len(existing)} records)")
        return

    # April 2026 working days (exclude weekends, 4/4 清明節, leave days)
    leave_days = {4, 14, 22, 28, 29}  # 4=清明節, others=leave

    random.seed(42)  # Reproducible
    count = 0
    for day in range(1, 31):
        d = date(2026, 4, day)
        # Skip weekends
        if d.weekday() >= 5:
            continue
        # Skip holidays and leave days
        if day in leave_days:
            continue

        # Check-in: 09:00 ± 10 min Taipei (= 01:00 UTC ± 10 min)
        ci_min = random.randint(0, 10)
        ci_dt = datetime(2026, 4, day, 1, ci_min, random.randint(0, 59))

        # Check-out: 18:00 ± 15 min (18:00 Taipei = 10:00 UTC)
        co_min = random.randint(0, 15)
        co_dt = datetime(2026, 4, day, 10, co_min, random.randint(0, 59))

        # GPS: Taipei with minor variance
        lat_base, lng_base = 25.0330, 121.5654
        in_lat = lat_base + random.uniform(-0.001, 0.001)
        in_lng = lng_base + random.uniform(-0.001, 0.001)
        out_lat = lat_base + random.uniform(-0.001, 0.001)
        out_lng = lng_base + random.uniform(-0.001, 0.001)

        create(models, db, uid, pw, 'hr.attendance', {
            'employee_id': emp_id,
            'check_in': ci_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'check_out': co_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'in_latitude': in_lat,
            'in_longitude': in_lng,
            'out_latitude': out_lat,
            'out_longitude': out_lng,
            'in_mode': 'systray',
            'out_mode': 'systray',
        })
        count += 1

    print(f"[ok] Created {count} attendance records")


# ─── Task 4: Leave Types, Allocations, Requests ─────────────────
def seed_leaves(models, db, uid, pw, emp_id):
    """Create leave types, allocations, and leave requests."""
    # Check if leaves already exist
    existing = search(models, db, uid, pw, 'hr.leave', [
        ('employee_id', '=', emp_id),
        ('date_from', '>=', '2026-04-01'),
        ('date_from', '<=', '2026-04-30'),
    ])
    if existing:
        print(f"[ok] Leaves already seeded ({len(existing)} records)")
        return

    # Get or create leave types
    annual_ids = search(models, db, uid, pw, 'hr.leave.type', [('name', '=', '特休假')])
    if annual_ids:
        annual_lt = annual_ids[0]
    else:
        annual_lt = create(models, db, uid, pw, 'hr.leave.type', {
            'name': '特休假',
            'requires_allocation': 'yes',
            'leave_validation_type': 'hr',
        })
        print(f"[ok] Created leave type 特休假 (id={annual_lt})")

    sick_ids = search(models, db, uid, pw, 'hr.leave.type', [('name', '=', '病假')])
    if sick_ids:
        sick_lt = sick_ids[0]
    else:
        sick_lt = create(models, db, uid, pw, 'hr.leave.type', {
            'name': '病假',
            'requires_allocation': 'no',
            'leave_validation_type': 'hr',
        })
        print(f"[ok] Created leave type 病假 (id={sick_lt})")

    # Create allocation for annual leave (14 days)
    alloc_ids = search(models, db, uid, pw, 'hr.leave.allocation', [
        ('employee_id', '=', emp_id),
        ('holiday_status_id', '=', annual_lt),
        ('state', '=', 'validate'),
    ])
    if not alloc_ids:
        alloc_id = create(models, db, uid, pw, 'hr.leave.allocation', {
            'employee_id': emp_id,
            'holiday_status_id': annual_lt,
            'number_of_days': 14,
            'date_from': '2026-01-01',
            'state': 'confirm',
        })
        # Approve the allocation
        models.execute_kw(db, uid, pw, 'hr.leave.allocation', 'action_validate', [[alloc_id]])
        print("[ok] Created and approved 14-day annual leave allocation")

    # Leave 1: 特休 4/14 (approved)
    leave1 = create(models, db, uid, pw, 'hr.leave', {
        'employee_id': emp_id,
        'holiday_status_id': annual_lt,
        'request_date_from': '2026-04-14',
        'request_date_to': '2026-04-14',
        'name': '個人事務',
    })
    models.execute_kw(db, uid, pw, 'hr.leave', 'action_validate', [[leave1]])
    print("[ok] Created leave 4/14 特休 (approved)")

    # Leave 2: 病假 4/22 (approved)
    leave2 = create(models, db, uid, pw, 'hr.leave', {
        'employee_id': emp_id,
        'holiday_status_id': sick_lt,
        'request_date_from': '2026-04-22',
        'request_date_to': '2026-04-22',
        'name': '身體不適',
    })
    models.execute_kw(db, uid, pw, 'hr.leave', 'action_validate', [[leave2]])
    print("[ok] Created leave 4/22 病假 (approved)")

    # Leave 3: 特休 4/28-4/29 (pending - stay in confirm state)
    create(models, db, uid, pw, 'hr.leave', {
        'employee_id': emp_id,
        'holiday_status_id': annual_lt,
        'request_date_from': '2026-04-28',
        'request_date_to': '2026-04-29',
        'name': '家庭旅遊',
    })
    print("[ok] Created leave 4/28-29 特休 (pending)")


# ─── Task 5: Expense Products and Records ───────────────────────
def seed_expenses(models, db, uid, pw, emp_id):
    """Create expense products and expense records."""
    existing = search(models, db, uid, pw, 'hr.expense', [
        ('employee_id', '=', emp_id),
        ('date', '>=', '2026-04-01'),
        ('date', '<=', '2026-04-30'),
    ])
    if existing:
        print(f"[ok] Expenses already seeded ({len(existing)} records)")
        return

    # Create expense products
    def get_or_create_product(name):
        ids = search(models, db, uid, pw, 'product.product',
                     [('name', '=', name), ('can_be_expensed', '=', True)])
        if ids:
            return ids[0]
        pid = create(models, db, uid, pw, 'product.product', {
            'name': name,
            'can_be_expensed': True,
            'type': 'service',
            'list_price': 0,
        })
        print(f"  [ok] Created product: {name}")
        return pid

    transport_prod = get_or_create_product('交通費')
    office_prod = get_or_create_product('辦公用品')
    meal_prod = get_or_create_product('餐費')

    # Expense 1: Taxi (draft) — shows "Submit" button
    create(models, db, uid, pw, 'hr.expense', {
        'name': '計程車費 — 客戶拜訪來回',
        'employee_id': emp_id,
        'product_id': transport_prod,
        'total_amount_currency': 350.0,
        'date': '2026-04-10',
    })
    print("[ok] Created expense: 計程車費 (draft)")

    # Expense 2: Stationery (reported/submitted)
    exp2 = create(models, db, uid, pw, 'hr.expense', {
        'name': '辦公文具 — A4紙張、資料夾',
        'employee_id': emp_id,
        'product_id': office_prod,
        'total_amount_currency': 890.0,
        'date': '2026-04-15',
    })
    # Create expense sheet and submit
    # NOTE: Method names (action_submit_sheet, approve_expense_sheets)
    # may vary by Odoo 18 version — verify against running instance
    sheet_id = create(models, db, uid, pw, 'hr.expense.sheet', {
        'name': '2026年4月費用報銷 — 文具',
        'employee_id': emp_id,
        'expense_line_ids': [(4, exp2)],
    })
    models.execute_kw(db, uid, pw, 'hr.expense.sheet', 'action_submit_sheet', [[sheet_id]])
    print("[ok] Created expense: 辦公文具 (submitted)")

    # Expense 3: Team dinner (approved)
    exp3 = create(models, db, uid, pw, 'hr.expense', {
        'name': '員工聚餐攤提',
        'employee_id': emp_id,
        'product_id': meal_prod,
        'total_amount_currency': 500.0,
        'date': '2026-04-18',
    })
    sheet3 = create(models, db, uid, pw, 'hr.expense.sheet', {
        'name': '2026年4月費用報銷 — 聚餐',
        'employee_id': emp_id,
        'expense_line_ids': [(4, exp3)],
    })
    models.execute_kw(db, uid, pw, 'hr.expense.sheet', 'action_submit_sheet', [[sheet3]])
    models.execute_kw(db, uid, pw, 'hr.expense.sheet', 'approve_expense_sheets', [[sheet3]])
    print("[ok] Created expense: 員工聚餐 (approved)")


# ─── Task 6: Payroll Structure, Contract, Payslip ───────────────
def seed_payslip(models, db, uid, pw, emp_id):
    """Create salary structure, contract, and April payslip."""
    # Check if payslip already exists (any state — handles partial failures)
    existing = search(models, db, uid, pw, 'hr.payslip', [
        ('employee_id', '=', emp_id),
        ('date_from', '=', '2026-04-01'),
    ])
    if existing:
        print(f"[ok] Payslip already seeded (id={existing[0]})")
        return

    # ─── Salary Rule Categories ───
    def get_or_create_category(name, code):
        ids = search(models, db, uid, pw, 'hr.salary.rule.category',
                     [('code', '=', code)])
        if ids:
            return ids[0]
        return create(models, db, uid, pw, 'hr.salary.rule.category', {
            'name': name, 'code': code,
        })

    cat_basic = get_or_create_category('基本薪資', 'BASIC')
    cat_ded = get_or_create_category('扣款', 'DED')
    cat_net = get_or_create_category('淨額', 'NET')

    # ─── Salary Structure Type (for contract) ───
    struct_type_ids = search(models, db, uid, pw, 'hr.payroll.structure.type',
                            [('name', '=', '基本薪資類型')])
    if struct_type_ids:
        struct_type_id = struct_type_ids[0]
    else:
        struct_type_id = create(models, db, uid, pw, 'hr.payroll.structure.type', {
            'name': '基本薪資類型',
        })

    # ─── Salary Structure ───
    struct_ids = search(models, db, uid, pw, 'hr.payroll.structure',
                       [('name', '=', '基本薪資結構')])
    if struct_ids:
        struct_id = struct_ids[0]
    else:
        struct_id = create(models, db, uid, pw, 'hr.payroll.structure', {
            'name': '基本薪資結構',
            'code': 'BASIC_STRUCT',
        })

    # ─── Salary Rules (linked via structure.rule_ids many2many) ───
    def get_or_create_rule(name, code, category_id, sequence, amount_fix):
        ids = search(models, db, uid, pw, 'hr.salary.rule',
                     [('code', '=', code)])
        if ids:
            return ids[0]
        return create(models, db, uid, pw, 'hr.salary.rule', {
            'name': name,
            'code': code,
            'category_id': category_id,
            'sequence': sequence,
            'amount_select': 'fix',
            'amount_fix': amount_fix,
        })

    rule_ids = []
    rule_ids.append(get_or_create_rule('底薪', 'BASIC_SALARY', cat_basic, 1, 32000))
    rule_ids.append(get_or_create_rule('勞保自付', 'LABOR_INS', cat_ded, 10, -1042))
    rule_ids.append(get_or_create_rule('健保自付', 'HEALTH_INS', cat_ded, 11, -372))
    rule_ids.append(get_or_create_rule('勞退自提', 'PENSION', cat_ded, 12, 0))
    rule_ids.append(get_or_create_rule('淨額', 'NET_SALARY', cat_net, 99, 30586))

    # Link rules to structure
    write(models, db, uid, pw, 'hr.payroll.structure', [struct_id],
          {'rule_ids': [(6, 0, rule_ids)]})

    # ─── Contract ───
    contract_ids = search(models, db, uid, pw, 'hr.contract', [
        ('employee_id', '=', emp_id), ('state', '=', 'open'),
    ])
    if contract_ids:
        contract_id = contract_ids[0]
    else:
        contract_id = create(models, db, uid, pw, 'hr.contract', {
            'name': '陳美玲 — 僱傭合約',
            'employee_id': emp_id,
            'wage': 32000,
            'date_start': '2025-01-01',
            'state': 'open',
            'structure_type_id': struct_type_id,
        })
        print(f"[ok] Created contract (id={contract_id})")

    # ─── Payslip ───
    payslip_id = create(models, db, uid, pw, 'hr.payslip', {
        'employee_id': emp_id,
        'name': '2026年4月薪資單 — 陳美玲',
        'date_from': '2026-04-01',
        'date_to': '2026-04-30',
        'contract_id': contract_id,
        'struct_id': struct_id,
        'state': 'draft',
    })

    # Directly create payslip lines (fixed amounts, no compute needed)
    lines = [
        ('底薪', 'BASIC_SALARY', cat_basic, 1, 32000),
        ('勞保自付', 'LABOR_INS', cat_ded, 10, -1042),
        ('健保自付', 'HEALTH_INS', cat_ded, 11, -372),
        ('勞退自提', 'PENSION', cat_ded, 12, 0),
        ('淨額', 'NET_SALARY', cat_net, 99, 30586),
    ]
    for name, code, cat_id, seq, amount in lines:
        # Find matching salary rule
        rule_ids = search(models, db, uid, pw, 'hr.salary.rule', [('code', '=', code)])
        rule_id = rule_ids[0] if rule_ids else False
        create(models, db, uid, pw, 'hr.payslip.line', {
            'slip_id': payslip_id,
            'name': name,
            'code': code,
            'category_id': cat_id,
            'sequence': seq,
            'amount': amount,
            'quantity': 1.0,
            'salary_rule_id': rule_id,
        })

    # Add worked days entry
    create(models, db, uid, pw, 'hr.payslip.worked_days', {
        'payslip_id': payslip_id,
        'name': '正常工作日',
        'code': 'WORK100',
        'number_of_days': 20,
        'number_of_hours': 160,
        'sequence': 1,
    })

    # Confirm payslip (state -> done)
    models.execute_kw(db, uid, pw, 'hr.payslip', 'action_payslip_done', [[payslip_id]])
    print(f"[ok] Created and confirmed April 2026 payslip (id={payslip_id})")


# ─── Main ───────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed staff sample data for Mujimed Odoo")
    parser.add_argument('--url', default=ODOO_URL, help='Odoo URL')
    parser.add_argument('--db', default=ODOO_DB, help='Database name')
    parser.add_argument('--user', default=ADMIN_USER, help='Admin login')
    parser.add_argument('--password', default=ADMIN_PASS, help='Admin password')
    args = parser.parse_args()

    uid, models, db, pw = connect(args.url, args.db, args.user, args.password)
    print("=" * 50)
    print("[mujimed] Staff Sample Data Seeder")
    print("=" * 50)

    staff_uid, emp_id = seed_staff_user(models, db, uid, pw)
    if not emp_id:
        print("[ERROR] Failed to create employee. Aborting.")
        sys.exit(1)

    seed_attendance(models, db, uid, pw, emp_id)
    seed_leaves(models, db, uid, pw, emp_id)
    seed_expenses(models, db, uid, pw, emp_id)
    seed_payslip(models, db, uid, pw, emp_id)

    print("=" * 50)
    print("[mujimed] All sample data seeded successfully!")
    print("  Login: staff / staff")
    print("  Portal: /my/office")
    print("=" * 50)
