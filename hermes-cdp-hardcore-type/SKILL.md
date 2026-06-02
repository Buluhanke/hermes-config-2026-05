---
name: hermes-cdp-hardcore-type
description: CDP直连真实Chrome + 硬核逐字输入 + 智能滚屏, 攻克React+Shadow DOM+虚拟列表三大天坑
category: web-agent-os
---

# Hermes CDP 硬核自动化方案

## 核心场景
Mac Mini 24GB 无 Docker、无 OCR 前提下, 用 Python + CDP 自动化现代 AI 站点
(DeepSeek/ChatGPT/Claude/豆包/Gemini/Grok等) 的对话输入、提交、读取。

## 四大天坑 (必须知道)
1. **React 受控组件** — `element.value = "x"` 不触发 onChange, 按钮永远 disabled
2. **keyDown 重复字符** — keyDown 带 `text` + char 事件, React 双计为双倍字符
3. **Shadow DOM 按钮** — `btn.click()` 穿透不了 Shadow Root, 返回 null
4. **虚拟列表懒加载** — scrollHeight 远大于 clientHeight, 真实滚动容器是内部 div, window.scrollTo 无效

## 破局方案
CDP 直连真实 Chrome (debug port 9333) + 4 大武器：

### 武器0: 贝塞尔鼠标轨迹（真人化鼠标划行）
```python
def calculate_bezier_point(p0, p1, p2, p3, t):
    x = (1-t)**3*p0[0] + 3*(1-t)**2*t*p1[0] + 3*(1-t)*t**2*p2[0] + t**3*p3[0]
    y = (1-t)**3*p0[1] + 3*(1-t)**2*t*p1[1] + 3*(1-t)*t**2*p2[1] + t**3*p3[1]
    return int(x), int(y)

def generate_human_mouse_path(start, end, steps_count=None):
    """三阶贝塞尔曲线 + cos 缓动S-curve + 微幅抖动"""
    x0, y0 = start
    x1, y1 = end
    dist = math.sqrt((x1-x0)**2 + (y1-y0)**2)
    if steps_count is None:
        steps_count = max(15, int(dist / random.choice([15, 20, 25])))
    off = dist * 0.2
    p1 = (x0+(x1-x0)*0.25+random.uniform(-off,off), y0+(y1-y0)*0.25+random.uniform(-off,off))
    p2 = (x0+(x1-x0)*0.75+random.uniform(-off,off), y0+(y1-y0)*0.75+random.uniform(-off,off))
    path = []
    for i in range(steps_count+1):
        prog = i / steps_count
        t = (1-math.cos(prog*math.pi)) / 2  # S-curve 缓动：两头慢、中间快
        x, y = calculate_bezier_point(start, p1, p2, end, t)
        if i < steps_count:
            shake = (1.0 - prog)  # 越接近终点抖动越小
            x += int(random.uniform(-1,1) * shake)
            y += int(random.uniform(-1,1) * shake)
        path.append((x, y))
    return path

async def human_mouse_click(cdp, target_x, target_y, current_mouse_pos=(100, 100)):
    """贝塞尔轨迹划行 + Hover悬停 + 物理按压时长"""
    path = generate_human_mouse_path(current_mouse_pos, (target_x, target_y))
    for x, y in path:
        await cdp.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y, "button": "none"})
        await asyncio.sleep(random.uniform(0.008, 0.015))   # 8~15ms 高频回报率
    await asyncio.sleep(random.uniform(0.12, 0.28))      # Hover悬停（真人瞄按钮停顿）
    await cdp.send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": target_x, "y": target_y, "button": "left", "clickCount": 1})
    await asyncio.sleep(random.uniform(0.05, 0.10))      # 肉体按压延迟（50~100ms）
    await cdp.send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": target_x, "y": target_y, "button": "left", "clickCount": 1})
    return (target_x, target_y)  # 返回最新位置，供下次划行作起点
```

**核心**: 鼠标轨迹从"直线瞬移"变为"物理划行"，服务器抓到的 Mouse Tracking 数据是带惯性微抖动的完美贝塞尔曲线，直接击碎风控特征匹配。

