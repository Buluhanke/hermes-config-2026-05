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
```

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

**核心**：所有时长均为正态分布（非匀速）+ 标点后追加"大脑组织语言的呼吸停顿"，彻底消除机器人匀速特征。**keyDown.text="" 必须空**（硬核发现）。

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
**适用**（2026-06-03 重新核对）：豆包 ✅、ChatGLM ✅、**DeepSeek ❌ 必须用逐字**（React state 不接管 value=）
**不适用**：ChatGPT（ProseMirror 受控组件，value 被忽略）、Gemini（textarea 在 webview 里跨域）

### ⚠️ DeepSeek 实战坑：ta.value= 设值成功但按钮点击无效
实测（2026-06-02）：`ta.value=` 能把文字写进 textarea，`btns[8]` 按钮能 click 出 "clicked"，但 AI 就是不回复。

**根因**：DeepSeek 的 React 输入框在 `ta.value=` 后没有真正被"用户输入"事件激活——缺少光标位置变化事件 + input 事件的完整性验证，按钮虽然看起来可点（`ds-button--disabled` 的 disabled 属性为 null），但 React 内部状态未更新，点击后 textarea 被清空。

**已验证有效的解法**：
1. **聚焦 + `Input.dispatchKeyEvent` 逐字输入**（正确流程）：
   ```javascript
   document.querySelector('textarea').focus();
   ```
   然后用 `Input.dispatchKeyEvent(type='keyDown', text='字', key='字')` 逐字触发 React onChange
2. **Enter 兜底**：`Input.dispatchKeyEvent(key='Enter')` 比按钮点击更可靠

**已验证失效的解法**：
- `ta.value=` + `dispatchEvent(new Event('input', {bubbles:true}))` → DeepSeek 收到事件但 React 状态未更新
- 按钮 `btns[8].click()` → 点击返回 "clicked" 但不触发发送
- `ta.value=` + `dispatchEvent(new Event('change', {bubbles:true}))` → 同上

**ChatGLM 可以用 ta.value=**（已实测成功），**DeepSeek 必须逐字输入**。

## 主动寄生式 CDP 脚本规范（2026-06-03 确立）

**三大铁律**：不杀进程、不拉起浏览器、不擅自创建 tab。

所有 CDP 自动化脚本必须遵循。完整实现参考 `chrome-cdp-automation` skill 的 `references/ai-site-input-strategies.md`。以下是规范核心：

### 端口扫描 — 必须先嗅探再连接（2026-06-03 新增）

不要硬编码单一端口。Chrome 可能在 9333、9444 或 9222 上：

```python
CDP_PORTS = [9333, 9444, 9222]

def detect_cdp_port() -> tuple[str, int] | None:
    import urllib.request, json
    for port in CDP_PORTS:
        try:
            tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3).read())
            if tabs: return ("127.0.0.1", port)
        except Exception: continue
    return None
```

**已知端口场景**：
- 9333：用户手动 `open -a "Google Chrome" --args --remote-debugging-port=9333`
- 9444：`launch_chrome_cdp.sh`（pkill → open → --args --remote-debugging-port=9444）
- 9222：Chrome DevTools 默认值

**launch_chrome_cdp.sh 可靠性注记（2026-06-03）**：模式 `pkill -9 -f "Google Chrome" && open -a "Google Chrome" --args --remote-debugging-port=9444` 并不能保证新 Chrome 使用 9444——`open -a` 可能激活了未彻底杀死的旧进程。如果 9444 扫描失败则回退到 9333。

**关键要求**：
1. **启动前必嗅探** — `find_target()` 返回 None 则报错退出
2. **输入前必清空** — `clear_input(selector)` 每次填入前强制清空 textarea
3. **零生命周期** — 脚本只做 CDP 命令发送，不执行 `pkill`/`kill`/`open -a`

```python
def clear_input(self, selector: str) -> bool:
    self.evaluate(f"document.querySelector('{selector}')?.focus()")
    time.sleep(0.1)
    self.evaluate(
        f"var el = document.querySelector('{selector}');"
        f"if(el){{ el.value = '';"
        f"  el.dispatchEvent(new Event('input',{{bubbles:true}}));"
        f"  el.dispatchEvent(new Event('change',{{bubbles:true}}));}}"
    )
    val = self.get_value(selector)
    return len(val) == 0
