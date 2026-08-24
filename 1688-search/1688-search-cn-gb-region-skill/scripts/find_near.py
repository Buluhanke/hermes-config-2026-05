#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""找 46*26*10 的现货或定制货源：搜定制/画框/平邮类词，抓每个卖家全部含 46/26/10 的尺寸 + 店名 + 链接。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp1688 as C

DIM = "46*26*10"
TARGET = set(C.target_perms(DIM))  # 顺序无关
NEAR = {"46", "26", "10"}  # 近邻尺寸

def main():
    cat = ["46*26*10cm纸箱", "画框纸箱 定制", "平邮箱 定制", "46*26 纸箱", "字画箱 定制"]
    c = C.CDP("http://127.0.0.1:9222")
    wt, ws = c.new_page("https://www.1688.com/")
    time.sleep(6)
    seen = set(); ids = []
    for kw in cat:
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
    for oid in ids[:90]:
        try:
            url = f"https://detail.1688.com/offer/{oid}.html"
            c.navigate(vs, url); time.sleep(2.5)
            ttl = c.evaluate(vs, "document.title", await_promise=False) or ""
            body = c.get_sku(vs, oid, timeout=12)
            if not body:
                print(f"[   ] {oid} 无SKU", flush=True); time.sleep(2); continue
            rows = C.parse_sku_json(body)
            # 精确命中？
            exact = False
            near_sizes = []
            for spec, price, stock in rows:
                conn, lw, heights = C.extract_sizes_from_spec(spec)
                if any(p in conn for p in TARGET):
                    exact = True
                # 近邻：含 46 或 26 或 10 的尺寸
                for s in conn:
                    if any(n in s.split("*") for n in NEAR):
                        near_sizes.append((s, price, stock))
            if exact:
                print(f"[HIT] {oid} {ttl[:30]}", flush=True)
                out.append({"id": oid, "title": ttl[:40], "url": url, "exact": True, "near": near_sizes[:8]})
            else:
                # 只保留“含 46 或 26”的近邻卖家，避免噪音
                if any("46" in s or "26" in s for s, _, _ in near_sizes):
                    out.append({"id": oid, "title": ttl[:40], "url": url, "exact": False, "near": near_sizes[:10]})
            if len(out) % 10 == 0:
                print(f"[progress] collected {len(out)}", flush=True)
        except Exception as ex:
            print(f"[ERR] {oid} {repr(ex)[:60]}", flush=True)
        time.sleep(2)
    c.close_target(vt, vs)
    c.ws.close()
    with open(os.path.join(C.SKILL, "store", "46x26x10_near.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[done] exact_or_near sellers={len(out)} exact={sum(1 for o in out if o['exact'])} -> store/46x26x10_near.json", flush=True)

if __name__ == "__main__":
    main()
