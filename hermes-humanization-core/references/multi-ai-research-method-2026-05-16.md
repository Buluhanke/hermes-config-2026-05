# 三AI同时对比研究法
**来源**：2026-05-16 Hermes自我诊断工作流

---

## 适用场景

- 需要多角度分析复杂技术决策
- 不确定哪个AI的方案最可落地
- 想同时获取中文+英文+不同技术路线的视角

---

## 操作流程

### 1. 用CDP同时打开多个AI标签页

```python
import urllib.request, json

# CDP HTTP端点
BASE = "http://localhost:9333"

# 获取现有tabs
tabs = json.loads(urllib.request.urlopen(f"{BASE}/json").read())
print("当前tabs:", [(t["id"], t["url"][:50]) for t in tabs])

# 用PUT创建新tab
req = urllib.request.Request(
    f"{BASE}/json/new",
    data=b'{"url":"about:blank"}',
    headers={"Content-Type": "application/json"}
)
new_tab = json.loads(urllib.request.urlopen(req).read())
ws_url = new_tab["webSocketDebuggerUrl"]
tab_id = new_tab["id"]
print(f"新tab: {tab_id}, WS: {ws_url[:60]}...")
```

### 2. 同时导航到多个AI平台

用Python WebSocket直连每个tab，分别发Page.navigate：

```python
import websocket, json, time

platforms = [
    ("deepseek", "https://chat.deepseek.com"),
    ("chatgpt", "https://chatgpt.com"),
    ("chatglm", "https://chatglm.com"),
]

for name, url in platforms:
    # 用websocket-client连接tab
    ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=15)
    
    # 导航
    ws.send(json.dumps({
        "id": 1, "method": "Page.navigate", "params": {"url": url}
    }))
    # 等待加载
    time.sleep(3)
    
    # 发问题到输入框（用JS直接设value属性）
    ws.send(json.dumps({
        "id": 2,
        "method": "Runtime.evaluate",
        "params": {
            "expression": """
(function() {
    var ta = document.querySelector('textarea');
    if (!ta) ta = document.querySelector('div[contenteditable="true"]');
    if (ta) {
        ta.value = '你的问题';
        ta.dispatchEvent(new Event('input', {bubbles: true}));
        return 'ok';
    }
    return 'not found';
})()
            """,
            "returnByValue": True
        }
    }))
    time.sleep(0.5)
    
    # 按Enter发送
    ws.send(json.dumps({
        "id": 3,
        "method": "Runtime.evaluate",
        "params": {
            "expression": "document.querySelector('textarea')?.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', keyCode: 13, bubbles: true}))",
            "returnByValue": True
        }
    }))
    ws.close()
```

### 3. 等待回复后同时截图

```python
time.sleep(10)  # 等待回复生成

screenshots = {}
for name, tab in zip(["deepseek", "chatgpt", "chatglm"], tabs):
    ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=15)
    ws.send(json.dumps({"id": 1, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
    resp = json.loads(ws.recv())
    img_b64 = resp["result"]["data"]
    path = f"/tmp/{name}_response.png"
    with open(path, "wb") as f:
        f.write(base64.b64decode(img_b64))
    screenshots[name] = path
    ws.close()
```

### 4. 提取回复文本

DeepSeek/ChatGPT的DOM通常无法用JS提取（React动态渲染），截图是唯一可靠方式。用vision_analyze或本地VLM读取：

```python
# 用screen_vision工具读取截图
from hermes_tools import screen_vision
for name, path in screenshots.items():
    result = screen_vision(model="ahmadwaqar/smolvlm2-agentic-gui:latest",
                           question="读取这个AI助手的完整回复文字",
                           image_path=path)
    print(f"=== {name} ===\n{result}\n")
```

---

## 三AI分析结论汇总（2026-05-16）

### 眼睛（屏幕感知）— 最高优先
- Qwen2-VL-7B (AWQ 4-bit) — 7B参数，中文OCR最强，mlx-vlm库加载
- Moondream2 (1.8B) — 轻量实时监控，<2GB
- 不用Ollama跑VL（内存常驻问题），用mlx-vlm按需加载

### 嘴巴（TTS）— 次优先
- 最强情感：ChatTTS（约2GB，有笑声叹气）
- Apple Silicon最优：MeloTTS-MLX（<1GB，实时）
- 零成本：macOS Siri + SSML

### 手（电脑控制）— OS级替代MCP
- atomacos > Chrome MCP（系统级稳定）
- PyAutoGUI + VLM闭环（Anthropic Computer Use方案）
- Open Interpreter杀手功能：原生AppleScript执行

### 手机端
- iPhone Mirroring (macOS 15 Sequoia)
- Shortcuts + Flask API桥接
- Scriptable App + iCloud同步

---

## 关键教训

1. **MCP bridge死了≠Chrome不可控** — Python WebSocket直连CDP完全独立
2. **React按钮无法用CDP鼠标事件点击** — 用JS直接触发click事件
3. **DOM查询返回0元素** — 某些AI页面（DeepSeek/ChatGPT）React动态渲染导致querySelectorAll返回空，用截图+OCR
4. **不要同时开太多tab** — CDP WebSocket连接数有限制
