#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单ID侦察：打开用户给的详情页，dump 真实标题 + 全部SKU尺寸 + 价格，定位品类信号。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 复用 cdp1688.py 的 CDP 类与 JS 资源
import importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cdp1688", os.path.join(HERE, "cdp1688.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
CDP = m.CDP
PRICE_JS = m.PRICE_JS

OID = "933173241"
URL = f"https://detail.1688.com/offer/{OID}.html"

c = CDP("http://127.0.0.1:9222")
tid, sess = c.new_page(URL)
time.sleep(8)

# 标题
title = c.evaluate(sess, "document.title", await_promise=False) or ""
html = c.evaluate(sess, "document.documentElement.outerHTML", await_promise=False) or ""
href = c.evaluate(sess, "location.href", await_promise=False) or ""

print("=== URL ===")
print(href)
print("=== TITLE ===")
print(title)

# 登录墙检测
if "taobao.com" in href or "登录" in title or "验证码" in title:
    print("!!! 登录墙/验证码 — 通道异常，需重注cookie")
else:
    # 抠 skuMapOriginal
    sm = None
    if "skuMapOriginal" in html:
        # 抓 skuMapOriginal 数组
        mm = re.search(r"skuMapOriginal\"?\s*:\s*(\[.*?\])\s*,\s*\"", html)
        if not mm:
            mm = re.search(r"skuMapOriginal\s*[:=]\s*(\[.*?\])\s*}", html[:html.find("skuMapOriginal")+4000]) if "skuMapOriginal" in html else None
        if mm:
            raw = mm.group(1)
            try:
                sm = json.loads(raw)
            except Exception as e:
                print("skuMapOriginal JSON解析失败:", repr(e)[:80])
                sm = None
    print("=== skuMapOriginal 是否命中 ===", "YES" if sm is not None else "NO (走整页规则)")
    if sm:
        print(f"=== SKU 条数: {len(sm)} ===")
        for it in sm[:40]:
            sa = it.get("specAttrs", "")
            dp = it.get("discountPrice", "")
            cb = it.get("canBookCount", "")
            print(f"  | {sa} | ¥{dp} | 库存{cb}")
    else:
        # 整页尺寸抽取（兜底）
        print("=== 整页尺寸/品类片段(前60个含尺寸or纸的词) ===")
        for line in re.findall(r".{0,40}(?:cm|CM|纸|盒|箱|*{1,2}[0-9]+[x*×][0-9]+).{0,40}", html):
            pass
        # 直接打印标题附近 + 品类信号
        # 提取页面里出现的尺寸串
        dims = set(re.findall(r"(\d+(?:\.\d+)?)\s*[x*×]\s*\d+(?:\.\d+)?\s*[x*×]\s*\d+(?:\.\d+)?)\s*cm?", html))
        print("尺寸串(连写3D):", list(dims)[:30])
        # 品类词
        for sig in ["纸盒","纸箱","飞机盒","包装盒","礼品盒","卡盒","彩盒","瓦楞","天地盖","翻盖","白卡","牛皮纸","礼品"]:
            if sig in html:
                print("品类信号:", sig)

    # 价格兜底 JS
    try:
        pv = c.evaluate(sess, PRICE_JS, await_promise=True)
        print("=== PRICE_JS 返回 ===", str(pv)[:400])
    except Exception as e:
        print("PRICE_JS err:", repr(e)[:80])

c.close_target(tid, sess)
