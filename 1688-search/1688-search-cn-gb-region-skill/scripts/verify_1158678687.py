#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证单ID 1158678687 是否真含 25*13*32，并抠精确价/库存/起订量。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp1688 as C

DIM = "25*13*32"
TARGET = set(C.target_perms(DIM))

def main():
    oid = "1158678687"
    c = C.CDP("http://127.0.0.1:9222")
    vt, vs = c.new_page("about:blank")
    url = f"https://detail.1688.com/offer/{oid}.html"
    c.navigate(vs, url); time.sleep(3)
    ttl = str(c.evaluate(vs, "document.title", await_promise=False) or "")
    print("TITLE:", ttl)
    body = c.get_sku(vs, oid, timeout=20)
    if not body:
        print("NO SKU / 登录墙")
        return
    rows = C.parse_sku_json(body)
    print(f"SKU rows={len(rows)}")
    for spec, price, stock in rows:
        conn, lw, heights = C.extract_sizes_from_spec(spec)
        hit = any(p in conn for p in TARGET)
        mark = " <<<25*13*32" if hit else ""
        if hit or any(n in spec for n in ("25","13","32")):
            print(f"  spec={spec!r} price={price} stock={stock}{mark}")
    c.close_target(vt, vs)

if __name__ == "__main__":
    main()
