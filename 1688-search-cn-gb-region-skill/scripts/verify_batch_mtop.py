#!/usr/bin/env python3
"""Batch-fetch 1688 detail raw HTML from a logged-in Chrome page context, then run
two_axis_core verification on each. Replaces the slow per-page CDP-navigate approach
(task-0 empirical: same-origin fetch of detail HTML is 0.82s/5 offers, no render, no captcha).

The detail HTML contains `skuMapOriginal` (full SKU list, no virtual-scroll truncation)
and `freightInfo.location` (structured province). two_axis_core.norm_dim parses specAttrs.
"""
import sys, os, json, time, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cdp_client import _new_client
from two_axis_core import norm_dim, prov_re_for

TL, TW, TH = 8, 8, 9
PROV = "江浙沪"
prov_re = prov_re_for(PROV)


def batch_specs(cdp, ids, gap=1.5):
    """Fetch detail raw HTML one-by-one (SERIAL, low rate) to avoid RGV587 rate-limit.
    High concurrency triggered FAIL_SYS_USER_VALIDATE captcha pages. Serial + 1.5s gap is safe.
    Returns dict offerId -> {specs, loc, cap, len}."""
    result = {}
    for oid in ids:
        js = """(async()=>{
          const id='%s';
          try{
            const r=await fetch('https://detail.1688.com/offer/'+id+'.html',{credentials:'include'});
            const h=await r.text();
            const specs=[...new Set([...h.matchAll(/"specAttrs"\\s*:\\s*"([^"]{1,140})"/g)].map(m=>m[1]))];
            const locM=h.match(/"location"\\s*:\\s*"(浙江|江苏|上海|[^"]{2,8}省[^"]{0,10})"/);
            return JSON.stringify({len:h.length, cap:/x5secdata|验证码拦截/.test(h),
                     loc: locM?locM[1]:'', specs});
          }catch(e){ return JSON.stringify({err:String(e).slice(0,80)}); }
        })()""" % oid
        try:
            r = cdp.send("Runtime.evaluate",
                         {"expression": js, "returnByValue": True, "awaitPromise": True, "timeout": 30000},
                         timeout=35)
            val = r.get("result", {}).get("result", {}).get("value")
            if isinstance(val, str):
                try:
                    result[oid] = json.loads(val)
                except Exception:
                    result[oid] = {"err": "parse"}
            else:
                result[oid] = {"err": "no-val"}
        except Exception as e:
            result[oid] = {"err": "sendfail:%s" % str(e)[:60]}
        time.sleep(gap)
    return result


def verify_ids(ids, out_path="/tmp/mtop_verify.json"):
    cdp = _new_client(); cdp.enable()
    cdp.navigate("https://detail.1688.com/offer/677701816838.html", wait=5)
    raw = batch_specs(cdp, ids)
    hits = []
    for oid, info in raw.items():
        if not isinstance(info, dict):
            continue
        if info.get("cap"):
            continue
        specs = info.get("specs", [])
        hit = None
        for s in specs:
            d = norm_dim(s)
            if d and d[0] == TL and d[1] == TW and d[2] == TH:
                hit = s; break
        loc = info.get("loc", "")
        jzh = bool(prov_re.search(loc)) if loc else False
        if hit and jzh:
            hits.append({"id": oid, "spec": hit, "prov": loc})
            print("  HIT %s | %s | %s" % (oid, hit, loc), flush=True)
        else:
            print("  -- %s spec_hit=%s jzh=%s n=%d" % (oid, hit is not None, jzh, len(specs)), flush=True)
    json.dump(hits, open(out_path, "w"), ensure_ascii=False, indent=2)
    print("VERIFY_DONE hits=%d -> %s" % (len(hits), out_path))
    return hits


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("ids_file")
    ap.add_argument("--out", default="/tmp/mtop_verify.json")
    a = ap.parse_args()
    ids = [l.strip() for l in open(a.ids_file, encoding="utf-8") if l.strip()]
    verify_ids(ids, a.out)
