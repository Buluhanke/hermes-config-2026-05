#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, time, urllib.parse, urllib.request, websocket, threading
ver = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json/version', timeout=5).read())
ws = websocket.create_connection(ver['webSocketDebuggerUrl'], timeout=60)
evs = []
def rd():
    while True:
        try: evs.append(json.loads(ws.recv()))
        except Exception: break
threading.Thread(target=rd, daemon=True).start()
_id = [0]
def cmd(m, p=None, s=None):
    _id[0]+=1; o={'id':_id[0],'method':m}
    if p is not None: o['params']=p
    if s is not None: o['sessionId']=s
    ws.send(json.dumps(o))
    for _ in range(10000):
        for i,e in enumerate(evs):
            if e.get('id')==_id[0]: evs.pop(i); return e
        time.sleep(0.02)
def ev(expr, s):
    mid=_id[0]+1
    ws.send(json.dumps({'id':mid,'method':'Runtime.evaluate','params':{'expression':expr,'returnByValue':True,'awaitPromise':False},'sessionId':s}))
    for _ in range(10000):
        for i,e in enumerate(evs):
            if e.get('id')==mid: evs.pop(i); return e.get('result',{}).get('result',{}).get('value')
r = cmd('Target.createTarget', {'url':'about:blank','background':True}); tid=r['result']['targetId']
r2 = cmd('Target.attachToTarget', {'targetId':tid,'flatten':True}); s=r2['result']['sessionId']
cmd('Page.enable', {}, s); cmd('Runtime.enable', {}, s)
kw = "牛皮纸手提袋"
url = "https://s.1688.com/selloffer/offer_search.htm?keywords=" + urllib.parse.quote(kw.encode("gbk")) + "&province=%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%B7&beginPage=1"
cmd('Page.navigate', {'url':url}, s)
time.sleep(8)
for _ in range(6):
    ev("window.scrollTo(0,document.body.scrollHeight)", s); time.sleep(1.2)
EXTRACT = r"""
(()=>{const h=document.documentElement.outerHTML;const ids=new Set();let m;
const re1=/detail\.1688\.com\/offer\/([0-9]+)/g;while((m=re1.exec(h))!==null)ids.add(m[1]);
return JSON.stringify({ids:[...ids].filter(id=>id.length>=9&&id.length<=14),len:h.length});})();
"""
print("EXTRACT result:", ev(EXTRACT, s))
print("page title:", ev("document.title", s))
ws.close()
