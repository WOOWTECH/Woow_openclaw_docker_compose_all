# POS Order Import Module — Design Spec

## Purpose

Allow batch importing external platform orders (Shopee/momo/etc.) into POS as `pos.order` records using `pay_later` payment method. Each import targets a specific POS store, deducting stock from that store's warehouse. Accounting entries record receivables (`not_paid`) until the external platform remits payment.

## Module

- **Name:** `pos_order_import`
- **Depends:** `point_of_sale`
- **Parallel to:** `sale_order_import` (independent, no dependency)

## CSV Format

Same columns as `sale_order_import`:

```
ORDER,CUSTOMER,PRODUCT,QUANTITY,PRICE,DATE,TAX,DISCOUNT
SHOPEE-001,王小明,善緣香,2,899,2026-05-20,,
SHOPEE-001,王小明,財神香,1,899,2026-05-20,,
SHOPEE-002,李小花,柬埔寨沉香,1,1200,2026-05-21,,5
```

- Rows grouped by ORDER reference
- CUSTOMER must exist in `res.partner`
- PRODUCT matched by name/internal ref/barcode

## Wizard Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pos_config_id` | Many2one → pos.config | Yes | Target POS store |
| `file` | Binary | Yes | CSV or Excel file |
| `import_type` | Selection | Yes | CSV / Excel (.xlsx) |
| `product_by` | Selection | Yes | Name / Internal Reference / Barcode |
| `error_mode` | Selection | Yes | Strict / Flexible |

No `state_option` field — POS orders are always paid→done.

## Processing Flow

```
1. Parse CSV/Excel → validate headers → group by ORDER
2. Ensure pay_later PM exists on target POS config
3. Open a single batch POS session for the target store
4. For each ORDER group:
   a. Find/validate customer
   b. Find/validate products
   c. Create pos.order with:
      - session_id = batch session
      - partner_id = customer
      - lines = product lines (with optional discount)
      - payment_ids = [{pay_later PM, amount_total}]
   d. Call action_pos_order_paid()
5. Close session (action_pos_session_closing_control → validate)
6. Return result: count of imported orders, any errors
```

## Key Behaviors

- **Payment method:** Always `pay_later` (type=`pay_later`, name=`客戶帳戶`). If not on the target POS config, automatically added.
- **Warehouse isolation:** POS config → warehouse_id → stock deducted from that warehouse on session close.
- **Accounting:** Session close creates POSS journal entries with `payment_state=not_paid` (receivable). Settled manually when platform remits.
- **One session per import:** All orders in one batch go into a single session. Session opens before import, closes after.
- **Error handling:** Strict (all-or-nothing) or Flexible (skip bad rows). On strict failure, session is abandoned (no orders created).

## Menu Placement

```
Point of Sale / Orders / Import POS Orders  (sequence=50)
```

Parent: `point_of_sale.pos_order_menu` (POS → Orders)

## Module Structure

```
pos_order_import/
├── __init__.py
├── __manifest__.py
├── wizard/
│   ├── __init__.py
│   ├── pos_order_import_wizard.py
│   └── pos_order_import_wizard_views.xml
├── views/
│   └── pos_order_import_menu.xml
├── static/data/
│   ├── sample_pos_order_import.csv
│   └── sample_pos_order_import.xlsx
├── security/
│   └── ir.model.access.csv
└── i18n/
    └── zh_TW.po
```

## Security

- Access: `point_of_sale.group_pos_manager` (POS Manager)
- Read/Create on transient model `import.pos.order.wizard`

## Result Action

After import, redirect to POS Orders list filtered by the created order IDs:

```python
action = self.env['ir.actions.act_window']._for_xml_id('point_of_sale.action_pos_pos_form')
action['domain'] = [('id', 'in', created_order_ids)]
```

## Out of Scope

- Loyalty/reward line import from CSV
- Automatic payment reconciliation when platform remits
- POS frontend (JS) integration — this is a backend wizard only
