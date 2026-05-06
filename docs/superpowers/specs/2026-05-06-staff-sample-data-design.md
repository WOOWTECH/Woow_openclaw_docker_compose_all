# Staff Sample Data — Design Spec

## Goal

Deploy the updated Odoo 18 mujimed instance and seed realistic employee sample data for `staff/staff` (陳美玲 / 行政助理) to demonstrate the `woow_hr_portal` (Office Assistant) module features.

## Accounts

| Login | Password | Role | Name |
|-------|----------|------|------|
| admin | admin | Manager/Boss, HR Manager | (existing) |
| staff | staff | Employee (Portal User) | 陳美玲 |

## Sample Data Scope (April 2026, one full month)

### 1. Employee Record

- Name: 陳美玲
- Job Title: 行政助理 (Administrative Assistant)
- Department: 行政部 (Administration)
- Work Email: staff@mujimed.com
- Linked to `staff` user
- Company: Mujimed
- Timezone: Asia/Taipei

### 2. Attendance (~20 records)

- Working days in April 2026 (exclude weekends, holidays, leave days)
- Check-in: ~09:00 ± random 0-10 min
- Check-out: ~18:00 ± random 0-15 min
- GPS coordinates: 25.0330, 121.5654 (Taipei) with minor variance
- Exclude: 4/14 (leave), 4/22 (leave), 4/28-4/29 (leave)

### 3. Leave

| Date | Type | Status |
|------|------|--------|
| 4/14 | 特休假 (Annual Leave) | validate (approved) |
| 4/22 | 病假 (Sick Leave) | validate (approved) |
| 4/28-4/29 | 特休假 (Annual Leave) | confirm (pending) |

Prerequisites:
- Leave types: 特休假, 病假 (with `requires_allocation = 'no'` or matching allocations)
- Leave allocation: 14 days Annual Leave for the employee

### 4. Expense

| Description | Amount | Category | Status |
|-------------|--------|----------|--------|
| 計程車費 (Taxi) | 350 TWD | 交通費 | draft |
| 辦公文具 (Stationery) | 890 TWD | 辦公用品 | reported (submitted) |
| 員工聚餐攤提 (Team dinner) | 500 TWD | 餐費 | approved |

Prerequisites:
- Expense product categories: 交通費, 辦公用品, 餐費 (with `can_be_expensed = True`)

### 5. Payslip (April 2026, state=done)

Salary Structure: 基本薪資結構 (Basic Salary Structure)

| Rule | Category | Amount |
|------|----------|--------|
| 底薪 (Basic Salary) | BASIC | +32,000 |
| 勞保自付 (Labor Insurance) | DED | -1,042 |
| 健保自付 (Health Insurance) | DED | -372 |
| 勞退自提 (Pension) | DED | 0 |
| 淨額 (Net Salary) | NET | =30,586 |

Prerequisites:
- Salary rule categories: BASIC, DED (Deduction), NET
- Salary rules with proper computation
- hr.contract for the employee with salary structure assigned
- Worked days entry (standard working days)

## Technical Notes

### Module Directory Naming

`Woow_odoo_office_enhance` repo must be extracted to directory `woow_hr_portal/` (not the repo name) because `__manifest__.py` references assets as `woow_hr_portal/static/src/...`. The download script uses tuple `(repo_name, local_dir_name)` to handle this rename.

### Payslip PDF Report

The report `hr_payroll_community.report_payslipdetails` is provided by the `hr_payroll_community` module inside the `hr_payslip_monthly_report` repo. No additional modules needed.

### Expense States (Odoo 18)

- `draft` → not yet submitted (shows "Submit" button)
- `reported` → in an expense sheet (submitted to manager)
- `approved` → manager approved
- `done` → paid

### Expense Categories

These are `product.product` records with `can_be_expensed = True`, not `product.category`.

### Contract Requirements

`hr.contract` must have: `state = 'open'`, valid `date_start`, `wage = 32000`, linked `structure_type_id`.

### April 2026 Holidays (Taiwan)

Exclude from attendance: Apr 4 (清明節), weekends. Working days: ~20 days.

## Implementation Approach

A Python script (`mujimed-manifests/seed_sample_data.py`) that connects via XML-RPC to the running Odoo instance and creates all sample data programmatically. This script runs as a post-deploy step after Odoo is fully initialized.

The script will:
1. Authenticate as admin
2. Create `staff` user with `base.group_portal` group and set `user_id` on employee
3. Create department, leave types, expense products (`can_be_expensed=True`)
4. Create salary structure, rules, categories, and contract
5. Insert attendance (with GPS + `in_mode='systray'`), leave, expense, and payslip records
6. Be idempotent (skip if data already exists)

## Success Criteria

- `staff/staff` can log in to portal at `/my/office`
- Attendance hub shows ~20 records with check-in/out times and GPS
- Leave page shows balance cards and 3 leave requests in different states
- Expense page shows 3 expenses; the draft one has "Submit" button
- Payslip page shows April 2026 payslip with correct net amount and PDF download works
