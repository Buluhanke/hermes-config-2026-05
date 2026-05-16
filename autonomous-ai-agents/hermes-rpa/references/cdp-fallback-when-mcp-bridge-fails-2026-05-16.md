# CDP Fallback — MCP Bridge挂了怎么控Chrome（2026-05-16实测）

## 核心结论

**MCP bridge断了 ≠ Chrome不可控**。只要Chrome在跑，Python就能直连CDP WebSocket。

| 通道 | 依赖 | 可用性 |
|------|------|--------|
| CDP HTTP端点（枚举tabs） | Chrome端口9333 | ✅ 不依赖MCP |
| Raw Python WebSocket + CDP | Chrome端口9333 | ✅ 不依赖MCP |
| AppleScript导航 | macOS原生 | ✅ 不依赖MCP |
| cliclick点击 | brew安装 | ✅ 不依赖MCP |
| mcp_chrome_* 工具 | mcp-chrome-stdio bridge | ❌ 断联时全挂 |

## 实测场景

2026-05-16：mcp-chrome-stdio进程stale，mcp_chrome_navigate/mcp_chrome_read_page等全部报`ClosedResourceError`。但CDP HTTP端点（`curl http://127.0.0.1:9333/json`）正常返回tab列表，Python WebSocket直连CDP截图成功。

## Python直连CDP模板

```python
import socket, struct, json, time, urllib.request, base64, os

# 1. 枚举tabs（CDP HTTP）
tabs = json.loads(urllib.request.urlopen('http://localhost:9333/json').read())
target = next((t for t in tabs if 'chat.deepseek.com' in t.get('url','')), tabs[0])

# 2. 原生socket WebSocket握手
ws_url = target['webSocketDebuggerUrl']
path = ws_url.replace('ws://localhost:9333', '')
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(20)
sock.connect(("localhost", 9333))
key = base64.b64encode(os.urandom(16)).decode()
sock.send(f"GET {path} HTTP/1.1\r\nHost: localhost:9333\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n".encode())
resp = b""
while b"\r\n\r\n" not in resp: resp += sock.recv(4096)

# 3. 发帧（masked）
def send_frame(sock, data):
    payload = json.dumps(data).encode()
    blen = len(payload)
    if blen < 126: hdr = bytes([0x81, 0x80 | blen])
    elif blen < 65536: hdr = bytes([0x81, 0x80 | 126]) + struct.pack('>H', blen)
    else: hdr = bytes([0x81, 0x80 | 127]) + struct.pack('>Q', blen)
    mask = os.urandom(4)
    m = bytearray(payload)
    for i in range(len(m)): m[i] ^= mask[i % 4]
    sock.send(hdr + mask + bytes(m))

# 4. 收帧（unmasked）
def recv_frame(sock):
    hdr = b""
    while len(hdr) < 2: hdr += sock.recv(2)
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

# 5. 截图
send_frame(sock, {"id": 1, "method": "Page.captureScreenshot", "params": {"format": "png", "quality": 50}})
resp = recv_frame(sock)
d = json.loads(resp)
img_data = d.get('result', {}).get('data', '')
with open('/tmp/screenshot.png', 'wb') as f:
    f.write(base64.b64decode(img_data))

# 6. 导航到URL
send_frame(sock, {"id": 2, "method": "Page.navigate", "params": {"url": "https://chat.deepseek.com"}})
time.sleep(3)
```

## 关键细节

- **Chrome启动必须加`--remote-allow-origins=***`：否则WebSocket握手返回403
- **mask key**：4字节`os.urandom(4)`，每次帧不同
- **字段名**：`webSocketDebuggerUrl`（不是webSocketURL）
- **不要用`websocket-client`库**：会被系统SOCKS代理拦截，用原生socket手写帧
- **不要用`websockets`库**：同上原因

## DeepSeek专家模式激活

位置：顶部导航栏y=185处（不是聊天区域y=323）。CDP坐标点击(960, 185)激活。

## Tab ID会过期

浏览器重启后，之前保存的tab ID全部失效。重新枚举tabs获取新ID。

## 新建Tab的正确方式（AppleScript，非PUT）

`/json/new` PUT 在 aimac 上返回 **405 Method Not Allowed**，必须用 AppleScript：

```python
import subprocess

script = '''
tell application "Google Chrome"
    activate
    delay 0.3
    tell window 1
        make new tab with properties {URL:"https://kimi.moonshot.cn"}
    end tell
end tell
'''
subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=10)
```
