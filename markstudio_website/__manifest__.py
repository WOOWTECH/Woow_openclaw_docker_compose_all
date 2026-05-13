# -*- coding: utf-8 -*-
{
    'name': 'Mark Studio Website',
    'version': '18.0.2.0.0',
    'category': 'Website',
    'summary': '馬克健身按摩預約平台 — 單頁式前台',
    'author': 'WoowTech',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [
        'views/homepage_templates.xml',
        'views/news_templates.xml',
        'views/appointment_templates.xml',
    ],
    'assets': {
        'web.assets_frontend_minimal': [
            'markstudio_website/static/src/js/appointment_detect.js',
        ],
        'web.assets_frontend': [
            'markstudio_website/static/src/css/markstudio.css',
            'markstudio_website/static/src/js/smooth_scroll.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
