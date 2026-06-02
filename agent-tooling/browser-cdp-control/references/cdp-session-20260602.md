# CDP Session Notes (2026-06-02)

## mcp-chrome-stdio Failure Pattern

**Symptom**: `ECONNREFUSED 127.0.0.1:12306` — mcp-chrome-stdio process running but not listening on port 12306.

**Root cause**: MCP chrome bridge (mcp-chrome-stdio) has a separate stdio-config.json that must match the running Chrome debug port. When it can't connect to its configured Chrome instance, it fails silently at port 12306.

**Workaround**: Bypass entirely. Chrome debug port 9333 is directly accessible via HTTP+WebSocket. No bridge needed.

## Verified Working: Python CDP with `websockets`

```python
import urllib.request, json, websocket, time

CDP = 'http://localhost:9333'

# 1. HTTP: create new tab
req = urllib.request.Request(f'{CDP}/json/new', method='POST')
with urllib.request.urlopen(req, timeout=10) as f:
    tab = json.loads(f.read())

# 2. WebSocket: navigate
ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=15)
ws.send(json.dumps({"id":1,"method":"Page.navigate","params":{"url":url}}))
ws.recv(); ws.close()
```

## Active Chrome Tabs (2026-06-02 session)

| Site      | Tab ID           | Type  |
|-----------|-----------------|-------|
| Grok      | 5E2311C0CA3F    | page  |
| ChatGPT   | 5A2213186C84    | page  |
| ChatGLM   | C12511A3F357    | page  |
| Doubao    | D926D91C4D30    | page  |
| DeepSeek  | C419026B476B    | page  |
| DeepSeek  | 9F5ACAD89DE9    | page  |
| Gemini    | (A9F032A3FF2B)  | webview |

Gemini tab is `webview` type — some CDP operations restricted.

## Chrome Debug Port Status

- **Port 9333**: Active and working (user's Chrome with debug flag)
- **Chrome PID**: 68636
- **mcp-chrome-stdio PID**: 93563 (faulty, not listening)
- **websockets installed**: `~/.hermes/hermes-agent/venv/bin/pip install websockets -q`