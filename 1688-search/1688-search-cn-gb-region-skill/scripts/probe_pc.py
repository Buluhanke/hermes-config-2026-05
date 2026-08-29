#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针4：PC 搜页 s.1688.com/selloffer 抓真实纸盒结果卡（排除 opportunity 推荐）。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cdp1688", os.path.join(HERE, "cdp1688.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
CDP = m.CDP

kw = "18*14*10cm纸盒"
url = ("https://s.1688.com/selloffer/offer_search.htm?keywords="
       + __import__("urllib.parse", fromlist=["quote"]).quote(kw.encode("gbk"))
       + "&province=%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%BD&beginPage=1")
c = CDP("http://127.0.0.1:9222")
tid, sess = c.new_page(url)
time.sleep(9)
html = c.evaluate(sess, "document.documentElement.outerHTML", await_promise=False) or ""
print("=== PC 搜页 HTML len:", len(html))
print("=== 是否验证码/拦截 ===", "验证码" in html or "阿里1688" in (c.evaluate(sess,"document.title",await_promise=False) or ""))
# 真实结果卡：排除 opportunity / pages-fast 推荐
ids_all = re.findall(r"detail\.1688\.com/offer/([0-9]{9,14})", html)
print("detail.1688 offerId 数:", len(ids_all), "unique:", len(set(ids_all)))
# 打印前几个真实卡的标题
titles = re.findall(r'class="[^"]*title[^"]*"[^>]*>([^<]{4,80})<', html)
print("=== 含title的可见标题(前30) ===")
n=0
for t in titles:
    if re.search(r"纸|盒|箱|cm|CM|长宽|高", t):
        print("  ", t); n+=1
        if n>=30: break
# 看 opportunity 占比
print("=== opportunity 推荐模块出现次数 ===", html.count("opportunity.CardItem"))
c.close_target(tid, sess)
