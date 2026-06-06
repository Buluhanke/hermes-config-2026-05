---
name: ai-site-browser-e2e
description: Drive 11 AI websites (Gemini/Doubao/ChatGLM/DeepSeek/ChatGPT/Grok/Perplexity/Kimi/Tongyi/Copilot/Poe) via local Chrome CDP. Type into React/Next.js controlled textareas, send, capture the full streaming reply, persist as knowledge. Hard-won lessons from the 2026-06-03 through 2026-06-05 cross-tests. Use when the user asks to "open the browser and ask AI", automate a logged-in chat site, or capture a long AI reply that web_extract cannot render.
---

# AI-Site Browser E2E — CDP control of logged-in AI chats

## When to use
- Ask a question to Gemini / Doubao / ChatGLM / DeepSeek / ChatGPT / Grok / Perplexity / Kimi / Tongyi Qianwen / Copilot / Poe (or similar) as a logged-in human, so account history, custom GPTs, plugin access all work.
- The reply is long / streaming / has images / has code blocks — anything `web_extract` cannot capture.
- The user wants the reply saved as knowledge in `/tmp/ai_knowledge_*.md` or to fact_store, not just shown in chat.

## When NOT to use
- Pure API call (cheaper, faster). Only do this when API is unavailable, quota'd, or the user explicitly needs the logged-in experience.
- Static page reading (use `web_extract`).
- Sites that don't have a logged-in chat (public Q&A, docs).

## Before running any multi-site batch (multi_ask_v3 / 9-site broadcast / cross-test) — mandatory preflight (2026-06-05 lesson)

A multi-site batch means: you plan to send one question to N≥4 AI sites in parallel via `multi_ask_v3.py` (or any batch driver). It is **NOT** a 1-off `browser_navigate`. Two failure modes the 13:00 and 13:50 sessions hit:

**Failure mode A — no Chrome running at all** (13:00): you call `multi_ask_v3.py` straight away. It walks `http://localhost:9333/json` looking for tabs matching site names. Zero matches → 0/6 logged as "tab不存在". User yells. The script is not broken — Chrome simply isn't running with debug port open.

**Failure mode B — Chrome running but uBlock blocks 4/9 sites** (13:50): Chrome is up (good), but the user has uBlock Origin (or another content blocker) installed. `browser_navigate` to chatglm/chatgpt/grok/deepseek returns `net::ERR_BLOCKED_BY_CLIENT`. The 4 created tabs are silently killed by Chrome. The other 5 work. The multi_ask ends up with a mix of success and mysterious gaps.

**Mandatory preflight before any multi-site batch:**

```bash
# 1. Is Chrome up with debug port? If not, start it.
lsof -i :9333 >/dev/null 2>&1 || {
    pkill -9 -f "Google Chrome" 2>/dev/null; sleep 2
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
        --remote-debugging-port=9333 \
        --user-data-dir="$HOME/.hermes/chrome-debug" \
        --disable-extensions \
        --no-first-run --no-default-browser-check \
        >/dev/null 2>&1 &
    sleep 5
}
# 2. Are the target AI sites actually reachable tabs?
curl -s http://localhost:9333/json | python3 -c "
import sys, json
tabs = json.load(sys.stdin)
need = ['gemini.google.com','doubao.com','chatglm.cn','chat.deepseek.com','chatgpt.com','grok.com','yuanbao.tencent.com','yiyan.baidu.com','tongyi.aliyun.com']
got = {n: any(n in t.get('url','') for t in tabs if t.get('type')=='page') for n in need}
for n, ok in got.items():
    print(('✅' if ok else '❌'), n)
missing = [n for n,ok in got.items() if not ok]
sys.exit(1 if missing else 0)
"
# 3. If any missing, open them via Target.createTarget + Page.navigate
#    (see "Bulk-open" section below for the full 9-site script)
# 4. THEN run multi_ask_v3
```

**Use `--disable-extensions` for multi-site batches.** The price (no ad blocking) is worth it: every blocked site costs a re-navigation + 5s re-login + a missed reply. The user's local Chrome on the regular port keeps its extensions; the debug port profile at `~/.hermes/chrome-debug` is the disposable sandbox.

**Why not also block uBlock via CDP** (e.g. `Network.setBlockedURLs`): uBlock works at the browser-internal URL filter level, not the network layer, so CDP can't see it. The only way to neuter it for a batch session is to launch Chrome without it loaded.

**Symptom → root cause → fix table** for the four failure modes you will hit:

