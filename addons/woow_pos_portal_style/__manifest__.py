{
    'name': 'Woow POS Portal Style',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': '自訂銷售點與廚房顯示螢幕的入口圖示與說明',
    'description': """
        Customizes the portal/home cards for Point of Sale and Kitchen Display:
        - Unique flat-style SVG icons for POS and Kitchen Display
        - 8-12 character Chinese descriptions under each card title
        - Consistent visual design with other module cards
    """,
    'author': 'WOOWTECH',
    'website': 'https://woowtech.io',
    'depends': ['point_of_sale', 'pos_restaurant'],
    'assets': {
        'web.assets_frontend': [
            'woow_pos_portal_style/static/src/css/pos_portal_cards.css',
            'woow_pos_portal_style/static/src/js/pos_portal_cards.js',
        ],
        'web.assets_backend': [
            'woow_pos_portal_style/static/src/css/pos_portal_cards.css',
            'woow_pos_portal_style/static/src/js/pos_portal_cards.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
