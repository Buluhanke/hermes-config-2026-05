#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""真人模式 1688 找品：复用 9333 已登录常驻实例。
阶段1 搜页一次拿全(ID+标题+店铺+卡片价)，阶段2 逐条详情页只补目标尺寸SKU单价。
每页/每条增量落盘。用法:
  python3 human_mode.py --dims 15*15*15 --kw "15*15*15cm纸箱" "正方形纸箱" --pages 2 --maxverify 60 --out store/human_15cube.json
"""
import sys, os, json, time, re, argparse, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cdp1688 as C

PROV = "%E6%B1%9F%E8%8B%8F,%E6%B5%99%E6%B1%9F,%E4%B8%8A%E6%B5%BD"  # 江浙沪 GBK
CDP = "http://127.0.0.1:9333"  # 用户已登录常驻实例，绝不新建

# 搜页卡片：一次拿 ID + 标题 + 店铺名(innerText最后一行) + 卡片价
CARD_JS = """(()=>{const cs=[...document.querySelectorAll('[data-offer-grid-cell]')];
return JSON.stringify(cs.map(c=>({id:c.getAttribute('data-offer-expose-id'),
t:(c.innerText||'').split('\\n').map(x=>x.trim()).filter(Boolean)})));})()"""

def parse_card(card):
    oid = card.get("id")
    if not oid or not oid.isdigit(): return None
    lines = card.get("t", [])
    if not lines: return None
    title = lines[0]
    shop = ""
    for ln in reversed(lines):
        if re.search(r'(有限公司|有限责任公司|厂$|商行|贸易|纸制品|包装|箱包)', ln) and len(ln) >= 4:
            shop = ln; break
    if not shop and len(lines) > 1: shop = lines[-1]
    # 价格：找 '¥' 后的数字段（卡片拆成 ['¥','4','.99']）
    price = ""
    for i, ln in enumerate(lines):
        if ln == "¥" and i + 2 < len(lines):
            a, b = lines[i+1], lines[i+2]
            if re.match(r'^[0-9]+$', a) and b.startswith("."):
                price = a + b[:4]; break
            elif re.match(r'^[0-9]+$', a):
                price = a; break
    return {"id": oid, "title": title, "shop": shop, "card_price": price, "url": f"https://detail.1688.com/offer/{oid}.html"}

def target_hit(body, dims):
    """详情页 SKU 文本是否含目标尺寸（5类写法交给 cdp1688 的匹配；这里先做宽松串匹配）"""
    if not body: return False
    a, b, c = dims.split("*")
    pats = [f"{a}*{b}*{c}", f"{a}x{b}x{c}", f"{a}×{b}×{c}"]
    # 顺序无关
    import itertools
    for p in itertools.permutations([a, b, c]):
        pats.append("*".join(p))
    low = body.replace(" ", "").lower()
    return any(p.lower() in low for p in pats)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dims", required=True)
    ap.add_argument("--kw", nargs="+", required=True)
    ap.add_argument("--pages", type=int, default=2)
    ap.add_argument("--maxverify", type=int, default=60)
    ap.add_argument("--gap", type=float, default=2.0)
    ap.add_argument("--prov", default=PROV)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    c = C.CDP(CDP)
    # ---- 阶段1：搜页一次拿全 ----
    seen, cards = set(), []
    _, s = c.new_page("about:blank")
    for kw in args.kw:
        for pg in range(1, args.pages + 1):
            c.navigate(s, C.build_search_url(kw, pg, args.prov))
            time.sleep(6)
            for _ in range(5):
                c.evaluate(s, "window.scrollTo(0,document.body.scrollHeight)", await_promise=False)
                time.sleep(0.7)
            r = c.evaluate(s, CARD_JS, await_promise=False)
            try: raw = json.loads(r or "[]")
            except Exception: raw = []
            new = 0
            for card in raw:
                rec = parse_card(card)
                if rec and rec["id"] not in seen:
                    seen.add(rec["id"]); cards.append(rec); new += 1
            print(f"[search] {kw} p{pg} +{new} total={len(cards)}", flush=True)
            json.dump(cards, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    # ---- 阶段2：逐条详情页只补目标尺寸 ----
    _, vs = c.new_page("about:blank")
    login_streak, hits = 0, []
    for i, rec in enumerate(cards[:args.maxverify]):
        c.navigate(vs, rec["url"])
        time.sleep(3)
        ttl = c.evaluate(vs, "document.title", await_promise=False) or ""
        href = c.evaluate(vs, "location.href", await_promise=False) or ""
        if "taobao" in str(href) or "淘宝" in str(ttl):
            login_streak += 1
            print(f"[LOGIN-WALL] {rec['id']} ({login_streak})", flush=True)
            if login_streak >= 5:
                print("[STOP] 连续5个登录墙，停止", flush=True); break
            continue
        login_streak = 0
        body = c.get_sku(vs, rec["id"], timeout=20)
        if target_hit(body, args.dims):
            hits.append(rec)
            print(f"[HIT] {rec['id']} | ¥{rec['card_price']} | {rec['shop']}", flush=True)
        else:
            print(f"[   ] {rec['id']} 无{args.dims}", flush=True)
        json.dump({"cards": len(cards), "hits": hits}, open(args.out.replace(".json", "_result.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        time.sleep(args.gap)
    c.ws.close()
    print(f"[DONE] 命中 {len(hits)} 家 -> {args.out.replace('.json','_result.json')}", flush=True)

if __name__ == "__main__":
    main()
