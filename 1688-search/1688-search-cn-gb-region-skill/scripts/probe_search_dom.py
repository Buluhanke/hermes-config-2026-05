#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针：打开 m.1688.com 搜页，打印结果卡片 vs 推荐模块的 DOM 结构，定位干净抽取点。"""
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
print("=== HTML length:", len(html))
# 找 offerId 出现处的上下文
ids = re.findall(r"offerId=([0-9]{9,14})", html)
print("offerId= count:", len(ids), "unique:", len(set(ids)))
# 打印每个 offerId 前后 120 字符，看是 result-card 还是 recommend
seen=set()
for mm in re.finditer(r"offerId=([0-9]{9,14})", html):
    iid = mm.group(1)
    if iid in seen: continue
    seen.add(iid)
    s = max(0, mm.start()-120); e = min(len(html), mm.end()+120)
    ctx = html[s:e]
    # 判断是否在推荐区：看附近是否含 recommend/guess/相关/猜你/为你
    tag = "RECO?" if re.search(r"recommend|guess|猜你|为你|相关推荐|rec-|_rec", ctx, re.I) else "LIST?"
    print(f"\n[{tag}] {iid}")
    print("   ", re.sub(r"\s+", " ", ctx)[:240])
c.close_target(tid, sess)
print("\n=== DONE ===")
