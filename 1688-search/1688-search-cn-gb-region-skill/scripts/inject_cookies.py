#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读取默认 Chrome 的 1688/taobao 登录 cookie，注入后台 CDP Chrome (9222)。
不落盘明文 cookie。用法: python3 inject_cookies.py [port]
"""
import sys, json, time, urllib.request, websocket

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9222

try:
    import browser_cookie3 as bc
except Exception as e:
    print("browser_cookie3 不可用:", e); raise SystemExit(1)

cj = []
for getter in (bc.chrome, bc.chromium):
    for dom in (".1688.com", ".taobao.com"):
        try:
            for c in getter(domain_name=dom):
                cj.append(c)
        except Exception:
            pass
# 去重（name|domain|path）
seen = {}
for c in cj:
    seen[f"{c.name}|{c.domain}|{c.path}"] = c
cj = list(seen.values())
print(f"读取到 {len(cj)} 个 cookie (1688+taobao, 值不打印)")

ver = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=5).read())
ws = websocket.create_connection(ver["webSocketDebuggerUrl"], timeout=60)
_id = 0
def cmd(m, p=None, s=None):
    global _id
    _id += 1
    o = {'id': _id, 'method': m}
    if p is not None: o['params'] = p
    if s is not None: o['sessionId'] = s
    ws.send(json.dumps(o))
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            raw = ws.recv()
            if not isinstance(raw, str):
                raw = raw.decode('utf-8', 'ignore')
            e = json.loads(raw)
        except Exception:
            continue
        if isinstance(e, dict) and e.get('id') == _id:
            return e
        time.sleep(0.001)
    return None

r = cmd('Target.createTarget', {'url': 'https://www.1688.com/', 'background': True})
tid = r['result']['targetId']
r2 = cmd('Target.attachToTarget', {'targetId': tid, 'flatten': True})
s = r2['result']['sessionId']

n = 0
for c in cj:
    cookie = {"name": c.name, "value": c.value, "domain": c.domain, "path": c.path,
              "secure": bool(c.secure), "httpOnly": False}
    if c.expires and c.expires > 0:
        cookie["expirationDate"] = c.expires
    res = cmd('Network.setCookie', cookie, s)
    if res and res.get('result', {}).get('success'):
        n += 1

cmd('Target.closeTarget', {'targetId': tid})
ws.close()
print(f"注入成功 {n} 个 (登录态已写入 {PORT} 实例)")
