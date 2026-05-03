# -*- coding: utf-8 -*-
{
    'name': 'Mark Studio Website',
    'version': '18.0.1.0.0',
    'category': 'Website',
    'summary': '馬克健身按摩預約平台 — 前台頁面',
    'author': 'WoowTech',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [
        'views/news_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'markstudio_website/static/src/css/markstudio.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
