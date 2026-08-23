#!/usr/bin/env python3
"""Verify a local Chrome CDP instance is reachable, carries the user's login
state, and can navigate + read a page. Run: python3 verify_cdp.py
Requires: pip install websocket-client
"""
import json
import time
import urllib.request
import websocket

BASE = "http://127.0.0.1:9222"


def _cid():
    _cid.n += 1
    return _cid.n
_cid.n = 0


def send(ws, method, params=None):
    i = _cid()
    ws.send(json.dumps({"id": i, "method": method, "params": params or {}}))
    return i


def recv_id(ws, want):
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == want:
            return r


def main():
    ver = json.loads(urllib.request.urlopen(f"{BASE}/json/version", timeout=10).read())
    print("Browser:", ver["Browser"])
    ws = websocket.create_connection(ver["webSocketDebuggerUrl"], timeout=15)

    i = send(ws, "Storage.getCookies")
    cookies = recv_id(ws, i)["result"]["cookies"]
    domains = sorted({c["domain"] for c in cookies})
    print(f"Cookies: {len(cookies)} across {len(domains)} domains")
    for d in domains[:25]:
        print("  ", d)

    i = send(ws, "Target.createTarget", {"url": "https://example.com"})
    tid = recv_id(ws, i)["result"]["targetId"]
    time.sleep(3)

    targets = json.loads(urllib.request.urlopen(f"{BASE}/json", timeout=10).read())
    tinfo = next(t for t in targets if t["id"] == tid)
    tw = websocket.create_connection(tinfo["webSocketDebuggerUrl"], timeout=15)
    i1 = send(tw, "Runtime.enable"); recv_id(tw, i1)
    i2 = send(tw, "Runtime.evaluate", {"expression": "document.title"})
    title = recv_id(tw, i2)["result"]["result"]["result"]["value"]
    print("Navigated + read title:", repr(title))
    tw.close(); ws.close()
    print("CDP OK")


if __name__ == "__main__":
    main()
