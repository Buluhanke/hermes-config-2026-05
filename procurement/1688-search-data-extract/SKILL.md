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

## 1688开放平台API密钥配置（2026-05-29新增）

危险级别（--force也无法绕过）：`clawhub/1688-product-search`、`clawhub/1688-product-find`、`clawhub/1688-sourcing-inquiry` — 需 ALI1688_APP_KEY/SECRET/ACCESS_TOKEN/REFRESH_TOKEN

谨慎级别（--force可安装，运行需Key）：`clawhub/1688-shopkeeper`、`clawhub/1688-source-suppliers` 等

在 `~/.hermes/.env` 中添加：
```
ALI1688_APP_KEY=your_key
ALI1688_APP_SECRET=your_secret
ALI1688_ACCESS_TOKEN=your_token
ALI1688_REFRESH_TOKEN=your_refresh_token
```

## 当前已安装的1688技能（2026-05-29）

✅ 直接可用：`1688-sourcing-agent`、`1688-procurement-agent`、`1688-price-monitor`

✅ force安装可用：`1688-source-suppliers`、`1688-shopkeeper`、`1688-shop-health-check`、`1688-item-select`、`1688-product-analysis`、`1688-finance-tax`、`1688-item-title-optimizer`、`1688-item-one-click`

⚠️ 需配置API Key后才能运行：`1688-product-search`、`1688-product-find`、`1688-sourcing-inquiry`

## 已知限制
- 长关键词被截断（如"50*25cm气泡袋"变成乱码）
- 标题含HTML标签，需手动strip
- linkUrl是移动端链接