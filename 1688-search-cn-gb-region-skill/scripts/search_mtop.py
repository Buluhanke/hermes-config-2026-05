#!/usr/bin/env python3
"""1688 search via mtop JSON API, driven from a logged-in Chrome page context.

WHY (2026-08-22, task-0 empirical finding):
The old HTML endpoint `s.1688.com/selloffer/offer_search.htm` is now hard-blocked
by 1688 risk control (returns 验证码拦截 / tmd punish). But the SAME search done
through the mtop gateway `h5api.m.1688.com/.../WirelessRecommend.recommend/2.0/`
works perfectly WHEN the fetch is issued from a page that is already on a 1688
origin (real TLS fingerprint + full cookie). Raw socket / headless direct calls
still get RGV587_ERROR — so we MUST run the fetch inside the logged-in Chrome via
CDP Runtime.evaluate (awaitPromise).

Structured response path:
  data.data.OFFER.items[] -> each has:
    offerId (str/int), title, province, city, priceInfo.price, shop.text,
    bookedCount, isP4P (ad flag), type

Server-side hard filters that actually work (task-0 verified):
  categoryId=1033008  ->纸箱类目, 源头排除礼盒 (found 2000->428)
  sortType=booked      -> 清空 P4P 广告
  province=江苏,浙江,上海 -> 江浙沪硬筛 (服务端生效)

pageSize caps at 60 (61+ gets truncated). Page 5+ returns only dupes -> dedup by id to stop.
"""
import sys, os, json, time, hashlib, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cdp_client import _new_client, CDP

APP_KEY = "12574478"
APP_ID = "32517"
API_PATH = ("https://h5api.m.1688.com/h5/mtop.relationrecommend.wirelessrecommend.recommend/2.0/"
            "?jsv=2.5.1&appKey=" + APP_KEY + "&t={ts}&sign={sign}"
            "&api=mtop.relationrecommend.WirelessRecommend.recommend&v=2.0"
            "&type=originaljson&dataType=json&data={data}")


def _build_url(tok, kw, page, province="江苏,浙江,上海", category_id=None, sort="booked", page_size=60):
    ts = int(time.time() * 1000)
    # 类目硬筛：默认仍为纸箱(1033008)保持历史任务行为；搜其他品类用环境变量覆盖，
    # 如 CAT= (空串,不筛类目) 或 CAT=<其他类目id>。⚠ 用错类目会召回模糊杂品（坑42）。
    cat = category_id if category_id is not None else os.environ.get("CAT", "1033008")
    params = {
        "keywords": kw, "beginPage": page, "pageSize": page_size,
        "method": "getOfferList", "verticalProductFlag": "pcmarket",
        "searchScene": "pcOfferSearch", "province": province,
        "sortType": sort,
    }
    if cat:
        params["categoryId"] = cat
    inner = json.dumps(params, separators=(',', ':'), ensure_ascii=False)
    payload = json.dumps({"appId": APP_ID, "params": inner}, separators=(',', ':'), ensure_ascii=False)
    sign = hashlib.md5(f"{tok}&{ts}&{APP_KEY}&{payload}".encode()).hexdigest()
    return API_PATH.format(ts=ts, sign=sign, data=urllib.parse.quote(payload, safe=''))


def _eval_fetch(cdp, url):
    js = """(async()=>{
      try { const r = await fetch(%r, {credentials:'include'});
            const t = await r.text(); return t; }
      catch(e){ return JSON.stringify({err:String(e)}); }
    })()""" % url
    r = cdp.send("Runtime.evaluate",
                 {"expression": js, "returnByValue": True, "awaitPromise": True, "timeout": 45000},
                 timeout=50)
    return r.get("result", {}).get("result", {}).get("value")


def search_page(cdp, kw, page=1, province="江苏,浙江,上海"):
    """Return list of dicts {offerId,title,province,city,price,shop,booked,isAd} for one page."""
    tok = cdp.evaluate("(document.cookie.match(/_m_h5_tk=([^_]+)/)||[])[1] || ''", timeout=20)
    if not tok:
        raise RuntimeError("no _m_h5_tk cookie on this tab — navigate to a 1688 page first")
    url = _build_url(tok, kw, page, province=province)
    raw = _eval_fetch(cdp, url)
    if isinstance(raw, str):
        try:
            obj = json.loads(raw)
        except Exception:
            return []
        items = (obj.get("data", {}).get("data", {}).get("OFFER", {}).get("items", []))
        out = []
        for it in items:
            d = it.get("data", {}) if isinstance(it, dict) else {}
            if not isinstance(d, dict):
                continue
            out.append({
                "offerId": str(d.get("offerId", "")),
                "title": (d.get("title") or "").replace("\u003c", "<").replace("\u003e", ">"),
                "province": d.get("province", ""),
                "city": d.get("city", ""),
                "price": (d.get("priceInfo") or {}).get("price") if isinstance(d.get("priceInfo"), dict) else None,
                "shop": (d.get("shop") or {}).get("text") if isinstance(d.get("shop"), dict) else None,
                "booked": d.get("bookedCount", ""),
                "isAd": bool(d.get("isP4P") or d.get("isBid")),
            })
        return out
    return []


def search(kw, pages=4, province="江苏,浙江,上海", variant=None):
    """Search across pages, dedup by offerId. If variant given, use that query string
    instead of kw (for the multi-variant matrix). Returns deduped list."""
    cdp = _new_client(); cdp.enable()
    cdp.navigate("https://detail.1688.com/offer/677701816838.html", wait=5)
    query = variant if variant else kw
    seen, all_items = set(), []
    for pg in range(1, pages + 1):
        try:
            items = search_page(cdp, query, pg, province=province)
        except Exception as e:
            print("  [%s] page %d err: %s" % (query, pg, e), flush=True)
            break
        if not items:
            break
        new = [x for x in items if x["offerId"] and x["offerId"] not in seen]
        if not new:
            break  # page5+ returns only dupes
        for x in new:
            seen.add(x["offerId"]); all_items.append(x)
        print("  [%s] page %d -> %d new (total %d)" % (query, pg, len(new), len(all_items)), flush=True)
    return all_items


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("kw", nargs="?", default="8x8x9cm纸箱")
    ap.add_argument("--pages", type=int, default=4)
    ap.add_argument("--province", default="江苏,浙江,上海")
    ap.add_argument("--variant")
    ap.add_argument("--out", default="/tmp/mtop_ids.json")
    args = ap.parse_args()
    res = search(args.kw, pages=args.pages, province=args.province, variant=args.variant)
    json.dump(res, open(args.out, "w"), ensure_ascii=False, indent=2)
    print("SEARCH_DONE unique=%d -> %s" % (len(res), args.out))
    print(",".join(x["offerId"] for x in res))
