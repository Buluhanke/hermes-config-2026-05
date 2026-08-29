#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针9：用新 EXTRACT 逻辑跑 mobile 搜页，确认推荐挂件被过滤、剩下的是真纸盒。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cdp1688", os.path.join(HERE, "cdp1688.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
CDP = m.CDP
EXTRACT = m.EXTRACT
qp = __import__("urllib.parse", fromlist=["quote"])
url=("https://m.1688.com/offer_search.html?keywords="+qp.quote("18*14*10cm纸盒".encode("gbk"))
     +"&province=%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%BD&page=1")
c=CDP("http://127.0.0.1:9222")
tid,sess=c.new_page(url)
time.sleep(9)
raw=c.evaluate(sess, EXTRACT, await_promise=False)
data=raw if isinstance(raw, dict) else json.loads(raw)
ids=data.get("ids",[])
print("=== 新EXTRACT mobile候选:", len(ids), "unique:", len(set(ids)), "===")
print("前10:", ids[:10])
c.close_target(tid, sess)
