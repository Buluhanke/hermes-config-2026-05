#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用修好的「整页组合串识别」重验已知 ID 池，挖出 46*26*10（顺序无关）的便宜货源。
不依赖搜页（搜页常被风控拦），直接开详情页。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp1688 as C

DIM = "46*26*10"
PERMS = C.target_perms(DIM)

def main():
    pool = [l.strip() for l in open("/tmp/pool_ids.txt", encoding="utf-8") if l.strip()]
    # 去重保序
    seen=set(); pool=[x for x in pool if not (x in seen or seen.add(x))]
    print(f"[pool] {len(pool)} ids", flush=True)

    c = C.CDP("http://127.0.0.1:9222")
    wt, ws = c.new_page("https://www.1688.com/")
    time.sleep(6)
    vt, vs = c.new_page("about:blank")

    results = []
    for oid in pool:
        try:
            url = f"https://detail.1688.com/offer/{oid}.html"
            c.navigate(vs, url)
            time.sleep(2.5)
            ttl = c.evaluate(vs, "document.title", await_promise=False) or ""
            if "淘宝网" in ttl or "captcha" in (c.evaluate(vs, "location.href", await_promise=False) or "").lower():
                print(f"[LOGIN/CODE] {oid} skip", flush=True); time.sleep(2); continue
            h = c.evaluate(vs, "document.documentElement.outerHTML", await_promise=False) or ""
            if "验证码" in h:
                print(f"[CODE] {oid} 验证码, 停", flush=True); break
            # 整页逐段抽尺寸
            best = None
            # 先从 skuMapOriginal 精确匹配（价/库存最准）
            rows = C.parse_sku_json(h)
            for spec, price, stock in rows:
                conn, lw, heights = C.extract_sizes_from_spec(spec)
                if any(p in conn for p in PERMS):
                    if best is None or (price and (best[1] is None or float(price) < float(best[1]))):
                        best = (spec[:50], price, stock)
            # 整页文本兜底（覆盖 specAttrs 之外的组合串写法）
            if best is None:
                for seg in re.split(r"[;；\n|丨]", h):
                    if ("长" in seg or "宽" in seg or "高" in seg or re.search(r"[0-9][0-9.]*[xX×*][0-9]", seg)):
                        conn, lw, heights = C.extract_sizes_from_spec(seg)
                        if any(p in conn for p in PERMS):
                            best = (seg[:50], None, None)
                            break
            if best:
                shop = ""
                sm = re.search(r'([一-龥]{2,}(?:包装|纸业|纸箱|盒业|实业|工厂|科技|新材料|供应链)[一-龥]{0,12})', ttl)
                if sm: shop = sm.group(1)
                rec = {"id": oid, "title": ttl[:40], "shop": shop,
                       "spec": best[0], "price": best[1], "stock": best[2], "url": url}
                results.append(rec)
                print(f"[HIT] {oid} ¥{best[1]} 库存{best[2]} | {best[0][:40]}", flush=True)
            else:
                print(f"[   ] {oid} 无46x26x10", flush=True)
        except Exception as ex:
            print(f"[ERR] {oid} {repr(ex)[:60]}", flush=True)
        time.sleep(2)

    c.close_target(vt, vs)
    c.close_target(wt, ws)
    c.ws.close()
    results.sort(key=lambda r: float(r["price"]) if r["price"] else 999)
    with open(os.path.join(C.SKILL, "store", "46x26x10_reverify.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[done] hits={len(results)} -> store/46x26x10_reverify.json", flush=True)
    for r in results:
        print(f"  ¥{r['price']}  {r['id']}  {r['shop']}  {r['spec'][:36]}", flush=True)

if __name__ == "__main__":
    main()
