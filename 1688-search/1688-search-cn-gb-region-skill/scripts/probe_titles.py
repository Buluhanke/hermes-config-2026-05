#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针2：打印 m.1688 搜页真实可见商品标题(去推荐挂件)，看关键词到底命中什么。"""
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
# 拿可见文本里每行含 纸/盒/箱 的真实标题，并排除明显推荐词
html = c.evaluate(sess, "document.documentElement.outerHTML", await_promise=False) or ""
# 真实商品标题通常在 class 含 title/name/desc 的节点；先抽所有 offerId 并取其后最近的中文标题串
res = []
for mm in re.finditer(r"offerId=([0-9]{9,14})", html):
    iid = mm.group(1)
    tail = html[mm.end():mm.end()+600]
    # 推荐挂件标记
    is_rec = bool(re.search(r"BI_ZHUI_QU_SHI|GEN_FENG_RE_MAI|趋势商机|跟风热卖", tail))
    # 取最近一个可见中文标题（class含title的标签内容）
    title_m = re.search(r'class="[^"]*title[^"]*"[^>]*>([^<]{4,60})<', tail)
    t = title_m.group(1) if title_m else ""
    if not t:
        # 兜底：topicName
        tm = re.search(r"topicName=([^&\"]+)", tail)
        t = (__import__("urllib.parse", fromlist=["unquote"]).unquote(tm.group(1)) if tm else "")
    res.append((iid, is_rec, t))
print("offerId总数:", len(res), " 推荐挂件:", sum(1 for _,r,_ in res if r))
print("=== 非推荐挂件(疑似真实结果) ===")
for iid, rec, t in res:
    if not rec:
        print(f"  {iid} | {t}")
print("=== 推荐挂件样例(前8) ===")
n=0
for iid, rec, t in res:
    if rec:
        print(f"  {iid} | {t}"); n+=1
        if n>=8: break
c.close_target(tid, sess)
