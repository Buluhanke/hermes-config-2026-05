#!/usr/bin/env python3
"""Read a webpage's rendered text via local Chrome CDP — zero OCR.

Uses the VERIFIED SYNC websocket-client pattern (NOT asyncio, which detaches
the page context — see chrome-cdp-control SKILL.md pitfalls). Requires:
  pip install websocket-client
and a local CDP Chrome running on 127.0.0.1:9222 (see cdp-start.sh /
cdp_lifecycle.sh). This bypasses the cloud URL guard and datacenter-IP
anti-scrape that block web_extract / curl on sites like Zhihu.

Usage:
  python3 read_page_text.py <URL> [output_file]
Prints innerText to stdout; if output_file is given, also writes full text there.

Why document.body.innerText (not outerHTML+regex, not textContent): returns
only rendered, human-visible text, laid out by the page — closest to what the
browser shows, and it beats shadow-DOM/iframe blind spots on SPA sites.
"""
import json
import sys
import time
import urllib.request
import websocket

BASE = "http://127.0.0.1:9222"
SLEEP = 6  # wait for SPA/JS render (Zhihu etc. need it)


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
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    out = sys.argv[2] if len(sys.argv) > 2 else None

    ver = json.loads(urllib.request.urlopen(f"{BASE}/json/version", timeout=10).read())
    ws = websocket.create_connection(ver["webSocketDebuggerUrl"], timeout=15)

    i = send(ws, "Target.createTarget", {"url": url})
    tid = recv_id(ws, i)["result"]["targetId"]
    time.sleep(SLEEP)

    targets = json.loads(urllib.request.urlopen(f"{BASE}/json", timeout=10).read())
    tinfo = next(t for t in targets if t["id"] == tid)
    tw = websocket.create_connection(tinfo["webSocketDebuggerUrl"], timeout=15)

    i1 = send(tw, "Runtime.enable")
    recv_id(tw, i1)

    # retry a few times in case the context wasn't ready
    txt = ""
    for _ in range(3):
        i2 = send(tw, "Runtime.evaluate",
                  {"expression": "document.body.innerText", "returnByValue": True})
        res = recv_id(tw, i2)["result"]
        txt = res.get("result", {}).get("value", "") or ""
        if txt:
            break
        time.sleep(1)

    tw.close()
    ws.close()

    if out:
        open(out, "w").write(txt)
        print(f"Wrote {len(txt)} chars to {out}")
    else:
        print(txt)


if __name__ == "__main__":
    main()
