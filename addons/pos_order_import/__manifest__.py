# -*- coding: utf-8 -*-
{
    'name': 'POS Order Import',
    'author': 'WoowTech',
    'version': '18.0.1.0.0',
    'summary': 'Batch import POS orders from CSV or Excel files',
    'description': """
POS Order Import
================
Import POS orders in bulk from CSV or Excel (.xlsx) files.
Orders are created with pay_later payment method (Customer Account)
and stock is deducted from the selected POS store's warehouse.

Features:
- CSV and Excel (.xlsx) support
- Downloadable sample templates
- Product matching by name, internal reference, or barcode
- Pay-later payment (receivable until platform remits)
- Per-store warehouse isolation
- Strict or flexible error handling
- Bilingual: English + Traditional Chinese
    """,
    'license': 'LGPL-3',
    'depends': ['point_of_sale'],
    'external_dependencies': {
        'python': ['openpyxl'],
    },
    'data': [
        'security/ir.model.access.csv',
        'wizard/pos_order_import_wizard_views.xml',
        'views/pos_order_import_menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'category': 'Point Of Sale',
}
