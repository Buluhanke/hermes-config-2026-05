# 1688 搜索数据提取 — postMessage 拦截法（已废弃旧方法）

## 旧方法（已废弃，2026-05-28）

~~1688首页搜索框 → 精选货源区块 → innerText提取~~
~~原因：s.1688.com 搜索URL会触发滑块验证~~
~~现状：这种方法现在也走不通了，1688首页搜索框的结果被推荐算法覆盖，无法精准搜索~~

## 正确方法（2026-05-28 实测）

**核心发现**：1688 搜索结果页（s.1688.com）的数据通过 `window.postMessage` 从父窗口注入，DOM 中不直接渲染。innerText/querySelector 都提取不到商品数据。

**数据路径**：`window.data.offerV2.response.data.OFFER.items`

**完整流程**：

```python
import urllib.request, json, websocket, time

# 1. 连接CDP
req = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
tabs = json.loads(req.read())
t = tabs[-1]  # 最新标签

# 2. 导航到搜索页
ws = websocket.create_connection(t['webSocketDebuggerUrl'], timeout=15, suppress_origin=True)
def sv(m, p=None):
    ws.send(json.dumps({"id": 1, "method": m, "params": p or {}}))
    return json.loads(ws.recv())

sv("Page.navigate", {"url": "https://s.1688.com/selloffer/offer_search.htm?keywords=气泡袋+50*25cm"})
time.sleep(8)

# 3. 导航后websocket可能断开，重新连接
ws.close()
req2 = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
tabs2 = json.loads(req2.read())
t2 = tabs2[-1]
ws2 = websocket.create_connection(t2['webSocketDebuggerUrl'], timeout=15, suppress_origin=True)

# 4. 等待数据到达（postMessage异步注入）
for _ in range(8):
    r = ws2.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {
        "expression": "window.data?.offerV2?.response?.data?.OFFER?.items?.length || 'waiting'",
        "returnByValue": True}}))
    val = json.loads(ws2.recv()).get('result',{}).get('result',{}).get('value','')
    if val and val != 'waiting' and val > 0:
        break
    time.sleep(1.5)

# 5. 提取数据
r = ws2.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {
    "expression": """
    (function(){
      var items = window.data.offerV2.response.data.OFFER.items;
      var out = [];
      for(var i=0; i<items.length; i++){
        var d = items[i].data || items[i];
        out.push({
          offerId: d.offerId,
          title: (d.title||'').replace(/<[^>]+>/g,''),
          price: (d.priceInfo||{}).price||'',
          priceUnit: (d.priceInfo||{}).unit||'',
          sold: d.bookedCount||'',
          comp: d.companyName||d.loginId||'',
          loc: d.province||'',
          city: d.city||'',
          href: (d.linkUrl||'').replace('http://','https://')
        });
      }
      return JSON.stringify(out);
    })()
    """,
    "returnByValue": True}}))
items = json.loads(json.loads(ws2.recv()).get('result',{}).get('result',{}).get('value','[]'))
```

## 关键数据结构

```js
window.data.offerV2.response.data.OFFER = {
  keywords: "姘旇 50*25cm",   // GBK编码后的搜索词
  found: "2000",            // 总结果数
  hasMore: true,            // 是否还有更多
  items: [
    {
      data: {
        offerId: "575605333710",
        title: "防震气泡袋25*35cm100个双面加厚透明...",  // 含<font>标签
        priceInfo: { price: "26.5", unit: "" },
        bookedCount: "1640",         // 已售
        companyName: "正永包装",      // 公司名
        province: "广东",            // 省份
        city: "深圳市",
        linkUrl: "http://detail.m.1688.com/page/index.html?offerId=..."
      }
    }
  ]
}
```

## 关键陷阱

1. **导航后必须重新连接WebSocket** — Page.navigate 会断开当前连接
2. **数据到达有延迟** — 需等待8秒，多次轮询 `items?.length`
3. **title含HTML标签** — 用 `.replace(/<[^>]+>/g,'')` 清除
4. **WebSocket发送后必须读取响应** — 否则msg_id不递增，后续消息混乱

## 筛选江浙沪气泡袋

```python
jiangzhe = [it for it in items if it['loc'] in ['浙江','江苏','上海','安徽'] and '气泡' in it['title']]
```

## 50*25cm气泡袋搜索结果（2026-05-28）

- 总结果：2000条，第一页60条
- 江浙沪气泡袋：34家
- **没有50*25cm标准规格**，最接近：20×25cm（金华翼美，¥5）、25×30cm（艺诺/ wutao，¥0.12起）
- 推荐艺诺包装（ID:808613438216）：多规格可选，可询问是否有50*25