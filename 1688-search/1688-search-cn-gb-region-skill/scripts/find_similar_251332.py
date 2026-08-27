#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从种子 1158678687 详情页挖 同店其他商品+同款推荐 的 offerId，逐个验是否含 25*13*32 牛皮纸手提袋。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp1688 as C

DIM = "25*13*32"
TARGET = set(C.target_perms(DIM))
SEED = "1158678687"

def grab_ids(html):
    ids = set()
    for m in re.finditer(r"detail\.1688\.com/offer/(\d+)", html):
        ids.add(m.group(1))
    for m in re.finditer(r"[?&]offerId=(\d+)", html):
        ids.add(m.group(1))
    for m in re.finditer(r"offerId[\"']?\s*[:=]\s*[\"']?(\d+)", html):
        ids.add(m.group(1))
    return {i for i in ids if 9 <= len(i) <= 14}

def main():
    c = C.CDP("http://127.0.0.1:9222")
    vt, vs = c.new_page("about:blank")
    # 1) 种子页挖推荐/同店 ID
    c.navigate(vs, f"https://detail.1688.com/offer/{SEED}.html"); time.sleep(3)
    h = c.evaluate(vs, "document.documentElement.outerHTML", await_promise=False) or ""
    pool = grab_ids(h)
    pool.discard(SEED)
    print(f"[seed] 挖到关联ID {len(pool)} 个", flush=True)

    hits = []
    for oid in sorted(pool):
        try:
            c.navigate(vs, f"https://detail.1688.com/offer/{oid}.html"); time.sleep(2.5)
            ttl = str(c.evaluate(vs, "document.title", await_promise=False) or "")
            if "淘宝网" in ttl or "验证码" in ttl:
                time.sleep(2); continue
            body = c.get_sku(vs, oid, timeout=15)
            if not body:
                time.sleep(2); continue
            rows = C.parse_sku_json(body)
            best = None
            for spec, price, stock in rows:
                conn, lw, heights = C.extract_sizes_from_spec(spec)
                if any(p in conn for p in TARGET):
                    if best is None or (price and (best[1] is None or float(price) < float(best[1]))):
                        best = (spec[:60], price, stock)
            if best:
                is_kraft = ("牛皮纸" in ttl) or ("纸袋" in ttl)
                rec = {"id": oid, "title": ttl[:40], "kraft": is_kraft,
                       "spec": best[0], "price": best[1], "stock": best[2],
                       "url": f"https://detail.1688.com/offer/{oid}.html"}
                hits.append(rec)
                print(f"[HIT] {oid} {'牛皮纸' if is_kraft else '其他'} ¥{best[1]} 库存{best[2]} | {best[0][:38]}", flush=True)
            else:
                print(f"[   ] {oid} 无25*13*32 ({ttl[:24]})", flush=True)
        except Exception as e:
            print(f"[ERR] {oid} {repr(e)[:50]}", flush=True)
        time.sleep(2)
    c.close_target(vt, vs)
    hits.sort(key=lambda r: float(r["price"]) if r["price"] else 999)
    with open(os.path.join(C.SKILL, "store", "25x13x32_similar.json"), "w", encoding="utf-8") as f:
        json.dump({"seed": SEED, "hits": hits}, f, ensure_ascii=False, indent=2)
    print(f"[done] 关联ID={len(pool)} 命中25*13*32={len(hits)}", flush=True)

if __name__ == "__main__":
    main()
