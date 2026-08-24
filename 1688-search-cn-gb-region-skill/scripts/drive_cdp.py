#!/usr/bin/env python3
# Raw-CDP driver for 1688 江浙沪找品 (replaces Playwright connectOverCDP which fails
# with setDownloadBehavior on externally-launched Chrome).
# Drives the REAL logged-in Chrome at CDP 127.0.0.1:9222. Same CDP method FRIDAY uses.
import json, time, sys, urllib.parse, re, urllib.request
import websocket

# localhost fetch: bypass macOS MITM proxy (urllib hangs on 127.0.0.1 otherwise)
_noproxy = urllib.request.build_opener(urllib.request.ProxyHandler({}))
def http_get(url):
    return _noproxy.open(url, timeout=10).read().decode("utf-8")

CDP = "http://127.0.0.1:9222"
SKILL = "/Users/kk/.hermes/skills/1688-search-cn-gb-region-skill/scripts"
DIM = "8*8*9"
CARTON = "纸箱"
PROV = "江苏,浙江,上海"
PAGES = 5
STOP_HIT = 12

def gbk(kw):
    return urllib.parse.quote(kw.encode("gbk"))

prov_enc = urllib.parse.quote(PROV)
def build_base(note):
    kw = note + "cm" + CARTON
    return "https://s.1688.com/selloffer/offer_search.htm?keywords=" + gbk(kw) + "&province=" + prov_enc + "&beginPage="

DIMX = DIM.replace("*", "x")

# Combined extraction: old detail.1688.com/offer/<id> + ?offerId= + inline offerId
EXTRACT = """
(() => {
  const h = document.documentElement.outerHTML;
  const ids = new Set(); let m;
  const re1 = /detail\\.1688\\.com\\/offer\\/(\\d+)/g;
  while ((m = re1.exec(h)) !== null) ids.add(m[1]);
  const re2 = /[?&]offerId=(\\d+)/g;
  while ((m = re2.exec(h)) !== null) ids.add(m[1]);
  const re3 = /offerId["']?\\s*[:=]\\s*["']?(\\d+)/g;
  while ((m = re3.exec(h)) !== null) ids.add(m[1]);
  const box = document.querySelector('input.search-input,input.box-input,input#jsk-search-input') || {};
  return JSON.stringify({title: document.title, boxVal: box.value || '', ids: [...ids].filter(id => id.length >= 9 && id.length <= 14)});
})();
"""

with open(SKILL + "/verify_carton.js") as f:
    VERIFY = f.read()
with open(SKILL + "/price_clean3.js") as f:
    PRICE = f.read()

class CDPClient:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=60)
        self._id = 0
    def send(self, method, params=None, sessionId=None):
        self._id += 1
        msg = {"id": self._id, "method": method, "params": params or {}}
        if sessionId: msg["sessionId"] = sessionId
        self.ws.send(json.dumps(msg))
        return self._id
    def recv(self, want_id=None, sessionId=None):
        while True:
            raw = self.ws.recv()
            d = json.loads(raw)
            if d.get("id") == want_id:
                return d
            # ignore events
    def call(self, method, params=None, sessionId=None):
        i = self.send(method, params, sessionId)
        return self.recv(i, sessionId)

def main():
    # browser ws
    v = json.loads(http_get(CDP + "/json/version"))
    browser_ws = v["webSocketDebuggerUrl"]
    bc = CDPClient(browser_ws)
    # new tab
    r = bc.call("Target.createTarget", {"url": "about:blank"})
    target_id = r["result"]["targetId"]
    r = bc.call("Target.attachToTarget", {"targetId": target_id, "flatten": True})
    sess = r["result"]["sessionId"]

    def ev(method, params=None):
        return bc.call(method, params, sess)
    def evaluate(expr):
        r = ev("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True, "timeout": 30000})
        res = r.get("result", {}).get("result", {})
        if "exceptionDetails" in r.get("result", {}):
            return ""
        return res.get("value", "")
    def navigate(url):
        ev("Page.enable")
        ev("Page.navigate", {"url": url})
        time.sleep(0.5)

    # warmup
    navigate("https://www.1688.com/")
    time.sleep(6)

    seen = set(); all_ids = []
    for note in [DIM, DIMX]:
        base = build_base(note)
        for pg in range(1, PAGES + 1):
            navigate(base + str(pg))
            time.sleep(7)
            for _ in range(8):
                evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
            d = json.loads(evaluate(EXTRACT) or "{}")
            ids = d.get("ids", [])
            for i in ids:
                if i not in seen:
                    seen.add(i); all_ids.append(i)
            print(f"[{note} p{pg}] +{len(ids)} total {len(all_ids)} box={d.get('boxVal','')[:20]}", flush=True)

    print(f"[extract] unique {len(all_ids)}", flush=True)

    hits = []
    for oid in all_ids:
        navigate(f"https://detail.1688.com/offer/{oid}.html")
        time.sleep(3)
        evaluate(f"window.TARGET='{DIM}';")
        time.sleep(0.6)
        vj = json.loads(evaluate(VERIFY) or "{}")
        pj = json.loads(evaluate(PRICE) or "{}")
        is_c = bool(vj.get("isCarton"))
        if is_c:
            hits.append({"id": oid, "title": vj.get("title",""), "price": pj.get("targetPrice",""),
                         "stock": pj.get("targetStock",""), "moq": pj.get("moq",""),
                         "url": f"https://detail.1688.com/offer/{oid}.html"})
            print(f"[HIT {len(hits)}] {oid} | {vj.get('title','')} | {pj.get('targetPrice','')} | 库存 {pj.get('targetStock','')}", flush=True)
        else:
            print(f"[   ] {oid} skuHit={vj.get('skuHit')} carton={vj.get('cartonSig')} gift={vj.get('giftSig')}", flush=True)
        if STOP_HIT and len(hits) >= STOP_HIT:
            break
        time.sleep(3)

    # sort by price asc
    def pf(x):
        m = re.search(r"[\d.]+", x.get("price","¥0") or "¥0")
        return float(m.group()) if m else 0
    hits.sort(key=pf)
    out = {"query": f"{DIM}cm {CARTON}, {PROV}", "unique_ids": len(all_ids), "hits": hits}
    with open(SKILL + "/../../store/8x8x9_jiangzhehu_result.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    rows = "\n".join(f"| {i+1} | {h['id']} | {h['title']} | {h['price']} | {h['stock']} | {h['moq']}个 | {h['url'] } |" for i,h in enumerate(hits))
    md = f"# 1688 找品结果：{DIM}cm {CARTON}，{PROV}\n\n提取候选 {len(all_ids)} 个，验证命中 {len(hits)} 个（逐详情页核对真实在售 SKU 含 {DIM}）\n\n| # | 商品ID | 标题 | 单价 | 库存 | 起批 | 链接 |\n|---|--------|------|------|------|------|------|\n{rows}\n"
    with open(SKILL + "/../../store/8x8x9_jiangzhehu_report.md", "w") as f:
        f.write(md)
    print(f"[done] hits={len(hits)} -> report written", flush=True)

if __name__ == "__main__":
    main()
