# Chrome CDP Direct Control (Python WebSocket)

When `mcp-chrome-stdio` bridge is down or buggy, control local Chrome directly via Chrome DevTools Protocol (CDP) using raw Python WebSocket.

**Architecture**: Chrome listens on `--remote-debugging-port=9333`. You open a WebSocket to `ws://localhost:9333/devtools/page/<tab-id>`. CDP JSON-RPC commands go in, events/responses come out.

**Key insight**: Chrome's CDP WebSocket uses masked frames (client→server) and **unmasked** frames (server→client). The mask key must be exactly 4 bytes. Use `os.urandom(4)` for mask generation.

---

## Finding the Right Tab

```python
import urllib.request, json

# List all tabs
tabs = json.loads(urllib.request.urlopen('http://localhost:9333/json').read())

# Find tab by URL pattern
gh_tab = next((t for t in tabs if 'github.com' in t.get('url', '')), tabs[-1])
ws_url = gh_tab['webSocketDebuggerUrl']  # ws://localhost:9333/devtools/page/...
```

## WebSocket Handshake (Manual)

Chrome requires a proper 16-byte base64-encoded random key (not the usual 24-charGUID style):

```python
import base64, os

key = base64.b64encode(os.urandom(16)).decode()  # 16 bytes → 24+ char base64

request = (
    f"GET {path} HTTP/1.1\r\n"
    f"Host: localhost:9333\r\n"
    f"Upgrade: websocket\r\n"
    f"Connection: Upgrade\r\n"
    f"Sec-WebSocket-Key: {key}\r\n"
    f"Sec-WebSocket-Version: 13\r\n\r\n"
)
sock.send(request.encode())
# Read until blank line, verify b"101" in first 20 bytes
```

## Sending CDP Commands (Masked Frame)

```python
def send_frame(sock, data):
    payload = json.dumps(data).encode()
    blen = len(payload)
    if blen < 126:
        hdr = bytes([0x81, 0x80 | blen])
    elif blen < 65536:
        hdr = bytes([0x81, 0x80 | 126]) + struct.pack('>H', blen)
    else:
        hdr = bytes([0x81, 0x80 | 127]) + struct.pack('>Q', blen)
    mask = os.urandom(4)
    masked = bytearray(payload)
    for i in range(len(masked)):
        masked[i] ^= mask[i % 4]
    sock.send(hdr + mask + bytes(masked))
```

## Receiving CDP Responses (Unmasked Frame)

Chrome sends unmasked frames. Handle both masked and unmasked:

```python
def recv_frame(sock):
    hdr = b""
    while len(hdr) < 2:
        d = sock.recv(2 - len(hdr))
        if not d: return None
        hdr += d
    length = hdr[1] & 0x7F
    if length == 126:
        ext = b""
        while len(ext) < 2: ext += sock.recv(2)
        length = struct.unpack('>H', bytes(ext))[0]
    elif length == 127:
        ext = b""
        while len(ext) < 8: ext += sock.recv(8)
        length = struct.unpack('>Q', bytes(ext))[0]
    masked = hdr[1] & 0x80
    mbytes = b""
    if masked:
        while len(mbytes) < 4: mbytes += sock.recv(4)
    payload = b""
    while len(payload) < length:
        chunk = sock.recv(length - len(payload))
        if not chunk: break
        payload += chunk
    if masked:
        m = bytearray(payload)
        for i in range(len(m)): m[i] ^= mbytes[i % 4]
        return m.decode()
    return payload.decode()
```

## Common CDP Commands

| Task | Method | Params |
|------|--------|--------|
| Navigate | `Page.navigate` | `{"url": "https://..."}` |
| Scroll | `Runtime.evaluate` | `{"expression": "window.scrollTo(0, n)", "returnByValue": True}` |
| Screenshot | `Page.captureScreenshot` | `{"format": "png", "quality": 50}` |
| Find element | `Runtime.evaluate` | `{"expression": "document.querySelectorAll(...)...", "returnByValue": True}` |
| Click | `Input.dispatchMouseEvent` | `{"type": "mousePressed", "x": 960, "y": 540, "button": "left", "clickCount": 1}` |
| Type | `Input.insertText` | `{"text": "hello"}` |

## Practical Workflow for GitHub Delete

```python
# 1. Navigate to settings
send_frame(sock, {"id": 1, "method": "Page.navigate", "params": {"url": url}})

# 2. Wait for load
time.sleep(6)

# 3. Scroll to bottom
send_frame(sock, {"id": 2, "method": "Runtime.evaluate", "params": {
    "expression": "window.scrollTo(0, document.body.scrollHeight)",
    "returnByValue": True
}})
time.sleep(2)

# 4. Find delete button by exact text match
send_frame(sock, {"id": 3, "method": "Runtime.evaluate", "params": {
    "expression": "(function(){var btns=document.querySelectorAll('button');for(var i=0;i<btns.length;i++){var t=btns[i].textContent.trim();if(t==='Delete this repository'){var r=btns[i].getBoundingClientRect();return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)})}}return 'null'})()",
    "returnByValue": True
}})

# 5. Click via mouse event
send_frame(sock, {"id": 4, "method": "Input.dispatchMouseEvent", "params": {
    "type": "mousePressed", "x": pos['x'], "y": pos['y'], "button": "left", "clickCount": 1
}})
send_frame(sock, {"id": 5, "method": "Input.dispatchMouseEvent", "params": {
    "type": "mouseReleased", "x": pos['x'], "y": pos['y'], "button": "left", "clickCount": 1
}})
```

## Pitfalls

- **MCP bridge vs raw CDP**: When MCP `mcp-chrome-stdio` is broken, fall back to this raw WebSocket approach immediately rather than spending time debugging the bridge
- **SOCKS proxy**: `websockets` library auto-detects system proxy and fails if `python-socks` not installed. Use raw `socket` + manual frame handling instead — the proxy only affects the TCP connection, not the WebSocket protocol itself
- **Frame size limits**: Screenshot responses are large (>100KB). Ensure socket buffer can handle it; read in a loop until all bytes received
- **Mask key size**: Must be exactly 4 bytes. `os.urandom(4)`, not `os.urandom(16)` applied as mask
- **`window.scrollTo()` returns `undefined`** in CDP — use a compound expression like `window.scrollTo(0, n); document.body.scrollHeight` to verify position
