---
name: chrome-cdp-automation
description: Drive a real Chrome via DevTools Protocol from Python — bypass Shadow DOM, simulate real keyboard input so React/Vue onChange fires, control AI chat sites (DeepSeek, Grok, Doubao, ChatGPT) without OCR for most tasks. Use when Playwright/Selenium Puppeteer isn't enough, or when you need to reuse an existing Chrome profile's login state.
---

# Chrome CDP Automation

## When to load
- Need to drive a real Chrome (with login cookies intact) from Python/Node
- Target is a modern SPA (React/Vue/Angular) where `input.value = "x"` doesn't trigger handlers
- AI chat site where the reply text is inside Shadow DOM (DeepSeek, Grok, Doubao all do this)
- Mac/Linux box with no Docker, want zero-OCR reading of static structure
- Cookies/SQLite import into Playwright is blocked (decryption needs closed Chrome + pycryptodome)

## The core technique: real keyboard via `char` events

Modern frameworks watch `input` events, not the `.value` property. Setting `.value` directly updates the DOM but fires no `input` event — so the framework's state stays out of sync, the submit button stays disabled, and submission silently fails.

`Input.dispatchKeyEvent` simulates real keyboard at the OS level. There are three event types per character:
- `keyDown` — physical press
- `char` — character typed (this is what the browser inserts into the focused input)
- `keyUp` — physical release

Fire all three, with `text=""` on keyDown — see `references/cdp-react-vue-bypass.md` for the full pattern and the gotcha that makes `text` in keyDown cause double-character input in React.

## Connection essentials
```python
WS_URL = f"ws://localhost:9333/devtools/page/{tabId}"  # 19-char hex tab ID
async with websockets.connect(WS_URL, max_size=20*1024*1024) as ws:
    ...
```

### ⚠️ Chrome 148+ refuses WebSocket without correct Origin header (2026-06-03 verified)

Chrome 148+ added an origin check. Raw Python `websocket-client` and `websockets` from localhost will get **HTTP 403** unless one of these is true:

- Chrome was launched with `--remote-allow-origins=*` (broadest; works for any Origin)
- The client sends `Origin: http://localhost` (or `devtools://devtools`) header

**Tested on Chrome 148.0.7778.216**:
- `websocket-client` from default `ws://localhost:9333/devtools/page/...` → **403 Forbidden** (handshake closes)
- `websockets` library from `ws://127.0.0.1:9333/...` → also **403** (origin mismatch)
- Hermes `browser_cdp` tool → **works** (Hermes layer injects the correct Origin header)

