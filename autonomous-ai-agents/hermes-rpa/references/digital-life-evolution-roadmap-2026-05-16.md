# 数字生命体进化路线图 — M4 24GB Mac mini 优化版
**来源**：2026-05-16 三AI（DeepSeek + ChatGPT + ChatGLM）同时对比分析
**硬件**：Apple M4 (10核CPU) + 24GB统一内存，无独立显存

---

## 核心结论

**优先级排序**：眼睛 > 嘴巴 > 手 > 脚

**三个AI共识**：
1. 眼睛是所有能力的基础——没有眼睛，验证码做不了，移动端做不了，真人化也做不了
2. Chrome MCP是过渡方案，最终要用OS级API
3. 24GB通过AWQ量化完全够用，不需要大显存

---

## M4 24GB 内存调度方案（免费/低成本）

| 步骤 | 能力 | 方案 | 内存占用 | 成本 |
|------|------|------|---------|------|
| 1 | 主脑 | Qwen2.5-7B (mlx) | ~5GB常驻 | 免费 |
| 2 | 眼睛 | Qwen2-VL-7B (AWQ 4-bit) 按需加载 | ~5GB按需 | 免费 |
| 3 | 嘴巴 | MeloTTS-MLX 或 macOS Siri+SSML | ~1GB | 免费 |
| 4 | 手 | atomacos + PyAutoGUI + Open Interpreter | 几乎0 | 免费 |
| 5 | 反思 | VLM截屏验证 + ChromaDB错误记忆 | 很小 | 免费 |
| 6 | 手机 | iPhone Mirroring (macOS 15) + Shortcuts + Flask | - | 免费 |

**内存调度原则**：不要所有模型同时常驻内存，按需加载。

---

## 各维度具体方案

### 眼睛（屏幕感知）— 最高优先

**推荐本地VL模型**：
- 主力：Qwen2-VL-7B-Instruct (AWQ 4-bit量化) — 中文OCR和UI理解天花板，~5GB，15-20 tokens/s
- 轻量备选：Moondream2 (1.8B) + macOS原生Vision框架 — 实时监控屏幕用，<2GB
- 本地部署：用mlx-vlm库加载，不要用Ollama（内存常驻占用大）

**落地步骤**：
1. 先用GPT-4V或Qwen-VL API验证概念
2. 稳定后迁移到本地（SecAgent约3B参数，16GB显存可跑）

**不要做的事**：不要试图分析每一帧，仅在触发时（用户点击/提问）或低帧率（1帧/秒）使用VLM。

### 嘴巴（TTS情感）— 次优先

**方案对比**：
- 最强情感：ChatTTS — 支持[laugh]、[break]等控制符，能笑能叹气，但约2GB，M4跑实时稍有延迟
- Apple Silicon优化：MeloTTS-MLX — 速度极快可实时，支持中英日韩，<1GB
- 零成本极简：macOS AVSpeechSynthesizer + SSML — Sequoia全新Siri声音非常自然，零延迟零内存

**务实建议**：先用macOS Siri语音+SSML打基础，升级到MeloTTS-MLX。

### 手（电脑控制）— OS级替代MCP

**为什么Chrome MCP不稳定**：依赖DOM结构，网页改版或动态加载就傻

**绝对稳定方案**：macOS Accessibility API (atomacos库)
- 系统级稳定，不被网页防爬拦截
- 能读取所有原生App和网页的元素坐标和文字

**通用方案**：PyAutoGUI + VLM视觉闭环（Anthropic Computer Use方案）
- VLM截屏 → 识别出"发送按钮在坐标(500,300)" → PyAutoGUI点击
- 没有DOM依赖，人能用的它就能用

**杀手级框架**：Open Interpreter — 原生支持编写和执行AppleScript/Python控制Mac

### 反思/自我判断

**视觉验证闭环（最关键）**：
- Hermes执行动作 → 截屏 → VLM检查("屏幕上是否出现'邮件已删除'提示？")
- 如果VLM返回"没有"，则判断操作失败，重新规划

**双重模型校验**：
- 主脑（8B）做决策
- 1.5B小模型做"有害性判断"，有风险则触发阻断

**痛觉记忆**：将错误动作+原因写入向量数据库（ChromaDB），下次优先检索

