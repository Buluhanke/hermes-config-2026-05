#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对已知 ID 池逐条开详情页，抠目标尺寸的精确 SKU 价/库存。
连 9333 常驻已登录实例：零新建、零注入、零抢焦点。条目携带的店铺/所在地/链接直接透传。
用法: python3 verify_dim_pool.py --dim "16*16*16" --pool pool.json --out result.json
"""
import sys, os, json, time, re, argparse, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp1688 as C

# 新版 ant-design 页 skuMapOriginal 的正则兜底（specAttrs 在 price 前后两种顺序）
REGEX_ROWS = [
    re.compile(r'"specAttrs"\s*:\s*"([^"]*)"[^}]{0,500}?"(?:discountPrice|price)"\s*:\s*"([0-9.]+)"'),
    re.compile(r'"(?:discountPrice|price)"\s*:\s*"([0-9.]+)"[^}]{0,500}?"specAttrs"\s*:\s*"([^"]*)"'),
]


def sku_rows(body):
    rows = C.parse_sku_json(body)
    if rows:
        return rows
    out = []
    for rgx in REGEX_ROWS:
        for m in rgx.finditer(body):
            a, b = m.group(1), m.group(2)
            if a.replace('.', '', 1).isdigit():
                price, spec = a, b
            else:
                spec, price = a, b
            out.append((spec, price, None))
        if out:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dim', required=True, help='目标尺寸，如 16*16*16')
    ap.add_argument('--pool', required=True, help='候选 JSON 列表（cli search 的 offers）')
    ap.add_argument('--out', required=True)
    ap.add_argument('--gap', type=float, default=2.2)
    ap.add_argument('--maxverify', type=int, default=80)
    args = ap.parse_args()

    offers = json.load(open(args.pool, encoding='utf-8'))
    perms = C.target_perms(args.dim)
    c = C.CDP('http://127.0.0.1:9333')
    # 主页维持会话；详情页复用单后台 tab，结束即关
    _wt, _ws = c.new_page('https://www.1688.com/')
    time.sleep(1.5)
    vt, vs = c.new_page('about:blank')

    hits, checked, login_streak = [], 0, 0
    try:
        for i, o in enumerate(offers[:args.maxverify], 1):
            oid = str(o.get('offerId') or o.get('id'))
            try:
                c.navigate(vs, f'https://detail.1688.com/offer/{oid}.html')
                time.sleep(args.gap)
                href = str(c.evaluate(vs, 'location.href', await_promise=False) or '')
                if 'taobao.com' in href or 'login.' in href:
                    login_streak += 1
                    print(f'[{i}/{len(offers)}] LOGIN {oid}', flush=True)
                    if login_streak >= 5:
                        print('连续5个登录墙，早停', flush=True); break
                    continue
                h = c.evaluate(vs, 'document.documentElement.outerHTML', await_promise=False)
                if isinstance(h, dict) or not h or '验证码' in h:
                    print(f'[{i}/{len(offers)}] BLOCK {oid}', flush=True)
                    login_streak += 1
                    if login_streak >= 5:
                        break
                    continue
                if 'skuMapOriginal' not in h:
                    time.sleep(1.5)
                    h = c.evaluate(vs, 'document.documentElement.outerHTML', await_promise=False) or ''
                login_streak = 0
                checked += 1

                best = None
                for spec, price, stock in sku_rows(h):
                    conn, _lw, _hh = C.extract_sizes_from_spec(str(spec))
                    if any(p in conn for p in perms):
                        try:
                            pv = float(price) if price is not None else None
                        except (TypeError, ValueError):
                            pv = None
                        if best is None or (pv is not None and (best[1] is None or pv < best[1])):
                            best = (str(spec)[:60], pv, stock)
                if best:
                    rec = dict(o)
                    rec.update(hit_spec=best[0], sku_price=best[1], stock=best[2],
                               detail=f'https://detail.1688.com/offer/{oid}.html')
                    hits.append(rec)
                    print(f'[{i}/{len(offers)}] HIT {oid} ¥{best[1]} 库存{best[2]} | {best[0][:45]}', flush=True)
                else:
                    print(f'[{i}/{len(offers)}] miss {oid}', flush=True)
            except Exception as e:
                print(f'[{i}/{len(offers)}] ERR {oid}: {e}', flush=True)
            if i % 3 == 0:
                json.dump(hits, open(args.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            time.sleep(max(0.8, args.gap * 0.3))
    finally:
        json.dump(hits, open(args.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        c.close_target(vt, vs)
        c.close_target(_wt, _ws)
        print(f'[DONE] checked={checked} hits={len(hits)} -> {args.out}', flush=True)


if __name__ == '__main__':
    main()
