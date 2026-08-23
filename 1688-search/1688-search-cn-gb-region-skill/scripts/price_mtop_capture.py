#!/usr/bin/env python3
# price_mtop_capture.py - 环节⑦升级：Playwright 接管真实登录 Chrome (CDP 9333)，
# 从详情页内联 HTML 抠 skuMapOriginal (1688 PC 端 SSR 直出，含全 SKU 价格+库存)。
# 比 price_clean3.js 的 DOM 点击稳：不依赖渲染、不踩 size-bar、拿全 SKU 价格表。
# 实测 2026-08-21：skuMapOriginal 在页面内联 JSON 里，非 MTOP 包。
#
# 用法：python3 price_mtop_capture.py <offer_id> [target_spec]
#   target_spec 例 "8*8*9" -> 只回显匹配该尺寸组合的行；不传则回显全部 SKU。
# 前置：真实登录 Chrome 以 --remote-debugging-port=9333 启动 (~/.chrome_1688_scraper，已登录1688)

import sys, json, re
from playwright.sync_api import sync_playwright

OFFER = sys.argv[1] if len(sys.argv) > 1 else None
if len(sys.argv) > 2:
    TARGET = sys.argv[2].replace('*', 'x').replace('×', 'x').lower()
else:
    TARGET = None

if not OFFER:
    print(json.dumps({"error": "usage: price_mtop_capture.py <offer_id> [target_spec]"}))
    sys.exit(1)

CDP = "http://127.0.0.1:9333"
URL = "https://detail.1688.com/offer/" + OFFER + ".html"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP)
    context = browser.contexts[0]
    page = context.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000)
    html = page.content()
    browser.close()

m = re.search(r'skuMapOriginal"\s*:\s*(\[.*?\}\s*\])', html, re.DOTALL)
if not m:
    print(json.dumps({"offerId": OFFER, "error": "skuMapOriginal not found (maybe not logged in / page blocked)"}, ensure_ascii=False))
    sys.exit(0)

arr_text = m.group(1).replace('\\"', '"').replace('\\\\', '\\')
try:
    skus = json.loads(arr_text)
except Exception:
    skus = []
    for x in re.findall(r'\{[^{}]*"specId"[^{}]*\}', arr_text):
        try:
            skus.append(json.loads(x))
        except Exception:
            pass

rows = []
for s in skus:
    spec = s.get("specAttrs") or s.get("spec") or ""
    price = s.get("discountPrice") or s.get("price")
    stock = s.get("canBookCount") or s.get("stock")
    rows.append({"spec": spec, "price": price, "stock": stock})

total = len(skus)
if TARGET:
    # TARGET 形如 8x8x9 -> 拆成 [8,8,9]，spec 形如 "8x8（长宽）;9cm（高）" -> 抽 [8,8,9]
    tgt_nums = re.findall(r'\d+(?:\.\d+)?', TARGET)
    def spec_nums(sp):
        return re.findall(r'\d+(?:\.\d+)?', sp)
    rows = [r for r in rows if spec_nums(r["spec"])[:len(tgt_nums)] == tgt_nums]

out = {
    "offerId": OFFER,
    "target": TARGET,
    "totalSku": total,
    "matched": len(rows),
    "skus": rows[:60],
}
print(json.dumps(out, ensure_ascii=False))
