# 1688 搜索数据提取 — postMessage 拦截法

## 核心发现（2026-05-28）

1688 搜索结果页（s.1688.com）的数据**不走XHR/fetch，直接通过 `window.postMessage` 从父窗口注入**。

- DOM中只渲染搜索框和空壳，结果数据在内存里的 JS 全局变量中
- `innerText` 提取不到价格/公司名/offerID
- `document.querySelectorAll` 找不到商品元素

**正确路径**：`window.data.offerV2.response.data.OFFER.items`

## 数据结构

```js
window.data.offerV2.response.data.OFFER.items[i].data = {
  offerId: String,          // 数字ID，用于拼接详情页URL
  title: String,           // 含<font color=red>标签，需 replace(/<[^>]+>/g,'')
  priceInfo: {
    price: String,         // 起批价
    showPrice: String,
    unit: String           // 单位
  },
  bookedCount: String,    // 已售数量
  companyName: String,    // 公司名
  loginId: String,        // 登录ID（公司名为空时用这个）
  province: String,        // 省份
  city: String,
  linkUrl: String,        // 移动端详情页，http://开头
  // ... 其他字段
}
```

## reqParams 结构（用于确认搜索关键词）

```js
window.data.offerV2.reqParams = {
  beginPage: 1,
  pageSize: 60,
  method: 'getOfferList',
  keywords: '%E6%B0%94%E8%A2%8B+50*25cm',  // GBK编码
  ...
}
```

## 验证方法

在 CDP console 中执行：
```js
window.data?.offerV2?.response?.data?.OFFER?.items?.length
// 返回 60 = 数据已到达
// 返回 undefined = 还在等待
```

## 关键陷阱

1. **导航后WebSocket断开**：每次 Page.navigate 后需重新连接CDP
2. **数据到达有延迟**：需等待8秒，多次轮询 `items?.length`
3. **价格单位**：priceInfo.unit 可能为空（按件卖），price 字段就是单价
4. **title含HTML标签**：用 `.replace(/<[^>]+>/g,'')` 清除

## 50*25cm气泡袋搜索结果（2026-05-28）

共2000条结果，60条在第一页。江浙沪气泡袋34家。

接近50*25cm规格的：
- 金华翼美包装（ID:903586941684）：20×25cm ¥5/件，已售43
- 艺诺包装源头厂家（ID:808613438216）：10~30cm多规格，¥0.11/件起，已售329 — **可询问是否有50*25**
- wutao19860806（ID:623635256786）：25*30cm ¥0.12/件，已售149