### 武器1: 硬核逐字输入（Biometric Typing）
```python
PUNCTUATION = {",", ".", "!", "?", "，", "。", "！", "？", " ", "\n"}

async def human_type_text(cdp, text):
    """高斯按压时长 + 标点思维停顿，突破匀速打字指纹"""
    for ch in text:
        dur = random.gauss(0.05, 0.015)   # 按压时长：高斯分布 30~90ms
        dur = max(0.03, min(dur, 0.09))
        await cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": ch, "text": ""})  # text空防双字符
        await asyncio.sleep(dur)
        await cdp.send("Input.dispatchKeyEvent", {"type": "char", "text": ch})  # 触发React onChange
        await cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": ch})
        iv = random.gauss(0.06, 0.02)    # 字间隔：高斯分布
        iv = max(0.03, min(iv, 0.15))
        if ch in PUNCTUATION:
            iv += random.uniform(0.25, 0.55)  # 标点后额外思维停顿 250~550ms
        await asyncio.sleep(iv)
```

**核心**: 所有时长均为正态分布（非匀速）+ 标点后追加"大脑组织语言的呼吸停顿"，彻底消除机器人匀速特征。**keyDown.text="" 必须空**（硬核发现）。

### 武器1+0: 快速注入模式 (direct value) — 替代逐字打字
用户反馈逐字打字太慢（"你模拟人工打字速度太慢了"）。对于支持 `textarea.value=` 的站点，用 direct value 比逐字快 10 倍：

```javascript
(function(){
  const ta = document.querySelector('textarea');
  if(ta){
    ta.value = '我们电脑配置免费不要OCR能直接读取屏幕内容吗';
    ta.dispatchEvent(new Event('input', {bubbles:true}));
    ta.dispatchEvent(new Event('change', {bubbles:true}));
    return 'ok';
  }
  return 'no textarea';
})()
```

**触发**：value 赋值 → React onChange → 发送按钮自动变亮
**发送**：`Input.dispatchKeyEvent(key='Enter')` 穿透，不需要 .click()
**适用**：DeepSeek ✅、豆包 ✅、ChatGLM ✅
**不适用**：ChatGPT（ProseMirror 受控组件，value 被忽略）、Gemini（textarea 在 webview 里跨域）

### ⚠️ DeepSeek 实战坑：ta.value= 设值成功但按钮点击无效
实测（2026-06-02）：`ta.value=` 能把文字写进 textarea，`btns[8]` 按钮能 click 出 "clicked"，但 AI 就是不回复。

**根因**：DeepSeek 的 React 输入框在 `ta.value=` 后没有真正被"用户输入"事件激活——缺少光标位置变化事件 + input 事件的完整性验证，按钮虽然看起来可点（`ds-button--disabled` 的 disabled 属性为 null），但 React 内部状态未更新，点击后 textarea 被清空。

**已验证有效的解法**：
1. **聚焦 + `Input.dispatchKeyEvent` 逐字输入**（正确流程）：
   ```javascript
   // 先 JS 聚焦
   document.querySelector('textarea').focus();
   ```
   然后用 `browser_cdp` tool 逐字 `Input.dispatchKeyEvent(type='keyDown', text='字', key='字')` — 每字触发 React onChange，这是唯一让 DeepSeek 可靠发送的方式。
2. **Enter 兜底**：`Input.dispatchKeyEvent(key='Enter')` 比按钮点击更可靠。

**已验证失效的解法**：
- `ta.value=` + `dispatchEvent(new Event('input', {bubbles:true}))` → DeepSeek 收到事件但 React 状态未更新
- 按钮 `btns[8].click()` → 点击返回 "clicked" 但不触发发送
- `ta.value=` + `dispatchEvent(new Event('change', {bubbles:true}))` → 同上

**ChatGLM 可以用 ta.value=**（已实测成功），DeepSeek 必须逐字输入。

### 武器1+0 联合调用模式
```python
# 鼠标位置追踪（贯穿全流程）
last_pos = (100, 100)

# 1. 贝塞尔滑入输入框 → 2. 真人呼吸打字
last_pos = await human_mouse_click(cdp, input_x, input_y, current_mouse_pos=last_pos)
await asyncio.sleep(0.2)
await human_type_text(cdp, "Hello MiniMax 2.7...")

# 3. 贝塞尔滑到发送按钮 → 4. 物理点击
last_pos = await human_mouse_click(cdp, send_x, send_y, current_mouse_pos=last_pos)
```

