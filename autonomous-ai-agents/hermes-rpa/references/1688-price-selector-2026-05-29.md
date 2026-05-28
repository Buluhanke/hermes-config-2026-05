# 1688 详情页数据抓取 — 2026-05-29 实测

## 价格选择器 `.item-price-stock`

1688 详情页价格字段选择器：**`.item-price-stock`**

这是阶梯价，每个元素对应一个数量区间的单价：

```html
<span class="item-price-stock">¥3.6</span>  <!-- 库存869463个 -->
<span class="item-price-stock">¥3.4</span>  <!-- 库存873709个 -->
<span class="item-price-stock">¥2.9</span>  <!-- ... -->
<span class="item-price-stock">¥2.1</span>
<span class="item-price-stock">¥1.9</span>
<span class="item-price-stock">¥1.6</span>
```

价格是动态渲染的，静态HTML里没有，JS渲染后才出现。

## 抓取代码（execute_code 直接运行）

```python
from playwright.sync_api import sync_playwright
import time

pw = sync_playwright().start()
browser = pw.chromium.connect_over_cdp("http://localhost:9333")
# ⚠️ 注意：9333端口的Chrome没有用户1688登录态
# 需要用户Chrome开启调试端口9222并连接
ctx = browser.contexts[0]

page = ctx.new_page()
page.goto("https://detail.1688.com/offer/{offer_id}.html", timeout=20000)
page.wait_for_load_state("domcontentloaded", timeout=15000)
time.sleep(6)  # 等JS渲染

result = page.evaluate(r"""() => {
    const prices = [];
    document.querySelectorAll('.item-price-stock').forEach(el => {
        prices.push(el.innerText.trim());
    });
    // 找起订量（正则匹配）
    const body = document.body.innerText;
    const moqM = body.match(/起订[^\n]{0,50}/) || 
                 body.match(/(\d+\.?\d*)\s*件/);
    const soldM = body.match(/已售[^\n]{0,40}/);
    const titleEl = document.querySelector('h1') || 
                    document.querySelector('[class*="title"]');
    return {
        prices: prices,
        moq: moqM ? moqM[0] : null,
        sold: soldM ? soldM[0] : null,
        title: titleEl ? titleEl.innerText.slice(0, 100) : null
    };
}""")

print(f"价格: {result['prices']}")      # ['¥3.6', '¥3.4', '¥2.9', ...]
print(f"起订: {result['moq']}")         # None（动态加载，可能拿不到）
print(f"已售: {result['sold']}")        # '已售2.0万+个'
print(f"标题: {result['title']}")

pw.stop()
```

## 搜索页商品列表抓取

搜索页用 `offerId` 字段：

```python
import re
html = page.content()
offer_ids = re.findall(r'"offerId":(\d+)', html)
titles = re.findall(r'"title":"([^"]{5,60})"', html)
print(f"商品数: {len(offer_ids)}")  # 搜索页60个offerId
```

注意：搜索结果页的 offerId 在 JSON 里，详情页 URL 用 `https://detail.1688.com/offer/{offerId}.html`

## 已知问题

1. **9333 Chrome无用户登录态** — 搜索/详情页会被重定向到淘宝登录页
2. **价格字段渲染时机** — 需要 `time.sleep(5~6)` 等JS渲染
3. **起订量匹配** — `起订` 关键字匹配不一定准，1688详情页结构经常变
4. **cloakbrowser.launch() vs CDP连接** — 前者开新浏览器无登录态，后者连已有浏览器可继承cookies
