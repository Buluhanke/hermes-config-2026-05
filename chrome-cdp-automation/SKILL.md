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

## Reading Shadow DOM content
The Accessibility tree CANNOT pierce Web Components' private Shadow DOM. This is a hard limit of the Web Platform, not a CDP bug. Workarounds ranked by speed:

1. **Direct API call** — fastest, but doesn't share context with the visible chat. Use when the task is "ask X" and you don't care about the visible conversation history.
2. **Screenshot + vision model** — ~200-500ms, ~95% accurate. `subprocess.run(["screencapture", "-x", "-t", "png", path])` then `vision_analyze(image_url=path)`. Fall back to this when CDP `Page.captureScreenshot` returns empty bytes (some Chrome GPU compositing issues).
3. **Network response capture** + stream parsing — fragile, sites change their streaming protocol often. Not recommended.

### ⚠️ Tab state matters for AX tree reading

Verified 2026-06-02: a **freshly opened tab** (`Target.createTarget` → navigate → ask → wait) renders the AI reply such that `Accessibility.getFullAXTree` can read it via `StaticText` nodes. An **old tab with conversation history** puts the reply behind a private Shadow DOM and AX returns empty. Pattern: if AX returns empty on the first attempt, open a fresh tab to the same URL and retry. This bypasses the Shadow DOM limitation for ~50% of sites (DeepSeek: full reply; Doubao: partial).

## Input element types — not all sites use `<textarea>`

Three patterns in the wild (verified across DeepSeek, Doubao, Kimi, Grok, ChatGPT, Claude):

- `<textarea>` × 1 — DeepSeek, Grok, ChatGPT. Standard `DOM.querySelector("textarea")` + `DOM.focus`.
- `<textarea>` × 2+ — Doubao (user input + hidden search box), some 1688 composer pages. **Don't blindly pick the first** — use a JS pick: `visible + non-readonly + has placeholder` (priority 1) → first non-readonly → last.
- `<div contenteditable="true">` — **Kimi** (`.chat-input-editor`), Claude.ai, Notion-style editors. Focus via `document.querySelector('[contenteditable=true]').focus()`. Note: `textarea.value` reads empty after typing into a contenteditable; read `textContent` instead.

Full multi-textarea pick pattern and per-site quirks: see `references/multi-site-orchestration.md`.

## Multi-site comparison orchestration

To ask the same question to N AI sites and read all replies, run sites **serially** (not in parallel) — Chrome CDP doesn't handle concurrent WS connections to different tabs well. The orchestration pattern and the working script: `scripts/multi_ai_ask.py`. Verified 2026-06-02 across 4 sites:

| Site | Input | AX readable? | Notes |
|------|-------|--------------|-------|
| DeepSeek | textarea×1 | ✅ (new tab) | Best signal; ~1000-2000 chars across 20-40 segments |
| Doubao | textarea×2 (JS-pick) | ✅ (partial) | 2-4 segments, ~150-300 chars |
| Kimi | contenteditable | ⚠️ short replies | textContent read, not value |
| Grok | textarea×1 | ⚠️ needs login | xAI account cookies required |
| ChatGPT | textarea×1 | ❌ Shadow DOM | Use API instead |

## Pitfalls
- **Empty `text` in keyDown is mandatory.** Otherwise React double-counts characters (verified: `用3句话` → `用用33句句话话`).
- **Don't reuse msg_id=0** — Chrome's internal events use 0 too, you'll lose responses.
- **`DOM.enable` is required for `DOM.focus` / `DOM.querySelector`.** Enable before using, disable if you switch tasks.
- **DeepSeek submit key:** plain Enter submits; Shift+Enter is newline. If the textarea doesn't clear after Enter, you're probably in 识图模式 (image mode) or 深度思考 (deep thinking) toggled differently.
- **`screencapture -x` works** when CDP `Page.captureScreenshot` returns 0 bytes (Chrome GPU layer issue on some macOS versions).
- **Login state:** do NOT launch a fresh `chromium.launch()` — it has no cookies. Either reuse the user's Chrome via debug port, or copy the entire `Default/` profile directory before launch.

## See also
- `references/cdp-react-vue-bypass.md` — full technique writeup with the double-character gotcha explained
- `references/multi-site-orchestration.md` — multi-AI comparison pattern (input element detection, per-site quirks, site table)
- `scripts/cdp_ask_ai.py` — minimal working bot (asks DeepSeek, screenshots, prints path for vision readback)
- `scripts/multi_ai_ask.py` — ask the same question to N AI sites, read replies from AX tree
- Working production version: `~/.hermes/scripts/hermes_web_bot_v2.py`