### 手机端（iPhone免越狱）

**正向控制（Mac → iPhone）**：Apple Shortcuts + Flask API
- Mac开本地HTTP服务，iPhone快捷指令触发条件（时间/NFC/Siri语音）
- 结果通过ntfy或Bark推送iPhone通知栏

**反向控制（iPhone → Mac）**：Scriptable App（免费）
- iPhone安装Scriptable，写JS调用iOS API（日历/提醒/照片/剪贴板）
- Hermes生成脚本 → iCloud同步 → iPhone执行

**终极生态桥**：macOS Sequoia iPhone Mirroring
- macOS 15可直接在桌面上操作iPhone镜像窗口
- 等于用PyAutoGUI + VLM控制Mac屏幕上的iPhone窗口

---

## 三AI分析对比

| AI | 眼睛方案 | 嘴巴方案 | 手机方案 | 反思方案 | 综合评分 |
|----|---------|---------|---------|---------|---------|
| DeepSeek | SecAgent(3B)本地/云API | CosyVoice情感强 | Shortcuts+Flask | Reflexion框架 | 偏学术 |
| ChatGPT | GPT-4V/Qwen-VL API | ChatTTS本地 | iPhone Mirroring | 视觉验证闭环 | 偏通用 |
| ChatGLM | Qwen2-VL-7B AWQ/mlx-vlm | MeloTTS-MLX | Scriptable+iCloud | ChromaDB痛觉记忆 | **最具体可落地** |

**ChatGLM最实用**——给出了具体模型名+内存占用+落地步骤。

---

## 用户明确纠正（2026-05-16）

**旧思维（过时）**：1688找品采购是Hermes的核心价值
**新思维（正确）**：数字生命体是目标，1688只是其中一个应用场景
**触发信号**：用户说"你的思路还没改表，还是什么1688什么采购，这都说了太多次了过时了"

**教训**：不要再提1688，除非用户主动提。

---

## MCP Bridge断联时的Python直连CDP方案

当mcp-chrome-stdio断联时，不需要重启bridge，直接用Python直连：

```python
import websocket, json, time, base64

# 1. 获取tab列表（HTTP端点，不依赖bridge）
import urllib.request
tabs = json.loads(urllib.request.urlopen('http://localhost:9333/json').read())

# 2. WebSocket直连（用websocket-client库，已安装）
WS_URL = tabs[0]['webSocketDebuggerUrl']  # 字段名是webSocketDebuggerUrl，不是webSocketURL
ws = websocket.create_connection(WS_URL, timeout=15)

# 3. 截图
def send(ws, method, params=None):
    ws.send(json.dumps({"id": 1, "method": method, "params": params or {}}))

def recv(ws):
    while True:
        msg = json.loads(ws.recv())
        if "id" in msg:
            return msg

send(ws, "Page.captureScreenshot", {"format": "png", "quality": 50})
resp = recv(ws)
img_data = base64.b64decode(resp["result"]["data"])
with open("/tmp/screenshot.png", "wb") as f:
    f.write(img_data)

# 4. 查找元素
send(ws, "Runtime.evaluate", {"expression": """
(function() {
  var els = document.querySelectorAll('button, [role="button"]');
  var result = [];
  els.forEach(function(el) {
    var rect = el.getBoundingClientRect();
    if (rect.width > 0) {
      result.push({
        text: el.textContent?.trim().substring(0, 50),
        x: Math.round(rect.x + rect.width/2),
        y: Math.round(rect.y + rect.height/2)
      });
    }
  });
  return JSON.stringify(result.slice(0, 20));
})()
"""})
resp = recv(ws)
elements = json.loads(resp["result"]["result"]["value"])

# 5. 点击
send(ws, "Input.dispatchMouseEvent", {"type": "mousePressed", "x": 500, "y": 300, "button": "left", "clickCount": 1})
recv(ws)
send(ws, "Input.dispatchMouseEvent", {"type": "mouseReleased", "x": 500, "y": 300, "button": "left", "clickCount": 1})
recv(ws)

ws.close()
```

**关键字段名**：`webSocketDebuggerUrl`（不是webSocketURL）
**依赖**：需要Chrome启动时加`--remote-allow-origins=*`，否则WebSocket握手403
