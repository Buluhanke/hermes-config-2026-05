#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针3：取一个非推荐 offerId，打印其前后 1500 字符原始 HTML，看清真实卡片结构。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cdp1688", os.path.join(HERE, "cdp1688.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
CDP = m.CDP

kw = "18*14*10cm纸盒"
url = ("https://m.1688.com/offer_search.html?keywords="
       + __import__("urllib.parse", fromlist=["quote"]).quote(kw.encode("gbk"))
       + "&province=%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%BD&page=1")
c = CDP("http://127.0.0.1:9222")
tid, sess = c.new_page(url)
time.sleep(8)
html = c.evaluate(sess, "document.documentElement.outerHTML", await_promise=False) or ""
# 找一个非推荐 offerId
target = None
for mm in re.finditer(r"offerId=([0-9]{9,14})", html):
    tail = html[mm.end():mm.end()+400]
    if not re.search(r"BI_ZHUI_QU_SHI|GEN_FENG_RE_MAI", tail):
        target = mm
        break
if target:
    iid = target.group(1)
    s = max(0, target.start()-200); e = min(len(html), target.end()+1400)
    print(f"=== 非推荐 offerId {iid} 上下文 ===")
    print(html[s:e])
else:
    print("无可用非推荐 ID")
c.close_target(tid, sess)