| Symptom | Root cause | Fix |
|---------|-------|-----|
| `multi_ask_v3` says "tab不存在" for all 6 sites | Chrome not running on 9333 | Preflight step 1 |
| `multi_ask_v3` says "tab不存在" for all 6 sites, BUT `lsof -i :9333` shows Chrome is up | **Chrome running on 9333 but ZERO page tabs** — debug port is up, system profile cookies are intact, just no AI tabs opened yet. Happens after a Chrome restart with `--user-data-dir=.../Default` because tab state is in-memory. | Run the bulk-open script in `references/expanding-ai-sites-20260605.md` to create + navigate 9 tabs. Then re-run preflight step 2. |
| `browser_navigate` to a specific site returns `net::ERR_BLOCKED_BY_CLIENT` | uBlock / content blocker extension | Restart Chrome with `--disable-extensions` |
| `Target.createTarget` returns a targetId but `/json` doesn't list it | New tab is `background=true` and the navigation got blocked; Chrome killed it | Use `Target.activateTarget` after create, or use `browser_navigate` (which auto-acquires the fresh context) instead |

**Don't trust the title alone** — a tab titled "ChatGPT" might be on a login page or a Cloudflare challenge. After opening, wait 5s, then `browser_snapshot` and check for the user-account indicator (avatar / sidebar / "New chat" button) before declaring victory.

**Don't trust the user's "it didn't work" claim without verifying either** — a 2026-06-05 incident: agent reported "9 站 tab 全开" after seeing the right titles, user said "都是空白 about:blank", agent immediately believed it and started apologizing. `curl /json` actually showed all 9 tabs with real chat URLs and the bodies had real content. Rule: any user claim about agent state (tabs are blank, files are missing, services are down) — verify with a fresh `curl /json`, `ls`, `lsof`, or `Runtime.evaluate` reading `document.body.innerText.slice(0, 200)` BEFORE acting on the claim. Don't auto-concede; verify, then speak.

**Don't trust the "navigate ok" log line either** — `Target.createTarget` + `Page.navigate` returning "ok" does NOT mean the tab landed on a working chat page. The 2026-06-05 13:50 multi_ask run reported "9 站创建+navigate 全部 ok", but `/json` showed 0 page tabs afterward — uBlock killed them silently between create and verify. **Mandatory post-batch verification**: after any batch-open script, re-`curl /json`, count `type=='page'` tabs, sample 2-3 with `Runtime.evaluate` reading `document.body.innerText.slice(0, 200)`. If the count or the body content is wrong, debug before reporting "success".

**Generalize**: the "trust but verify" discipline is not unique to multi-site batches. It applies any time the agent is about to report state: tab list, file existence, service health, memory content, config keys, user attribute. Run the live query that proves the claim. The discipline is captured as a class-level pitfall in `verification-before-reporting` (if loaded).

## Critical: `browser.cdp_url` must point to local Chrome (2026-06-04 fix)

**The original failure (5/6 sites blocked)**: Hermes' browser tools default to a **headless Chromium** backend (no login cookies, triggers Cloudflare/CAPTCHA on all major AI sites).

**The fix**: Set `browser.cdp_url=ws://127.0.0.1:9333` in `~/.hermes/config.yaml`. This makes `browser_navigate` / `browser_snapshot` / `browser_type` / `browser_press` / `browser_console` all drive the **user's real Chrome** that's already logged into all 6 AI sites.

```bash
hermes config set browser.cdp_url ws://127.0.0.1:9333
# No reload command needed — takes effect on next browser_navigate call
```

After setting this, all 6 sites (Gemini, Doubao, ChatGLM, DeepSeek, ChatGPT, Grok) work reliably from the same logged-in Chrome profile. This was verified 2026-06-04 with 100% success across all 6 stations.

**How to tell which backend is active**: `browser_navigate` returns a snapshot with a `stealth_warning` field mentioning `"cdp_override"` when using local Chrome CDP. If you see `"Running WITHOUT residential proxies"` the backend is headless — set `browser.cdp_url` immediately.

**⚠️ `browserContextId` staleness trap (discovered 2026-06-05)**: `Target.getTargets` returns a `browserContextId` (e.g. `C6BE3C0E0487E102EEC9583E79D2323A`). This ID is **ephemeral** — it changes every time the CDP WebSocket connection is re-established (gateway restart, session reconnect, `browser_cdp` call that re-initializes the connection). When the context ID goes stale:
- `Target.createTarget` fails with `Failed to find browser context with id ...`
- `Target.getTargets` still succeeds but returns only service workers, zero page tabs

**Recovery pattern** (two options, in order of reliability):
1. **Just use `browser_navigate(url)`** — it auto-acquires the fresh context from the currently-connected Chrome CDP session. No manual context ID needed.
2. **Call `Target.getTargets` fresh** to get the new context ID, then use `Target.createTarget` with the new ID.

Never hardcode a `browserContextId` across sessions or assume it persists within a session after a gateway event. The `browser_navigate` tool is more resilient precisely because it uses the active CDP connection's current context.

**Shebang trap (2026-06-04)**: Scripts that launch Chrome via Playwright (`chrome-debug-launcher.py`, ad-hoc bots) MUST use Hermes' own Python venv, not system Python or `/usr/bin/env python3`:

