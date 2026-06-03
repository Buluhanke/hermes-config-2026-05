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
## AI response completion signal = bodyLen growth, not stopBtn (2026-06-02 verified)
Modern AI sites render the "停止生成" button inside private Shadow DOM. `Runtime.evaluate` and AX tree both return nothing for it. The robust completion signal is `document.body.innerText.length` monotonic growth. Poll every 2s, compare to previous cycle's bodyLen. If grew → still generating. If stable for 5+ cycles (10s) → done. This works for React/Vue/Vanilla.

## 6大AI网站browser工具链（2026-06-03 全部验证通过）

| 网站 | 输入框ref | 发送方式 | 读回复 | 备注 |
|------|---------|---------|--------|------|
| **DeepSeek** | e17 (textarea) | `browser_press(Enter)` | `browser_snapshot` StaticText | ⚠️ ta.value=不触发React，必须逐字Input或Enter |
| **ChatGPT** | e19 (textarea) | `browser_click(e25)` | `browser_snapshot` StaticText | |
| **豆包** | e44 (textarea) | `browser_click(e59)` | `browser_vision` | |
| **智谱清言** | e21 (textarea) | `browser_press(Enter)` | `browser_vision` | e41按钮无效 |
| **Gemini** | e17 (textarea) | `browser_click(e18)` | `browser_vision` | |
| **Grok** | e81 (textarea) | `browser_press(Enter)` | `browser_snapshot` | |

**通用流程**：browser_navigate → browser_snapshot找ref → browser_type填入 → **browser_press(Enter)优先**（比按钮点击更稳定）→ 等待 → browser_snapshot读AX树验证

**读回复优先级**：`browser_snapshot`(AX树) > `browser_vision`(截图)。browser_vision有rate limit（usage limit exceeded 2056），触发后用browser_snapshot替代。

**DeepSeek坑**：输入后点按钮文字被清空（React状态未更新）。解法：browser_press(Enter)穿透，或用Input.dispatchKeyEvent逐字触发React onChange。

**Complete working pipeline**:
```python
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
| Doubao (豆包) | textarea×1 (Semi Design) | yes for full features | ⚠️ (partial) | **2026-06-03 deep-dive: Semi Design + React 18 + ByteDance `SyncInputEngine` (sync-input-engine-infra-interactive.71f86969.js) maintains internal state separate from React. `ta.value=` + dispatchEvent FAILS — engine's debounce keeps send-btn disabled. React fiber `__reactProps` direct call needs COMPLETE SyntheticEvent template (with `nativeEvent` + all the preventDefault/stopPropagation/persist methods) — if missing `event.target` it crashes. Call `props.onCompositionEnd` FIRST to release IME lock, then onChange/onInput. Real `Input.dispatchKeyEvent` char-by-char is the last-resort path. 2nd textarea is hidden search; use JS pick.** |
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
- **`Input.insertText` for ProseMirror (ChatGPT) — 2026-06-03 verified**: The cleanest fast path for ProseMirror contenteditable. First `Runtime.evaluate` to focus the editor, then one `Input.insertText` call (no char-by-char) puts the text in the right place AND the ProseMirror node updates correctly. Confirmed against `#prompt-textarea` on chatgpt.com: text appears in `<p data-placeholder="...">` and the `send-button` becomes enabled. Sequence:
  ```python
  await cdp.send("Runtime.evaluate", {"expression": "document.querySelector('#prompt-textarea').focus()"})
  await cdp.send("Input.insertText", {"text": "your question here"})
  # Then dispatchKeyEvent Enter or click the send button
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
- **Playwright `press_sequentially` as the universal input strategy (2026-06-03 verified)**: `loc.press_sequentially(text, delay=50)` with a prior `loc.click()` to focus is the single most reliable way to trigger React/Vue/Angular/Tiptap/Semi Design input handlers across ALL tested sites. Verified working: ChatGPT (ProseMirror) ✅, Doubao (SyncInputEngine) ✅, Grok (Tiptap) ✅. The key is that it fires genuine OS-level `keydown`/`keyup`/`input` events through the browser's event system, unlike `element.value =` which only touches the DOM. This is always the **first strategy to try** before falling back to CDP `Input.dispatchKeyEvent` char-by-char. It requires Playwright's own Chromium (NOT the user's debug Chrome via CDP), so it means a fresh browser session with no login cookies — use it when you don't need existing login state.
- **Login state:** do NOT launch a fresh `chromium.launch()` — it has no cookies. Either reuse the user's Chrome via debug port, or copy the entire `Default/` profile directory before launch.
- **⚠️ User preference: close browser tabs/windows after use (2026-06-03)**: This user has called out "你调用完浏览器为什么都不关掉？" / "屏幕上全是浏览器" as a recurring complaint. When you create tabs via `Target.createTarget` or `browser_navigate`, **you are responsible for closing them when the task is done**. For multi-site comparison tasks: open → ask → read → close the tab. Do not leave 6 AI sites open on the user's screen after the comparison is done. The exception is when the user explicitly asks to keep a tab open (e.g. "let me see ChatGPT's reply"). Concrete pattern:
  ```python
  # After reading reply and saving it, close the tab
  await cdp.send("Target.closeTarget", {"targetId": tab_id})
  # Or via browser_cdp tool:
  browser_cdp(method="Target.closeTarget", params={"targetId": tab_id})
  ```
  When using `browser_navigate` (which goes through Browserbase cloud), navigate to `about:blank` at the end instead of leaving the site open.
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
- `references/ai-site-input-strategies.md` — **input-strategy decision tree per site** (which input method works for ChatGPT/豆包/DeepSeek/ChatGLM/Gemini/Grok, with the 2026-06-03 verified patterns)
- `references/ai-site-dom-selectors.md` — working CSS selectors for reading AI reply text across sites
- `references/ai-sites-verification-20260603.md` — 6 AI sites end-to-end verification results (4/6 passed, strategy comparison, DeepSeek streaming trap)
- `references/cdp-react-vue-bypass.md` — full technique writeup with the double-character gotcha explained
- `references/multi-site-orchestration.md` — multi-AI comparison pattern (input element detection, per-site quirks, site table)
- `references/production-network-sniffer.md` — verified production script network_sniffer3.py (complete pipeline + verification log)
- `scripts/multi_ai_ask.py` — ask the same question to N AI sites, read replies from AX tree
- `scripts/cdp_ask_ai.py` — minimal working bot (asks DeepSeek, screenshots, prints path for vision readback)
- `scripts/ask_ai_sites.py` — end-to-end demo (real input → wait → DOM read reply → JSON result) using Tier 1 selector + bodyLen completion signal
- Working production version: `~/.hermes/scripts/hermes_web_bot.py` (12KB, 4 strategies, Playwright Chromium 147)
- Playwright-native bot (no Docker): `scripts/hermes_web_bot.py` — `pip install playwright && playwright install chromium` then run directly
