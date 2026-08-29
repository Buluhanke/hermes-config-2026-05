#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针5：PC搜页链接结构 + 真实标题来源。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cdp1688", os.path.join(HERE, "cdp1688.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
CDP = m.CDP
qp = __import__("urllib.parse", fromlist=["quote"])
kw = "18*14*10cm纸盒"
url = ("https://s.1688.com/selloffer/offer_search.htm?keywords=" + qp.quote(kw.encode("gbk"))
       + "&province=%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%BD&beginPage=1")
c = CDP("http://127.0.0.1:9222")
tid, sess = c.new_page(url)
time.sleep(9)
html = c.evaluate(sess, "document.documentElement.outerHTML", await_promise=False) or ""
print("detail.m.1688 出现:", html.count("detail.m.1688"))
print("offerId= 出现:", len(re.findall(r"offerId=([0-9]{9,14})", html)))
print("offerId\": 出现:", len(re.findall(r'"offerId":"?([0-9]{9,14})', html)))
# 真实标题：搜含 纸/盒/cm 且像商品标题的中文串
print("=== 含 纸盒/cm 的中文片段(前25) ===")
chunks = re.findall(r'[一-鿿][^<>]{4,60}?(?:纸盒|纸|盒|cm|CM|长宽|高|快递|瓦楞)[^<>]{0,40}', html)
seen=set(); n=0
for ch in chunks:
    if ch in seen: continue
    seen.add(ch)
    print("  ", ch[:80]); n+=1
    if n>=25: break
# 看是否有搜索结果容器 class
print("=== 可能的结果容器 class ===")
offer_cls = list(set(re.findall(r'class="([^"]*offer[^"]*)"', html)))[:10]
for cls in offer_cls:
    print("  ", cls)
list_cls = list(set(re.findall(r'class="([^"]*list[^"]*)"', html)))[:10]
for cls in list_cls:
    print("  list:", cls)
# 真实结果卡：搜 detail.m.1688 附近的标题
print("=== detail.m.1688 真实卡上下文 ===")
for mm in list(re.finditer(r"detail\.m\.1688\.com/page/index\.html\?offerId=([0-9]{9,14})", html))[:6]:
    iid=mm.group(1)
    tail=html[mm.end():mm.end()+400]
    tm=re.search(r'title["\']?\s*[:=]\s*["\']?([^"\'<]{4,60})', tail)
    print(f"  {iid} | {tm.group(1) if tm else tail[:60]}")
c.close_target(tid, sess)