```
#!/Users/aimac/.hermes/hermes-agent/venv/bin/python
```

System Python 3.14 resolves to the playwright package in `/Library/Frameworks/Python.framework/...` which installs browsers to the wrong `ms-playwright` cache (e.g. `chromium_headless_shell-1208`), while Hermes' venv playwright uses `chromium_headless_shell-1217` or later. Symptom: `playwright._impl._errors.Error: Executable doesn't exist at ...chromium_headless_shell-1208`. Fix: always use the venv python shebang.

**uBlock / content blocker trap (2026-06-05)**: When launching Chrome for a multi-site batch, ALWAYS pass `--disable-extensions`. The user's local Chrome typically has uBlock Origin installed; it lives in `~/.hermes/chrome-debug/Extensions/bpoadfkcbjbfhfodiogcnhhhpibjhbnh/` (the `bpoadfkcb...` ID is uBlock Origin's stable extension ID on the Chrome Web Store). uBlock works at the browser-internal URL filter level, so it will:
- Block `chatglm.cn`, `chatgpt.com`, `grok.com`, `chat.deepseek.com` with `net::ERR_BLOCKED_BY_CLIENT` when you call `browser_navigate` or `Page.navigate` on them
- Silently kill the newly-created tab (`Target.createTarget` returns a targetId, but the tab disappears from `/json` after a few hundred ms)
- The other 5 sites (Gemini, Doubao, ChatGLM if whitelisted, etc.) work fine, masking the problem

Detection: any `browser_navigate` to a known AI site returning `net::ERR_BLOCKED_BY_CLIENT`. Fix: `pkill -9 -f "Google Chrome"; sleep 2; "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9333 --user-data-dir="$HOME/.hermes/chrome-debug" --disable-extensions --no-first-run --no-default-browser-check &`. The user's regular Chrome keeps its extensions; the debug-profile Chrome is the sandbox.

Per-site whitelist as an alternative (preserves uBlock for the user): visit `chrome://extensions` in their real Chrome, find uBlock Origin, click "Details", then add `chatglm.cn`, `chatgpt.com`, etc. to the "Allow in incognito" / site whitelist. Permanent fix but requires user action.

**Cloudflare / 验证码 trap (2026-06-05)**: Perplexity and Poe show a "正在进行安全验证" CAPTCHA iframe on the first navigation. **Not a login failure** — waiting 5s and re-navigating resolves it. If after 2 retries the iframe is still up, the session is poisoned and you'll need to close that tab and start fresh.

**Which Chrome runs on 9333**: The user's Chrome is started with `--remote-debugging-port=9333 --user-data-dir=~/.hermes/chrome-debug`. Check with:
```bash
lsof -i :9333 | grep Chrome
```

```
"${HERMES_CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}" \
    --remote-debugging-port=9333 \
    --user-data-dir="$HOME/.hermes/chrome-debug" \
    --remote-allow-origins=* \
    about:blank >/dev/null 2>&1 &
```

## The 4-line skeleton (works on 4 of 6 sites)

**2026-06-06 fix**: the original skeleton used `Target.attachToTarget` with `flatten:True` and tried to read the response — that path is buggy because CDP's `attachedToTarget` is delivered as an **event** (params.sessionId), not a response. The simpler and more reliable path is to **skip attach entirely** and use the `page` tab's `webSocketDebuggerUrl` directly — that WS is already tab-scoped, every CDP command sent on it executes in that page's context.

```python
import sys
sys.path.insert(0, "/Users/aimac/.hermes/hermes-agent")
from hermes_tools import browser_cdp

# 1. Find the target tab via /json (the browser_*/Target.getTargets path)
tabs = browser_cdp(method="Target.getTargets")
tab = next(t for t in tabs["result"]["targetInfos"]
           if "gemini.google.com" in t["url"])
# 2. The tab's webSocketDebuggerUrl from /json is the per-tab WS — use directly
#    (DON'T re-attach; it's already attached)
import json, urllib.request
all_tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9333/json").read())
page_tab = next(t for t in all_tabs if t["id"] == tab["targetId"])
import websockets
ws = await websockets.connect(page_tab["webSocketDebuggerUrl"], max_size=5*1024*1024)
# 3. Send commands directly, no sessionId needed for page-scoped WS
async def js(expr):
    mid = 1
    await ws.send(json.dumps({"id": mid, "method": "Runtime.evaluate",
        "params": {"expression": expr, "returnByValue": True, "awaitPromise": True}}))
    r = json.loads(await ws.recv())
    return r["result"]["result"]["result"].get("value")
# 4. Now read DOM, dispatch events, click
print(js("document.querySelector('div[contenteditable=true]')?.innerText"))
```

**Why skip attach**: attaching a second session to an already-attached target causes `Session with given id not found` errors when subsequent calls reference the wrong scope. The page tab's WS is one session per page; just use it.

