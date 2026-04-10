#!/usr/bin/env python3
"""
Mujimed Content Migration Helper
Connects to Odoo XML-RPC and provides utility functions for content migration.
"""
import xmlrpc.client
import urllib.request
import base64
import ssl
import re
import time
from html.parser import HTMLParser

ODOO_URL = "https://mujimed-odoo.woowtech.io"
ODOO_DB = "mujimed"
ODOO_USER = "admin"
ODOO_PASS = "admin"
ODOO_UID = 2

# SSL context for fetching images
SSL_CTX = ssl.create_default_context()

def get_models():
    return xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

def create_blog_post(models, blog_id, title, content_html, tag_ids=None,
                     subtitle="", cover_image_url=None, published=True):
    """Create a blog post with optional cover image."""
    vals = {
        'blog_id': blog_id,
        'name': title,
        'subtitle': subtitle,
        'content': content_html,
        'is_published': published,
        'website_published': published,
    }
    if tag_ids:
        vals['tag_ids'] = [(6, 0, tag_ids)]

    post_id = models.execute_kw(ODOO_DB, ODOO_UID, ODOO_PASS,
                                 'blog.post', 'create', [vals])

    # Upload cover image if provided
    if cover_image_url and post_id:
        try:
            img_data = fetch_image_base64(cover_image_url)
            if img_data:
                models.execute_kw(ODOO_DB, ODOO_UID, ODOO_PASS,
                                   'blog.post', 'write', [[post_id], {
                                       'cover_properties': f'{{"background-image": "url(/web/image/blog.post/{post_id}/cover_properties)", "resize_class": "o_record_has_cover o_half_screen_height", "opacity": "0"}}',
                                   }])
                # Upload as attachment
                att_id = models.execute_kw(ODOO_DB, ODOO_UID, ODOO_PASS,
                                            'ir.attachment', 'create', [{
                                                'name': f'cover_{post_id}.jpg',
                                                'datas': img_data,
                                                'res_model': 'blog.post',
                                                'res_id': post_id,
                                                'type': 'binary',
                                            }])
        except Exception as e:
            print(f"  [warn] Cover image failed: {e}")

    return post_id


def fetch_image_base64(img_url, timeout=15):
    """Download an image and return base64-encoded data."""
    try:
        req = urllib.request.Request(img_url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; MujimBot/1.0)'
        })
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout)
        data = resp.read()
        if len(data) < 100:
            return None
        return base64.b64encode(data).decode('utf-8')
    except Exception as e:
        print(f"  [warn] Image fetch failed ({img_url[:60]}...): {e}")
        return None


def download_and_embed_images(html_content, models):
    """Find all <img> tags in HTML, download images, upload to Odoo as
    attachments, and replace src with Odoo attachment URLs."""
    img_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
    matches = img_pattern.findall(html_content)

    for img_url in matches:
        if not img_url.startswith('http'):
            if img_url.startswith('/'):
                img_url_full = f"https://www.mujing-med.com{img_url}"
            else:
                continue
        else:
            img_url_full = img_url

        try:
            img_data = fetch_image_base64(img_url_full)
            if not img_data:
                continue

            # Determine filename
            fname = img_url_full.split('/')[-1].split('?')[0]
            if not fname or len(fname) > 100:
                fname = f"img_{hash(img_url_full) % 100000}.jpg"

            # Upload to Odoo
            att_id = models.execute_kw(ODOO_DB, ODOO_UID, ODOO_PASS,
                                        'ir.attachment', 'create', [{
                                            'name': fname,
                                            'datas': img_data,
                                            'type': 'binary',
                                            'public': True,
                                        }])

            # Replace URL in HTML
            odoo_img_url = f"/web/image/{att_id}"
            html_content = html_content.replace(img_url, odoo_img_url)
            print(f"    [img] {fname} -> attachment {att_id}")

        except Exception as e:
            print(f"    [img-err] {img_url[:50]}: {e}")
            continue

    return html_content


def verify_post(models, post_id):
    """Verify a blog post was created correctly."""
    post = models.execute_kw(ODOO_DB, ODOO_UID, ODOO_PASS,
                              'blog.post', 'read', [post_id],
                              {'fields': ['name', 'blog_id', 'is_published',
                                          'tag_ids', 'website_url']})
    if post:
        p = post[0]
        print(f"  [verified] id={post_id} blog={p['blog_id'][1]} "
              f"published={p['is_published']} url={p.get('website_url','?')}")
        return True
    return False


# Blog ID mapping
BLOG_IDS = {
    '醫美療程服務': 1,
    'SPA全身服務': 2,
    '衛教專欄': 3,
    '網紅推薦': 4,
    '最新消息': 5,
    'LPG法式體雕': 6,
    '膠原館': 7,
    '體重管理': 8,
}

# Tag ID mapping
TAG_IDS = {
    '微整注射': 1, '雷射光療': 2, '完美纖體': 3, '微整形手術': 4,
    '美容保養': 5, '體重管理': 6, 'SPA課程': 7, '複合療程': 8,
    '臉部': 9, '身體': 10, '眼周': 11, '鼻部': 12, '唇部': 13,
    '頸部': 14, '胸部': 15, '腿部': 16, '手臂': 17, '腹部': 18,
    '飲食營養': 19, '術後保養': 20, '產後瘦身': 21, '美容保健': 22,
    '雷射光療知識': 23,
}
