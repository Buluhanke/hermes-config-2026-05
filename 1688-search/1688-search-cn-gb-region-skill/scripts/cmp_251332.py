#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比 25*13*32 牛皮纸手提袋：种子森烨 + 近邻牛皮纸袋厂，抠最接近尺寸真实单价。"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp1688 as C

DIM = "25*13*32"
TARGET = set(C.target_perms(DIM))
# 候选：森烨种子 + 之前 near 结果里 score>=3 的牛皮纸袋厂
POOL = [
    "1158678687",   # 森烨(种子,已知有25*13*32)
    "1066611511095", # 月饼牛皮纸 26*13*33
    "976892640516", # 加厚牛皮纸 44*32*13
    "835919358954", # 牛皮纸手提袋 32*11*25
    "1064783011964", # 手提牛皮纸袋 32*11*25
    "704414041833", # 牛皮纸袋 40*13*30
    "832563669429", # 牛皮纸手提袋 32*11*25
    "696158031878", # 外卖牛皮纸袋 32*11*25
    "943636086644", # 牛皮纸袋 40.5*13*31
]

def main():
    c = C.CDP("http://127.0.0.1:9222")
    vt, vs = c.new_page("about:blank")
    out = []
    for oid in POOL:
        try:
            c.navigate(vs, f"https://detail.1688.com/offer/{oid}.html"); time.sleep(2.5)
            ttl = str(c.evaluate(vs, "document.title", await_promise=False) or "")
            if "淘宝网" in ttl or "验证码" in ttl:
                print(f"[WALL] {oid}", flush=True); time.sleep(2); continue
            body = c.get_sku(vs, oid, timeout=15)
            if not body:
                print(f"[NOSKU] {oid}", flush=True); time.sleep(2); continue
            rows = C.parse_sku_json(body)
            # 找精确25*13*32 或 最接近(含≥2轴且差<=2cm)
            exact = None; best_near = None
            for spec, price, stock in rows:
                conn, lw, heights = C.extract_sizes_from_spec(spec)
                if any(p in conn for p in TARGET):
                    if exact is None or (price and float(price) < float(exact[1] or 999)):
                        exact = (spec, price, stock)
                # 近邻评分
                for s in conn:
                    parts = [p for p in re.split(r"[*×xX]", s) if p.replace(".","",1).isdigit()]
                    if len(parts) == 3:
                        score = sum(1 for t in ("25","13","32") if any(abs(float(p)-float(t))<=2 for p in parts))
                        if score >= 2:
                            key = float(price) if price else 999
                            if best_near is None or key < best_near[3]:
                                best_near = (s, price, stock, key)
            if exact:
                out.append({"id":oid,"title":ttl[:36],"match":"EXACT 25*13*32","spec":exact[0],"price":exact[1],"stock":exact[2],"url":f"https://detail.1688.com/offer/{oid}.html"})
                print(f"[EXACT] {oid} ¥{exact[1]} {exact[0][:40]}", flush=True)
            elif best_near:
                out.append({"id":oid,"title":ttl[:36],"match":f"NEAR {best_near[0]}","spec":best_near[0],"price":best_near[1],"stock":best_near[2],"url":f"https://detail.1688.com/offer/{oid}.html"})
                print(f"[NEAR] {oid} ¥{best_near[1]} {best_near[0]}", flush=True)
            else:
                print(f"[   ] {oid} 无近邻", flush=True)
        except Exception as e:
            print(f"[ERR] {oid} {repr(e)[:50]}", flush=True)
        time.sleep(2)
    c.close_target(vt, vs)
    with open(os.path.join(C.SKILL,"store","25x13x32_cmp.json"),"w",encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[done] {len(out)} 家", flush=True)

if __name__ == "__main__":
    main()
