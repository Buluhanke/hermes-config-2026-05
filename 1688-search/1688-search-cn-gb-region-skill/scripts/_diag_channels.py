#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose which search channel returns IDs after cooldown + fresh Chrome."""
import sys, os, json, time, urllib.parse, urllib.request, threading
import websocket

PROV = "%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%BD"  # 江苏,浙江,上海
KW = "40*10*3 纸箱"
KW_GB = urllib.parse.quote(KW.encode("gbk"))

PC = "https://s.1688.com/selloffer/offer_search.htm?keywords=" + KW_GB + "&province=" + PROV + "&beginPage=1"
MB = "https://m.1688.com/offer_search.html?keywords=" + KW_GB + "&page=1&province=" + PROV

EXTRACT = r"""(() => {
  const h = document.documentElement.outerHTML;
  const ids = new Set(); let m;
  const re1 = /detail\.1688\.com\/offer\/([0-9]+)/g;
  while ((m = re1.exec(h)) !== null) ids.add(m[1]);
  const re2 = /[?&]offerId=([0-9]+)/g;
  while ((m = re2.exec(h)) !== null) ids.add(m[1]);
  return JSON.stringify({ids: [...ids].filter(id => id.length >= 9 && id.length <= 14), len: h.length, hasVerify: h.includes("验证码"), hasLogin: h.includes("login.taobao") || h.includes("淘宝网")});
})();"""

v = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=5).read())
ws = websocket.create_connection(v["webSocketDebuggerUrl"], timeout=60)
ev = []; myid = [0]; SID = None
def reader():
    while True:
        try: ev.append(json.loads(ws.recv()))
        except: break
threading.Thread(target=reader, daemon=True).start()
def send(method, params=None, sid=None):
    myid[0] += 1; o = {"id": myid[0], "method": method, "params": params or {}}
    if sid: o["sessionId"] = sid
    ws.send(json.dumps(o))
    t = time.time()
    while time.time() - t < 25:
        for i, e in enumerate(ev):
            if e.get("id") == myid[0]:
                ev.pop(i); return e
        time.sleep(0.02)
    return None
r = send("Target.createTarget", {"url": "about:blank", "background": True})
TID = r["result"]["targetId"]
SID = send("Target.attachToTarget", {"targetId": TID, "flatten": True})["result"]["sessionId"]
for mm in ("Page", "Runtime", "Network"): send(mm + ".enable", {}, SID)
def navigate(url):
    send("Page.navigate", {"url": url, "timeout": 40000}, SID)
def evaluate(expr):
    o = send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True, "timeout": 20000}, SID)
    if not o or "error" in o: return None
    res = o["result"]["result"]
    if res.get("subtype") == "error": return ("JSERR", res.get("description", "")[:200])
    return res.get("value")

def test(label, url):
    print(f"\n=== {label}: {url[:80]} ===")
    navigate(url)
    for w in (15, 15):
        time.sleep(w)
        # scroll to trigger lazy load
        evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
    href = evaluate("location.href") or "(no href)"
    print("  final href:", href)
    result = evaluate(EXTRACT)
    print("  extract:", result if isinstance(result, str) else result)

import urllib.request
test("PC search", PC)
test("Mobile search", MB)
send("Target.closeTarget", {"targetId": TID})
