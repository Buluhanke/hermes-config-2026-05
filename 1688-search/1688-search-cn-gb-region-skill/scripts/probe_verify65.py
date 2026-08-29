#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针10：验证新EXTRACT的65个mobile候选详情页是否真纸盒。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cdp1688", os.path.join(HERE, "cdp1688.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
CDP = m.CDP
clean_title = m.clean_title
ids=["1079368937295","1079356989654","1077424851909","1077425763717","1080345608368","1080337968779","1077427215396","1080344428098","1080331504634","1078274998468"]
c=CDP("http://127.0.0.1:9222")
tid,sess=c.new_page("about:blank")
for oid in ids:
    c.navigate(sess, f"https://detail.1688.com/offer/{oid}.html")
    time.sleep(3)
    ttl=clean_title(c.evaluate(sess,"document.title",await_promise=False) or "")
    box=bool(re.search(r"纸盒|纸箱|飞机盒|瓦楞|包装盒|天地盖|翻盖盒|彩盒|卡盒", ttl))
    print(f"  {oid} | box={box} | {ttl[:46]}")
c.close_target(tid, sess)