**When you DO need attach**: if you're on the **browser-level** WS (the one from `/json/version`) and want to drive a specific tab without re-connecting — that's the case for `multi_ask_v3` which keeps one browser WS open and attaches per site. There, the `params.sessionId` from the `Target.attachedToTarget` event IS the per-site sessionId, and all subsequent commands must include `sessionId` in the **message top level** (not in `params`) when `flatten:True`, or in `params.sessionId` when `flatten:False`.

## React 18 / Next.js controlled textarea — 6-step escalation

Different AI sites use different frameworks. The textarea value is wired into React's internal state, so writing to `el.value` and dispatching `input` does NOT trigger React onChange. Bypass the framework:

| Step | Code | Use when |
|------|------|----------|
| 1 | `Input.insertText` CDP command, then `el.focus()` | Plain contenteditable divs — works on Gemini, ChatGPT, DeepSeek |
| 2 | `ta.value=...` + `Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(ta, v)` + `dispatchEvent(new Event('input',{bubbles:true}))` | React-controlled textarea — works on ChatGLM |
| 3 | Find `el[Object.keys(el).find(k=>k.startsWith('__reactProps'))]` and call `onChange({target:{value: v}, preventDefault:()=>{}, stopPropagation:()=>{}})` | When the framework reads `event.target` and rejects synthetic events — fix by also passing `nativeEvent: new Event('input')` |
| 4 | If `__reactProps` includes `onCompositionEnd` — call it FIRST to release the IME lock | Some React-Intl builds refuse to accept input while "composing" |
| 5 | `Input.dispatchKeyEvent` char-by-char through CDP | Bypasses the React state engine entirely. Slow (about 50ms per char) but bulletproof |
| 6 | Give up on the textarea. Use `appleScript` / `computer_use` to physically Cmd-V a clipboard string, then press Return | The only reliable path for Grok's Next.js streaming placeholder (see Grok section) |

Diagnostic: if you dispatchEvent and the DOM updates but the send button stays disabled for more than 5s, React's internal state diff is not matching what you wrote. The button-enable state is the truth signal.

## Site-specific tactics (verified 2026-06-03)

### Gemini (gemini.google.com) — EASIEST
- Editor: `div.ql-editor[contenteditable=true]` — works via `browser_type` + `browser_click` send button
- Approach: `browser_navigate` → `browser_snapshot` (AX tree) → `browser_type` into textbox ref → `browser_click` send ref
- Reply read: `browser_snapshot(full=true)` returns AX tree with full StaticText — no AppleScript needed
- The send button ref is `@e19` (disabled initially, becomes enabled after typing)
- Key: after sending, poll `browser_snapshot` until the response content stabilizes (new paragraphs appear under "Gemini 说")
- Gemini AX tree response includes heading structure, lists, blockquote — richer than `innerText`

### DeepSeek (chat.deepseek.com) — EASY but often logged out
- `browser_navigate` often lands on `/sign_in` login page — if login page, stop and report
- Editor (logged in): textarea with placeholder `请输入手机号` or `给 DeepSeek 发送消息`
- Approach: `browser_type` + Enter key via `browser_press('Enter')`
- Reply read: `browser_snapshot(full=true)` poll until last paragraph stops growing

### ChatGPT (chatgpt.com) — EASY
- Editor: `div#prompt-textarea[contenteditable=true]`
- Approach: focus + `Input.insertText`. Click submit via Enter, not the button (the button selector rotates per A/B test)

### ChatGLM (chatglm.cn) — MEDIUM
- Editor: React-controlled textarea with `onChange` in `__reactProps`
- Approach: Step 2 from the table. The third arg to `dispatchEvent` must be `{bubbles:true}` or onChange won't fire
- After send, wait for the streaming container to STOP by polling the same DOM element — chatglm streams in chunks and a naive `wait_for_text` returns the first sentence only

### Doubao (doubao.com) — MEDIUM, requires login
- `browser_navigate` often lands on login page first — if login modal shows, stop and report
- Editor (logged in): `textarea[placeholder="发消息..."]` ref `@e18`
- Approach: `browser_type` + `browser_press('Enter')`
- Reply read: poll `browser_snapshot` (DOM grows in paragraphs)
- Caveat: if page shows a verification CAPTCHA / drag-to-match game in an iframe, Doubao is blocked — cannot automate past it
- Known limitation: the `Iframe` with a Canvas drag game appears after login — this blocks CDP automation

