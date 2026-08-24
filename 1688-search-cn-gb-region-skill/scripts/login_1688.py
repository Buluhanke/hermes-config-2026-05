#!/usr/bin/env python3
# 1688 登录授权脚本（收编版，可复用）
#
# 用途：唤起 DrissionPage 独立 Chromium，打开 1688 主站登录入口，
#       留 180s 窗口期给用户扫二维码/过风控。登录态写入 drission_user_data，
#       与 1688-Scraper-MCP（server.py 同目录 drission_user_data）共享同一会话。
#
# 关键结论（2026-08-20 实测）：
#   - 入口必须走 member.1688.com（1688 主站），不要走 login.1688.com/login.taobao.com 中转页
#     —— 中转页 cookie 落在 taobao 域，1688 搜索页不认。
#   - member.1688.com 打开后会 302 到 www.1688.com 首页；若已登录则不弹码、直接进首页。
#   - 登录态持久化在 USER_DATA 目录，重启浏览器/进程不丢（除非手动清）。
#
# 用法：
#   ~/.hermes/1688-mcp/venv/bin/python login_1688.py
# 前置：隔离 venv 已装 DrissionPage（见 references/1688_mcp_setup.md）。本脚本自清 PYTHONPATH 防污染。

import os, sys, time, json

# ---- 自清 Hermes 网关注入的 PYTHONPATH（防 pydantic_core 冲突）----
os.environ.pop('PYTHONPATH', None)
# 路径相对化（坑24 分发铁律）：本 skill 的 venv / drission_user_data 随 skill 走，不写死机器
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
VENV_SP = os.path.join(SKILL_ROOT, 'venv', 'lib', 'python3.14', 'site-packages')
if os.path.isdir(VENV_SP):
    sys.path.insert(0, VENV_SP)
sys.path = [p for p in sys.path if 'hermes-agent/venv' not in p and p not in ('', '.')]

from DrissionPage import ChromiumPage, ChromiumOptions

# ---- 可改常量 ----
TARGET = 'https://member.1688.com/'                                   # 1688 主站登录入口（非 taobao 中转）
USER_DATA = os.path.join(SKILL_ROOT, 'venv', 'drission_user_data')   # 与 MCP server.py 共享登录态（随 skill 走）
SHOT = '/tmp/1688_qr_login.png'                                       # 二维码/登录态截图
STATE = '/tmp/1688_login_state.json'                                  # 登录态落盘
WINDOW_S = 180                                                        # 留窗期（秒）

co = ChromiumOptions()
co.set_user_data_path(USER_DATA)
co.headless(False)
co.set_argument('--disable-blink-features=AutomationControlled')
co.set_argument('--disable-infobars')
co.auto_port()

page = ChromiumPage(co)
page.get(TARGET)
time.sleep(6)

try:
    page.get_screenshot(SHOT)
    print('SHOT_OK', SHOT)
except Exception as e:
    print('SHOT_ERR', e)

print('URL', page.url)
print('TITLE', page.title)
with open(STATE, 'w') as f:
    json.dump({'shot': SHOT, 'url': page.url, 'title': page.title}, f, ensure_ascii=False)
print('KEEP_ALIVE')
sys.stdout.flush()
time.sleep(WINDOW_S)
print('DONE_WAIT')
page.quit()