```

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

**核心**：JS 内部 `focus()` 一次搞定, 不需要 nodeId

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

**注意 2026-06-03 实际踩坑**：`modifiers` 必须 int32 不是字符串, `clickCount` 同理，`windowsVirtualKeyCode` 要数字。如果遇到 "Invalid parameter" 错误，先检查这些类型。

### 武器4: 智能滚屏 (逼出虚拟列表内容)
```python
async def hermes_scroll_to_bottom(cdp, timeout=60, settle=2.0):
    """自动找可滚动容器 (virtual-list), 滚到底再回顶, 强制渲染"""
    start = time.time()
    last_height = 0
    stable_count = 0

    while time.time() - start < timeout:
        find_expr = """
        (() => {
            const virtuals = document.querySelectorAll('[class*="virtual-list"], [class*="VirtualList"]');
            for (let v of virtuals) {
                if (v.scrollHeight > v.clientHeight + 10) {
                    return {sel: 'virtual', scrollH: v.scrollHeight, cls: v.className};
                }
            }
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

## 实测效果 (6个AI站点, 2026-06-03 重新核对 — 2026-06-03 Grok 再次失败)
| 站点 | 输入方式 | 发送方式 | 回复读法 | 状态 |
|------|---------|---------|---------|------|
| DeepSeek | `Input.dispatchKeyEvent` 逐字 ✅ (React 受控) | `Input.dispatchKeyEvent` Enter ✅ | `document.body.innerText` ✅ | ✅ 完全通过 |
| 豆包 | `Input.insertText` ✅ (sync-input-engine 突破) | send-btn click ✅ | `document.body.innerText` growth ✅ | ✅ 完全通过 |
| ChatGLM | `Input.insertText` ✅ | `Input.dispatchKeyEvent` Enter ✅ | `document.body.innerText` ✅ | ✅ 完全通过 |
| Grok | ⚠️ **复杂** — 旧对话 el.click() 触发但命中错对话；新对话 React state 不接管 (见下) | — | — | ⚠️ 不可靠 |
| ChatGPT | `Input.insertText` on `pmViewDesc.contentDOM` ✅ | `composer-submit-btn` click ✅ | `document.body.innerText` ✅ | ✅ 完全通过 |
| Gemini | 物理外挂 Cmd+V + Return ✅ (绕过 zone.js) | 同上 | `document.body.innerText` ✅ | ✅ 完全通过 (AppleScript 路径) |

### ⚠️ 豆包/字节跳动系 Cookie 加密坑（2026-06-04 重大发现）

**症状**：所有豆包关键 session cookie（`sessionid`, `sid_tt`, `odin_tt`, `__tea_session_id` 等）的 `value` 字段为空，`encrypted_value` 非空。

**根因**：Chrome（macOS）对 `*.doubao.com`、`*.bytedance.com` 等字节系域名使用 **OS X Keychain 主密钥**加密 cookie。加密密钥绑定到 Chrome 实例（每个 Chrome.app 实例启动时生成独立 Keychain 身份），复制 cookie 文件到另一个 profile 后，新 Chrome 实例无法用**自己的** Keychain 解密**别人的**加密值。

**验证方法**：
```bash
# 查看 doubao.com cookie 的加密状态
sqlite3 ~/.hermes/chrome-debug/Default/Cookies "SELECT host_key, name, value, encrypted_value FROM cookies WHERE host_key LIKE '%doubao%';"
# value='' 且 encrypted_value 非空 → Keychain 加密，复制无效
```

**Session Storage 中有数据，但不够用**：
- `Session Storage/000003.log`（LevelDB）中存在 `namespace-d48d_49d5_9eb3_73dd0a64061f-https://www.doubao.com/` 和 `__tea_session_id` 字段
- 这证明豆包的 session **信息**存在，但 Token 本身存在服务端，设备 UUID 只是关联标识
- 换设备（新的 debug profile）=新用户，这是抖音/豆包系的登录态设计逻辑

**解法（按可靠性排序）**：

| 方案 | 原理 | 状态 |
|------|------|------|
| 用真实 Chrome.app 启动 debug profile | 真实 Chrome 用自己的 Keychain 解密自己的加密 cookie | ✅ 理论上可行，但 Session Storage token 仍为设备级 |
| 在 debug Chrome 中**重新登录一次**（推荐） | 豆包 session token 是设备 UUID，换设备重新登录即可 | ✅ 简单可靠，cookies 写入后明文化 |
| 复制 Session Storage 文件到 debug profile | session 信息在 LevelDB 里，可能被新 Chrome 读取 | ⚠️ 未验证，ByteDance 可能检查设备签名 |
| 用 Playwright 操作用户 Chrome | CDP 直连用户已登录的 Chrome，不走复制 | ⚠️ 需要用户 Chrome 开启 debug 端口 |

**登录方式提示**：豆包/抖音系大概率是手机号+验证码登录，或抖音 App 扫码登录（字节系常见），不是 Google/Apple 联合登录。

**预防**：如果任务是"保持豆包登录态"，不要尝试 cookie 文件复制，直接在 debug Chrome 中完成一次登录即可。

### ⚠️ 豆包消息区 Shadow DOM 加密导致 innerText 读不到（2026-06-05 新发现）

**症状**：
- `document.body.innerText` 只能读到侧边栏和输入框，AI 回复内容完全空白
- `querySelectorAll` 所有 div/span/textnode 都返回空或只有侧边栏内容
- React 虚拟列表 `[role="article"]` 或 `[class*="message"]` 返回 0 个匹配

**根因**：豆包的消息区域（对话气泡）渲染在**加密 Shadow DOM** 里，字节系用 `attachShadow({mode: 'closed'})` 将对话内容封在 shadow root 内，外部 JS 无法通过 `innerText` / `querySelector` / `TreeWalker` 访问到。

**实测无效的读取方式**：
```javascript
// ❌ 全返回空
document.body.innerText
// ❌ 返回空数组
document.querySelectorAll('[role="article"]')
// ❌ TreeWalker 摸不到 shadow root
document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false)
```

**✅ 解法：Vision 截图兜底**
当 innerText 读不到时，用 `browser_vision` 截图 + VLM 读取：
```python
# 先确认 innerText 是否真的为空（排除流式输出未完成）
r = browser_console(expression="document.body.innerText.length")
if r['result'] < 500:  # 正常侧边栏+欢迎语约300字符
    # 兜底 vision
    browser_vision(question="请完整读取页面上AI回复的所有文字内容")
```

**注**：此问题影响**读取**，不影响**输入**——输入框和发送按钮仍在主文档，输入发送流程与普通站点相同。

### ⚠️ Grok 实战坑（2026-06-03 实测，纠正旧"✅ 完全通过"声明）

**症状**：textarea 是 Next.js 流式占位符（`y=0, h=16px` 极小尺寸），plain HTML 无 `__reactProps`，所有派发方案都拿不到 React fiber。

**实测失败的 5 条路径**：
1. `ta.value=` + `dispatchEvent('input')` → React state 不接管，按钮永远 disabled
2. `ta.focus()` + `Input.insertText` → value 写入 18 字符但 React onChange 不触发
3. 找 parent `__reactProps` → parent 是 BODY，`__reactProps` 只有 `className, children`，无 onChange
4. `form.requestSubmit()` → 返回 "submitted" 但 Grok 无响应
5. `ta.closest('form')` → null（无 form 包裹）

**唯一意外的"成功"**：el.click() 提交按钮在 `grok.com/c/<旧对话 uuid>` 旧对话 tab 上**真的**触发了一次 Grok 回复（"M?"），证明这条路整体通，只是命中错了 tab。/chat/new tab 上的提交按钮 el.click() 没看到回应。

**根因猜想**：Grok 的 chat input 在 cross-origin iframe 内（不是本地 Stripe iframe，是另一个 x.com/x.ai 子域），CDP 顶层 document 触达不到真实 React state；Next.js 流式占位符 textarea 是 proxy，真正的输入在 hydration 后的 React Portal。

**临时解法**：
- 在已有旧对话里续写（这条路已确认可发送）
- 或换用 Gemini（已通过 AppleScript 物理外挂解决）

### 自我矛盾修正（2026-06-03）
本表 `DeepSeek — Input.insertText` 与下方"DeepSeek 实战坑"段矛盾。**真实结论**：
- `ta.value=` + `dispatchEvent` → 写入成功但 React state 不接管（实测）
- `Input.dispatchKeyEvent` 逐字输入 → 唯一可靠路径
- 之前的"✅"声明是误报

**修正后的"快速输入"适用范围**：豆包 ✅、ChatGLM ✅、**不含 DeepSeek**。

### 豆包 2026-06-03 突破
ByteDance `sync-input-engine-infra-interactive` 的内部状态曾导致所有派发方式失效。2026-06-03 实测：`Input.insertText` 触发完整 keydown/keyup/char 事件链 → React 状态更新 → 发送按钮激活。**成功断言**：
- `ta.value` 从问题长度变为 0（已发送）
- URL 从 `/chat/` 跳转到 `/chat/<uuid>`（新对话创建）
- `body.innerText` 从 ~610 增长到 ~3158+ 字符（回复生成中）
- 完整回复约 30-60 秒后出现在 DOM

### Gemini 协议层限制 — AppleScript 物理外挂解法（2026-06-03 新增）
Gemini 使用 Quill 编辑器 (`.ql-editor`) + Angular zone.js。`Input.dispatchKeyEvent` 的 `browser_cdp` 工具缺少 `nativeVirtualKeyCode: Int32` 字段，无法触发 Angular 的 `ɵzone_symbol__ZENUNBOUND__` 事件链。这是工具栈协议层约束，前端代码无法修复。

**解法**（已实测成功，完整 OCR 方案回复存档到 `/tmp/grok_gemini_physical_hack_20260603.md`）：
1. `osascript` 激活 Chrome 窗口
2. `pbcopy` 写入剪贴板
3. AppleScript `keystroke "v" using command down` 触发 Cmd+V（绕过 zone.js）
4. `keystroke return` 发送

## 关键环境
- Chrome: 系统 Chrome + debug port 9333 启动
- Python: 3.x + websockets 库
- 不需要 Playwright, 不需要 Docker, 不需要 OCR (Vision 备选)

**browser.cdp_url 配置**：Hermes 的 `browser_navigate` 等工具默认走内建 headless Chromium（触发 Cloudflare）。通过 `hermes config set browser.cdp_url ws://127.0.0.1:9333` 指向你的 debug Chrome 后，这些工具直接驱动你的真实 Chrome 登录态。详见 `ai-site-browser-e2e` skill。

## 调试清单
- 字符重复 → keyDown.text 必须空
- 按钮没反应 → 用 Enter 穿透, 不要.click()
- 找不到textarea → 试 contenteditable (ProseMirror/tiptap)
- 滚屏无效 → 找 virtual-list 容器, 别用 window
- Shadow DOM → 用 JS 内部 focus(), 不用 querySelector
- TAB ID 会变 → 每次从 http://localhost:9333/json 重新拿
- **Grok 特别坑（2026-06-03）**：textarea 是 Next.js 流式占位符，`y=0, h=16px` 极小，所有 `__reactProps` 派发都拿不到；cross-origin iframe 触达不到；用 AppleScript 物理外挂或换 Gemini
- **CDP 参数类型严格（2026-06-03）**：`modifiers` 必须 int32 不是字符串, `clickCount` 同理, `windowsVirtualKeyCode` 要数字但 `modifiers` 不要
