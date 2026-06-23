# -*- coding: utf-8 -*-
{
    'name': 'O.G 老地方身體修復 Website',
    'version': '18.0.4.0.0',
    'category': 'Website',
    'summary': 'O.G老地方身體修復 — Website Builder 可編輯首頁',
    'author': 'WoowTech',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [
        # Snippet 定義（必須在首頁之前載入）
        'views/snippets/s_og_hero.xml',
        'views/snippets/s_og_story.xml',
        'views/snippets/s_og_services.xml',
        'views/snippets/s_og_flow.xml',
        'views/snippets/s_og_booking.xml',
        'views/snippets/s_og_contact.xml',
        'views/snippets/snippets.xml',
        # 首頁（繼承 website.homepage）
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
        'portal.assets_chatter': [
            'markstudio_website/static/src/css/markstudio_chatter.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