**效果**: 风控服务器看到的是完美贝塞尔鼠标轨迹 + 非匀速生物识别打字律动，双重真人化特征叠加。
### 武器2: 智能聚焦 (穿透 Shadow DOM)
### 武器2: 智能聚焦 (穿透 Shadow DOM)
```python
# JS直接定位, 不用 querySelector (后者拿不到 Shadow DOM 里的 nodeId)
focus_expr = """
(() => {
    const tas = Array.from(document.querySelectorAll('textarea'));
    for (let t of tas) {
        if (!t.readOnly && t.offsetParent !== null && t.placeholder) {
            t.focus();
            return {ok: true, type: 'textarea', ph: t.placeholder};
        }
    }
    // 找 contenteditable (ProseMirror/tiptap)
    const ces = Array.from(document.querySelectorAll('[contenteditable=true]'));
    for (let e of ces) {
        if (e.offsetParent !== null) {
            e.focus();
            return {ok: true, type: 'contenteditable', cls: e.className};
        }
    }
    return {ok: false};
})()
"""
```

**核心**: JS 内部 `focus()` 一次搞定, 不需要 nodeId

### 武器3: Enter穿透 (绕过 Shadow DOM 按钮)
```python
# Enter 是全局事件, 会冒泡到 form.onSubmit, 不需要点按钮
for t in ["keyDown", "keyUp"]:
    await cdp.send("Input.dispatchKeyEvent", {
        "type": t, "modifiers": 0, "timestamp": 0,
        "text": "\r", "unmodifiedText": "\r",
        "key": "Enter", "code": "Enter",
        "keyCode": 13, "windowsVirtualKeyCode": 13,
        "location": 0, "isKeypad": False, "isAutoRepeat": False
    })
```

### 武器4: 智能滚屏 (逼出虚拟列表内容)
```python
async def hermes_scroll_to_bottom(cdp, timeout=60, settle=2.0):
    """自动找可滚动容器 (virtual-list), 滚到底再回顶, 强制渲染"""
    start = time.time()
    last_height = 0
    stable_count = 0
    
    while time.time() - start < timeout:
        # 找最大可滚动容器
        find_expr = """
        (() => {
            // 优先找 virtual-list (DeepSeek模式)
            const virtuals = document.querySelectorAll('[class*="virtual-list"], [class*="VirtualList"]');
            for (let v of virtuals) {
                if (v.scrollHeight > v.clientHeight + 10) {
                    return {sel: 'virtual', scrollH: v.scrollHeight, cls: v.className};
                }
            }
            // 找 scrollHeight 最大的可见div
            const all = document.querySelectorAll('div, main, section, article');
            let maxH = 0, target = null;
            for (let d of all) {
                if (d.scrollHeight > d.clientHeight + 10 && d.clientHeight > 200) {
                    if (d.scrollHeight > maxH) { maxH = d.scrollHeight; target = d; }
                }
            }
            if (target) return {sel: 'div', scrollH: target.scrollHeight, cls: target.className?.substring(0,60)};
            return {sel: 'window', scrollH: document.documentElement.scrollHeight};
        })()
        """
        r = await cdp.send("Runtime.evaluate", {"expression": find_expr, "returnByValue": True})
        h = r.get("result",{}).get("result",{}).get("value", {}).get("scrollH", 0)
        
        if h == last_height or h == 0:
            stable_count += 1
            if stable_count >= 2: break
        else:
            stable_count = 0
            last_height = h
        
        # 滚到对应容器底部
        await cdp.send("Runtime.evaluate", {
            "expression": """
            (() => {
                const all = document.querySelectorAll('div, main, section, article');
                let maxH = 0, target = null;
                for (let d of all) {
                    if (d.scrollHeight > d.clientHeight + 10 && d.clientHeight > 200) {
                        if (d.scrollHeight > maxH) { maxH = d.scrollHeight; target = d; }
                    }
                }
                if (target) target.scrollTop = target.scrollHeight;
                else window.scrollTo(0, """ + str(h) + """);
            })()
            """,
            "userGesture": True
        })
        await asyncio.sleep(settle)
    
    # 滚回顶
    await cdp.send("Runtime.evaluate", {
        "expression": "(document.querySelector('[class*=virtual-list]') || {}).scrollTop = 0; window.scrollTo(0, 0);",
        "userGesture": True
    })
```

## 完整流程
```
1. Page.navigate → URL
2. DOM.enable + JS聚焦 (textarea或contenteditable)
3. hardcore_type 逐字输入
4. Enter keyDown+keyUp 发送
5. asyncio.sleep(30) 等待AI生成
6. hermes_scroll_to_bottom 智能滚屏 (找virtual-list)
7. Accessibility.getFullAXTree 读所有AI回复
8. 必要时 screencapture + vision_analyze
```

