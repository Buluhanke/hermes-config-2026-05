#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 探测 1688 详情页 SKU 接口返回结构：用裸 CDP Network 监听 + getResponseBody 抓 queryofferskuselectormodel / window context 里的 skuMapOriginal
import json, time, base64, threading, urllib.request, websocket

OFFER = "1158678687"
ver = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json/version', timeout=5).read())
ws = websocket.create_connection(ver['webSocketDebuggerUrl'], timeout=60)
Q = []
def reader():
    while True:
        try:
            Q.append(json.loads(ws.recv()))
        except Exception:
            break
t = threading.Thread(target=reader, daemon=True); t.start()

_id = [0]
def cmd(m, p=None, s=None):
    _id[0]+=1; o={'id':_id[0],'method':m}
    if p is not None: o['params']=p
    if s is not None: o['sessionId']=s
    ws.send(json.dumps(o))
    while True:
        msg = Q.pop(0) if Q else None
        while msg is None:
            time.sleep(0.02); msg = Q.pop(0) if Q else None
        if msg.get('id')==_id[0]: return msg
        # event -> ignore here
def ev(expr, s):
    mid=_id[0]+1
    ws.send(json.dumps({'id':mid,'method':'Runtime.evaluate','params':{'expression':expr,'returnByValue':True,'awaitPromise':False},'sessionId':s}))
    while True:
        msg = Q.pop(0) if Q else None
        while msg is None:
            time.sleep(0.02); msg = Q.pop(0) if Q else None
        if msg.get('id')==mid: return msg.get('result',{}).get('result',{}).get('value')

r=cmd('Target.createTarget',{'url':'about:blank','background':True}); tid=r['result']['targetId']
r2=cmd('Target.attachToTarget',{'targetId':tid,'flatten':True}); s=r2['result']['sessionId']
cmd('Page.enable',{},s); cmd('Network.enable',{},s); cmd('Runtime.enable',{},s)

seen=[]  # (requestId, url)
def drain_events():
    # pull any pending Network events into seen
    while Q:
        m=Q.pop(0)
        if m.get('method')=='Network.responseReceived':
            u=m['params']['response']['url']
            if any(k in u.lower() for k in ('sku','queryoffer','offerskuselector','skuprops')):
                seen.append((m['params']['requestId'], u))
        elif m.get('method')=='Network.loadingFinished':
            # pair with seen if still there
            pass

cmd('Page.navigate',{'url':f'https://detail.1688.com/offer/{OFFER}.html'},s)
for _ in range(25):  # ~12.5s
    time.sleep(0.5); drain_events()

print("=== candidate SKU-ish response URLs ===")
for rid,u in seen[:20]:
    print(rid, u[:120])

# try getResponseBody on each candidate, look for skuMapOriginal
print("\n=== bodies containing skuMapOriginal / skuPropsList ===")
for rid,u in seen:
    try:
        rb=cmd('Network.getResponseBody',{'requestId':rid},s)
        res=rb.get('result',{})
        b=res.get('body','')
        if res.get('base64'): b=base64.b64decode(b).decode('utf-8','ignore')
        if 'skuMapOriginal' in b or 'skuPropsList' in b or 'skuMap' in b:
            print("URL:",u[:100])
            for key in ('skuMapOriginal','skuPropsList','skuMap'):
                i=b.find(key)
                if i>=0:
                    print(f"  [{key}] ...{b[i-30:i+400]}")
    except Exception as e:
        pass
print("\n=== done ===")
try: ws.close()
except: pass
