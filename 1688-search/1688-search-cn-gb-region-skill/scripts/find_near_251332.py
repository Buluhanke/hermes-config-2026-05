#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""25*13*32 牛皮纸手提袋：找精确命中 + 近邻(含某轴25/13/32)可定制卖家。
复用 cdp1688 的尺寸提取与 CDP 通道。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp1688 as C

DIM = "25*13*32"
TARGET = set(C.target_perms(DIM))
NEAR = {"25", "13", "32"}

CAT = ["25*13*32cm手提袋", "25*13*32cm牛皮纸手提袋", "牛皮纸手提袋",
       "纸手提袋", "手提袋定做", "牛皮纸袋"]

def main():
    c = C.CDP("http://127.0.0.1:9222")
    # 暖场建会话
    wt, ws = c.new_page("https://www.1688.com/")
    time.sleep(6)
    seen = set(); ids = []
    for kw in CAT:
        for pg in range(1, 4):
            url = C.build_search_url(kw, pg)
            c.navigate(ws, url); time.sleep(7)
            for _ in range(6):
                c.evaluate(ws, "window.scrollTo(0,document.body.scrollHeight)", await_promise=False); time.sleep(0.8)
            data = c.evaluate(ws, C.EXTRACT, await_promise=False)
            try: j = json.loads(data) or {}
            except Exception: j = {}
            for i in (j.get("ids") or []):
                if i not in seen: seen.add(i); ids.append(i)
            print(f"[search] {kw} p{pg} total {len(ids)}", flush=True)
    c.close_target(wt, ws)
    print(f"[extract] candidates={len(ids)}", flush=True)

    vt, vs = c.new_page("about:blank")
    out = []
    for oid in ids:
        try:
            url = f"https://detail.1688.com/offer/{oid}.html"
            c.navigate(vs, url); time.sleep(2.5)
            ttl = str(c.evaluate(vs, "document.title", await_promise=False) or "")
            body = c.get_sku(vs, oid, timeout=12)
            if not body:
                time.sleep(2); continue
            rows = C.parse_sku_json(body)
            exact = False; near_sizes = []
            for spec, price, stock in rows:
                conn, lw, heights = C.extract_sizes_from_spec(spec)
                if any(p in conn for p in TARGET):
                    exact = True
                for s in conn:
                    if any(n in s.split("*") for n in NEAR):
                        near_sizes.append((s, price, stock))
            if exact:
                print(f"[HIT] {oid} {ttl[:30]} | {url}", flush=True)
                out.append({"id": oid, "title": ttl[:40], "url": url, "exact": True, "near": near_sizes[:8]})
            else:
                if near_sizes:
                    print(f"[NEAR] {oid} {ttl[:30]} | {[s for s,_,_ in near_sizes][:6]}", flush=True)
                    out.append({"id": oid, "title": ttl[:40], "url": url, "exact": False, "near": near_sizes[:8]})
        except Exception as e:
            print(f"[ERR] {oid} {e}", flush=True)
        time.sleep(2.5)
    # 写盘
    with open(os.path.join(C.SKILL, "store", "25x13x32_near.json"), "w", encoding="utf-8") as f:
        json.dump({"dim": DIM, "exact": [o for o in out if o["exact"]],
                   "near": [o for o in out if not o["exact"]]}, f, ensure_ascii=False, indent=2)
    print(f"[done] exact={len([o for o in out if o['exact']])} near={len([o for o in out if not o['exact']])}", flush=True)

if __name__ == "__main__":
    main()