### Grok (grok.com) — EASY with local Chrome CDP, HARD with headless
- **CRITICAL**: Grok Cloudflare challenge ONLY fires when using Hermes' built-in headless browser (`browser_navigate` with no `cdp_url` configured). When `browser.cdp_url=ws://127.0.0.1:9333` is set in `~/.hermes/config.yaml` and the user is already logged into Grok in their local Chrome, Grok works perfectly — Cloudflare sees the real Chrome profile and lets it through.
- **CRITICAL**: Grok Cloudflare challenge ONLY fires when using Hermes' built-in headless browser (`browser_navigate` with no `cdp_url` configured). When `browser.cdp_url=ws://127.0.0.1:9333` is set in `~/.hermes/config.yaml`, Grok works — but Grok is NOT automatically logged in via the Chrome profile (unlike the other 5 sites). You must separately log into Grok once; its cookies are stored in the same `~/.hermes/chrome-debug` profile, so the login persists across sessions.

**Login verification**: When `browser.cdp_url` is configured, Grok's page shows `button "登录"` and `button "注册"` when logged out, versus a chat interface when logged in. Do not assume any AI site is logged in — always verify by navigating and reading the AX tree.
- Editor: `textarea[placeholder="Ask Grok anything"]` — standard React textarea, use `browser_type` + `browser_press('Enter')`
- Reply read: poll `browser_console` with `document.body.innerText.slice(-N)` until streaming completes
- After sending, wait ~9s for Grok's "思考了 Xs" to appear before reading the reply

### Tongyi Qianwen (qianwen.com) — MEDIUM, requires Enter not click (2026-06-06 verified)
- Editor: `div[class*="whitespace-pre-wrap break-words"][contenteditable=true]` — ProseMirror-like custom contenteditable
- **CRITICAL: send via `browser_press('Enter')`, NOT `browser_click` on the send button**. The "发送消息" button is enabled in the AX tree after typing, but `browser_click` on it does NOT actually trigger the send — likely a React `onClick` that consumes the synthetic event before bubbling. Pressing Enter on the focused textbox does trigger send.
- Login verification: after `browser_navigate`, the sidebar must show username "Qwen1929" (or whatever your account is). If it shows "未登录" / blank avatar, stop and report — Qwen has separate SSO cookies and a fresh tab sometimes opens in logged-out state even when cookies are present.
- Approach: `browser_navigate` → `browser_snapshot` (find textbox ref + send button ref) → `browser_click` on textbox to focus → `browser_type` → `browser_press('Enter')`
- Reply read: Qwen's reply is in `div.markdown-pc-special-class` and `div.qk-markdown`. The browser_console probe `document.querySelectorAll('.markdown, [class*="markdown"]')` returns the right container. Read with `el.innerText` — the rendered markdown text is what you want.
- Polling pattern: after Enter, wait 20-30s (Qwen is slower than DeepSeek for long answers), then `browser_console` to read. The reply container appears below the user's question paragraph in the conversation thread.
- Known quirk: `browser_click` on the send button (`@e32` in the typical snapshot) appears to succeed ("clicked: @e32") but the text stays in the input box and no reply is generated. Always use Enter, never the button, on Qwen.

## Polling the streaming reply — the right pattern

```python
def wait_for_reply_done(sel, stable_for=1.5, max_wait=120):
    import time
    last_text, stable_since = "", 0
    t0 = time.monotonic()
    while time.monotonic() - t0 < max_wait:
        text = js(f"[...document.querySelectorAll({sel!r})].map(e=>e.innerText).join('\\n')")
        if text and text == last_text:
            if time.monotonic() - stable_since > stable_for:
                return text
        else:
            stable_since = time.monotonic()
            last_text = text
        time.sleep(0.4)
    return last_text
```

Do not use a fixed `sleep(N)` — streaming replies vary from 3s (one-liner) to 90s (essay). The size-stability heuristic saves minutes per query and never truncates.

## Persist the reply

```python
import datetime, pathlib
out = pathlib.Path(f"/tmp/ai_knowledge_{datetime.date.today()}.md")
with out.open("a", encoding="utf-8") as f:
    f.write(f"# Q: {question}\n\nA ({model}):\n\n{reply}\n\n---\n")
```

Use a daily rotating file in `/tmp/`, append-mode. Do not dump to stdout — user cannot grep terminal scrollback.

## Chrome-on-macOS fd ceiling trap
macOS default `kern.maxfilesperproc=256`. Cloudflare Warp (and most transparent proxies) leave sockets in `CLOSE_WAIT` longer than Linux. If you open a fresh `httpx.AsyncClient` per request, you hit the 256 fd ceiling around request #35 and the asyncio loop starves, producing `telegram.error.TimedOut: Pool timeout`. Already solved project-wide by `gateway/platforms/_shared_http_client.py`. But if you write a one-off browser-bot script, always mount a shared `httpx.AsyncClient` with:

```
Limits(max_connections=50, max_keepalive_connections=10, keepalive_expiry=2.0, pool_timeout=5.0)
```

Reference: `/Users/aimac/.hermes/hermes-agent/gateway/platforms/_shared_http_client.py`.

## Cleanup on exit

