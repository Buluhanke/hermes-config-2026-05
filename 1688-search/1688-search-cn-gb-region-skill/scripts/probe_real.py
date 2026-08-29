#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针7：PC全页抽 detail.m.1688?offerId，并排除 opportunity 推荐挂件；打印真实卡标题。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cdp1688", os.path.join(HERE, "cdp1688.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
CDP = m.CDP
qp = __import__("urllib.parse", fromlist=["quote"])

url=("https://s.1688.com/selloffer/offer_search.htm?keywords="+qp.quote("18*14*10cm纸盒".encode("gbk"))
     +"&province=%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%BD&beginPage=1")
c=CDP("http://127.0.0.1:9222")
tid,sess=c.new_page(url)
time.sleep(9)
html=c.evaluate(sess,"document.documentElement.outerHTML",await_promise=False) or ""
# 所有 detail.m.1688 offerId
all_ids=re.findall(r"detail\.m\.1688\.com/page/index\.html\?offerId=([0-9]{9,14})", html)
print("全页 detail.m offerId:", len(all_ids), "unique:", len(set(all_ids)))
# 哪些是 opportunity 推荐挂件（附近含 opportunity.CardItem 或 pages-fast）
rec_ids=set()
for mm in re.finditer(r"detail\.m\.1688\.com/page/index\.html\?offerId=([0-9]{9,14})", html):
    tail=html[mm.end():mm.end()+500]
    if re.search(r"opportunity\.CardItem|pages-fast\.1688\.com", tail):
        rec_ids.add(mm.group(1))
# 真实卡：有 nearby 真实标题(含 纸/盒/cm)
real=set(all_ids)-rec_ids
print("推荐挂件:", len(rec_ids), " 疑似真实:", len(real))
# 验证真实卡附近是否有真实中文标题
print("=== 真实卡附近的标题(前10) ===")
n=0
for iid in list(real)[:40]:
    # 在 html 里找该 iid，取其后第一个 class=offer-title 内容或附近中文
    mm=re.search(re.escape(iid), html)
    if not mm: continue
    tail=html[mm.start()-50:mm.start()+500]
    tm=re.search(r'class="offer-title[^"]*"[^>]*>([^<]{4,80})<', tail)
    title=tm.group(1) if tm else ""
    # 也试 desc
    if not title:
        dm=re.search(r'class="offer-desc[^"]*"[^>]*>([^<]{4,80})<', tail)
        title=dm.group(1) if dm else tail[:40]
    print(f"  {iid} | {title}")
    n+=1
    if n>=10: break
c.close_target(tid, sess)