**If you need raw Python**: launch Chrome with `--remote-allow-origins=*` (port 9333 in this user's setup). The Hermes CDP tool already handles this for you, so prefer it.

### ⚠️ Chrome 148+ blocks `/json/new` (2026-06-03 verified)

The HTTP shortcut `POST /json/new` returns **405 Method Not Allowed** in Chrome 148+. Old guides and the legacy `browser-cdp-control` skill still recommend it — **don't follow them**, the endpoint is gone. Use CDP `Target.createTarget` over an existing WebSocket connection instead:

```python
# CORRECT: create new tab via CDP over the browser-level WebSocket
# Get the browser WS endpoint from /json/version
ver = json.loads(urllib.request.urlopen("http://localhost:9333/json/version").read())
browser_ws = ver["webSocketDebuggerUrl"]  # ws://localhost:9333/devtools/browser

async with websockets.connect(browser_ws) as ws:
    await ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": "https://chatgpt.com/"}}))
    resp = json.loads(await ws.recv())
    new_tab_id = resp["result"]["targetId"]  # 36-char UUID
    # Then open a page-level WS to interact with it
    page_ws = f"ws://localhost:9333/devtools/page/{new_tab_id}"
```

The legacy `urllib POST /json/new` + Page.navigate combo no longer works.

- Chrome must be launched with `--remote-debugging-port=9333` and a stable `--user-data-dir` for cookie persistence.
- Get tab list: `urllib.request.urlopen("http://localhost:9333/json")` — note `/devtools/browser` WS endpoint returns 404, use the HTTP list.
- CDP does NOT support JSON-RPC 2.0 — send `{"id": N, "method": "...", "params": {}}` (no `jsonrpc` field).
- `id` must be monotonically increasing and unique per session — never reuse 0.
- Skip non-target events in the recv loop: `Page.loadEventFired`, `Page.frameNavigated`, etc. arrive unsolicited.

## Reading structure (no OCR)
```python
r = await cdp.send("Accessibility.getFullAXTree", {"depth": 20})
nodes = r["result"]["nodes"]
# roles: link, button, textbox, radio, heading, StaticText, etc.
```
Speed: ~50ms. Returns `link`/`button`/`textbox`/`radio`/`heading` with their accessible name. Verified on 1688 product pages (1964 nodes) and DeepSeek sidebar (all 20 chat history links).

## Reading AI reply text — the 3-tier hierarchy (2026-06-02 verified)

Modern AI sites (DeepSeek, Doubao, ChatGPT, Kimi, Grok) put the assistant's reply inside custom elements + private Shadow DOM. Reading it requires trying strategies in order from cleanest to noisiest:

### Tier 1: `Runtime.evaluate` + site-specific CSS selector (BEST, 100% clean)
**Verified 2026-06-02 against DeepSeek** — reads full reply in a single `Runtime.evaluate` call, no OCR noise, no AX tree walking. Zero dependencies on Accessibility tree or shadow DOM traversal.

```python
# DeepSeek (verified)
r = await cdp.send("Runtime.evaluate", {
    "expression": """
    (() => {
        const els = document.querySelectorAll('.ds-markdown');
        if (els.length === 0) return {err: 'no .ds-markdown'};
        return {full: els[els.length-1].innerText};
    })()
    """,
    "returnByValue": True
})
reply = r["result"]["result"]["value"]["full"]
```

This works because `.ds-markdown` is a regular DOM element outside the Shadow DOM boundary — the AI reply text is mounted as a child. Same pattern works for many other sites (see `references/ai-site-dom-selectors.md` for the working selector dictionary).

**Key advantage over AX tree**: returns the actual text content directly. AX tree returns `StaticText` nodes that need walking, and breaks on old tabs.

### Tier 2: `Accessibility.getFullAXTree` (clean text, fragile on old tabs)
Returns `StaticText` nodes that you walk and concatenate. Works for ~50% of sites when the tab is fresh (just created via `Target.createTarget`). Old tabs with conversation history: Shadow DOM blocks AX. Pattern: if AX returns empty on first try, open a fresh tab and retry. Verified on DeepSeek (full reply, 1000-2000 chars) and Doubao (partial, 150-300 chars).

### Tier 3: `screencapture` + `ocrmac` OCR (FALLBACK only)
Only when both DOM and AX fail (rare — currently no known site requires this for AI reply text). Use:
```python
import subprocess
from ocrmac import ocrmac
subprocess.run(['screencapture', '-x', '-t', 'png', '/tmp/reply.png'], check=True)
annotations = ocrmac.OCR('/tmp/reply.png').recognize()
full = "\n".join(str(a[0]) for a in annotations if str(a[0]).strip())
```
**WARNING**: OCR reads the entire screen including chrome UI, browser chrome, status bar — heavy noise, need post-processing. End-to-end 244ms screenshot + 418ms OCR = 662ms, but cleanup cost > the time saved vs Tier 1.

**Decision rule**: Always try Tier 1 first. If `.ds-markdown` (or equivalent) returns empty, try Tier 2. Use Tier 3 only as last resort. This is faster, cleaner, and more reliable than the AX-only approach.

## Reading Shadow DOM content
The Accessibility tree CANNOT pierce Web Components' private Shadow DOM. This is a hard limit of the Web Platform, not a CDP bug. Workarounds ranked by speed:

1. **Direct API call** — fastest, but doesn't share context with the visible chat. Use when the task is "ask X" and you don't care about the visible conversation history.
2. **`Runtime.evaluate` + site-specific selector (TIER 1 above)** — second fastest, 100% clean, works on old tabs. **This is now the recommended path** for AI sites that mount the reply in a named class outside Shadow DOM.
3. **Screenshot + vision model** — ~200-500ms, ~95% accurate. `subprocess.run(["screencapture", "-x", "-t", "png", path])` then `vision_analyze(image_url=path)`. Fall back to this when CDP `Page.captureScreenshot` returns empty bytes (some Chrome GPU compositing issues).
4. **Network response capture** + stream parsing — fragile, sites change their streaming protocol often. Not recommended.

### ⚠️ Tab state matters for AX tree reading

Verified 2026-06-02: a **freshly opened tab** (`Target.createTarget` → navigate → ask → wait) renders the AI reply such that `Accessibility.getFullAXTree` can read it via `StaticText` nodes. An **old tab with conversation history** puts the reply behind a private Shadow DOM and AX returns empty. Pattern: if AX returns empty on the first attempt, open a fresh tab to the same URL and retry. This bypasses the Shadow DOM limitation for ~50% of sites (DeepSeek: full reply; Doubao: partial).

## Input element types — not all sites use `<textarea>`
## Input element types — not all sites use `<textarea>`
Three patterns in the wild (verified across DeepSeek, Doubao, Kimi, Grok, ChatGPT, Claude):

- `<textarea>` × 1 — DeepSeek, Grok, ChatGPT. Standard `DOM.querySelector("textarea")` + `DOM.focus`.
- `<textarea>` × 2+ — Doubao (user input + hidden search box), some 1688 composer pages. **Don't blindly pick the first** — use a JS pick: `visible + non-readonly + has placeholder` (priority 1) → first non-readonly → last.
- `<div contenteditable="true">` — **Kimi** (`.chat-input-editor`), Claude.ai, Notion-style editors. Focus via `document.querySelector('[contenteditable=true]').focus()`. Note: `textarea.value` reads empty after typing into a contenteditable; read `textContent` instead.
- `#prompt-textarea` (ProseMirror DIV) — **ChatGPT**. The `#prompt-textarea` element is a DIV container, NOT a real textarea. Inside it is `.pmViewDesc.contentDOM` (the actual ProseMirror document node). `Input.insertText` on `#prompt-textarea` itself FAILS — must target `contentDOM`. See **ChatGPT ProseMirror workflow** below.
## AI response completion signal = bodyLen growth, not stopBtn (2026-06-02 verified)
Modern AI sites render the "停止生成" button inside private Shadow DOM. `Runtime.evaluate` and AX tree both return nothing for it. The robust completion signal is `document.body.innerText.length` monotonic growth. Poll every 2s, compare to previous cycle's bodyLen. If grew → still generating. If stable for 5+ cycles (10s) → done. This works for React/Vue/Vanilla.

## 6大AI网站browser工具链（2026-06-03 全部验证通过）

| 网站 | 输入框ref | 发送方式 | 读回复 | 备注 |
|------|---------|---------|--------|------|
| **DeepSeek** | e17 (textarea) | `browser_press(Enter)` | `browser_snapshot` StaticText | ⚠️ ta.value=不触发React，必须逐字Input或Enter |
| **ChatGPT** | e19 (textarea) | `browser_click(e25)` | `browser_snapshot` StaticText | |
| **豆包** | e44 (textarea) | `browser_click(e59)` | `browser_vision` | |
| **智谱清言** | e21 (textarea) | `browser_press(Enter)` | `browser_vision` | e41按钮无效 |
| **Gemini** | Quill/Angular zone.js | ✅ **物理外挂（AppleScript）**（2026-06-03） | Quill `.ql-editor` + zone.js 对 CDP `Input.dispatchKeyEvent` 失效（缺 `nativeVirtualKeyCode: Int32`），但 `computer_use` 物理按键（Cmd+V 粘贴 + Return）直接走 Mac 系统事件，完全绕过 zone.js。步骤：① `Target.activateTarget` 激活标签页 ② `Runtime.evaluate` focus `.ql-editor` ③ `echo -n "问题" \| pbcopy` 写入剪贴板 ④ `computer_use key cmd+v` ⑤ `computer_use key return` → Gemini 收到完整问题并生成回复。Reply 读 body.innerText。 |
| **Grok** | Tiptap + Next.js streaming | ❌ **plain HTML textarea 阻塞**（2026-06-03） | textarea `h=16px y=0` — Next.js 流式占位符，非真实输入框。plain HTML textarea（无 `__reactProps`），JavaScript 写入 value 不触发 React onChange。`form.requestSubmit()` 返回 "submitted" 但 Grok 前端静默失败（认为 textarea 为空）。物理按键（Cmd+V+Return）只写入 DOM value，Grok 的 Next.js React 状态机不感知，submit 仍失败。AppleScript 物理外挂对 Grok 也无效（两者根因不同）。需要寄生到真正的聊天 iframe 内部 session 才能操作。 |

**通用流程**：browser_navigate → browser_snapshot找ref → browser_type填入 → **browser_press(Enter)优先**（比按钮点击更稳定）→ 等待 → browser_snapshot读AX树验证

**读回复优先级**：`browser_snapshot`(AX树) > `browser_vision`(截图)。browser_vision有rate limit（usage limit exceeded 2056），触发后用browser_snapshot替代。

**DeepSeek坑**：输入后点按钮文字被清空（React状态未更新）。解法：browser_press(Enter)穿透，或用Input.dispatchKeyEvent逐字触发React onChange。

**Complete working pipeline**:```python
import asyncio, json, websockets, urllib.request, base64, os, time, sys

# 1. Find tab
tabs = json.loads(urllib.request.urlopen("http://localhost:9333/json").read())
tab = next(t for t in tabs if t["type"]=="page" and "deepseek" in t["url"].lower())

# 2. WebSocket connect
async with websockets.connect(tab["webSocketDebuggerUrl"], max_size=50*1024*1024) as ws:
    # 3. Eavesdropper (天眼) - async message router
    async def eavesdrop():
        while True:
            data = json.loads(await ws.recv())
            if data.get("id") in pending:
                pending[data["id"]].set_result(data)
            else:
                events.put_nowait(data)

    # 4. Enable Network monitoring
    await cdp.send("Network.enable")
    await cdp.send("Runtime.enable")

    # 5. Focus + hardcode_type (逐字 keyDown→char→keyUp, 0.05s delay)
    await cdp.send("Runtime.evaluate", {
        "expression": "document.querySelector('textarea').focus()",
        "returnByValue": True
    })
    for ch in text:
        await cdp.send("Input.dispatchKeyEvent", {"type": "keyDown", "key": ch, "text": ""})
        await cdp.send("Input.dispatchKeyEvent", {"type": "char", "text": ch})
        await cdp.send("Input.dispatchKeyEvent", {"type": "keyUp", "key": ch})
        await asyncio.sleep(0.05)

    # 6. Enter send
    await cdp.send("Input.dispatchKeyEvent", {
        "type": "keyDown", "key": "Enter", "code": "Enter",
        "text": "\r", "keyCode": 13, "location": 0
    })

    # 7. Eavesdrop on Network.loadingFinished — captures SSE stream
    # DeepSeek uses patch protocol: {"v": "x"} appends to fragments
    # Accumulate all {"v": "..."} strings = full reply
```

**Key insight — AI response completion signal**: `document.body.innerText.length` monotonic growth (not stopBtn). Poll every 2s, stable for 10s = done.

**Move to production**: `cp /tmp/network_sniffer3.py ~/.hermes/scripts/network_sniffer3.py`

## Multi-site comparison orchestration

To ask the same question to N AI sites and read all replies, run sites **serially** (not in parallel) — Chrome CDP doesn't handle concurrent WS connections to different tabs well. The orchestration pattern and the working script: `scripts/multi_ai_ask.py`. Verified 2026-06-02 across 4 sites:

| Site | Input | AX readable? | Notes |
|------|-------|--------------|-------|
| DeepSeek | textarea×1 | optional (works without) | ✅ full reply | **2026-06-03 update: UI uses `<div role="button">` not `<button>`. Send button = `[role="button"].ds-button--primary.ds-button--filled.ds-button--circle`, find by walking UP 5 levels from textarea. `Input.insertText` after focus works. ⚠️ Reply streaming trap: after click, `body.innerText` may show ONLY the conversation title for 30-60s before the SSE stream completes — DO NOT abort early. Poll bodyLen until stable 10s = done. Full reply ~2000 chars after ~60-90s total.** |
| Doubao (豆包) | textarea×1 (Semi Design) | ✅ `Input.insertText` + send-btn click (2026-06-03) | `document.body.innerText` growth | **2026-06-03: ByteDance `sync-input-engine-infra-interactive` maintains internal state. `Input.insertText` triggers keydown/keyup/char chain → React state update → send-btn click succeeds. Assertion: `ta.value` goes to 0 (sent) AND URL changes to `/chat/<uuid>` (new conversation created). body.innerText grows from ~610 to ~3158 chars. Wait 30-60s for full reply.** |
| ChatGLM | textarea×1 | yes | ✅ (full reply) | **direct value injection works — 完整三种机制分析** |
| Kimi | contenteditable div | yes | ❌ (mostly) | textContent read; new tab: AX works |
| Grok | `textarea` (Tiptap) | `press_sequentially` via Playwright | ⚠️ 60-90s | **2026-06-03: Tiptap wrapper means `__reactProps` is on `t.parentElement` not the textarea itself. `Input.insertText` fails to populate via CDP; use React fiber parent-props path with `onCompositionEnd` first. Send button: `button[aria-label="提交"]`. Reply in `document.body.innerText` after ~60-90s (xAI Reasoning slow). `press_sequentially` via Playwright Chromium 147 WORKS (2026-06-03 verified — same pattern as ChatGPT).** |
| ChatGPT | `#prompt-textarea` (ProseMirror div) | `Input.insertText` after `focus()` | ✅ full reply | 2026-06-03: `Input.insertText` cleanest path. `press_sequentially` also works. Send via Enter or `button[data-testid="send-button"]`. Reply readable via `document.body.innerText` after ~30s. **Playwright `press_sequentially` (real_typing strategy) verified 2026-06-03 — opens fresh Chromium 147, types 76 chars at 50ms/char, sends, waits, extracts reply.** |
| Claude.ai | contenteditable | yes | ❌ Shadow DOM | use API instead |
| Gemini | webview iframe | yes | ❌ (outer page) | **CDP 无法穿透 `<webview>`；textarea 在 iframe 里跨域** |

## Pitfalls
- **Empty `text` in keyDown is mandatory.** Otherwise React double-counts characters (verified: `用3句话` → `用用33句句话话`).
- **Don't reuse msg_id=0** — Chrome's internal events use 0 too, you'll lose responses.
- **`DOM.enable` is required for `DOM.focus` / `DOM.querySelector`.** Enable before using, disable if you switch tasks.
- **Direct value injection (fastest for textarea sites)**: For sites that use pure `<textarea>` (DeepSeek, ChatGLM), setting `ta.value = 'text'` + `dispatchEvent(new Event('input', {bubbles:true}))` is 10× faster than char-by-char. Verified working: DeepSeek ✅, ChatGLM ✅. **NOT working: 豆包 Doubao (2026-06-03)** — Semi Design `<Input>` + React 18 concurrent state swallows synthesized input events; `send-btn` stays `disabled`. 2026-06-03 verified.
- **`Input.insertText` for ProseMirror (ChatGPT) — 2026-06-03 verified**: The cleanest fast path for ProseMirror contenteditable. First `Runtime.evaluate` to focus the `.pmViewDesc.contentDOM` (the REAL editing node inside the `#prompt-textarea` wrapper div), then one `Input.insertText` call puts the text AND ProseMirror correctly updates. Confirmed: text appears in `<p data-placeholder="...">` and the `send-button` becomes enabled. Sequence:
  ```python
  # WRONG: focus the wrapper div — insertText silently fails (val stays 0)
  await cdp.send("Runtime.evaluate", {"expression": "document.querySelector('#prompt-textarea').focus()"})
  
  # CORRECT: focus the actual ProseMirror document node inside the wrapper
  await cdp.send("Runtime.evaluate", {
      "expression": "document.querySelector('#prompt-textarea .pmViewDesc.contentDOM').focus()"
  })
  await cdp.send("Input.insertText", {"text": "your question here"})
  
  # Click send — DO NOT use Enter keyDown (CDP tool int32 nativeVirtualKeyCode issues)
  await cdp.send("Runtime.evaluate", {
      "expression": "document.querySelector('.composer-submit-btn')?.click()"
  })
  ```
  Much faster and more reliable than `Input.dispatchKeyEvent` char-by-char for ProseMirror.
- **React 18+ controlled input bypass (last resort)**: When neither `dispatchEvent` nor `Input.insertText` work (e.g. Semi Design's dedup on `input` event), the underlying trick is to bypass React's value-tracking dedup:
  ```javascript
  const ta = document.querySelector('textarea');
  const proto = Object.getPrototypeOf(ta);
  const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
  setter.call(ta, 'text');
  ta.dispatchEvent(new Event('input', {bubbles: true, cancelable: true}));
  ```
  This works on most React 16-17 sites. React 18 + Semi Design may still swallow the event because the framework re-checks its own internal state on next render — true char-by-char `Input.dispatchKeyEvent` (keyDown→char→keyUp with `text=""` on keyDown) is the most reliable escape.
- **`screencapture -x` works** when CDP `Page.captureScreenshot` returns 0 bytes (Chrome GPU layer issue on some macOS versions).
- **AI response completion signal = bodyLen growth, not stopBtn (2026-06-02 verified)**: Modern AI sites render the "停止生成" button inside private Shadow DOM. `Runtime.evaluate` and AX tree both return nothing for it. The robust completion signal is `document.body.innerText.length` monotonic growth. Poll every 2s, compare to previous cycle's bodyLen. If grew → still generating. If stable for 5+ cycles (10s) → done. This works for React/Vue/Vanilla.
- **⚠️ `browser_navigate` is broken in many sessions — fall back to `browser_cdp` (2026-06-05)**: The `browser_navigate` tool can fail with `[Errno 2] No such file or directory: '/Users/aimac/.hermes/hermes-agent/node_modules/.bin/agent-browser'` even when `agent-browser` is actually installed (e.g. in `node_modules/.bin/`). When this happens, the tool is unusable for that session. **Fallback ladder**:
  1. `browser_cdp(method="Target.createTarget", params={"url": "..."})` — opens a new tab. Use this for any "open this URL" task.
  2. `browser_cdp(method="Page.navigate", params={"url": "..."}, target_id=existing_tab_id)` — navigates an existing tab.
  3. `mcp_cua_driver_launch_app` with `additional_arguments=[--remote-debugging-port=9333, <url>]` — last resort; needs an `additional_arguments` array, NOT a flat string. **Caveat**: cua-driver ignores `--user-data-dir` on macOS and uses the system default Chrome profile, so login state is whatever the foreground user has — usually a bonus.
- **⚠️ CDP supervisor `Runtime.evaluate` rejects Python `bool` for `returnByValue` (2026-06-05)**: The MCP/Hermes `browser_cdp` wrapper that goes through the CDP supervisor fails with `Failed to deserialize params.returnByValue - BINDINGS: bool value expected at position NNN` if you pass the Python literal `True`/`False`. The wrapper actually wants a JSON boolean, but its deserializer is buggy with the wire format. **Workaround**: drop the `returnByValue` field (you get the full result dict back and read `r["result"]["result"]["value"]` yourself), or pass the field as the string `"true"`/`"false"`. This burned 4 attempts in one session before the diagnosis. Always drop `returnByValue` and read the raw result if you only need a primitive value.
- **Don't `pkill Chrome` from a CDP script — Chrome is the user's session (2026-06-05)**: The `mcp_cua_driver_launch_app` tool starts a new Chrome process which **takes over port 9333** and pre-empts whatever was there. The user's foreground Chrome is unaffected, but if you `pkill Google Chrome` to "clean up" you will silently drop the user's tabs and login state. The right pattern: leave the new Chrome alive (it has its own profile dir), or close tabs via CDP `Target.closeTarget` if you opened them. See `references/foreground-vs-debug-chrome.md` for the full profile lifecycle.

- **⚠️ Chrome 148+ pushes unsolicited event frames over page WS (2026-06-05 verified)**: After `Page.enable` / `Runtime.enable`, Chrome will push `Runtime.executionContextCreated`, `Page.frameNavigated`, `Runtime.consoleAPICalled`, etc. without you asking. A raw `ws.recv()` after a `send()` may return one of these events instead of the command response, causing `KeyError: 'result'` on the next JSON parse. **Symptom**: `r['result']['result']['value']` raises `'result'` or your script hangs waiting for a response that already came (and was discarded as "event").

**Fix — `sendrecv` pattern that loops past events**:
```python
class CDPSession:
    def __init__(self, ws_url, timeout=5):
        self.ws = websocket.create_connection(ws_url, timeout=timeout)
        self.msg_id = 0

    def close(self):
        self.ws.close()

    def sendrecv(self, method, params=None):
        self.msg_id += 1
        my_id = self.msg_id
        self.ws.send(json.dumps({'id': my_id, 'method': method, 'params': params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            # event frames have no 'id' (or id != my_id); skip them
            if 'id' in msg and msg['id'] == my_id:
                return msg
```

**Why single `recv()` works sometimes but breaks under load**: a single `Runtime.evaluate` on a fresh quiet tab often works because no events fire in the microsecond window between `send` and `recv`. But once you `Page.enable` first (required for `addScriptToEvaluateOnNewDocument`), Chrome immediately pushes `Runtime.executionContextCreated` for every frame on the page — and you'll get the event, not your response. Use `sendrecv` from the start; never rely on raw `ws.recv()` after `Page.enable` / `Runtime.enable`.

**Compatible with the existing `returnByValue` gotcha** — when you don't get `r['result']['result']['value']`, also check `r.get('error')` and `r['result'].get('exceptionDetails')` before raising. CDP return shape varies slightly between Chrome 146/147/148/150.

## Chrome debug profile 磁盘占用诊断（2026-06-04 added）

`~/.hermes/chrome-debug` 是 Hermes 寄生调试 Chrome 的 user-data-dir，登录态都在里面，**别瞎清**。但因为是 debug Chrome，下载的 on-device AI 模型会无脑塞进去，**几个月后能涨到 5+ GB**，看起来像登录态出问题了。

### 诊断 3 步走

```bash
# 1. 总大小
du -sh ~/.hermes/chrome-debug

# 2. 内部 TOP 10（重点关注 OptGuideOnDevice* / optimization_guide* / screen_ai）
du -sh ~/.hermes/chrome-debug/* | sort -hr | head -10

# 3. 登录态实际大小（应该 < 10MB）
ls -la ~/.hermes/chrome-debug/Default/Cookies \
       ~/.hermes/chrome-debug/Default/"Local Storage"/ \
       ~/.hermes/chrome-debug/Default/"Session Storage"/
```

### 已知大头（2026-06-04 实测 5.6GB 拆解）

| 文件/目录 | 实测大小 | 是什么 | 跟登录态有关？ | 能删吗 |
|---|---|---|---|---|
| `OptGuideOnDeviceModel/` | **4.0 GB** | Chrome 152+ 内置 Gemini Nano 本地 LLM | ❌ 无关 | ✅ 零风险，Chrome 按需重下 |
| `Default/Cookies` | ~30 KB | 6 个 AI 站登录态 | ✅ 真正担心的 | ❌ 删了重登 |
| `Default/"Local Storage"/` | ~5 MB | 各站 session 数据 | ✅ 部分 | ⚠️ 删了重登 |
| `Default/` 整体 | ~800 MB | 浏览器配置/历史/扩展设置 | 部分 | ⚠️ 备份后可清 |
| `Extensions/` | 228 MB | 装的扩展 | ❌ | ✅ 删了重装 |
| `component_crx_cache/` | 146 MB | 组件下载缓存 | ❌ | ✅ 零风险 |
| `screen_ai/` | 123 MB | Chrome 屏幕 AI 识别 | ❌ | ✅ 零风险 |
| `OptGuideOnDeviceClassifierModel/` | 120 MB | 分类小模型 | ❌ | ✅ 零风险 |
| `optimization_guide_model_store/` | 76 MB | 优化指南模型 | ❌ | ✅ 零风险 |
| `Safe Browsing/` | 22 MB | 钓鱼/恶意软件黑名单 | ❌ | ✅ Chrome 重下 |

### 通用清理脚本（保留登录态 + 删 on-device AI）

```bash
# 清理前：总 5.6GB
# 清理后：约 800MB（保留 Default / Extensions）
# 零登录态丢失

du -sh ~/.hermes/chrome-debug
rm -rf ~/.hermes/chrome-debug/OptGuideOnDeviceModel
rm -rf ~/.hermes/chrome-debug/OptGuideOnDeviceClassifierModel
rm -rf ~/.hermes/chrome-debug/optimization_guide_model_store
rm -rf ~/.hermes/chrome-debug/screen_ai
rm -rf ~/.hermes/chrome-debug/component_crx_cache
rm -rf ~/.hermes/chrome-debug/Safe\ Browsing
du -sh ~/.hermes/chrome-debug
```

### Chrome 152+ On-Device AI 用途速查（用户问"这 4GB 是干啥的"时用）

| 用途 | 触发场景 | 用户感不感觉得到 |
|---|---|---|
| **整页翻译** | 右键 → 翻译成中文 | ✅ 强（替代云端 Google 翻译） |
| **AI 摘要** | 长文章/报告 | ✅ 中 |
| **写作/改写** | Gmail "帮我写" | ✅ 弱（用 Gmail 才知道） |
| **语言检测** | 中英混输自动判语言 | ⚠️ 几乎不知道 |
| **语法纠错** | 邮件实时挑错 | ⚠️ 不开 Gmail 用不到 |
| **Screen AI** | 无障碍读屏（盲人辅助） | ❌ 普通用户无感 |

**对 Hermes Agent 用户**：本地 AI 模型**完全不影响** Hermes 的云端 AI 站对话（MiniMax-M3 / ChatGPT / Gemini 等），它们走 CDP 不走 Chrome 内置 API。**删 4.5GB 模型 = Hermes 零影响**。

## Port detection — scan, don't assume (2026-06-03 verified)

CDP scripts must NOT hardcode a single debug port. The user's Chrome may be on any port depending on how it was started. **Always scan** the known ports in priority order:

```python
CDP_PORTS = [9333, 9444, 9222]  # ordered by likelihood

def detect_cdp_port() -> tuple[str, int] | None:
    """
    Returns (host, port) of the first responding CDP endpoint.
    Tries 9333 first (user manually started Chrome with --remote-debugging-port=9333),
    then 9444 (what launch_chrome_cdp.sh uses), then 9222 (Chrome DevTools default).
    """
    import urllib.request
    for port in CDP_PORTS:
        try:
            url = f"http://127.0.0.1:{port}/json"
            tabs = json.loads(urllib.request.urlopen(url, timeout=3).read())
            if tabs:
                return ("127.0.0.1", port)
        except Exception:
            continue
    return None
```

**Why not `socket.connect()`**: Chrome's CDP HTTP endpoint returns a JSON tab list — if it responds with any content, the CDP WS is guaranteed to be at `ws://host:port/devtools/...`. A TCP connect check on port 9333 can succeed even when Chrome's CDP HTTP server is dead (stale port).

**Common port scenarios**:
| Port | How it gets set |
|------|----------------|
| 9333 | User manually: `open -a "Google Chrome" --args --remote-debugging-port=9333` |
| 9444 | The helper script `launch_chrome_cdp.sh` (pkill → open → --args --remote-debugging-port=9444) |
| 9222 | Chrome DevTools default (no --remote-debugging-port flag) |

**launch_chrome_cdp.sh reliability note (2026-06-03)**: The pattern `pkill -9 -f "Google Chrome" && open -a "Google Chrome" --args --remote-debugging-port=9444` is NOT guaranteed to set the new port on the freshly opened Chrome — `open -a` may reactivate an existing un-killed process or the new Chrome may ignore `--args` if another instance is already running. If port 9444 scan fails, fall back to 9333. The user may already have a stable Chrome on 9333 started outside the script.

### ⚠️ Chrome GUI 打开 ≠ CDP 端口监听（2026-06-07 实测根因）

**症状**：`curl http://127.0.0.1:9333/json` → Connection refused，但 `ps aux | grep Chrome` 显示 Chrome 进程在跑，TCP connect `connect_ex()` 返回 0（端口 TCP 连通）。

**根因**：Chrome 从 Spotlight/Dock/Alfred GUI 启动，**没有带 `--remote-debugging-port` 参数**，CDP HTTP/WS 服务器从未启动。进程在跑但调试端口没开。

**诊断流程**：
```python
# Step 1: 确认 Chrome 在跑
ps aux | grep "Google Chrome" | grep -v grep | grep -v Helper | wc -l
# → > 0 说明 Chrome 在跑

# Step 2: 确认端口真正监听（TCP ok ≠ HTTP ok）
python3 -c "
import socket, urllib.request
s = socket.socket()
s.settimeout(2)
tcp_ok = s.connect_ex(('127.0.0.1', 9333)) == 0
s.close()
try:
    tabs = urllib.request.urlopen('http://127.0.0.1:9333/json', timeout=3)
    http_ok = True
except Exception as e:
    http_ok = False
print(f'TCP={tcp_ok} HTTP={http_ok}')  # TCP=yes + HTTP=no = GUI启动未带参数
"
```

**正确修复**：
```bash
# 用 chrome-on-demand.sh（正确的启动方式）
bash ~/.hermes/scripts/chrome-on-demand.sh start

# 或强制重启
bash ~/.hermes/scripts/chrome-on-demand.sh --force

# 验证
curl -s http://127.0.0.1:9333/json/version
```

**不要用的方法**：
- ❌ `pkill -9 Chrome` 然后 GUI 重开 — 丢失用户所有 tab
- ❌ `open -a "Google Chrome"` — 不带调试参数
- ❌ "Chrome 在另一个 Space" — macOS 上不是这个问题

**keepalive 脚本状态**：
```bash
launchctl list | grep chrome-keepalive
# Should show PID > 0, not "Stop"
```

### Known port mismatch symptoms (2026-06-03)
- Script error: `HTTP Error 502: Bad Gateway` or `Connection refused` when connecting to CDP
- `curl http://127.0.0.1:9444/json` returns empty `[]` but `lsof -iTCP:9333` shows Chrome listening
- **Fix**: Scan all ports. Never assume.

### Text truncation / duplicate submission symptom (2026-06-03)
If the textarea shows the question repeated 3× (e.g., "用3句话用3句话用3句话"), the `Input.insertText` was called 3 times without clearing the textarea first. The **clear_input()** defense is mandatory — always call it before `insert_text()`:
```python
# WRONG (causes duplication)
insert_text(question)

# CORRECT (clears first)
clear_input(selector)   # → el.value = '' + input/change events
insert_text(question)
```

## 主动寄生式 CDP 脚本三大铁律（2026-06-03）

所有 CDP 自动化脚本必须严格遵循，违反任意一条都会导致用户投诉「屏幕上全是浏览器」：

### 1. 不杀进程、不拉起浏览器
Chrome debug port 9333 是用户已经运行的浏览器实例，脚本只能「寄生」已有 tab，绝对不能：
- 执行 `pkill Chrome` / `killall Chrome`
- 用 `open -a "Google Chrome"` 拉起新窗口
- 执行任何控制浏览器生命周期的命令

**正确做法**：启动前用 `http://127.0.0.1:9333/json` 嗅探 tab，不存在则报错退出。
```python
def find_target(url_match: str):
    try:
        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:9333/json").read())
    except Exception as e:
        print(f"❌ CDP 端点无响应: {e}"); return None
    for t in tabs:
        if url_match in t.get("url", ""): return t
    print(f"❌ 未检测到 {url_match}，请手动打开并登录"); return None
```

### 2. 输入前必清空 textarea
多次运行脚本时，textarea 不会自动清空，`Input.insertText` 会把新文本追加到旧文本后面，导致重复发送。

**正确做法**：每次填入前执行 `clear_input()`：
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
    return len(self.get_value(selector)) == 0
```

### 3. 任务完成后关闭 tab 或跳转 about:blank
用户明确投诉「屏幕上全是浏览器」，所以任务完成后必须清理：
- 读取完回复 → `browser_cdp(method="Target.closeTarget", params={"targetId": tab_id})`
- 用 `browser_navigate` 时 → 任务完成后 navigate 到 `about:blank`

**例外**：用户明确要求保留 tab（如「让我看看 ChatGPT 的回复」）则不关闭。

### ⚠️ 必读：端口扫描必须在连接前执行

**永远不要硬编码单一端口**。Chrome 9333/9444/9222 都可能。脚本必须先嗅探再连接：

```python
CDP_PORTS = [9333, 9444, 9222]

def detect_cdp_port() -> tuple[str, int] | None:
    import urllib.request, json
    for port in CDP_PORTS:
        try:
            tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3).read())
            if tabs:
                return ("127.0.0.1", port)
        except Exception:
            continue
    return None
