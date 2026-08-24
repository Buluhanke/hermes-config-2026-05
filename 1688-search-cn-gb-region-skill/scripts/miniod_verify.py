#!/usr/bin/env python3
"""miniod 零渲染核验通道：在已登录 Chrome 的 1688 源页面上下文里
fetch mtop.1688.laputa.miniod，拿全量 SKU（skuMapOriginal）+ 所在地，
完全绕开 Page.navigate 渲染（风控触发点）。"""
import sys, os, json, time, hashlib, urllib.parse
HERE = "/Users/kk/.hermes/skills/1688-search-cn-gb-region-skill/scripts"
sys.path.insert(0, HERE)
from cdp_client import _new_client

APP_KEY = "12574478"
API = ("https://h5api.m.1688.com/h5/mtop.1688.laputa.miniod/1.0/"
       "?jsv=2.5.1&appKey=%s&t={ts}&sign={sign}&api=mtop.1688.laputa.miniod"
       "&v=1.0&type=originaljson&dataType=json&data={data}" % APP_KEY)


def build_url(tok, offer_id):
    ts = int(time.time() * 1000)
    payload = json.dumps({"sk": "", "offerId": int(offer_id),
                          "parametersMap": json.dumps({"fromPC": True})},
                         separators=(',', ':'))
    sign = hashlib.md5(f"{tok}&{ts}&{APP_KEY}&{payload}".encode()).hexdigest()
    return API.format(ts=ts, sign=sign, data=urllib.parse.quote(payload, safe=''))


def fetch_detail(cdp, offer_id):
    tok = cdp.evaluate("(document.cookie.match(/_m_h5_tk=([^_]+)/)||[])[1] || ''", timeout=20)
    if not tok:
        raise RuntimeError("no _m_h5_tk on tab")
    js = """(async()=>{ try { const r = await fetch(%r, {credentials:'include'});
            return await r.text(); } catch(e){ return JSON.stringify({err:String(e)}); } })()""" % build_url(tok, offer_id)
    raw = cdp.send("Runtime.evaluate", {"expression": js, "returnByValue": True,
                                        "awaitPromise": True, "timeout": 45000}, timeout=50)
    val = raw.get("result", {}).get("result", {}).get("value")
    try:
        obj = json.loads(val)
    except Exception:
        return {"err": "nonjson", "head": str(val)[:200]}
    ret = " ".join(obj.get("ret", []))
    if "SUCCESS" not in ret:
        return {"err": ret[:150]}
    model = (obj.get("data") or {}).get("model") or {}
    od = ((model.get("offerModel") or {}).get("offerDetail")) or {}
    dm = model.get("dataModel") or {}
    # SKU：优先 mainPrice.fields.finalPriceModel.skuMapOriginal
    mp = dm.get("mainPrice") or {}
    skus = []
    try:
        skus = mp["fields"]["finalPriceModel"]["tradeWithoutPromotion"]["skuMapOriginal"] or []
    except Exception:
        pass
    loc = ""
    for key in ("shippingServices",):
        svc = dm.get(key) or {}
        txt = json.dumps(svc, ensure_ascii=False)
        import re
        m = re.search(r'"(?:recieveAddress|location)"\s*:\s*"([^"]{2,30})"', txt)
        if m:
            loc = m.group(1); break
    if not loc:
        import re
        m = re.search(r'"(?:recieveAddress|location)"\s*:\s*"((?:浙江|江苏|上海|广东)[^"]{0,20})"',
                      json.dumps(model, ensure_ascii=False))
        if m: loc = m.group(1)
    return {
        "title": od.get("subject") or dm.get("productTitle", ""),
        "location": loc,
        "n_sku": len(skus),
        "specs": [s.get("specAttrs", "") for s in skus][:80],
        "price_stock": [{"spec": s.get("specAttrs"), "price": s.get("price"),
                         "stock": s.get("canBookCount")} for s in skus][:10],
    }


if __name__ == "__main__":
    ids = sys.argv[1:] or ["677701816838"]
    cdp = _new_client(); cdp.enable()
    out = {}
    for oid in ids:
        r = fetch_detail(cdp, oid)
        out[oid] = r
        print(oid, "->", "ERR:" + str(r.get("err", "")) if r.get("err") else
              f'loc={r["location"]} n_sku={r["n_sku"]} spec0={r["specs"][0] if r["specs"] else "-"}')
        time.sleep(3)
    json.dump(out, open("/tmp/miniod_test.json", "w"), ensure_ascii=False, indent=1)
