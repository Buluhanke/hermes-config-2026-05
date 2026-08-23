#!/usr/bin/env python3
# drission_search_251332.py — 用 DrissionPage 直接操作 drission_user_data(已复制登录态)，
# 搜 25*13*32cm 牛皮纸袋(江浙沪) + 牛皮纸袋，提取 offerId。绕过 MCP server 缓存的旧 browser 引用。
import urllib.parse, time, re, json
from DrissionPage import ChromiumPage, ChromiumOptions

co = ChromiumOptions()
co.set_user_data_path("/Users/aimac/.hermes/1688-mcp/repo/drission_user_data")
co.headless(False)
co.set_argument('--disable-blink-features=AutomationControlled')
co.set_argument('--disable-infobars')
page = ChromiumPage(co)

PROV = urllib.parse.quote("江苏,浙江,上海")
KW1 = urllib.parse.quote("25*13*32cm牛皮纸袋".encode('gbk'))
KW2 = urllib.parse.quote("牛皮纸袋".encode('gbk'))

all_ids = set()
for label, kw in [("dim", KW1), ("bag", KW2)]:
    for pg in (1, 2, 3):
        url = f"https://s.1688.com/selloffer/offer_search.htm?keywords={kw}&province={PROV}&beginPage={pg}"
        page.get(url)
        time.sleep(4)
        page.scroll.to_bottom()
        time.sleep(2)
        html = page.html
        ids = set(re.findall(r'detail\.1688\.com/offer/(\d+)', html))
        ids |= set(re.findall(r'offerId[=:](\d{9,14})', html))
        ids = {i for i in ids if 9 <= len(i) <= 14}
        all_ids |= ids
        print(f"[{label} p{pg}] +{len(ids)} ids (total {len(all_ids)})")

with open("/tmp/251332_ids.txt", "w") as f:
    f.write("\n".join(sorted(all_ids)) + "\n")
print("TOTAL", len(all_ids), "-> /tmp/251332_ids.txt")
page.quit()
