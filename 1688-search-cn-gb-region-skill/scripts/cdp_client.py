#!/usr/bin/env python3
"""CDP client for 1688 search/verify, driving the real logged-in Chrome on :9222.

Bypasses:
 - AppleScript 'execute javascript' (disabled on this Chrome profile)
 - Playwright connectOverCDP (broken on Chrome 151: setDownloadBehavior unsupported)

Uses raw CDP over websocket (websocket-client). Reuses the skill's verify_carton.js
and price_clean3.js (read from disk -> 'runtime.evaluate' string). Mirrors 方案0
semantics: open search via page.goto, scroll to lazy-load, parse outerHTML for offerIds;
open each detail page, set window.TARGET, evaluate verify+price, decode ASCII-safe JSON.
"""
import sys, os, json, time, base64, urllib.parse, urllib.request
from websocket import create_connection

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACT_JS = open(os.path.join(SKILL, "scripts", "extract_ids.js"), encoding="utf-8").read()
VERIFY_JS = open(os.path.join(SKILL, "scripts", "verify_carton.js"), encoding="utf-8").read()
PRICE_JS = open(os.path.join(SKILL, "scripts", "price_clean3.js"), encoding="utf-8").read()

PROV = "%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%BD"  # 江苏,浙江,上海


def decode_payload(s):
    """JSON string returned by JS is ASCII-safe (\\uXXXX). Decode to real unicode."""
    try:
        return json.loads(s.encode("utf-8").decode("unicode_escape"))
    except Exception:
        return {}


class CDP:
    def __init__(self, ws_url):
        self.ws = create_connection(ws_url, timeout=60)
        self._id = 0

    def send(self, method, params=None, timeout=40, retries=2):
        last = None
        for attempt in range(retries + 1):
            try:
                self._id += 1
                msg = {"id": self._id, "method": method, "params": params or {}}
                self.ws.send(json.dumps(msg))
                start = time.time()
                while time.time() - start < timeout:
                    raw = self.ws.recv()
                    obj = json.loads(raw)
                    if obj.get("id") == self._id:
                        return obj
                    # ignore events
                raise TimeoutError("CDP no response for %s" % method)
            except Exception as e:
                last = e
                time.sleep(1.5)
        raise last or TimeoutError("CDP send failed: %s" % method)

    def enable(self):
        self.send("Page.enable")
        self.send("Runtime.enable")

    def navigate(self, url, wait=7):
        self.send("Page.navigate", {"url": url})
        time.sleep(wait)

    def evaluate(self, js, timeout=30):
        r = self.send("Runtime.evaluate",
                      {"expression": js, "returnByValue": True,
                       "timeout": timeout * 1000},
                      timeout=timeout + 10)
        res = r.get("result", {}).get("result", {})
        if "value" in res:
            return res["value"]
        if "exceptionDetails" in r.get("result", {}):
            return "EXC:" + str(r["result"]["exceptionDetails"].get("exception", {}).get("description", ""))
        return None

    def scroll(self, times=8, gap=1):
        for _ in range(times):
            self.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
        self.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    def get_tab(self):
        http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        data = http.open("http://127.0.0.1:9222/json").read()
        for t in json.loads(data):
            if t.get("type") == "page":
                return t["webSocketDebuggerUrl"]
        raise RuntimeError("no page target")


def gbk_url(kw):
    # keywords must be GBK percent-encoded
    enc = urllib.parse.quote(kw.encode("gbk"))
    return "https://s.1688.com/selloffer/offer_search.htm?keywords=" + enc + "&province=" + PROV + "&beginPage="


def search(dim_notation, pages=4):
    """Return dedup list of offer ids across both * and x notations."""
    seen, all_ids = set(), []
    for note in (dim_notation, dim_notation.replace("*", "x")):
        base = gbk_url(note + "cm纸箱")
        for pg in range(1, pages + 1):
            print("  search %s page %d" % (note, pg), flush=True)
            cdp.navigate(base + str(pg), wait=7)
            cdp.scroll(8, 1)
            raw = cdp.evaluate(EXTRACT_JS) or "{}"
            if not isinstance(raw, str):
                raw = json.dumps(raw)
            d = decode_payload(raw)
            for oid in d.get("ids", []):
                if oid not in seen:
                    seen.add(oid)
                    all_ids.append(oid)
            print("    +got %d, total %d, boxVal=%s" % (len(d.get("ids", [])), len(all_ids), d.get("boxVal", "")), flush=True)
    return all_ids


def verify(dim, oid, gap=3):
    """Open detail page, verify exact size + 江浙沪 location via shared two-axis core.

    Uses scripts/two_axis_core.py (skuMapOriginal parsing) — the authoritative
    path that catches two-axis SKUs like `8x8（长宽）;9cm（高）`. The legacy
    verify_carton.js DOM path missed these (2026-08-22 user-corrected miss).
    """
    from two_axis_core import verify_one, parse_dim, prov_re_for
    try:
        PROV = os.environ.get("PROV", "江浙沪")
        TL, TW, TH = parse_dim(dim)
        return verify_one(cdp, oid, TL, TW, TH, prov_re_for(PROV))
    except Exception as e:
        return {"id": oid, "err": str(e), "url": "https://detail.1688.com/offer/%s.html" % oid}


def _new_client():
    http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    data = json.loads(http.open("http://127.0.0.1:9222/json", timeout=10).read())
    for t in data:
        if t.get("type") == "page":
            return CDP(t["webSocketDebuggerUrl"])
    # No page target open — auto-create one (Chrome is up but all tabs closed).
    return _ensure_tab()


