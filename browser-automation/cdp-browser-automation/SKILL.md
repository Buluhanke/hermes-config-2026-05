---
name: cdp-browser-automation
description: Chrome DevTools Protocol 浏览器自动化 — 6 大 AI 网站端到端验证实战技能库
trigger: "CDP 控制、browser_cdp、浏览器自动化、6 大 AI 网站、寄生 Chrome、全网联网搜索、browser.cdp_url 配置为空、Chrome debug 端口 9333 未被使用"
---

# CDP 浏览器自动化实战 — 6 大 AI 网站端到端验证

## 核心能力
通过 Chrome DevTools Protocol 控制本地已登录 Chrome，寄生已有 tab，实现：
- 全网 AI 网站联网搜索与知识采集
- 跨平台内容提取（ProseMirror/Quill/React fiber/Semi Design）
- 零新浏览器启动，复用登录态，端到端存档

## 工具栈
- `browser_cdp` — 主工具，CDP 协议操作 Chrome
- 端点：`http://127.0.0.1:9333/json/version` 取 browser-level WS URL
- 端口：9333（已登录 6 个 AI 网站 tab）

## 6 大 AI 网站编辑器类型与输入策略

| 站点 | 编辑器类型 | 输入节点选择器 | 发送按钮策略 |
|------|-----------|--------------|------------|
| ChatGPT | ProseMirror | `#prompt-textarea .ProseMirror` | `.composer-submit-btn` click |
| DeepSeek | 普通 textarea | `textarea[placeholder="给 DeepSeek 发送消息 "]` | `div[role="button"].ds-button--primary` (备选) |
| ChatGLM | textarea | `textarea` | Enter key dispatch (fallback 终极手段) |
| Grok | React fiber | `textarea` (parentElement 取 __reactProps) | `button[aria-label='提交'].click()` |
| 豆包 | Semi Design sync-input-engine | `textarea[placeholder="发消息..."]` | `[data-srategy='send']` JS click |
| Gemini | Quill | `.ql-editor` | Enter key dispatch |

## 关键发现（2026-06-03 实战）

### browser WS URL 来源
从 `http://127.0.0.1:9333/json/version` 取 `webSocketDebuggerUrl`（格式：`ws://127.0.0.1:9333/devtools/browser/UUID`），不要从 tab WS URL 替换（某些 Chrome 版本返回 404）

### Target.createTarget 无宽高
Grok 报错 "position can only be set for new windows"，创建新 tab 时不要传 `width/height` 参数

### CDP result 嵌套
`r.get("value")` 直接取（`Runtime.evaluate` 返回 `result.result {type, value}`），不要多套一层 `result`

### 豆包特殊性
Semi Design `sync-input-engine-infra-interactive` 组件：
- `Input.insertText` 有追加副作用（每次调用累加在原文本后）
- 用 JS click 触发发送
- React state 在某些 CDP 派发方式后会损坏

### Grok React fiber 策略
- textarea 自己没有 `__reactProps`
- 从 parentElement 取 `__reactProps$***`（加密 key）
- `nativeInputValueSetter` 写入 textarea
- 合成事件结构必须带 `nativeEvent` 字段

### ChatGLM Enter 提交
`button.send` click + JS click 均失败，Enter key dispatch 是最终手段

### Gemini Quill 编辑器
- `.ql-editor` 清空 textContent + insertText 触发 Quill 内部事件
- 不走 `Input.dispatchKeyEvent`

## 标准化流程

```python
# 1. 嗅探 tab
tabs = browser_cdp(method="Target.getTargets", params={})
# 找目标站点 tab，不存在则用 Target.createTarget 新建

# 2. 连接 browser-level WS
browser_ws = requests.get(f"http://127.0.0.1:9333/json/version").json()["webSocketDebuggerUrl"]
# 连接后的 WS 用 Target.setSubscribe 或者直接发 Target.attachToTarget

# 3. 等待输入框就绪
browser_cdp(method="Runtime.evaluate", params={
  "expression": "document.querySelector('textarea')"
})

# 4. 清空输入框
browser_cdp(method="Runtime.evaluate", params={
  "expression": "document.querySelector('textarea').value=''"
})

# 5. 填入文本（editor_type 分支）
# - textarea: Input.insertText
# - quill: .ql-editor.textContent = '' 然后 insertText
# - react_fiber: nativeInputValueSetter + 合成事件

# 6. 发送（多策略降级）
# 主按钮 click → JS click → Enter key dispatch

# 7. 等待回复稳定（轮询 body 变化）
```

## 参考知识库
- `references/mac-ocr-knowledge-base.md` — Mac OCR/视觉识别 5站跨测综合知识库（含 Vision/Accessibility/ocrtool-mcp/uitag/EasyScreenOCR 详解）
- `references/browser-cdp-url-config.md` — **browser.cdp_url 配置要点**（2026-06-04 新增：为什么 local Chrome 9333 没有被使用，根因是 config.yaml 里 `browser.cdp_url: ''` 为空，修复方法是添加 `ws://127.0.0.1:9333`）

## Chrome 148+ event 帧坑（cross-ref 2026-06-05）

