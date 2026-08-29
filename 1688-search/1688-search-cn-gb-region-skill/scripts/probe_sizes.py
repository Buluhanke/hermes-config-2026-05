#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针11：扫描候选池里真纸盒厂的 SKU 尺寸，看是否有 18*14*10 或近邻尺寸(如18*14*X / 17*14*10 等)。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cdp1688", os.path.join(HERE, "cdp1688.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
CDP = m.CDP
parse_sku_json = m.parse_sku_json
ids=json.load(open("store/181410_v4.json.ids.json", encoding="utf-8"))
# 只验真纸盒(非exclude)，看尺寸
c=CDP("http://127.0.0.1:9222")
tid,sess=c.new_page("about:blank")
target=set()
# 目标尺寸三轴
def norm(d):
    return tuple(sorted(float(x) for x in re.findall(r"[\d.]+", d)))
for oid in ids:
    c.navigate(sess, f"https://detail.1688.com/offer/{oid}.html")
    time.sleep(2.5)
    html=c.evaluate(sess,"document.documentElement.outerHTML",await_promise=False) or ""
    if "skuMapOriginal" not in html: continue
    body=html
    rows=parse_sku_json(body)
    for spec_, price, stock in rows:
        # 抽三维
        ds=re.findall(r"(\d+(?:\.\d+)?)\s*[x*×X]\s*(\d+(?:\.\d+)?)\s*[x*×X]\s*(\d+(?:\.\d+)?)", spec_)
        for a,b,cc in ds:
            tup=tuple(sorted([float(a),float(b),float(cc)]))
            # 命中 18*14*10 或 近邻(两轴相同,第三轴±3)
            if tup==(10.0,14.0,18.0):
                target.add((oid,spec_,price,stock))
            elif sorted([10,14,18])==sorted([round(float(a)),round(float(b)),round(float(cc))]) and (10,14,18)!=(round(float(a)),round(float(b)),round(float(cc))):
                pass
    # 打印该店所有尺寸(前15)看分布
    allspecs=set()
    for spec_,_,_ in rows:
        for a,b,cc in re.findall(r"(\d+(?:\.\d+)?)\s*[x*×X]\s*(\d+(?:\.\d+)?)\s*[x*×X]\s*(\d+(?:\.\d+)?)", spec_):
            allspecs.add((round(float(a)),round(float(b)),round(float(cc))))
    if allspecs:
        print(f"{oid}: {sorted(allspecs)[:12]}")
c.close_target(tid, sess)
print("=== 精确18*14*10命中 ===", target)
