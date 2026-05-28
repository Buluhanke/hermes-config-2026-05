# 1688 CDP 自动化参考代码（2026-05-28验证通过）

## 目标
用用户Chrome调试端口（9222）操作1688，继承用户登录态，避免验证码拦截。

## 前置条件
Chrome必须带`--remote-allow-origins=*`启动，否则WebSocket handshake 403。

**启动命令**：
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug \
  --remote-allow-origins=*
```

## 完整代码模板

```python
import urllib.request, json, time, websocket

# 1. 获取 CDP endpoints
req = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
targets = json.loads(req.read())

# 2. 找 browser target（发 Target.createTarget 用）
browser_target = next((t for t in targets if t.get('type') == 'browser'), targets[0])
browser_ws_url = browser_target.get('webSocketDebuggerUrl')

# 3. 连接 browser endpoint，创建1688新tab
ws_browser = websocket.create_connection(browser_ws_url, timeout=10, suppress_origin=True)

def cdp_send(ws, msg_id, method, params=None):
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    resp = json.loads(ws.recv())
    return resp

# 创建新tab
result = cdp_send(ws_browser, 1, "Target.createTarget", {"url": "https://www.1688.com/"})
new_target_id = result.get('result', {}).get('targetId', '')
print(f"新tab ID: {new_target_id}")
ws_browser.close()

time.sleep(3)  # 等待tab初始化

# 4. 获取新tab的websocket URL
req2 = urllib.request.urlopen("http://localhost:9222/json", timeout=5)
targets2 = json.loads(req2.read())
tab_ws_url = None
for t in targets2:
    if t.get('id') == new_target_id or '1688' in t.get('url', ''):
        tab_ws_url = t.get('webSocketDebuggerUrl')
        break

# 5. 连接tab，操作页面
ws_tab = websocket.create_connection(tab_ws_url, timeout=10, suppress_origin=True)
msg_id = [1]

def tab_send(method, params=None):
    ws_tab.send(json.dumps({"id": msg_id[0], "method": method, "params": params or {}}))
    resp = json.loads(ws_tab.recv())
    msg_id[0] += 1
    return resp

# 导航到搜索页
tab_send("Page.navigate", {
    "url": "https://s.1688.com/youzhan/search/searchDeal4Cloud.htm?keywords=纸箱"
})
time.sleep(5)

# 6. 提取数据（Runtime.evaluate）
result = tab_send("Runtime.evaluate", {
    "expression": "document.title",
    "returnByValue": True
})
print("标题:", result.get('result', {}).get('result', {}).get('value', ''))

# 提取offerId列表
offer_result = tab_send("Runtime.evaluate", {
    "expression": """(() => {
        const offerIds = [];
        document.querySelectorAll('*').forEach(el => {
            const text = el.textContent || '';
            const m = text.match(/"offerId":(\\d+)/);
            if (m) offerIds.push(m[1]);
        });
        return [...new Set(offerIds)].slice(0, 20);
    })()""",
    "returnByValue": True
})
offer_ids = offer_result.get('result', {}).get('result', {}).get('value', [])
print(f"找到 {len(offer_ids)} 个商品")

# 7. 点进详情页
if offer_ids:
    tab_send("Page.navigate", {
        "url": f"https://detail.1688.com/offer/{offer_ids[0]}.html"
    })
    time.sleep(4)
    
    # 拿价格
    price_result = tab_send("Runtime.evaluate", {
        "expression": """(() => {
            const prices = [];
            document.querySelectorAll('.item-price-stock').forEach(el => prices.push(el.innerText.trim()));
            const body = document.body.innerText;
            const moq = body.match(/起订[^\\n]{0,50}/);
            return { prices, moq: moq ? moq[0] : null };
        })()""",
        "returnByValue": True
    })
    print("价格:", price_result)

ws_tab.close()
print("done")
```

## 坑点记录

### 坑1：WebSocket 403 Forbidden
Chrome未加`--remote-allow-origins=*`，WebSocket handshake被拒绝。
- 报错：`WebSocketBadStatusException: Handshake status 403 Forbidden`
- 解：重启Chrome加`--remote-allow-origins=*`

### 坑2：用错了endpoint
`Target.createTarget`要发到**browser endpoint**，不是tab endpoint。
- 错：连接tab的websocket发`Target.createTarget`
- 对：连接browser的websocket发`Target.createTarget`

### 坑3：浏览器返回502但进程存在
`curl http://localhost:9222/json`返回502但Chrome进程PID存在。
- 原因：Chrome实例冲突，调试服务未正常启动
- 解：kill所有Chrome进程，重新用独立`--user-data-dir`启动

### 坑4：新Chrome遭遇验证码
全新Chrome第一次访问1688会触发验证码（无登录态）。
- 解：用户手动登录一次1688，之后的CDP操作会继承cookie

### 坑5：Playwright connect_over_cdp超时
`pw.chromium.connect_over_cdp("http://localhost:9222")`超时。
- 原因：Playwright的CDP实现与Chrome WebSocket版本不兼容
- 解：用`websocket`库直接连接，手动发CDP命令

## 依赖
```bash
pip install websocket-client
# Playwright已在venv: ~/.hermes/hermes-agent/.venv/bin/python3
```

## 相关文件
- `scripts/humanize_1688.py` — 1688真人化注入脚本
- `scripts/humanize_inject.py` — 通用注入脚本