Chrome 148+ 在 ws 上**主动 push event 帧**（`Runtime.executionContextCreated` / `Page.frameNavigated` / `Target.targetInfoChanged` 等）。本 skill 现有的"标准化流程"里 `Runtime.evaluate` 是单次 `recv()`，**没踩这个坑是因为时序**（CDP 总先发 command response 再发 event）；**一旦 addScript 后**或**多 tab 并发**必踩——`ws.recv()` 拿到的第一个消息是 event，访问 `result['result']['value']` 直接 `KeyError: 'result'`。

**修法**: 用 id 匹配循环跳过 event 帧。完整 `CDPSession` 类 + 详细坑见 `browser-automation/anti-detection-stealth` 的"方式 4: 持久 stealth"段和 `references/2026-06-05-stealth-persistent-inject.md`。

本 skill 的所有"标准化流程"代码示例**未来要加 `sendrecv` helper**，但旧示例先不动（仍能工作，只是 batch 注入场景会失败）。

## 存档路径
`/tmp/hermes_bot_{site}_{timestamp}.txt`

### Gemini 双 tab 陷阱
Gemini 在 Chrome 里同时存在 **webview** (`gemini.google.com/glic?hl=zh-CN`) 和 **page** (`gemini.google.com/app`) 两个 target。脚本必须优先匹配 `.app` URL，否则会拿到 webview（不可交互）。在 `find_or_create_target` 的 URL 匹配逻辑中要确保优先精确匹配。

### Grok Cloudflare Turnstile 拦截
当 Grok 显示"请稍候…"时，说明页面正在做 Cloudflare Turnstile 人机验证，此时 `textarea` 不存在。等待 title 变成实际对话标题后再继续。如果遇到 challenge 页面，需手动在浏览器中完成验证后才能继续自动化。

### Gemini 编辑器
Gemini 真实编辑器是 Quill（`.ql-editor`），但选择器 `[data-testid='prompt-input']` 已过时。正确选择器：`.ql-editor`
**通过 `browser_type` + `browser_click` 已验证工作正常（2026-06-04）**

## 常见陷阱

### 并行执行：terminal 不支持 `&` 后台化
```bash
# ❌ 报错：Foreground command uses '&' backgrounding
python hermes_web_bot_cdp.py chatgpt &
python hermes_web_bot_cdp.py deepseek &

# ✅ 正确：分两次 terminal 调用，sequential 执行
# 或者用 Python subprocess + notify_on_complete
```

### Tab 找不到时自动重建
`find_or_create_target` 会自动用 `Target.createTarget` 新建 tab，不存在则直接创建，无需手动干预。

### DeepSeek 备选按钮
主按钮 `[data-testid="send-button"]` 失败时，降级到 `div[role="button"].ds-button--primary`。

## 浏览器视觉缓存加速（2026-06-05 新增）

**复用本 skill 的 CDP 接线 + 视觉理解结果缓存层, 避免重复 VLM 调用**。

详见 `vision-cache` skill。当前默认脚本：`~/.hermes/scripts/vision_cache_browser.py`

**关键坑点**（从实现过程中踩出）：

### 坑 1: Python `hash()` 跨进程不稳定
DOM signature 计算后, **不能**用 Python 内置 `hash()` 函数做 key:
```python
# ❌ 错: 每次进程启动值都不同 (PYTHONHASHSEED 随机)
dom_hash = str(hash(dom_sig))

# ✅ 对: 用 sha256
import hashlib
dom_hash = hashlib.sha256(dom_sig.encode('utf-8')).hexdigest()[:16]
```

### 坑 2: VLM 模型名要对齐本地实际
```python
# ❌ 错: 假设 "qwen3-vl:latest" 存在
# ✅ 对: 先 curl http://localhost:11434/api/tags 查实际装的
# 本地实测: ["qwen3-vl:2b", "moondream:latest", "qwen2.5:1.5b"]
```

### 坑 3: 注入端不要用 String() 包装
```javascript
// ❌ 错: JSON.stringify 把 String(undefined) 序列化成 "undefined" 字符串
//      Python 端 isinstance(int) 永远 false
// ✅ 对: 直接传原值, Python 端做宽松判断
```

### DOM signature 模板 (复用)

```javascript
(() => {
    const sigs = [];
    sigs.push(document.title || '');
    sigs.push(document.body ? document.body.tagName : '');
    sigs.push(document.body ? document.body.children.length : 0);
    sigs.push('nodes=' + document.querySelectorAll('*').length);
    sigs.push('text_len=' + (document.body ? document.body.innerText.length : 0));
    Array.from(document.querySelectorAll('body *')).slice(0, 100)
         .forEach(el => sigs.push(el.tagName));
    document.querySelectorAll('button, a, input, textarea, select, [role=button]')
            .forEach(el => sigs.push(el.tagName + ':' + (el.textContent || '').trim().slice(0, 30)));
    return JSON.stringify({
        url: location.href,
        title: document.title,
        dom_sig: sigs.join('|').slice(0, 2000)
    });
})()
```

**为什么这样设计**: 视觉理解 (VLM) 的目的是"理解页面在表达什么", 不是像素比对。结构变了 = 内容变了, 需要重新理解。详见 `vision-cache/references/vision-cache-design-rationale.md`。