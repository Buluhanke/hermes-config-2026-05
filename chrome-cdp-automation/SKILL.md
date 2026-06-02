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
| DeepSeek | textarea×1 | optional (works without) | ✅ full reply | `.ds-markdown` selector works; full reply ~1000-2000 chars |
| Doubao | textarea×2 | yes for full features | ✅ (partial) | direct value injection works; JS-pick priority |
| ChatGLM | textarea×1 | yes | ✅ (full reply) | **direct value injection works — 完整三种机制分析** |
| Kimi | contenteditable div | yes | ❌ (mostly) | textContent read; new tab: AX works |
| Grok | textarea×1 | yes (xAI account) | ❌ blocked | **Cloudflare challenge 完全拦截，无法绕过** |
| ChatGPT | textarea×1 | yes | ❌ Shadow DOM | **ProseMirror 受控组件，direct value 被忽略；focus 后再输入** |
| Claude.ai | contenteditable | yes | ❌ Shadow DOM | use API instead |
| Gemini | webview iframe | yes | ❌ (outer page) | **CDP 无法穿透 `<webview>`；textarea 在 iframe 里跨域** |

## Pitfalls
- **Empty `text` in keyDown is mandatory.** Otherwise React double-counts characters (verified: `用3句话` → `用用33句句话话`).
- **Don't reuse msg_id=0** — Chrome's internal events use 0 too, you'll lose responses.
- **`DOM.enable` is required for `DOM.focus` / `DOM.querySelector`.** Enable before using, disable if you switch tasks.
- **Direct value injection (fastest for textarea sites)**: For sites that use pure `<textarea>` (DeepSeek, Doubao, ChatGLM), setting `ta.value = 'text'` + `dispatchEvent(new Event('input', {bubbles:true}))` is 10× faster than char-by-char. Verified working: DeepSeek ✅, Doubao ✅, ChatGLM ✅. Not working: ChatGPT (ProseMirror), Gemini (webview跨域).
- **`screencapture -x` works** when CDP `Page.captureScreenshot` returns 0 bytes (Chrome GPU layer issue on some macOS versions).
- **Login state:** do NOT launch a fresh `chromium.launch()` — it has no cookies. Either reuse the user's Chrome via debug port, or copy the entire `Default/` profile directory before launch.
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
- `references/ai-site-dom-selectors.md` — working CSS selectors for reading AI reply text across sites (DeepSeek verified, others TBD)
- `references/cdp-react-vue-bypass.md` — full technique writeup with the double-character gotcha explained
- `references/multi-site-orchestration.md` — multi-AI comparison pattern (input element detection, per-site quirks, site table)
- `references/ai-site-dom-selectors.md` — working CSS selectors for reading AI reply text across sites (DeepSeek verified, others TBD)
- `scripts/cdp_ask_ai.py` — minimal working bot (asks DeepSeek, screenshots, prints path for vision readback)
- `references/production-network-sniffer.md` — 已验证4次的生产脚本 network_sniffer3.py（完整pipeline+验证记录）
- `scripts/multi_ai_ask.py` — ask the same question to N AI sites, read replies from AX tree
- `scripts/ask_ai_sites.py` — end-to-end demo (real input → wait → DOM read reply → JSON result) using Tier 1 selector + bodyLen completion signal
- Working production version: `~/.hermes/scripts/hermes_web_bot_v2.py`