## 实测效果 (6个AI站点)
| 站点 | 输入方式 | 滚屏高度 | AX回复字符 | 备注 |
|------|---------|---------|-----------|------|
| DeepSeek | `Input.dispatchKeyEvent` 逐字 | 22864px | 2876字 | ❌ ta.value=不触发React；✅ 逐字可发 |
| 豆包 | textarea (direct value) | 19379px | 1468字 | ✅ ta.value=成功 |
| ChatGLM | textarea (direct value) | - | 完整分析 | ✅ ta.value=成功 |
| Gemini | contenteditable | 4022px | 38字 | ❌ textarea在webview跨域 |
| Grok | tiptap | 1085px | 99字 | ❌ Cloudflare拦截 |
| ChatGPT | contenteditable | - | 旧回答残留 | ⚠️ 需先focus |

## 快速输入方案（绕过逐字打字）
对于大多数现代 AI 站点（DeepSeek、豆包、ChatGLM），`ta.value=` + `dispatchEvent` 直接赋值比逐字输入快且稳定：

```javascript
(function(){
  const ta = document.querySelector('textarea');
  if(ta){
    ta.value = '我们电脑配置免费不要OCR能直接读取屏幕内容吗';
    ta.dispatchEvent(new Event('input', {bubbles:true}));
    ta.dispatchEvent(new Event('change', {bubbles:true}));
    return 'ok';
  }
  return 'no textarea';
})()
```

**触发流程**：`value` 赋值 → `input` 事件（React onChange） → `change` 事件 → AI 网站自动聚焦/发送按钮变亮。

**适用站点**：DeepSeek ✅、豆包 ✅、ChatGLM ✅、ChatGPT ❌（需要 contenteditable）、Gemini ❌（webview 跨域）。

**不适用原因**：
- **ChatGPT**：ProseMirror 受控组件，直接 value 赋值被 React 忽略
- **Gemini**：textarea 在 webview iframe 里（跨域），父级 document.querySelector 拿到 null

**发送**：赋值成功后 `Input.dispatchKeyEvent(key='Enter')` 即可，不需要 .click()。

## 关键环境
- Chrome: 系统 Chrome + debug port 9333 启动
- Python: 3.x + websockets 库
- 不需要 Playwright, 不需要 Docker, 不需要 OCR (Vision 备选)

## 调试清单
- 字符重复 → keyDown.text 必须空
- 按钮没反应 → 用 Enter 穿透, 不要.click()
- 找不到textarea → 试 contenteditable (ProseMirror/tiptap)
- 滚屏无效 → 找 virtual-list 容器, 别用 window
- Shadow DOM → 用 JS 内部 focus(), 不用 querySelector
- TAB ID 会变 → 每次从 http://localhost:9333/json 重新拿

## 武器5: 视觉点选 (vision_click) — 不依赖 selector
当按钮没有稳定 id/class/role, 或在 Shadow DOM 内, 用元素文字+坐标兜底:
```python
# 抓所有可交互元素 + 坐标
elements = await vision_click(target_ws, tab_id, mode="list")
# 返回 [{tag, text, x, y, hint}, ...]

# 关键词匹配点击 (语义锚定)
await vision_click(target_ws, tab_id, mode="click", keyword="开启新对话")

# 坐标直接点击 (兜底)
await vision_click(target_ws, tab_id, mode="click", coord="130,90")
```

**匹配算法 (按分排序)**:
- 完全匹配 +10, 开头 +5, 包含 +2
- 是按钮 +2 (有 `cursor:pointer` 或 button/a/role=button)
- 侧边栏词惩罚 -5 (含 "对话"/"chat"/"new" 但在 sidebar 容器内)
- 短文本 +1 (≤6字优先, 按钮通常短)

**坑**: 关键词匹配会被侧边栏聊天列表干扰 (e.g. "新对话" 命中10个), 优先用 `coord="x,y"` 兜底.

## 武器6: 反应堆循环 (reactor) — Sense→Think→Act
持续监控一个 tab, 周期性 Sense 抓状态, Think 决策, Act 执行:
```bash
python3 hermes_reactor.py deepseek 15  # 监控 deepseek tab, 跑 15 秒
```

**三层职责**:
- **Sense**: 抓 url/textarea 数/body 长度, 廉价高频
- **Think**: 把 Sense 输出给 LLM, 拿到行动列表 (e.g. `["DETECT: 找到输入框", "READY: 可输入"]`)
- **Act**: 执行 Think 决定的 CDP 动作 (聚焦/输入/发送/截屏/读回复)

