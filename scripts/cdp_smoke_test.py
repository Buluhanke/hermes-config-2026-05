#!/usr/bin/env python3
"""Full CDP smoke test using the pattern that works on Chrome 148+:
page-level WebSocket directly (no attachToTarget) + a per-socket message
queue keyed by id (so events/acks can't race).

Run: python3 cdp_smoke_test.py
Requires: pip install websocket-client
"""
import base64
import json
import queue
import threading
import time
import urllib.request

import websocket

BASE = "http://127.0.0.1:9222"
TARGET_URL = "https://example.com"


def make_session(ws):
    """Wrap a websocket so caller can send a method and await its id-keyed reply,
    while a background thread drains events into a queue."""
    q = queue.Queue()
    ws.settimeout(None)

    def loop():
        while True:
            try:
                q.put(json.loads(ws.recv()))
            except Exception:
                return

    threading.Thread(target=loop, daemon=True).start()

    counter = {"n": 0}

    def call(method, params=None, timeout=10):
        counter["n"] += 1
        cid = counter["n"]
        ws.send(json.dumps({"id": cid, "method": method, "params": params or {}}))
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                m = q.get(timeout=1)
            except queue.Empty:
                continue
            if m.get("id") == cid:
                return m
        return {"error": "timeout", "id": cid}

    return call


def main():
    ver = json.loads(urllib.request.urlopen(f"{BASE}/json/version", timeout=10).read())
    print("Browser:", ver["Browser"])
    browser_ws = websocket.create_connection(ver["webSocketDebuggerUrl"], timeout=15)
    b_call = make_session(browser_ws)

    print("\n[1] Storage.getCookies (proves login state carried over)")
    r = b_call("Storage.getCookies")
    cookies = r.get("result", {}).get("cookies", [])
    domains = sorted({c["domain"] for c in cookies})
    print(f"  {len(cookies)} cookies across {len(domains)} domains")
    for d in domains[:10]:
        print(f"   - {d}")

    print("\n[2] Target.createTarget + page-level WS")
    r = b_call("Target.createTarget", {"url": TARGET_URL})
    tid = r["result"]["targetId"]
    print(f"  targetId={tid}")
    time.sleep(0.3)
    targets = json.loads(urllib.request.urlopen(f"{BASE}/json", timeout=10).read())
    tinfo = next(t for t in targets if t["id"] == tid)
    page_ws = websocket.create_connection(tinfo["webSocketDebuggerUrl"], timeout=15)
    p_call = make_session(page_ws)
    # Enable immediately — do not sleep before this
    p_call("Runtime.enable")
    p_call("Page.enable")
    time.sleep(2)

    print("\n[3] Runtime.evaluate (keep expression trivial)")
    r = p_call("Runtime.evaluate", {"expression": "document.title"})
    title = r.get("result", {}).get("result", {}).get("value")
    print(f"  title = {title!r}")

    print("\n[4] DOM write")
    r = p_call("Runtime.evaluate",
               {"expression": "const h=document.querySelector('h1');h.textContent='Hermes CDP OK';h.textContent"})
    print(f"  h1 = {r.get('result',{}).get('result',{}).get('value')!r}")

    print("\n[5] Screenshot")
    r = p_call("Page.captureScreenshot", {"format": "png"})
    data = r.get("result", {}).get("data", "")
    png = base64.b64decode(data)
    out = "/tmp/hermes_cdp_smoke.png"
    open(out, "wb").write(png)
    print(f"  {len(png)} bytes -> {out}  magic={png[:8]!r}")

    print("\n[6] Close")
    b_call("Target.closeTarget", {"targetId": tid})
    page_ws.close(); browser_ws.close()
    print("\n>>> CDP smoke test PASSED")


if __name__ == "__main__":
    main()
