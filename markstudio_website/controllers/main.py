# -*- coding: utf-8 -*-
# markstudio_website/controllers/main.py
# '/' 路由已移除：改由 Odoo 原生 Website.index() 處理首頁
# 首頁內容透過 inherit_id="website.homepage" 注入

from odoo import http
from werkzeug.utils import redirect


class MarkStudioWebsite(http.Controller):

    @http.route('/news', type='http', auth='public', website=True, sitemap=False)
    def news_page(self, **kw):
        return redirect('/#news', code=301)
