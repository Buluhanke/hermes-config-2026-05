# CDP WebSocket直连绕过MCP Bridge（2026-05-16实测）
**问题**：MCP bridge（mcp-chrome-stdio）动不动断联，但Chrome本身运行正常。

**关键认知转变**：MCP bridge是Hermes和Chrome之间的协议层，但Chrome的CDP WebSocket端点（`ws://localhost:9333/devtools/page/xxx`）是独立开放的——bridge死了≠Chrome不可控。

## 最小可用模板

```python
import websocket, json, time, base64, urllib.request

TAB_ID = "TAB_ID_HERE"
WS_URL = f"ws://127.0.0.1:9333/devtools/page/{TAB_ID}"

def send(ws, method, params=None):
    ws.send(json.dumps({"id": 1, "method": method, "params": params or {}}))

def recv(ws, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        msg = json.loads(ws.recv())
        if "method" not in msg:
            return msg

ws = websocket.create_connection(WS_URL, timeout=15)

# 截图
send(ws, "Page.captureScreenshot", {"format": "png", "quality": 50})
resp = recv(ws, 10)
img_data = base64.b64decode(resp["result"]["data"])

# 导航
send(ws, "Page.navigate", {"url": "https://chat.deepseek.com"})
resp = recv(ws, 15)

# 执行JS
send(ws, "Runtime.evaluate", {"expression": "document.title", "returnByValue": True})
resp = recv(ws, 5)

# 点击
send(ws, "Input.dispatchMouseEvent", {"type": "mousePressed", "x": 1090, "y": 336, "button": "left", "clickCount": 1})
send(ws, "Input.dispatchMouseEvent", {"type": "mouseReleased", "x": 1090, "y": 336, "button": "left", "clickCount": 1})

# 键盘输入
send(ws, "Input.insertText", {"text": "你好"})
send(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Enter", "code": "Enter"})
send(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter"})

ws.close()
```

## 枚举所有tabs（HTTP端点，不依赖bridge）

```python
import urllib.request, json

tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9333/json").read())
for t in tabs:
    print(t.get("url", ""), t.get("id", ""))
```

## 创建新标签页

```python
import urllib.request, json

# PUT方法，不是POST
resp = json.loads(urllib.request.urlopen(
    urllib.request.Request("http://127.0.0.1:9333/json/new",
                          data=b'{"url":"about:blank"}',
                          method="PUT",
                          headers={"Content-Type": "application/json"})
).read())
# resp = {"id": "TAB_ID", "webSocketDebuggerUrl": "ws://...", "url": "about:blank"}
new_tab_id = resp["id"]
new_ws_url = resp["webSocketDebuggerUrl"]
```

## 已知限制

1. **React组件的click事件**：CDP `Input.dispatchMouseEvent` 点击React按钮时，React Fiber的内部状态可能不同步导致点击无效（如DeepSeek专家模式按钮）。`Runtime.evaluate` 的 JS `click()` 也无效。需要尝试：
   - 找父级可点击容器
   - 找 `__reactProps$xxx` 手动触发 onClick
   - 用 `element.click()` + `dispatchEvent(MouseEvent)`

2. **mask key要求**：WebSocket masking key 必须是4字节，用 `os.urandom(4)` 生成

3. **`webSocketDebuggerUrl`字段名**：不是 `webSocketURL`，是 `webSocketDebuggerUrl`

## 依赖

```bash
pip3 install websocket-client
```

## 什么时候用这个 vs MCP bridge

| 场景 | 方案 |
|------|------|
| MCP bridge正常 | 用 `mcp_chrome_*` 工具 |
| MCP bridge断联 | 用这个模板直连CDP |
| 枚举tabs/获取URL | HTTP端点，永远可用 |
| 需要完整CDP能力 | WebSocket直连 |
