#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick diagnostic: does m.1688.com offer_search support province filter + return IDs?"""
import sys, os, json, time, urllib.parse, re, threading
import websocket
HERE = os.path.dirname(os.path.abspath(__file__))
EXTRACT = r"""(()=>{
  const h=document.documentElement.outerHTML;
  const ids=new Set(); let m;
  const re1=/detail\.1688\.com\/offer\/([0-9]+)/g;
  while((m=re1.exec(h))!==null) ids.add(m[1]);
  const re2=/[?&]offerId=([0-9]+)/g;
  while((m=re2.exec(h))!==null) ids.add(m[1]);
  const re3=/(?:m\.)?1688\.com\/offer\/([0-9]+)/g;
  while((m=re3.exec(h))!==null) ids.add(m[1]);
  return JSON.stringify({ids:[...ids].filter(id=>id.length>=9&&id.length<=14),htmlLen:h.length,hasCaptcha:"验证码" in h,href:location.href});
})();"""
PROV = "%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%BD"
kw = "纸箱"
kw_gb = urllib.parse.quote(kw.encode("gbk"))
url_prov = ("https://m.1688.com/offer_search.html?keywords=" + kw_gb + "&page=1&province=" + PROV)
url_noprov = ("https://m.1688.com/offer_search.html?keywords=" + kw_gb + "&page=1")

import urllib.request
v = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=5).read())
wsurl = v["webSocketDebugUrl"] if "webSocketDebugUrl" in v else v["webSocketDebuggerUrl"]
ws = websocket.create_connection(v["webSocketDebuggerUrl"], timeout=60)
myid = [0]; ev = []
def reader():
    while True:
        try: ev.append(json.loads(ws.recv()))
        except: break
threading.Thread(target=reader, daemon=True).start()
def send(method, params=None, sid=None):
    myid[0]+=1; msg={"id":myid[0],"method":method,"params":params or {}}
    if sid: msg["sessionId"]=sid
    ws.send(json.dumps(msg))
    t=time.time()
    while time.time()-t<15:
        for i,e in enumerate(ev):
            if e.get("id")==myid[0]:
                ev.pop(i); return e
        time.sleep(0.02)
    return None
r = send("Target.createTarget", {"url":"about:blank","background":True})
tid = r["result"]["targetId"]
sid = send("Target.attachToTarget", {"targetId":tid,"flatten":True})["result"]["sessionId"]
for mm in ("Page","Runtime","Network"): send(mm+".enable", {}, sid)
def nav(u):
    send("Page.navigate", {"url":u,"timeout":40000}, sid); time.sleep(7)
    return send("Runtime.evaluate", {"expression":EXTRACT,"returnByValue":True,"awaitPromise":True,"timeout":20000}, sid)
def val(r):
    if not r: return None
    if "error" in r: return ("ERROR", r["error"])
    res = r.get("result",{}).get("result",{})
    if res.get("subtype")=="error": return ("JSERR", res.get("description"))
    return res.get("value")

print("=== with province filter ===")
nav(url_prov)
print("  ", val(send("Runtime.evaluate", {"expression":EXTRACT,"returnByValue":True,"awaitPromise":True,"timeout":20000}, sid)))

print("=== no province filter ===")
nav(url_noprov)
print("  ", val(send("Runtime.evaluate", {"expression":EXTRACT,"returnByValue":True,"awaitPromise":True,"timeout":20000}, sid)))

send("Target.closeTarget", {"targetId":tid})