```python
# Jump the tab to about:blank so the user does not see a half-typed prompt.
# NEVER close the tab — the session cookie lives in the same storage.
js("location.href = 'about:blank'")
```

## Failure modes to expect (and pre-empt)

| Symptom | Cause | Fix |
|---------|-------|-----|
| `dispatchEvent` updates DOM, send-btn still disabled 5s later | React internal state diff rejected your event | Use Step 3/4/5 escalation |
| `Input.dispatchKeyEvent` returns "Invalid 'text' parameter" | Chinese char with `nativeVirtualKeyCode` int32 missing | Use Step 5 with `text` field only, no `key` code |
| `Runtime.evaluate` returns `undefined` in `chat/new` tab | Cross-origin iframe — top page is just a shell | Give up, switch sites |
| Tab list shows the URL but `attachToTarget` returns no sessionId | Tab is in a different browser process (chrome `--site-per-process`) | Use `Target.setAutoAttach` first, or accept the iframe is unreachable |
| `Object.keys(el)` shows no `__reactProps$xxx` | Element is in a portal or virtualized list | Search parent for the React fiber, then walk to the props |
| Reply never stabilizes (always growing) | Site is regenerating content (e.g. "Searching the web...") | Add a 90s max_wait, accept partial reply |

## Two real-world pitfalls discovered in 2026-06-05 sessions (must-read)

### 1. 豆包 / ByteDance sites: Shadow DOM wraps the message container

`document.body.innerText` returns the outer shell (sidebar, header) but the AI reply lives inside a `ShadowRoot` and is invisible to `innerText`, `querySelectorAll('p')`, and `querySelectorAll('[class*="message"]')` from the top-level document. The `browser_console(expression="document.body.innerText")` call returns the page chrome but **zero reply text**.

**Detection probe** — run this first, before assuming innerText will work:

```js
(function(){
    var msgEl = document.querySelector('[class*="message-bubble"], [class*="chat-message"], [class*="message-content"]');
    if(!msgEl) return 'no message element found';
    var shadowRoot = msgEl.shadowRoot || msgEl.querySelector('*')?.shadowRoot;
    return shadowRoot ? 'SHADOW_DOM_detected' : 'normal_DOM';
})()
```

**If `SHADOW_DOM_detected` → skip DOM reading, go straight to vision screenshot.** Do not waste 10 minutes hunting for selectors. The fix path is:

```python
# instead of browser_console(expr="document.body.innerText")
screenshot = browser_vision(question="请完整读取页面上所有AI回复的文本内容，按原顺序保留")
```

Affects: 豆包, and any future ByteDance/抖音系 product. Claude/Perplexity/Kimi/Tongyi are normal DOM and don't need this.

### 2. Anti-detect injection evaporates across Chrome restarts

The `~/.hermes/anti_detect_plugins.js` patch only takes effect:
- For new tabs created after `addScriptToEvaluateOnNewDocument` is registered
- For the current tab within the current CDP session

When Chrome restarts (manual or after `pkill -9 -f "Google Chrome"`), the next session's tabs are fresh, **without the patch**. Symptom: `verify_all_3.py` drops from 100/100 to 97/100 — `plugins.length=5` (Puppeteer default leaks through), `chrome.runtime=undefined`.

**Rule**: before any multi-site batch, run:

```bash
python3 ~/.hermes/scripts/anti_detect_inject.py --port 9333
```

This re-injects the plugins patch into all 7-9 open tabs and re-registers `addScriptToEvaluateOnNewDocument` for future tabs. Takes <1s, no Chrome restart needed. The session can then proceed.

Full reverse-detection surface lives in the `anti-detection-stealth` skill.

## Quick-start script (Gemini demo, about 80 lines)
Save as `/tmp/ask_gemini.py` and run with the question as argv[1].

```python
import sys, time, pathlib, datetime
sys.path.insert(0, "/Users/aimac/.hermes/hermes-agent")
from hermes_tools import browser_cdp

def find_tab(needle):
    ts = browser_cdp(method="Target.getTargets")["result"]["targetInfos"]
    return next((t for t in ts if needle in t.get("url","")), None)

def attach(tid):
    return browser_cdp(method="Target.attachToTarget",
                       params={"targetId": tid, "flatten": True})["result"]["sessionId"]

def js(expr, tid):
    return browser_cdp(method="Runtime.evaluate",
                       params={"expression": expr, "returnByValue": True,
                               "awaitPromise": True},
                       target_id=tid)["result"]["result"]["result"].get("value")

Q = sys.argv[1] if len(sys.argv) > 1 else "用一句话解释量子纠缠"
t = find_tab("gemini.google.com/app")
assert t, "No Gemini tab open — open gemini.google.com/app in Chrome first"
SID = attach(t["targetId"]); TID = t["targetId"]

# Focus + clear
js("(async()=>{const ed=document.querySelector('div.ql-editor[contenteditable=true]');ed.focus();ed.innerText='';return 1})()", TID)
# InsertText via CDP (the magic step)
browser_cdp(method="Input.insertText", params={"text": Q}, target_id=TID)
time.sleep(0.5)
# Send
js('document.querySelector(\'button[aria-label="Send message"]\')?.click()', TID)

# Wait for reply
last, stable = "", 0
t0 = time.time()
while time.time() - t0 < 120:
    cur = js("[...document.querySelectorAll('.markdown')].map(e=>e.innerText).join('\\n')", TID)
    if cur and cur == last:
        stable += 1
        if stable > 4: break
    else:
        stable = 0; last = cur
    time.sleep(0.5)

# Persist + clean
out = pathlib.Path(f"/tmp/ai_knowledge_{datetime.date.today()}.md")
out.parent.mkdir(exist_ok=True)
with out.open("a", encoding="utf-8") as f:
    f.write(f"# Q: {Q}\n\nA: {last}\n\n---\n")
js("location.href='about:blank'", TID)
print(f"GEMINI: {len(last)} chars saved to {out}")
```

