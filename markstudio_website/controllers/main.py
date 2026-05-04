# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from werkzeug.utils import redirect


class MarkStudioWebsite(http.Controller):

    @http.route('/', type='http', auth='public', website=True, sitemap=True)
    def homepage(self, **kw):
        return request.render('markstudio_website.homepage')

    @http.route('/news', type='http', auth='public', website=True, sitemap=False)
    def news_page(self, **kw):
        return redirect('/#news', code=301)
