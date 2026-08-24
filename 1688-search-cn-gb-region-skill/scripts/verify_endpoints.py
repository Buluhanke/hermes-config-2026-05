#!/usr/bin/env python3
# 验证 1688 两个端点的风控差异（收编版，诊断用）
#
# 结论（2026-08-20 实测，已定论）：
#   - detail.1688.com/offer/<id>.html  -> 免中转登录，自动化浏览器可直开，无墙
#   - s.1688.com/selloffer/offer_search.htm -> 端点级风控，自动化浏览器强制踢回
#       login.taobao.com 中转页（即便首页已登录），故 MCP search_1688_products 走不通。
#   这是端点风控，非 cookie 域问题；先过首页 session 再跳搜索页照样踢。
#
# 用法：
#   ~/.hermes/1688-mcp/venv/bin/python verify_endpoints.py

import os, sys, time, urllib.parse

os.environ.pop('PYTHONPATH', None)
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
VENV_SP = os.path.join(SKILL_ROOT, 'venv', 'lib', 'python3.14', 'site-packages')
if os.path.isdir(VENV_SP):
    sys.path.insert(0, VENV_SP)
sys.path = [p for p in sys.path if 'hermes-agent/venv' not in p and p not in ('', '.')]

from DrissionPage import ChromiumPage, ChromiumOptions

USER_DATA = os.path.join(SKILL_ROOT, 'venv', 'drission_user_data')
co = ChromiumOptions()
co.set_user_data_path(USER_DATA)
co.headless(False)
co.set_argument('--disable-blink-features=AutomationControlled')
co.set_argument('--disable-infobars')
co.auto_port()
p = ChromiumPage(co)

# 先建首页 session（模拟真人路径，验证是否仍被踢）
p.get('https://www.1688.com/')
time.sleep(5)

# 搜索页（带 GBK 关键词 + 江浙沪 province）
kw = urllib.parse.quote('20*20*10cm纸箱'.encode('gbk'))
prov = urllib.parse.quote('江苏,浙江,上海'.encode('utf-8'))
p.get(f'https://s.1688.com/selloffer/offer_search.htm?keywords={kw}&province={prov}&beginPage=1')
for _ in range(10):
    time.sleep(3)
    if 'login' not in p.url and 'punish' not in p.url:
        break
print('SEARCH_PAGE FINAL_URL', p.url[:90])
print('SEARCH_PAGE BLOCKED', ('login' in p.url) or ('punish' in p.url))

# 详情页
p.get('https://detail.1688.com/offer/708938768516.html')
time.sleep(5)
print('DETAIL_PAGE BLOCKED', ('login' in p.url) or ('punish' in p.url))
p.quit()
