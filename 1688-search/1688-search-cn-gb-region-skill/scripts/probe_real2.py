#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针8：直接开 PC搜页抽到的真实卡 offerId 详情页，确认是否为真纸盒 + 抓标题。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cdp1688", os.path.join(HERE, "cdp1688.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
CDP = m.CDP
clean_title = m.clean_title
c=CDP("http://127.0.0.1:9222")
tid,sess=c.new_page("about:blank")
ids=["624516717001","765855854493","565160526478","634522031289","1049675220084","681917028153"]
for oid in ids:
    c.navigate(sess, f"https://detail.1688.com/offer/{oid}.html")
    time.sleep(3.5)
    html=c.evaluate(sess,"document.documentElement.outerHTML",await_promise=False) or ""
    ttl=clean_title(c.evaluate(sess,"document.title",await_promise=False) or "")
    isbox = bool(re.search(r"纸盒|纸箱|飞机盒|瓦楞|包装盒|天地盖|翻盖盒|彩盒|卡盒", ttl))
    print(f"  {oid} | box={isbox} | {ttl[:50]}")
c.close_target(tid, sess)
print("DONE")
