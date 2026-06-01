# Chrome CDP 用户真实浏览器控制（2026-06-01 验证）

## 核心问题

browser工具控制的Chrome是Hermes自己开的独立browser实例（`~/.hermes/chrome-debug`），
**没有用户日常Chrome的登录态**。要操作用户已登录的AI网站，必须直连用户Chrome。

## 两种方式

### 方式A：AppleScript（快速但受限）

```bash
# 打开URL
osascript -e 'tell application "Google Chrome" to open location "https://www.doubao.com"'

# 获取当前URL
osascript -e 'tell application "Google Chrome" to get URL of active tab of front window'

# 缺点：只能控制Chrome app层，读不到网页DOM内容
```

### 方式B：Chrome Debug Port + CDP（完整控制）

#### 步骤1：启动Chrome（关键命令）

```bash
# 杀掉现有Chrome（必须）
pkill -9 "Google Chrome"
sleep 2

# 用用户真实profile启动debug Chrome
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9333 \
  --user-data-dir="/Users/aimac/Library/Application Support/Google/Chrome/Profile 1"
```

#### 步骤2：验证端口

```bash
curl -s http://127.0.0.1:9333/json
# 预期返回JSON数组，包含页面信息
```

#### 步骤3：CDP操作（Python示例）

```python
import urllib.request, json, websockets, asyncio

# 获取页面列表
with urllib.request.urlopen("http://127.0.0.1:9333/json") as r:
    pages = json.loads(r.read())

# 新建标签页
req = urllib.request.Request("http://127.0.0.1:9333/json/new", method="PUT")
with urllib.request.urlopen(req) as r:
    new_page = json.loads(r.read())
ws_url = new_page["webSocketDebuggerUrl"]

# 导航
async def navigate(ws_url, url):
    async with websockets.connect(ws_url) as ws:
        msg_id = [0]
        async def send(cmd):
            msg_id[0] += 1
            cmd["id"] = msg_id[0]
            await ws.send(json.dumps(cmd))
            for _ in range(15):
                data = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if data.get("id") == msg_id[0]:
                    return data.get("result", {}).get("result", {})
            return None
        await send({"method": "Page.navigate", "params": {"url": url}})
        await asyncio.sleep(3)

# 读页面内容
async def get_text(ws_url):
    async with websockets.connect(ws_url) as ws:
        msg_id = [0]
        async def send(cmd):
            msg_id[0] += 1
            cmd["id"] = msg_id[0]
            await ws.send(json.dumps(cmd))
            for _ in range(15):
                data = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if data.get("id") == msg_id[0]:
                    return data.get("result", {}).get("result", {})
            return None
        result = await send({
            "method": "Runtime.evaluate",
            "params": {"expression": "document.body.innerText.substring(0, 5000)", "returnByValue": True}
        })
        print(result.get("value"))

# 发消息
async def type_and_send(ws_url, text):
    async with websockets.connect(ws_url) as ws:
        msg_id = [0]
        async def send(cmd):
            msg_id[0] += 1
            cmd["id"] = msg_id[0]
            await ws.send(json.dumps(cmd))
            for _ in range(15):
                data = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if data.get("id") == msg_id[0]:
                    return data.get("result", {}).get("result", {})
            return None
        await send({"method": "Runtime.evaluate", "params": {
            "expression": f"document.querySelector('textarea').value = '{text}'; document.querySelector('textarea').dispatchEvent(new Event('input', {{bubbles: true}})); 'typed'",
            "returnByValue": True
        }})
        await send({"method": "Runtime.evaluate", "params": {
            "expression": "document.querySelector('textarea').dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true})); 'enter_pressed'",
            "returnByValue": True
        }})
```

## 已知坑

### Profile路径有空格
```bash
# ❌ 错误
--user-data-dir=/Users/aimac/Library/Application Support/Google/Chrome/Profile 1
# ✅ 正确（加引号）
--user-data-dir="/Users/aimac/Library/Application Support/Google/Chrome/Profile 1"
```

### 端口不监听：Chrome实例冲突
- `lsof -i :9333` 无输出，但 `ps aux | grep Chrome` 能看到进程
- 解法：`pkill -9 "Google Chrome"` 杀所有Chrome进程（包括Helper），再重启

### computer_use看不到Chrome网页内容
- cua-driver只能读Chrome框架元素，读不到网页内容（bounds全为0）
- 解法：用CDP WebSocket + `Runtime.evaluate`

### AI网站需要真实登录态
- 豆包/ChatGLM 无登录态时不回复（页面显示"登录"按钮）
- 解法：用包含用户登录态的Chrome profile启动debug端口

## Profile路径参考
```
~/Library/Application Support/Google/Chrome/
├── Default/
├── Profile 1/
├── Profile 2/
└── Profile 3/
```

## MCP chrome工具 vs 用户Chrome CDP

| | browser工具(MCP) | 用户Chrome(CDP 9333) |
|--|--|--|
| 登录态 | 无（独立profile） | 有（真实profile） |
| 控制方式 | mcp_chrome_* | Python websocket CDP |
| 适用场景 | 快速测试、无登录需求 | 需登录态的AI网站 |
