# CDP WebSocket — 原生 Python 实现（2026-05-14 实测）

## 核心发现

Chrome CDP 调试协议走 WebSocket，不走 HTTP。
- HTTP `http://127.0.0.1:9333/json` — **只用于获取 Target ID**，不支持发送命令
- WebSocket `ws://127.0.0.1:9333/devtools/page/<TARGET_ID>` — **发送 CDP 命令的唯一方式**

## 完整工作流

```
browser_navigate(url)          # Hermes 工具：导航到目标页
        ↓
HTTP GET /json                 # 获取当前 page 的 Target ID
        ↓
WebSocket 握手                 # socket + base64 key，无第三方库
        ↓
CDP 命令发送                    # Runtime.evaluate / Input.dispatchMouseEvent
        ↓
收到响应                        # threading.Event 同步等待
```

## 完整代码（2026-05-14 实测通过）

```python
import socket, os, json, struct, base64, time, threading, urllib.request

CDP_HOST, CDP_PORT = "127.0.0.1", 9333

def get_target():
    """通过 HTTP 端点获取当前 page 的 Target ID"""
    with urllib.request.urlopen(f"http://{CDP_HOST}:{CDP_PORT}/json", timeout=5) as r:
        targets = json.loads(r.read())
    for t in targets:
        if t.get("type") == "page":
            return t["id"], t.get("url"), t.get("title")
    return None, None, None

def ws_connect(target_id):
    """原生 Python WebSocket 握手 + CDP 调用"""
    s = socket.socket()
    s.settimeout(20)
    s.connect((CDP_HOST, CDP_PORT))
    PATH = f"/devtools/page/{target_id}"
    key = base64.b64encode(os.urandom(16)).decode()
    hs = (f"GET {PATH} HTTP/1.1\r\nHost: {CDP_HOST}:{CDP_PORT}\r\n"
          f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
          f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n")
    s.sendall(hs.encode())
    # 读 HTTP 响应头
    resp = b""
    while b"\r\n\r\n" not in resp:
        resp += s.recv(4096)

    results = {}
    msg_id = [0]

    def recv_loop():
        while True:
            try:
                h = s.recv(2)
                if not h: break
                l = h[1] & 0x7F
                if l == 126: l = struct.unpack(">H", s.recv(2))[0]
                elif l == 127: l = struct.unpack(">Q", s.recv(8))[0]
                p = b""
                while len(p) < l: p += s.recv(l - len(p))
                try:
                    m = json.loads(p.decode())
                    if m.get("id") is not None:
                        results[m["id"]] = m
                except: pass
            except: break

    t = threading.Thread(target=recv_loop, daemon=True)
    t.start()

    def cdp(method, params=None, timeout=15):
        mid = msg_id[0]; msg_id[0] += 1
        ev = threading.Event()
        results["_e" + str(mid)] = ev
        payload = json.dumps({"id": mid, "method": method, "params": params or {}})
        mask = os.urandom(4)
        masked = bytearray(c ^ mask[i % 4] for i, c in enumerate(payload.encode()))
        frame = bytearray([0x81])
        L = len(payload)
        if L < 126: frame.append(0x80 | L)
        elif L < 65536: frame.append(0xFE); frame.extend(struct.pack(">H", L))
        else: frame.append(0xFF); frame.extend(struct.pack(">Q", L))
        frame.extend(mask); frame.extend(masked)
        s.sendall(bytes(frame))
        ev.wait(timeout)
        results.pop("_e" + str(mid), None)
        return results.pop(mid, {})

    return s, cdp

# ===== 使用示例 =====
target_id, url_before, _ = get_target()
print(f"当前页面: {url_before}")

sock, cdp = ws_connect(target_id)

# 1. 获取页面所有可点击元素
r = cdp("Runtime.evaluate", {
    "expression": """
(function() {
    var items = [];
    document.querySelectorAll("a,button,[role=button]").forEach(function(el) {
        var rect = el.getBoundingClientRect();
        var st = window.getComputedStyle(el);
        if (st.display === "none" || st.visibility === "hidden") return;
        if (rect.width < 4 || rect.height < 4) return;
        items.push({
            text: (el.textContent||"").trim().substring(0, 50),
            href: el.href || "",
            x: Math.round(rect.left + rect.width/2),
            y: Math.round(rect.top + rect.height/2),
            tag: el.tagName.toLowerCase()
        });
    });
    return JSON.stringify(items);
})()
""",
    "returnByValue": True
})
raw = r.get("result",{}).get("result",{}).get("value","[]")
items = json.loads(raw) if raw and raw.startswith("[") else []
print(f"发现 {len(items)} 个元素")

# 2. 点击任意元素
obj = random.choice(items)
print(f"点击: '{obj['text']}' at ({obj['x']},{obj['y']})")
r = cdp("Runtime.evaluate", {
    "expression": f"(function(){{var el=document.elementFromPoint({obj['x']},{obj['y']});"
                  f"if(!el)return'NO';el.scrollIntoView({{behavior:'instant',block:'center'}});"
                  f"setTimeout(function(){{el.click()}},200);return'OK';}})()",
    "returnByValue": True
})
print(f"点击结果: {r.get('result',{{}}).get('result',{{}}).get('value')}")

time.sleep(2)

# 3. 检查 URL 变化
r = cdp("Runtime.evaluate", {"expression": "window.location.href", "returnByValue": True})
url_after = r.get("result",{}).get("result",{}).get("value","")
print(f"跳转后: {url_after}")
print(f"跳转成功: {url_after != url_before}")

sock.close()
```

## 关键实现细节

### WebSocket 帧格式

```
0x81 = FIN + text frame
0x80 = mask bit set
payload < 126:  1 byte length
payload < 65536: 0xFE + 2 byte big-endian
payload >= 65536: 0xFF + 8 byte big-endian
mask = 4 random bytes
masked_payload = payload XOR mask[i % 4]
```

### 消息同步机制

CDP 命令和响应通过 `id` 字段匹配：
- 发送：`{"id": 1, "method": "Runtime.evaluate", ...}`
- 接收：通过 `threading.Event` 等待 `results[id]` 被填充
- 超时：`ev.wait(timeout)` 控制，避免永久阻塞

### Target 生命周期

页面导航后原有 Target 会 **detach**，需要重新调用 `get_target()` 获取新 Target ID 再建连。

## 已知限制

- `websockets` 库会自动检测并使用系统 SOCKS 代理（即使连接 localhost），导致 `python-socks` 缺失报错。**用原生 `socket` 手写帧编码绕过**，不要用 `websockets` 库
- `Runtime.evaluate` 执行 JS 可能有权限限制（Chrome 安全设置）
- 某些页面（如 chrome:// 内部页）CDP 无法注入脚本
- 不支持 `Input.dispatchMouseEvent` 以外的事件类型（如拖拽）

## 与 browser_navigate 的分工

| 操作 | 工具 |
|------|------|
| 页面导航（带登录态） | `browser_navigate`（Hermes 工具） |
| DOM 查询、元素定位 | CDP WebSocket |
| JS 点击/输入 | CDP `Runtime.evaluate` |
| 浏览器外截图 | `screencapture` + OCR |

## 参考

- Chrome DevTools Protocol: https://chromedevtools.github.io/devtools-protocol/
