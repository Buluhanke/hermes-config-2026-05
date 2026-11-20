#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post-cooldown health probe: one PC search page for '纸箱' in 江浙沪."""
import sys, os, json, time, urllib.parse, threading, re
import websocket
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cdp1688 as C

PROV = "%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%BD"  # 江浙沪
KW = "纸箱"
url = C.build_search_url(KW, 1, PROV)

c = C.CDP("http://127.0.0.1:9222")
wt, ws = c.new_page("https://www.1688.com/")
time.sleep(5)
print("search url:", url)
c.navigate(ws, url)
time.sleep(8)
# scroll to load
for _ in range(6):
    c.evaluate(ws, "window.scrollTo(0, document.body.scrollHeight)", await_promise=False)
    time.sleep(1)
href = c.evaluate(ws, "location.href", await_promise=False) or ""
h = c.evaluate(ws, "document.documentElement.outerHTML", await_promise=False) or ""
data = c.evaluate(ws, C.EXTRACT, await_promise=False)
ids = []
try:
    ids = json.loads(data or {}).get("ids", [])
except Exception:
    pass
punish = "punish" in href or "x5sec" in href
print("final href tail:", href[-80:])
print("punish/x5sec:", punish, "| hasVerify:", "验证码" in h, "| htmlLen:", len(h))
print("candidate IDs:", len(ids))
if ids:
    print("sample:", ids[:5])
c.close_target(wt, ws); c.ws.close()