## Cross-references
- `chrome-cdp-automation` — generic CDP wrappers; use these instead of hand-rolling WebSocket
- `hermes-cdp-hardcore-type` — the React 18 + custom input engine 6-step escalation table
- `hermes-vision-agent` — fallback: if the textarea is in a cross-origin iframe, take a screenshot + use VLM to read the page
- `hermes_web_bot_cdp.py` (in `~/.hermes/scripts/`) — productionized 6-site driver
- `gateway/platforms/_shared_http_client.py` — shared httpx client all browser-bot scripts should use
- `~/.hermes/chrome-debug/` — the persistent Chrome profile (do not `pkill`)
- `references/chrome-cookie-sync-failure.md` — why copying Cookies/Login Data from the user's real Chrome to a Playwright profile does NOT transfer login sessions (os_crypt + SQLite WAL reasons); profile-launch is the right approach
- `references/login-state-taxonomy.md` — AX-tree signals for logged-in vs logged-out vs paywall-gated states across all 6 sites
 — why copying Cookies/Login Data from the user's real Chrome to a Playwright profile does NOT transfer login sessions (os_crypt + SQLite WAL reasons); profile-launch is the right approach
- `references/expanding-ai-sites-20260605.md` — **bulk-open N new sites for user login** (the 6→12 expansion workflow)
- `references/9-station-broadcast-results-2026-06-06.md` — **9 站 broadcast 实战 (实测 7 站真回复 + 共识表 + 假阳性判定 + 4 维证据验证 SOP)**
- `references/multi-site-parallel-research-20260605.md` — send-first-read-later pattern: which AI sites persist conversations in sidebar vs. which must be read in-page immediately. Includes 12-site broadcast script and Cloudflare behavior taxonomy.

## Expanding the AI site roster — bulk-open for one-time login (2026-06-05)

When the user wants to add new AI sites to the working roster (e.g. the 2026-06-05 expansion from 6→12 sites), the workflow is:

1. **Probe existing logins first** — the user's real Chrome likely already has Claude/ChatGPT/Gemini/etc. logged in. Use `browser_cdp(method="Target.getTargets")` to list open tabs. However, tab titles alone are NOT sufficient — a tab titled "Claude" might be on a login page. Always **navigate to the site and read the AX tree** for user-account indicators (see `references/login-state-taxonomy.md`). Avoids asking the user to re-login sites they're already in.
2. **Bulk-open remaining sites with `Target.createTarget`** — works even when the user has 0 tabs open on those sites. The MCP / Hermes `browser_navigate` tool is unreliable for this (see pitfall below), so go direct:
   ```python
   for url in ["https://www.perplexity.ai", "https://kimi.moonshot.cn", ...]:
       browser_cdp(method="Target.createTarget", params={"url": url})
   ```
3. **Tell the user to switch to Chrome and log in once per tab** — each site's cookies persist in the Chrome profile, so this is a one-time setup. They stay logged in across Chrome restarts.
4. **Verify by re-listing targets** after the user confirms — each site's title should change from "Sign in - Google" to the site's chat/homepage title.

**Why not `browser_navigate` for this**: the `browser_navigate` tool requires `node_modules/.bin/agent-browser` which is missing in some sessions. `browser_cdp` with `Target.createTarget` works without that dependency. Always prefer the CDP direct call for batch tab creation.

**Which sites to expand to first** (2026-06-05 priority list): Perplexity (search citations), Kimi (200K context Chinese), Tongyi Qianwen (Alibaba stack), MS Copilot (free GPT-4), Poe (1-account-30-models). All five worked on first CDP open.

### Verified login states (2026-06-05 full roster, 11 sites → 2026-06-05 9-site operational roster)

**9-site operational roster (2026-06-05, what multi_ask_v3 actually drives)**:

| # | Site | URL | Login State | Account | Tab title after open |
|---|------|-----|-------------|---------|----------------------|
| 1 | Gemini | gemini.google.com/app | ✅ Logged in | K H (hanlukebu@gmail.com) | "Google Gemini" |
| 2 | Doubao | www.doubao.com/chat | ✅ Logged in | 用户320735 | "豆包 - 字节跳动旗下 AI 智能助手" |
| 3 | ChatGLM | chatglm.cn/main/alltoolsdetail | ✅ Logged in | GLM-5.1 | "智谱清言" |
| 4 | DeepSeek | chat.deepseek.com | ⚠️ Login expires | 罗 | If `/sign_in` appears, must re-login |
| 5 | ChatGPT | chatgpt.com | ✅ Logged in | keke | "ChatGPT" |
| 6 | Grok | grok.com | ✅ Logged in | lukebu (hanlukebu@gmail.com) | "Grok" |
| 7 | Yuanbao | yuanbao.tencent.com | ✅ Logged in | (腾讯账号) | "元宝-腾讯旗下全能AI助手" |
| 8 | Wenxin | yiyan.baidu.com | ✅ Logged in | (百度账号) | "文心一言" |
| 9 | Tongyi | tongyi.aliyun.com | ✅ Logged in | Qwen1929 | "千问-阿里 AI 助手" |

**Working batch-open script for these 9 (2026-06-05 13:50 verified)**:

```python
import json, urllib.request, asyncio, websockets, time

SITES = [
    ("Gemini",   "https://gemini.google.com/app"),
    ("Doubao",   "https://www.doubao.com/chat"),
    ("ChatGLM",  "https://chatglm.cn/main/alltoolsdetail"),
    ("DeepSeek", "https://chat.deepseek.com/"),
    ("ChatGPT",  "https://chatgpt.com/"),
    ("Grok",     "https://grok.com/"),
    ("Yuanbao",  "https://yuanbao.tencent.com/"),
    ("Wenxin",   "https://yiyan.baidu.com/"),
    ("Tongyi",   "https://tongyi.aliyun.com/qianwen/"),
]

ver = json.loads(urllib.request.urlopen("http://localhost:9333/json/version").read())
browser_ws = ver['webSocketDebuggerUrl']

async def open_and_navigate():
    async with websockets.connect(browser_ws, max_size=10*1024*1024) as ws:
        results, msg_id = [], 0
        for name, url in SITES:
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Target.createTarget",
                                       "params": {"url": "about:blank", "background": True}}))
            r = json.loads(await ws.recv())
            tid = r.get('result', {}).get('targetId')
            if not tid:
                results.append((name, "create_failed")); continue
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Target.attachToTarget",
                                       "params": {"targetId": tid, "flatten": True}}))
            sid = json.loads(await ws.recv()).get('params', {}).get('sessionId')
            msg_id += 1
            await ws.send(json.dumps({"id": msg_id, "method": "Page.navigate",
                                       "params": {"url": url}, "sessionId": sid}))
            try:
                for _ in range(8):
                    m = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
                    if m.get('id') == msg_id:
                        results.append((name, "ok")); break
            except asyncio.TimeoutError:
                results.append((name, "navigate_timeout"))
        return results

print(asyncio.run(open_and_navigate()))
time.sleep(8)  # let pages settle, login state to load
tabs = json.loads(urllib.request.urlopen("http://localhost:9333/json").read())
pages = [t for t in tabs if t.get('type') == 'page']
print(f"Open tabs ({len(pages)}):")
for p in pages: print(f"  {p['title'][:40]:40s} | {p['url'][:70]}")
```

Verified 8/9 tabs land on the chat page (DeepSeek flips to `/sign_in` if the session cookie is stale). Always re-list `/json` and verify tab count + URL after the script finishes, not just trust the `navigate ok` log line.

**⚠️ CRITICAL PITFALL — Gemini/ChatGPT lose conversations when navigated away from**: Gemini and ChatGPT (possibly Copilot) do NOT persist new conversations to sidebar history — the conversation disappears the moment you navigate to another tab. If you broadcast to multiple sites and navigate away before reading, you lose the reply and have to re-ask the question. Pattern: read Gemini and ChatGPT replies IN-PAGE immediately after streaming completes, BEFORE navigating anywhere else. See `references/multi-site-parallel-research-20260605.md` for the full site persistence taxonomy.

**Only Copilot requires user action** to log in. All other 10 sites are already authenticated via the Chrome profile.

## What this skill does NOT cover (out of scope)
- Voice-mode AI (Gemini Live, ChatGPT voice) — different APIs, different UI
- Image generation tabs (Midjourney, DALL-E) — uses canvas, not textareas
- API-driven access (which is way simpler — see `freellm-api-aggregation` skill)
- Sites behind paywall or aggressive bot detection (LinkedIn, Twitter) — need residential proxies + browser fingerprint rotation, not just CDP