```

**常见错位**：脚本报 `HTTP Error 502` 或 `Connection refused` 但 Chrome 进程存在——说明端口不对。`lsof -iTCP:9333` 和 `lsof -iTCP:9444` 同时查，通常只有一个活着。

### ⚠️ Text truncation / 重复提交根因（2026-06-03）

如果 textarea 显示问题被重复塞入（如 "用3句话用3句话"），说明 `Input.insertText` 在 textarea 未清空状态下被调用了 3 次。每次运行脚本前必须清空：

```python
# WRONG — 会导致文本堆叠/重复
insert_text(question)

# CORRECT — 每次填入前清空
clear_input(selector)   # → el.value = '' + input + change 事件派发
insert_text(question)
```

这与是否在同一个脚本内无关——即使脚本重启，如果用户在 AI 界面手动输入过内容后运行脚本，textarea 仍有旧内容，`insertText` 会追加而非替换。

### 已验证脚本
- `~/.hermes/scripts/hermes_web_bot_cdp.py` — 完整实现三大铁律，支持 all/chatgpt/deepseek/doubao/chatglm/grok/gemini，输入前清空、不杀进程、不留 tab
- **macOS system proxy breaks Python urllib SSL (2026-06-02 verified)**: HTTP/HTTPS proxy env vars (e.g. Clash at `127.0.0.1:7897`) cause `[SSL: UNEXPECTED_EOF_WHILE_READING]` on `urllib.request.urlopen` to any external HTTPS endpoint. `no_proxy=*` is **NOT respected** by Python's urllib on macOS. **Fix**: use `subprocess.run(['curl', '-s', '--noproxy', '*', ...])` instead of urllib — curl respects `--noproxy` and bypasses the proxy correctly. Pattern (verified for v2.aicodee.com / api.minimaxi.com):

  ```python
  import subprocess, json
  result = subprocess.run([
      'curl', '-s', '--noproxy', '*', '-X', 'POST', url,
      '-H', 'Content-Type: application/json',
      '-H', f'Authorization: Bearer {api_key}',
      '-d', json.dumps(payload),
      '--max-time', str(timeout)
  ], capture_output=True, text=True, timeout=timeout + 5)
  resp = json.loads(result.stdout)
  ```
- **AI response completion signal = bodyLen growth, not stopBtn (2026-06-02 verified)**: Modern AI sites render the "停止生成" button inside private Shadow DOM. `Runtime.evaluate` and AX tree both return nothing for it. The robust completion signal is `document.body.innerText.length` monotonic growth. Poll every 2s, compare to previous cycle's bodyLen. If grew → still generating. If stable for 5+ cycles (10s) → done. This works for React/Vue/Vanilla.

## See also
- `references/foreground-vs-debug-chrome.md` — **foreground Chrome (已登录) vs debug Chrome 根本不是同一个实例**，Cookie Keychain 加密跨实例不通用问题（2026-06-04 新增）
- `references/browser-navigate-fallback-20260605.md` — **when `browser_navigate` is broken**, the CDP fallback ladder (Target.createTarget / Page.navigate / cua-driver launch_app) plus the returnByValue bool deserialization gotcha
- `references/chrome-debug-disk-diagnosis-20260604.md` — 5.6GB on-device AI 拆解脚本 + 4GB 清理 SOP
- `references/doubao-20260603-breakthrough.md` — **Doubao 发送突破完整记录**（insertText + 坐标点击 + 成功断言 + 失效方案列表）
- `references/ai-site-input-strategies.md` — input-strategy decision tree per site (which input method works for ChatGPT/豆包/DeepSeek/ChatGLM/Gemini/Grok, with the 2026-06-03 verified patterns)
- `references/ai-site-dom-selectors.md` — working CSS selectors for reading AI reply text across sites
- `references/ai-sites-verification-20260603.md` — 6 AI sites end-to-end verification results (4/6 passed, strategy comparison, DeepSeek streaming trap)
- `references/cdp-react-vue-bypass.md` — full technique writeup with the double-character gotcha explained
- `references/multi-site-orchestration.md` — multi-AI comparison pattern (input element detection, per-site quirks, site table)
- `references/production-network-sniffer.md` — verified production script network_sniffer3.py (complete pipeline + verification log)
- `scripts/multi_ai_ask.py` — ask the same question to N AI sites, read replies from AX tree
- `scripts/cdp_ask_ai.py` — minimal working bot (asks DeepSeek, screenshots, prints path for vision readback)
- `scripts/ask_ai_sites.py` — end-to-end demo (real input → wait → DOM read reply → JSON result) using Tier 1 selector + bodyLen completion signal
- `references/physical-keyboard-bypass.md` — 物理外挂 AppleScript 破解 Gemini zone.js（2026-06-03 验证）
- Playwright-native bot (no Docker): `scripts/hermes_web_bot.py` — `pip install playwright && playwright install chromium` then run directly
