# CDP Session Notes (2026-06-02)

## mcp-chrome-stdio Failure Pattern

**Symptom**: `ECONNREFUSED 127.0.0.1:12306` — mcp-chrome-stdio process running but not listening on port 12306.

**Root cause**: MCP chrome bridge (mcp-chrome-stdio) has a separate stdio-config.json that must match the running Chrome debug port. When it can't connect to its configured Chrome instance, it fails silently at port 12306.

**Workaround**: Bypass entirely. Chrome debug port 9333 is directly accessible via HTTP+WebSocket. No bridge needed.

## Verified Working: Python CDP with `websockets`

```python
import urllib.request, json, websocket, time

CDP = 'http://localhost:9333'

# 1. HTTP: list tabs
with urllib.request.urlopen(f'{CDP}/json') as f:
    tabs = json.load(f)

# 2. WebSocket: navigate (NO jsonrpc field!)
ws = websocket.create_connection(f"ws://{CDP}/devtools/page/{tab_id}", timeout=15)
ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": url}}))
ws.recv(); ws.close()
```

## Critical: Chrome CDP Does NOT Support JSON-RPC 2.0

❌ WRONG (causes `-32600` errors):
```python
msg = {"jsonrpc": "2.0", "id": 1, "method": "Page.bringToFront"}
```

✅ CORRECT:
```python
msg = {"id": 1, "method": "Page.bringToFront"}  # No jsonrpc field
```

## Accessibility.getFullAXTree — Verified Working

Best method for reading AI site content without OCR/screenshot. Returns 285 nodes for DeepSeek chat page.

```python
import json, asyncio, websockets

async def get_ax_tree(tab_id, depth=20):
    async with websockets.connect(f"ws://localhost:9333/devtools/page/{tab_id}", max_size=20*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Page.bringToFront"}))
        await ws.recv()
        await asyncio.sleep(0.5)
        await ws.send(json.dumps({"id": 2, "method": "Accessibility.getFullAXTree", "params": {"depth": depth}}))
        resp = json.loads(await ws.recv())
        return resp.get("result", {}).get("nodes", [])

asyncio.run(get_ax_tree("9F5ACAD89DE94001ECF1E57DEE0E3C19"))
```

Output per node:
- `role.value`: element type (RootWebArea, link, button, textbox, radio, StaticText, etc.)
- `name.value`: accessible name / text content
- `backendDOMNodeId`: for click targeting

## Input + Submit Pattern (Verified)

DeepSeek input box: `backendDOMNodeId = 4`

```python
# Fill input via JS
js_expr = """(function() {
    const t = document.querySelector('textarea') || document.querySelector('[contenteditable]');
    if (!t) return 'NO INPUT';
    t.focus();
    t.value = 'text here';
    t.dispatchEvent(new Event('input', {bubbles: true}));
    return 'OK: ' + t.value;
})()"""

# Submit via KeyboardEvent
ws.send(json.dumps({"id": N, "method": "Input.dispatchKeyEvent", "params": {
    "type": "keyDown", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13
}}))
```

## Key Tab IDs (2026-06-02 session)

| Site | Tab ID | Notes |
|------|--------|-------|
| DeepSeek chat | 9F5ACAD89DE94001ECF1E57DEE0E3C19 | ✅ AX tree works |
| Grok | 5E2311C0CA3F45EAEB6EEB3699AA608A | ✅ AX tree works |
| ChatGPT | 5A2213186C845F0F292E171EFD802B97 | ✅ AX tree works |
| 豆包 | D926D91C4D3022D003F1698B0FD2783C | ✅ AX tree works |
| ChatGLM | C12511A3F357953BA732CC110CA9CD6F | ✅ AX tree works |

## Chrome Debug Port Status

- **Port 9333**: Active and working (user's Chrome with debug flag)
- **Chrome PID**: 68636
- **mcp-chrome-stdio PID**: 93563 (faulty, not listening)
- **websockets installed**: `~/.hermes/hermes-agent/venv/bin/pip install websockets -q`