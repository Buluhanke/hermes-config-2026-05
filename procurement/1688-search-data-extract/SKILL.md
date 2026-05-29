---
name: 1688-search-data-extract
description: 从1688搜索结果页通过CDP拦截postMessage提取商品数据，绕过反爬限制。
triggers:
  - 1688搜索结果无法提取数据
  - 1688页面内容为空但有数据
  - 从1688提取供应商列表
---

# 1688 搜索数据提取 — CDP postMessage 拦截法

## 核心发现

1688 s.1688.com 的搜索结果数据通过 `window.postMessage` 从 opener 传递给页面，数据存储在：
```
window.data.offerV2.response.data.OFFER.items
```

每次搜索触发 Page.navigate 后，数据会通过 postMessage 刷新。需要重新连接 CDP WebSocket 才能读取新数据。

## 数据结构

每个 item 的 `data` 字段（含完整信息）：
- `offerId`: 商品ID
- `title`: 标题（带HTML标签，需 strip）
- `priceInfo.price` / `priceInfo.unit`: 价格和单位
- `bookedCount`: 已售数量
- `province` / `city`: 省 市
- `companyName`: 公司名
- `linkUrl`: m.1688.com 移动端链接

## 完整提取流程

1. 连接CDP → 获取最新标签 → WebSocket连接
2. Page.navigate 到搜索页 URL（含 keywords 参数）
3. **等待8秒** → 关闭原WS → 重新连接（新WS）
4. 轮询 `window.data.offerV2.response.data.OFFER.items.length` 直到 > 0
5. 提取所有 items 的 data 字段

## 常见问题

### BrokenPipe / WS断开
- navigate后必须重新连接WS

### items为0但关键词有数据
- postMessage异步，等8秒不够就多等几轮

### 提取到空字符串
- `returnByValue: True` 必须加

### 页面innerText为空，找不到元素
- 1688动态渲染，DOM里没有商品数据
- 直接从`window.data`读取，不要从DOM提取

## 1688开放平台API申请结论（2026-05-29验证）

**申请条件：**
- 企业支付宝账号（必须）
- 营业执照认证
- 需审核，审核时间1-3天

**适合场景：** 有自己1688店铺的卖家（需要管理店铺商品、订单、物流）

**迅龙贸易的情况：** 是买家身份（找供应商、采购），不是卖家，不需要店铺管理。申请1688开放平台API对采购场景没有直接帮助，且企业认证门槛暂时过不了。

**结论：** 不用申请1688 API Key。CDP方案（`1688-sourcing` skill）已经够用，数据质量和API接近，不需要花时间申请。

---

## 当前已安装的1688技能状态（2026-05-29）

⚠️ **需API Key（需企业认证，暂时跳过）：**
- `1688-source-suppliers` — 找供应商，需AK
- `1688-shopkeeper` — 店铺管理，需AK
- `1688-item-select` — 重点品圈选，需AK
- `1688-product-analysis` — 商品分析，需AK
- `1688-shop-health-check` — 店铺健康检查，需AK
- `1688-item-one-click` — 一键修改，需AK

✅ **直接可用（无需Key）：**
- `1688-sourcing` (`procurement/1688-sourcing/`) — CDP拦截法找品，5家比价，标准化流程
- `1688-search-data-extract` — 底层CDP数据提取，1688-sourcing依赖此技能

❌ **需换方案：**
- `1688-price-monitor` — 官方API方案，需AK；已用CDP方案替代

---

## 已知限制
- 长关键词被截断（如"50*25cm气泡袋"变成乱码）
- 标题含HTML标签，需手动strip
- linkUrl是移动端链接