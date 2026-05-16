# CDP 浏览器远程调试配置

## Hermes 独立 Chrome 实例

Hermes 通过 launchd 维护独立的持久化 Chrome 实例，调试端口 **9333**。

**关键区别**：
- Hermes Chrome：`ws://localhost:9333`（持久化登录态）
- 用户默认 Chrome：`ws://localhost:9222`

## 获取 Tab ID

```python
import subprocess, json, websocket

# 方法1：chrome-debugging-chrome MCP 工具
# mcp_chrome_get_windows_and_tabs（但 MCP server 可能离线）

# 方法2：直接用 CDP WebSocket 列举
import urllib.request
debugging = json.loads(urllib.request.urlopen("http://localhost:9333/json").read())
for tab in debugging:
    print(tab["id"], tab["title"], tab["url"])
```

## 连接 Tab 并执行 CDP 命令

```python
def cdp_evaluate(tab_url, script):
    ws_url = tab_url.replace("http://", "ws://").replace("https://", "wss://") + "/devtools/page/"
    ws = websocket.create_connection(ws_url, timeout=5)
    cdp_send(ws, "Runtime.evaluate", {"expression": script})
    ws.close()
```

## 已知坑

- `Runtime.evaluate` 在某些 React SPA（qwen.ai/chat）返回空 DOM，元素为 0 — 可能是 shadow DOM 隔离或 iframe，需要 `Document.getFlattenedDocuments` 或注入 content script
- MCP chrome 工具（`mcp_chrome_*`）依赖 MCP server 连接，MCP server 离线时所有工具报错 "Failed to connect to MCP server"，必须走 CDP WebSocket 绕过