def _ensure_tab():
    """Open a blank tab via the browser-level CDP websocket, return a CDP bound to it."""
    http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    ver = json.loads(http.open("http://127.0.0.1:9222/json/version", timeout=10).read())
    bws = ver["webSocketDebuggerUrl"]
    from websocket import create_connection
    ws = create_connection(bws, timeout=30)
    ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": "about:blank"}}))
    # read until our createTarget response
    target_id = None
    while True:
        obj = json.loads(ws.recv())
        if obj.get("id") == 1:
            target_id = obj.get("result", {}).get("targetId")
            break
    ws.close()
    if not target_id:
        raise RuntimeError("failed to open a tab on 9222")
    # re-read /json to find the new tab's debugger url
    data = json.loads(http.open("http://127.0.0.1:9222/json", timeout=10).read())
    for t in data:
        if t.get("type") == "page" and t.get("id") == target_id:
            return CDP(t["webSocketDebuggerUrl"])
    # fallback: first page target
    for t in data:
        if t.get("type") == "page":
            return CDP(t["webSocketDebuggerUrl"])
    raise RuntimeError("no page target on 9222 even after creating one")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["search", "verify"])
    ap.add_argument("dim", nargs="?", default="8*8*9")
    ap.add_argument("--pages", type=int, default=4)
    ap.add_argument("--ids", nargs="*", default=[])
    ap.add_argument("--ids-file", default=None)
    ap.add_argument("--out", default="/tmp/1688_result.json")
    ap.add_argument("--gap", type=float, default=3.0, help="seconds between detail-page visits (rate-limit)")
    ap.add_argument("--stop-on-cap", action="store_true", help="abort the batch if a captcha/intercept page is hit")
    ap.add_argument("--min-hits", type=int, default=0, help="stop early once this many confirmed hits are found")
    ap.add_argument("--cache", default=None, help="json file caching per-offer verify results (skip re-verified offers)")
    args = ap.parse_args()

    global cdp
    cdp = _new_client()
    cdp.enable()

    if args.cmd == "search":
        from search_mtop import search as msearch
        ids = msearch(args.dim, pages=args.pages)
        json.dump({"dim": args.dim, "ids": ids}, open(args.out, "w"), ensure_ascii=False)
        print("SEARCH_DONE ids=%d -> %s" % (len(ids), args.out))
        for it in ids:
            if isinstance(it, dict):
                print("%s | %s | %s%s | ¥%s | %s" % (
                    it.get("offerId", "?"), (it.get("title") or "")[:40],
                    it.get("province") or "?", it.get("city") or "",
                    it.get("price") or "?", "AD" if it.get("isAd") else ""))
            else:
                print(it)
    else:  # verify
        import time as _t
        raw_items = list(args.ids)
        meta = {}  # offerId -> mtop search dict (for title prefilter)
        if args.ids_file:
            if args.ids_file.endswith(".json"):
                data = json.load(open(args.ids_file, encoding="utf-8"))
                for it in data.get("ids", []):
                    if isinstance(it, dict) and it.get("offerId"):
                        meta[it["offerId"]] = it
                raw_items = list(meta.keys())
            else:
                with open(args.ids_file, encoding="utf-8") as f:
                    raw_items = [l.strip() for l in f if l.strip()]
        # --- title prefilter: rank candidates so likely hits verify first ---
        def _rank(oid):
            title = (meta.get(oid, {}).get("title") or "") if isinstance(meta.get(oid), dict) else ""
            score = 0
            if args.dim.replace("*", "") in title.lower().replace("x", "").replace("×", ""):
                score -= 10  # literal dims in title -> strongest signal
            return (score, oid)
        ordered = sorted(raw_items, key=_rank)
        cache = {}
        if args.cache and os.path.exists(args.cache):
            try:
                for r in json.load(open(args.cache, encoding="utf-8")):
                    cache[r["id"]] = r
            except Exception:
                pass
        hits = []
        n_hits = 0
        todo = [o for o in ordered if o not in cache]
        print("batch: %d candidates (%d cached, %d to verify)" % (len(ordered), len(cache), len(todo)), flush=True)
        for i, oid in enumerate(todo):
            print("[%d/%d] verify %s" % (i + 1, len(todo), oid), flush=True)
            r = verify(args.dim, oid)
            cache[oid] = r
            hits.append(r)
            if args.cache:
                json.dump(list(cache.values()), open(args.cache, "w"), ensure_ascii=False)
            if r.get("cap"):
                print("  CAPTCHA/INTERCEPT — session locked, stopping batch")
                if args.stop_on_cap:
                    break
                continue
            if r.get("hit") and r.get("jzh"):
                n_hits += 1
                print("  HIT 江浙沪+%s | %s | %s | price=%s stock=%s | %s" % (
                    args.dim, r.get("spec"), r.get("prov"), r.get("price"),
                    r.get("stock"), r.get("url")))
                if args.min_hits and n_hits >= args.min_hits:
                    print("  min-hits=%d reached — stopping early" % args.min_hits)
                    break
            else:
                print("  -- hit=%s prov=%r specs=%s" % (
                    r.get("hit"), r.get("prov"), r.get("n_specs")))
            if i < len(todo) - 1:
                _t.sleep(args.gap)
        all_results = [cache[o] for o in ordered if o in cache]
        json.dump(all_results, open(args.out, "w"), ensure_ascii=False)
        print("VERIFY_DONE hits=%d -> %s" % (
            sum(1 for h in all_results if h.get("hit") and h.get("jzh")), args.out))


if __name__ == "__main__":
    main()
