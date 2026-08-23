---
name: 1688-cdp-product-fetch
description: CDP直连用户Chrome逐个打开1688商品详情页抓规格/价格/供应商。
triggers:
  - "1688商品详情"
  - "打开1688商品页"
  - "1688规格表"
  - "1688阶梯价"
  - "1688供应商信息"
l1: 1688
l2: cdp-fetch
l3: product
---

# 1688 CDP 商品详情页抓取

## 核心 SOP

**Step 1: 搜索商品**（已有登录态）
```
browser_navigate → https://s.1688.com/selloffer/offer_search.html?keywords=<搜索词>
```
或从首页搜索框输入关键词。

**Step 2: 拿 offer ID**
1688 搜索结果页商品在深层 iframe，CDP Runtime.evaluate 查主 DOM 返回空。
- **推荐**：`findchain.py` 跑搜索列表，拿到 offer ID 列表
- **备选**：`Target.getTargets` frame_tree 里找商品 tab ID

**Step 3: CDP 打开详情页 + 抓数据**
```
browser_navigate → https://detail.1688.com/offer/<offer_id>.html
browser_cdp Runtime.evaluate → 下方JS脚本
```

抓数据 JS：
```javascript
(function() {
    var text = document.body.innerText || '';
    var price = text.match(/¥[\s\d.]+/g);
    var specs = [];
    document.querySelectorAll('tr').forEach(function(el) {
        var t = el.innerText || '';
        if (t.match(/\d/) && (t.includes('cm') || t.includes('mm') || t.includes('*') || t.includes('×')))
            specs.push(t.replace(/\s+/g, ' ').trim().slice(0, 120));
    });
    return JSON.stringify({
        price: price ? [...new Set(price)].slice(0, 8) : [],
        specs: specs.slice(0, 15),
        title: document.title.slice(0, 80)
    });
})()
```

## 搜索列表 vs 详情页

| 场景 | 方法 |
|------|------|
| 搜索列表（拿商品链接和标题） | `findchain.py`（1688-cli） |
| 商品详情页（拿规格表/价格/供应商） | CDP `Runtime.evaluate` + 上面 JS |

## 已知限制
- Google/百度搜索会被 CDP Chrome 检测触发 CAPTCHA，1688 搜索本身不会
- 1688 详情页可以直接打开，登录态完全保留
- 1688 搜索列表页直接 DOM query 拿不到商品数据（iframe 隔离）
