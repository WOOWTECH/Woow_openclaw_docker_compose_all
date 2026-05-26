# -*- coding: utf-8 -*-
import base64
import csv
import io
from collections import OrderedDict
from datetime import datetime

from odoo import _, api, Command, fields, models
from odoo.exceptions import UserError


REQUIRED_COLUMNS = {'ORDER', 'CUSTOMER', 'PRODUCT', 'QUANTITY', 'PRICE', 'DATE'}
OPTIONAL_COLUMNS = {'TAX', 'DISCOUNT'}


class ImportPosOrderWizard(models.TransientModel):
    _name = 'import.pos.order.wizard'
    _description = 'Import POS Orders'

    pos_config_id = fields.Many2one(
        'pos.config', string='POS Store', required=True,
        help='Target POS store. Orders will be created in this store '
             'and stock will be deducted from its warehouse.',
    )
    file = fields.Binary(string='File')
    file_name = fields.Char(string='File Name')
    import_type = fields.Selection([
        ('csv', 'CSV'),
        ('excel', 'Excel (.xlsx)'),
    ], string='File Type', default='csv', required=True)
    product_by = fields.Selection([
        ('name', 'Name'),
        ('code', 'Internal Reference'),
        ('barcode', 'Barcode'),
    ], string='Product Match By', default='name', required=True)
    error_mode = fields.Selection([
        ('strict', 'Strict (all or nothing)'),
        ('flexible', 'Flexible (skip error rows)'),
    ], string='Error Handling', default='strict', required=True)

    # ── Main entry point ──────────────────────────────────────────

    def action_import(self):
        self.ensure_one()
        if not self.file:
            raise UserError(_("Please upload a file."))

        data = base64.b64decode(self.file)
        rows = self._parse_csv(data) if self.import_type == 'csv' else self._parse_excel(data)

        if not rows:
            raise UserError(_("The file is empty or has no data rows."))

        self._validate_headers(set(rows[0].keys()))

        # Group rows by ORDER reference
        order_groups = OrderedDict()
        for idx, row in enumerate(rows, start=2):
            order_ref = (row.get('ORDER') or '').strip()
            if not order_ref:
                raise UserError(_("Row %d: ORDER column is empty.") % idx)
            order_groups.setdefault(order_ref, []).append((idx, row))

        # Ensure pay_later payment method is available
        pay_later_pm = self._ensure_pay_later_pm()

        # Open a batch POS session
        session = self._open_batch_session()

        try:
            if self.error_mode == 'strict':
                created_ids = self._import_strict(order_groups, session, pay_later_pm)
                errors = []
            else:
                created_ids, errors = self._import_flexible(order_groups, session, pay_later_pm)
        except Exception:
            # On failure, try to close the session cleanly
            self._close_session(session)
            raise

        # Close the batch session
        self._close_session(session)

        if not created_ids:
            raise UserError(_("No orders were imported."))

        created_orders = self.env['pos.order'].browse(created_ids)
        total_lines = sum(len(o.lines) for o in created_orders)

        msg = _("Successfully imported %d POS order(s) with %d line(s) "
                "into %s.") % (len(created_orders), total_lines,
                               self.pos_config_id.name)

        if errors:
            msg += '\n\n' + _("Skipped rows:") + '\n'
            for row_num, error_msg in errors:
                msg += _("  Row %d: %s") % (row_num, error_msg) + '\n'

        # Show imported orders
        action = self.env['ir.actions.act_window']._for_xml_id(
            'point_of_sale.action_pos_pos_form'
        )
        action['domain'] = [('id', 'in', created_ids)]
        action['context'] = {}
        action['help'] = msg
        action['target'] = 'main'
        return action

    # ── Session management ────────────────────────────────────────

    def _open_batch_session(self):
        """Open a new POS session for the batch import."""
        config = self.pos_config_id

        # Close any existing open sessions for this config
        open_sessions = self.env['pos.session'].search([
            ('config_id', '=', config.id),
            ('state', '!=', 'closed'),
        ])
        for s in open_sessions:
            self._close_session(s)

        # Disable cash control for batch import
        config.write({'cash_control': False})

        session = self.env['pos.session'].create({'config_id': config.id})
        session.action_pos_session_open()
        return session

    def _close_session(self, session):
        """Close a POS session, handling state transitions."""
        if session.state == 'closed':
            return
        try:
            session.action_pos_session_closing_control()
        except Exception:
            pass
        if session.state != 'closing_control':
            session.write({'state': 'closing_control'})
        try:
            session.action_pos_session_validate()
        except Exception:
            pass

    def _ensure_pay_later_pm(self):
        """Ensure pay_later payment method exists and is on the POS config."""
        PaymentMethod = self.env['pos.payment.method']
        config = self.pos_config_id

        # Find existing pay_later PM (filter in Python — type search
        # is unreliable on pos.payment.method in Odoo 18)
        all_pms = PaymentMethod.search([
            ('company_id', '=', config.company_id.id),
        ])
        pay_later = all_pms.filtered(lambda pm: pm.type == 'pay_later')[:1]

        if not pay_later:
            pay_later = PaymentMethod.create({
                'name': _('Customer Account'),
                'type': 'pay_later',
                'is_cash_count': False,
                'company_id': config.company_id.id,
                'split_transactions': True,
            })

        # Add to POS config if not already there
        if pay_later not in config.payment_method_ids:
            config.write({
                'payment_method_ids': [Command.link(pay_later.id)],
            })

        return pay_later

    # ── Import logic ──────────────────────────────────────────────

    def _import_strict(self, order_groups, session, pay_later_pm):
        """Validate all orders first, then create. All or nothing."""
        prepared = []
        errors = []
        for order_ref, rows in order_groups.items():
            try:
                vals = self._prepare_pos_order(order_ref, rows, session, pay_later_pm)
                prepared.append(vals)
            except UserError as e:
                errors.append((rows[0][0], str(e)))

        if errors:
            error_details = '\n'.join(
                _("Row %d: %s") % (r, m) for r, m in errors
            )
            raise UserError(
                _("Import failed. No orders were created.\n\n%s") % error_details
            )

        created_ids = []
        for vals in prepared:
            order = self.env['pos.order'].create(vals)
            try:
                order.action_pos_order_paid()
            except Exception:
                pass
            created_ids.append(order.id)

        return created_ids

    def _import_flexible(self, order_groups, session, pay_later_pm):
        """Import valid orders, skip errors."""
        created_ids = []
        errors = []
        for order_ref, rows in order_groups.items():
            try:
                vals = self._prepare_pos_order(order_ref, rows, session, pay_later_pm)
                order = self.env['pos.order'].create(vals)
                try:
                    order.action_pos_order_paid()
                except Exception:
                    pass
                created_ids.append(order.id)
            except (UserError, ValueError, KeyError) as e:
                for row_num, _ in rows:
                    errors.append((row_num, str(e)))
        return created_ids, errors

    def _prepare_pos_order(self, order_ref, rows, session, pay_later_pm):
        """Build pos.order values dict from grouped CSV rows."""
        first_row = rows[0][1]
        partner = self._find_partner(
            (first_row.get('CUSTOMER') or '').strip(), rows[0][0]
        )

        # Build order lines
        order_lines = []
        subtotal = 0
        for row_num, row in rows:
            product = self._find_product(
                (row.get('PRODUCT') or '').strip(), row_num
            )
            qty = self._parse_float(row.get('QUANTITY', ''), 'QUANTITY', row_num)
            price = self._parse_float(row.get('PRICE', ''), 'PRICE', row_num)

            discount = 0
            discount_str = (row.get('DISCOUNT') or '').strip()
            if discount_str:
                discount = self._parse_float(discount_str, 'DISCOUNT', row_num)

            line_price = price * (1 - discount / 100)
            line_total = line_price * qty
            subtotal += line_total

            line_vals = {
                'product_id': product.id,
                'qty': qty,
                'price_unit': price,
                'price_subtotal': line_total,
                'price_subtotal_incl': line_total,
            }
            if discount:
                line_vals['discount'] = discount

            order_lines.append(Command.create(line_vals))

        return {
            'session_id': session.id,
            'partner_id': partner.id,
            'lines': order_lines,
            'amount_tax': 0,
            'amount_total': subtotal,
            'amount_paid': subtotal,
            'amount_return': 0,
            'payment_ids': [Command.create({
                'amount': subtotal,
                'payment_method_id': pay_later_pm.id,
            })],
        }

    # ── Parsers ───────────────────────────────────────────────────

    def _parse_csv(self, data):
        try:
            text = data.decode('utf-8-sig')
        except UnicodeDecodeError:
            text = data.decode('latin-1')
        try:
            reader = csv.DictReader(io.StringIO(text))
            if reader.fieldnames:
                reader.fieldnames = [f.strip().upper() for f in reader.fieldnames]
            return list(reader)
        except csv.Error:
            raise UserError(
                _("Cannot read this file as CSV. "
                  "Please check the file format or select Excel (.xlsx).")
            )

    def _parse_excel(self, data):
        try:
            import openpyxl
        except ImportError:
            raise UserError(
                _("The 'openpyxl' Python library is required for Excel import. "
                  "Install it with: pip install openpyxl")
            )
        try:
            wb = openpyxl.load_workbook(
                io.BytesIO(data), read_only=True, data_only=True
            )
        except Exception:
            raise UserError(
                _("Cannot read this file as Excel (.xlsx). "
                  "Please check the file format or select CSV.")
            )
        sheet = wb.active
        rows_iter = sheet.iter_rows()
        header_row = next(rows_iter, None)
        if not header_row:
            return []
        headers = [
            (cell.value or '').strip().upper() for cell in header_row
        ]
        result = []
        for row in rows_iter:
            values = [
                str(cell.value).strip() if cell.value is not None else ''
                for cell in row
            ]
            if any(values):
                result.append(dict(zip(headers, values)))
        wb.close()
        return result

    def _validate_headers(self, headers):
        normalized = {h.strip().upper() for h in headers}
        missing = REQUIRED_COLUMNS - normalized
        if missing:
            raise UserError(
                _("Missing required columns: %s") % ', '.join(sorted(missing))
            )

    # ── Lookups ───────────────────────────────────────────────────

    def _find_partner(self, name, row_num):
        if not name:
            raise UserError(_("Row %d: CUSTOMER is empty.") % row_num)
        partner = self.env['res.partner'].search(
            [('name', '=ilike', name)], limit=1
        )
        if not partner:
            raise UserError(
                _("Row %d: Customer '%s' not found.") % (row_num, name)
            )
        return partner

    def _find_product(self, value, row_num):
        if not value:
            raise UserError(_("Row %d: PRODUCT is empty.") % row_num)
        field_map = {
            'name': 'name',
            'code': 'default_code',
            'barcode': 'barcode',
        }
        field_name = field_map[self.product_by]
        operator = '=ilike' if self.product_by == 'name' else '='
        product = self.env['product.product'].search(
            [(field_name, operator, value)], limit=1
        )
        if not product:
            label = dict(self._fields['product_by'].selection)[self.product_by]
            raise UserError(
                _("Row %d: Product with %s '%s' not found.") % (
                    row_num, label, value
                )
            )
        return product

    def _parse_float(self, value, field_name, row_num):
        if not value:
            raise UserError(
                _("Row %d: %s is empty.") % (row_num, field_name)
            )
        try:
            return float(value)
        except ValueError:
            raise UserError(
                _("Row %d: %s value '%s' is not a valid number.") % (
                    row_num, field_name, value
                )
            )

    # ── Template Downloads ────────────────────────────────────────

    def action_download_sample_csv(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/pos_order_import/static/data/sample_pos_order_import.csv',
            'target': 'self',
        }

    def action_download_sample_xlsx(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/pos_order_import/static/data/sample_pos_order_import.xlsx',
            'target': 'self',
        }
