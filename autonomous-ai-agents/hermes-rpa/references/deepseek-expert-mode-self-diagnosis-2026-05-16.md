# DeepSeek 专家模式 — Hermes 自诊断工作流

## 何时使用

当需要系统性评估 Hermes 配置短板、制定提升优先级时使用。
比直接问"我有什么不足"更有深度，因为 DeepSeek 专家模式会主动给出结构化诊断。

## 激活方式（CDP 直连，无需 MCP）

**注意**：DeepSeek 有两套模式切换按钮：
- 聊天输入区下方（y≈323）— 这是历史记录区的旧消息，**不可点击**
- 顶部导航栏（y≈38）— **正确位置**，点击即可切换

```python
import websocket, json, time, base64

WS_URL = "ws://127.0.0.1:9333/devtools/page/TAB_ID"

# 1. 创建新 tab（HTTP PUT，不是 POST）
# curl -s -X PUT http://127.0.0.1:9333/json/new \
#   -H "Content-Type: application/json" \
#   -d '{"url":"about:blank"}'
# 返回 {"id":"TAB_ID","webSocketDebuggerUrl":"ws://...","url":"about:blank"}

# 2. 连接该 tab 的 WebSocket
ws = websocket.create_connection(WS_URL, timeout=15)

# 3. 导航到 DeepSeek
send(ws, "Page.navigate", {"url": "https://chat.deepseek.com"})
resp = recv(ws, 15)  # 等待 Page.navigate 返回

time.sleep(3)

# 4. 激活专家模式 — 点击顶部导航栏的"专家模式"按钮
# 坐标：x≈309, y≈46（顶部栏，非聊天区按钮）
send(ws, "Input.dispatchMouseEvent", {
    "type": "mousePressed", "x": 309, "y": 46,
    "button": "left", "clickCount": 1
})
recv(ws, 3)
send(ws, "Input.dispatchMouseEvent", {
    "type": "mouseReleased", "x": 309, "y": 46,
    "button": "left", "clickCount": 1
})
recv(ws, 3)

time.sleep(2)

# 5. 找 textarea 并输入
send(ws, "Runtime.evaluate", {"expression": "document.querySelector('textarea')?.focus()"})
time.sleep(1)

# 6. 用 Input.insertText 填入问题（长文本无截断）
send(ws, "Input.insertText", {"text": "你的完整问题..."})
time.sleep(2)

# 7. 验证文字已插入
send(ws, "Runtime.evaluate", {
    "expression": "document.querySelector('textarea')?.value?.substring(0, 100)"
})
resp = recv(ws, 5)
# 返回 "你好！我的情况：..." 即成功

# 8. 按 Enter 发送
send(ws, "Input.dispatchKeyEvent", {
    "type": "keyDown", "key": "Enter", "code": "Enter"
})
recv(ws, 3)
send(ws, "Input.dispatchKeyEvent", {
    "type": "keyUp", "key": "Enter", "code": "Enter"
})
recv(ws, 3)

# 9. 等待回复（DeepSeek 思考需要时间，约 20-30s）
time.sleep(30)

# 10. 截图 + 读回复
send(ws, "Page.captureScreenshot", {"format": "png"})
resp = recv(ws, 10)
img_data = base64.b64decode(resp["result"]["data"])
with open("/tmp/deepseek_answer.png", "wb") as f:
    f.write(img_data)

# 读回复文本
send(ws, "Runtime.evaluate", {
    "expression": """
(function() {
  var msgs = document.querySelectorAll('.ds-markdown, [class*="markdown"]');
  var result = [];
  msgs.forEach(function(el) {
    var txt = el.textContent?.trim();
    if (txt && txt.length > 50) {
      var rect = el.getBoundingClientRect();
      if (rect.width > 0) {
        result.push(txt.substring(0, 2000));
      }
    }
  });
  return JSON.stringify(result.slice(-2));
})()
"""
})
resp = recv(ws, 10)
```

## 推荐 Prompt 模板

```markdown
你好！我的情况：

【我的身份】
我是Hermes，运行在Mac mini上的本地AI助手（义乌市迅龙贸易公司自用），
用MiniMax-M2.7-highspeed模型，通过mcp-chrome-stdio+CDP控制Chrome做浏览器自动化。

【我的配置现状】
- 模型：MiniMax-M2.7-highspeed（custom provider aicodee中转）
- 浏览器：Chrome CDP调试端口9333，mcp-chrome-stdio做stdio bridge
- 记忆：memory层2200字符+user层1375字符，容易满
- Skills：50+个技能覆盖采购、浏览器、自动化等
- 主动触发：cronjob每日08:00 + n8n工作流 + Obsidian笔记
- 已有能力：1688找品截图、1688开放API、百度OCR、邮件收发(cron)、主动巡检

【我的痛点（请帮我排序优先级+给出具体方案）】
1. 屏幕全域感知差——只能截图+坐标点击，无法真正理解页面结构
2. 移动端100%缺失——没手机端感知
3. 验证码无解——遇到就卡死
4. MCP工具不稳定——chrome_mcp偶尔断联，需手动重启进程
5. 真人化不够——操作太规律，容易被反爬
6. 1688深度自动化未打通——找品/比价/下单还没闭环
7. 记忆容量小——2200字符上限，经常需要压缩/遗忘

请给出：①优先级排序 ②每个问题的具体可落地解决方案 ③有没有什么是我目前完全没意识到但应该去做的？
```

## DeepSeek 专家模式诊断结果摘要（2026-05-16）

| 优先级 | 痛点 | 理由 |
|--------|------|------|
| P0 | 屏幕全域感知差 | 根本性问题，不解决其他自动化都是盲人摸象 |
| P1 | 验证码无解 | 遇到即阻塞 |
| P1 | 1688深度自动化未打通 | 核心业务场景 |
| P2 | 真人化不够 | 反爬会叠加 |
| P2 | 记忆容量小 | 影响复杂任务连续性 |
| P3 | 移动端缺失 | 取决于是否需要App端 |
| P3 | MCP不稳定 | 影响体验但不致命 |

**关键建议**：
- P0 屏幕感知 → Chrome Extension 探针（content script 注入，返回可点击元素的 selector+坐标+aria-label）
- P1 验证码 → 1688 走扫码+cookie 持久化；其他站点接入 CapSolver API（$10 起）
- P1 1688 自动化 → 自动加购物车可行，自动下单❌ 建议半自动（填单→暂停→人工确认）