**测试输出**:
```
[周期01] 0.0s
  📡 Sense: url=https://chat.deepseek.com/ ta=1 bodyLen=427
  🧠 Think: ['DETECT: 找到输入框']
```

**下一步演化**:
- Sense 加 Network 拦截 (天眼) 拿 AI 增量回复
- Think 用 MiniMax 实时解析 patch 协议
- Act 边收边决策 (流式双工, 不等 FINISHED)

## 调试清单 (扩充)
- 字符重复 → keyDown.text 必须空
- 按钮没反应 → 用 Enter 穿透, 不要 .click()
- 找不到textarea → 试 contenteditable (ProseMirror/tiptap)
- 滚屏无效 → 找 virtual-list 容器, 别用 window
- Shadow DOM → 用 JS 内部 focus(), 不用 querySelector
- TAB ID 会变 → 每次从 http://localhost:9333/json 重新拿
- 侧边栏干扰 vision_click → 用 coord="x,y" 直接点击
- 多 tab 抢 ws.recv() → 单一 recv 循环 + Queue 分发 (见下方"关键坑")

## 参考资料
- `references/network_sniffer.py` — 完整可运行的天眼模式脚本 (Network拦截+SSE解析)
- `references/multi-site-orchestration.md` — 多AI站点对比的配置/坑/优先级
- `references/vision-click.md` — 视觉点选原理 + 匹配算法 + 坐标兜底
- `references/reactor-loop.md` — 反应堆 Sense/Think/Act 详解 + 演化路径
- `references/screen-reading-without-ocr.md` — **2026-06-02 实测：免OCR三大机制 + 各站结果**
- `scripts/hermes_vision_click.py` — 162行, 元素列表+关键词/坐标点击
- `scripts/hermes_reactor.py` — 155行, Sense→Think→Act 循环框架
- `scripts/hermes_human_biometrics.py` — **贝塞尔鼠标轨迹 + 生物识别打字律动**独立模块，支持CDP集成或独立测试

## 进阶: Network天眼模式 (拿到最原始的AI回复)
CDP `Network.enable` + 监听 `Network.responseReceived` + `Network.loadingFinished`,
`Network.getResponseBody` 拿到服务器返回的原始 JSON/SSE, 跳过前端渲染.

### 关键坑: websockets 库不能并发 recv
**症状**: 监听任务和 send() 抢 ws.recv(), 抛 `ConcurrencyError`.
**解法**: 单一 recv 后台循环 + 队列分发, 用 future 等待响应id.

```python
class Eyes:
    def __init__(self, ws):
        self.ws = ws
        self.msg_id = 0
        self.pending = {}  # msg_id -> Future
        self.events = asyncio.Queue()
        self.running = True

    async def start(self):
        return asyncio.create_task(self._loop())

    async def _loop(self):
        while self.running:
            try:
                raw = await self.ws.recv()
                data = json.loads(raw)
                mid = data.get("id")
                if mid is not None and mid in self.pending:
                    self.pending[mid].set_result(data)
                else:
                    await self.events.put(data)
            except: return

    async def send(self, method, params=None):
        self.msg_id += 1
        fut = asyncio.get_event_loop().create_future()
        self.pending[self.msg_id] = fut
        await self.ws.send(json.dumps({"id": self.msg_id, "method": method, "params": params or {}}))
        return await fut
```

### 关键坑: getResponseBody 在流结束前是 0 字节
**症状**: SSE流还在传输时调用 getResponseBody 拿到 0 字节.
**解法**: 等 `Network.loadingFinished` 事件触发后再 getResponseBody.

### DeepSeek 用了 patch 协议 (不是 OpenAI delta 累加)
DeepSeek SSE 不是 `choices[].delta.content`, 而是 patch 指令:
```
data: {"v":{"response":{"fragments":[{"id":2,"type":"RESPONSE","content":"1",...}]}}}
data: {"p":"response/fragments/-1/content","o":"APPEND","v":" +"}
data: {"v":" "}
data: {"v":"1"}
data: {"v":" ="}
data: {"v":"2"}
```
**解析器**:
- OpenAI/ChatGPT: 累加 `choices[].delta.content`
- DeepSeek: 累加所有 `data: {"v": "x"}` 里的 v 字符串
- 老格式兜底: 取最大的 `v.response.fragments[].content`

### DeepSeek 防御: Proof of Work (create_pow_challenge)
发问题前会先请求 `/api/v0/chat/create_pow_challenge` 拿 PoW 挑战, 答对才能发.
通过 CDP 输入 + Enter 自动走通 PoW, 手动 fetch 会被拒 (429).
