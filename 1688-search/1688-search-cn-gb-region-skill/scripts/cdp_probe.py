#!/usr/bin/env python3
# cdp_probe.py — 验证 Playwright 接管真实 Chrome 9222 实例是否带 1688 登录态。
# 用法: python3 cdp_probe.py
import sys
from playwright.sync_api import sync_playwright

ADDR = "http://[::1]:9222"   # 独立实例(83433)在 IPv6

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(ADDR)
    ctx = browser.contexts[0]
    page = ctx.new_page()
    page.goto("https://www.1688.com", wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(1500)
    # 判断是否登录：1688 登录后页面有用户名/退出按钮，未登录有"登录"链接
    txt = page.inner_text("body") or ""
    logged = ("退出" in txt) or ("欢迎" in txt) or ("买家中心" in txt)
    title = page.title()
    print("CDP连接: OK")
    print("1688标题:", title)
    print("疑似登录态:", logged)
    # 打印当前cookie里的1688登录标记
    cookies = ctx.cookies()
    login_cookies = [c['name'] for c in cookies if '1688' in c.get('domain','') or c['name'] in ('__cn_logon_id__','cna','_m_h5_tk','ssl_agreement')]
    print("1688相关cookie:", login_cookies[:10])
    browser.close()
