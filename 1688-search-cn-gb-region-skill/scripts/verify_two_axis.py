#!/usr/bin/env python3
"""verify_two_axis.py -- 复核 1688 商品详情页是否含目标尺寸（双轴 SKU 写法优先）。

针对纸箱/纸盒类商品最常见的两种尺寸编码：
  1) 双轴写法（DOMINANT）：规格以两个独立 SKU 轴组合，如 "8x8（长宽）;9cm（高）"
     —— 1688 大量现货小白盒/瓦楞盒店都用这种 "长宽基型 + 高变体" 拆法。
  2) 连写写法：字面 "8x8x9cm" / "8*8*9cm" / "80*80*90mm"（mm 折算成 cm）。

提取方式（比 .module-od-sku-selection DOM 文本更稳）：直接抓页面内联 JSON
`skuMapOriginal` 的 `specAttrs` 字段，这是结构化的完整在售 SKU，不会被虚拟滚动截断。

所在地：从详情页 body.innerText 宽扫省份名，按 PROV 过滤（默认江浙沪）。

依赖：同目录 cdp_client.py（raw CDP 驱动真实登录 Chrome :9222）。
用法：
  DIM=8*8*9  PROV=江浙沪  python3 scripts/verify_two_axis.py --ids-file /tmp/ids.txt --out /tmp/hits.json
  DIM=16*16*16 PROV=江浙沪 python3 scripts/verify_two_axis.py 1234567890 9876543210
PROV 取值：江浙沪 / 江苏 / 浙江 / 上海（逗号分隔多个）
"""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cdp_client import _new_client
from two_axis_core import verify_one, parse_dim, prov_re_for

DIM = os.environ.get("DIM", "8*8*9")
PROV = os.environ.get("PROV", "江浙沪")
TL, TW, TH = parse_dim(DIM)
PROV_RE = prov_re_for(PROV)

def verify(cdp, oid):
    return verify_one(cdp, oid, TL, TW, TH, PROV_RE)

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", default=[])
    ap.add_argument("--ids-file", default=None)
    ap.add_argument("--out", default="/tmp/1688_hits.json")
    args = ap.parse_args()
    ids = list(args.ids)
    if args.ids_file:
        ids = [l.strip() for l in open(args.ids_file, encoding="utf-8") if l.strip()]
    cdp = _new_client(); cdp.enable()
    hits = []
    for i, oid in enumerate(ids):
        print("[%d/%d] %s" % (i + 1, len(ids), oid), flush=True)
        try:
            r = verify(cdp, oid)
        except Exception as e:
            print("  ERR %s" % e, flush=True)
            r = {"id": oid, "err": str(e)}
        if r.get("hit") and r.get("jzh"):
            hits.append(r)
            print("  *** HIT 江浙沪+%sx%sx%s: %s | %s | price=%s stock=%s | %s" % (
                TL, TW, TH, r["spec"], r["prov"], r["price"], r["stock"], r["url"]), flush=True)
        else:
            print("  -- jzh=%s hit=%s prov=%r specs=%s" % (
                r.get("jzh"), r.get("hit"), r.get("prov"), r.get("n_specs")), flush=True)
        time.sleep(4)
    json.dump(hits, open(args.out, "w"), ensure_ascii=False, indent=2)
    print("DONE hits=%d -> %s" % (len(hits), args.out))

if __name__ == "__main__":
    main()
