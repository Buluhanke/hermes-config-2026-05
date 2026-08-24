#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""趁详情页能开的窗口，批量开候选详情页，整页识别 46*26*10（容差5），取精确价+库存比价。
撞验证码就停（不硬撞）。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp1688 as C

DIM="46*26*10"
PERMS=C.target_perms(DIM)
TOL=C.tolerant_perms(DIM,5.0)

def main():
    ids=[l.strip() for l in open("/tmp/pool_ids.txt",encoding="utf-8") if l.strip()]
    seen=set(); ids=[x for x in ids if not (x in seen or seen.add(x))]
    print(f"[pool]{len(ids)} ids",flush=True)
    c=C.CDP("http://127.0.0.1:9222")
    wt,ws=c.new_page("https://www.1688.com/"); time.sleep(6)
    vt,vs=c.new_page("about:blank")
    results=[]
    for oid in ids:
        try:
            url=f"https://detail.1688.com/offer/{oid}.html"
            c.navigate(vs,url); time.sleep(2.5)
            h=c.evaluate(vs,"document.documentElement.outerHTML",await_promise=False) or ""
            if "验证码" in h:
                print(f"[CODE]{oid} 详情页被拦,停",flush=True); break
            ttl=c.evaluate(vs,"document.title",await_promise=False) or ""
            # 纸包装类目卡
            if not C.CARTON_SIG.search(h):
                print(f"[skip]{oid} 非纸包装",flush=True); time.sleep(1.5); continue
            rows=C.parse_sku_json(h)
            best=None
            for spec,price,stock in rows:
                conn,_,_=C.extract_sizes_from_spec(spec)
                if TOL(conn):
                    exact=any(p in conn for p in PERMS)
                    if best is None or (price and (best[1] is None or float(price)<float(best[1]))):
                        best=(spec[:50],price,stock,exact)
            if best:
                shop=""
                sm=re.search(r'([一-龥]{2,}(?:包装|纸业|纸箱|盒业|实业|工厂|科技|新材料|供应链)[一-龥]{0,12})',ttl)
                if sm: shop=sm.group(1)
                rec={"id":oid,"title":ttl[:40],"shop":shop,"spec":best[0],
                     "price":best[1],"stock":best[2],"exact":best[3],"url":url}
                results.append(rec)
                print(f"[HIT{'近似' if not best[3] else ''}] {oid} ¥{best[1]} 库存{best[2]} | {best[0][:36]}",flush=True)
            else:
                print(f"[   ]{oid} 无46x26x10±5",flush=True)
        except Exception as ex:
            print(f"[ERR]{oid} {repr(ex)[:60]}",flush=True)
        time.sleep(1.8)
    c.close_target(vt,vs); c.close_target(wt,ws); c.ws.close()
    results.sort(key=lambda r:float(r["price"]) if r["price"] else 999)
    with open(os.path.join(C.SKILL,"store","46x26x10_others.json"),"w",encoding="utf-8") as f:
        json.dump(results,f,ensure_ascii=False,indent=2)
    print(f"[done] hits={len(results)} -> store/46x26x10_others.json",flush=True)
    for r in results:
        print(f"  ¥{r['price']} {r['id']} {r['shop']} {r['spec'][:34]}",flush=True)

if __name__=="__main__":
    main()
