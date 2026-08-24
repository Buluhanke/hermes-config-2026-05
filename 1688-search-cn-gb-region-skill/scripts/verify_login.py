#!/usr/bin/env python3
# 验证 1688 登录态（收编版）
#
# 访问 www.1688.com 首页 + 一个 detail.1688.com 详情页，
# 判断登录态是否持久化成功、详情页是否免登录墙。
#
# 用法：
#   ~/.hermes/1688-mcp/venv/bin/python verify_login.py
#
# 期望输出：
#   www.1688.com  -> is_login True / has_user True
#   detail.1688.com -> BLOCKED False（直接打开商品页，无登录墙）

import os, sys, time, json

os.environ.pop('PYTHONPATH', None)
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
VENV_SP = os.path.join(SKILL_ROOT, 'venv', 'lib', 'python3.14', 'site-packages')
if os.path.isdir(VENV_SP):
    sys.path.insert(0, VENV_SP)
sys.path = [p for p in sys.path if 'hermes-agent/venv' not in p and p not in ('', '.')]

from DrissionPage import ChromiumPage, ChromiumOptions

USER_DATA = os.path.join(SKILL_ROOT, 'venv', 'drission_user_data')
TEST_OFFER = '708938768516'  # 已知真纸箱，用于验详情页免墙

co = ChromiumOptions()
co.set_user_data_path(USER_DATA)
co.headless(False)
co.set_argument('--disable-blink-features=AutomationControlled')
co.set_argument('--disable-infobars')
co.auto_port()
p = ChromiumPage(co)

# 1) 首页登录态
p.get('https://www.1688.com/')
time.sleep(4)
html = p.ele('tag:body').text if p.ele('tag:body', timeout=3) else ''
is_login = ('登录' not in p.title) and ('1688' in p.title)
has_user = any(k in html for k in ['我的', '卖家', '买家', '千牛', '已买', '我的阿里'])
print(json.dumps({'page': 'www.1688.com', 'url': p.url, 'title': p.title,
                  'is_login': is_login, 'has_user': has_user}, ensure_ascii=False))

# 2) 详情页免墙
p.get(f'https://detail.1688.com/offer/{TEST_OFFER}.html')
time.sleep(5)
blocked = ('login' in p.url) or ('punish' in p.url)
print(json.dumps({'page': 'detail.1688.com', 'url': p.url,
                  'title': p.title, 'BLOCKED': blocked}, ensure_ascii=False))
p.quit()
