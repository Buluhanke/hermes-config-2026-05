# AI Site Input Strategies — Deep Dive Notes (2026-06-03)

## ChatGPT — ProseMirror `.pmViewDesc.contentDOM`

The `#prompt-textarea` is a **wrapper DIV** with `class="ProseMirror"`. The real editing node is inside it at `.pmViewDesc.contentDOM`.

```javascript
// Finding it
const contentDOM = document.querySelector('#prompt-textarea .pmViewDesc.contentDOM')
// contentDOM is a <div class="ProseMirror-doc"> — the actual ProseMirror document

// Clear before insert (prevents duplicate submission)
contentDOM.textContent = ''
contentDOM.focus()

// Then insertText works
```

**Why wrapper focus fails**: The wrapper div has no actual text insertion point. `Input.insertText` after `wrapper.focus()` → value stays 0, send button stays disabled.

**Send button**: `.composer-submit-btn`. Click, don't Enter.

---

## Doubao — ByteDance SyncInputEngine + React 18

Doubao loads `sync-input-engine-infra-interactive.71f86969.js`. This engine maintains its own input state, completely separate from React fiber.

**The problem**: Engine debounces `onChange` events. `ta.value = 'x'` + `dispatchEvent('input')` → engine ignores it → send button stays disabled.

**The fix**: React fiber `__reactProps` direct call with complete SyntheticEvent. But the event must be complete — missing `nativeEvent` crashes React's event system.

**Complete SyntheticEvent template**:
```javascript
{
  type: 'change',
  bubbles: true,
  cancelable: true,
  defaultPrevented: false,
  isTrusted: true,
  target: ta,
  currentTarget: ta,
  nativeEvent: {
    isTrusted: true,
    data: ''
  },
  isDefaultPrevented: () => false,
  isPropagationStopped: () => false,
  persist: () => {},
  preventDefault: () => {},
  stopPropagation: () => {}
}
```

**CRITICAL — IME lock**: If the user previously used IME composition, React is locked in composition mode and silently drops `onChange`. Must call `props.onCompositionEnd` FIRST to release the lock.

```javascript
// Order matters: compositionEnd → change → input
props.onCompositionEnd(compositionEndEvent)
props.onChange(changeEvent)
props.onInput(inputEvent)
```

**2 textareas**: Doubao has 2 textarea elements. The real input has `placeholder="输入问题..."` and is visible. Use JS pick:
```javascript
const ta = Array.from(document.querySelectorAll('textarea'))
  .find(el => el.offsetParent !== null && !el.readOnly && el.placeholder)
// fallback: the last textarea
```

---

## Grok — Tiptap with `__reactProps` on parentElement

Grok uses Tiptap (same framework family as ProseMirror). The `__reactProps` is on `textarea.parentElement`, NOT on the textarea itself.

```javascript
// WRONG — textarea has no __reactProps
const ta = document.querySelector('textarea')
const key = Object.keys(ta).find(k => k.startsWith('__reactProps'))  // undefined

// CORRECT — look at parentElement
const parent = ta.parentElement
const pkey = Object.keys(parent).find(k => k.startsWith('__reactProps'))
const props = parent[pkey]  // has onChange, onInput, onKeyDown
```

**Send button**: `button[aria-label="提交"]`

**Native value setter** (bypasses React value tracker):
```javascript
const nativeSetter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set
nativeSetter.call(ta, 'question text')
```

---

## DeepSeek — `role="button"` divs, no `<button>` elements

DeepSeek renders buttons as `<div role="button">` instead of `<button>`. The send button:
```javascript
const btns = Array.from(document.querySelectorAll('[role="button"]'))
const sendBtn = btns.find(b =>
  b.classList.contains('ds-button--primary') &&
  b.classList.contains('ds-button--filled') &&
  b.classList.contains('ds-button--circle')
)
sendBtn?.click()
```

**Streaming trap**: After clicking send, `body.innerText` may show ONLY the conversation title for 30-90 seconds. Do NOT abort. Poll until bodyLen is stable for 10+ seconds.

---

## ChatGLM — Standard textarea, direct value injection works

ChatGLM uses a plain `<textarea>`. `ta.value = 'x'` + `dispatchEvent('input')` works fine. No special framework complexity.

```javascript
const ta = document.querySelector('textarea')
ta.value = 'question'
ta.dispatchEvent(new Event('input', {bubbles: true}))
ta.dispatchEvent(new Event('change', {bubbles: true}))
```

Send via Enter keyDown or button click.

---

## Gemini — `<webview>` vs page-tab 两种状态（2026-06-03 实测）

Gemini 有两种渲染状态：

1. **`gemini.google.com/glic`** — 渲染在 `<webview>` 元素里（Chromium 跨进程 iframe），CDP 从外部无法穿透，textarea 不可见
2. **`/app` 路径新建 tab** — `Target.createTarget` 新建的 tab 是 `page` 类型（非 webview），CDP 完全可控

**实测可用工作流**：
```python
# 从 browser-level WS 新建 /app tab（新 tab 是 page 类型，可 CDP 控制）
browser_ws = json.loads(urllib.request.urlopen("http://localhost:9333/json/version").read())["webSocketDebuggerUrl"]
async with websockets.connect(browser_ws) as ws:
    await ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": "https://gemini.google.com/app"}}))
    resp = json.loads(await ws.recv())
    new_tab_id = resp["result"]["targetId"]
```

Gemini（2026-06-03）使用 **Quill 编辑器**（`.ql-editor`），不是 contenteditable：
```python
# Quill 编辑器输入（实测 2026-06-03）
def clear_and_type_quill(cdp, text):
    cdp.send("Runtime.evaluate", {"expression": "document.querySelector('.ql-editor')?.focus()"})
    time.sleep(0.1)
    cdp.send("Runtime.evaluate", {"expression": "document.querySelector('.ql-editor').textContent = ''"})
    cdp.send("Input.insertText", {"text": text})  # 触发真实 keydown/char/keyUp 事件链
```

发送用 Enter keyDown + keyUp（Quill submit 按钮在 shadow DOM 里，Enter 最可靠）：
```python
cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Enter", "code": "Enter", "text": "\r", "keyCode": 13, "location": 0})
time.sleep(0.05)
cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter"})
```

---

## Common Patterns

### Text duplication / truncation root cause
`Input.insertText` **appends** to existing content. If textarea has old text, new text gets appended. Fix: clear before insert.
```javascript
// For standard textarea
el.value = ''
el.dispatchEvent(new Event('input', {bubbles: true}))

// For ProseMirror/Tiptap
document.querySelector('.pmViewDesc.contentDOM').textContent = ''
```

### Completion signal — use bodyLen growth, not buttons
AI sites put "stop generating" button inside Shadow DOM — invisible to CDP. Use `document.body.innerText.length` monotonic growth.
```javascript
let prevLen = 0
let stableCount = 0
while (stableCount < 5) {  // stable for 10s = done
  const len = document.body.innerText.length
  if (len === prevLen) stableCount++
  else stableCount = 0
  prevLen = len
  await new Promise(r => setTimeout(r, 2000))
}
```

### Port scanning before connecting
```python
CDP_PORTS = [9333, 9444, 9222]
for port in CDP_PORTS:
    try:
        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3).read())
        if tabs: break  # found live CDP
    except: continue
```
