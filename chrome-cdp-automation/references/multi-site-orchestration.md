# Multi-Site AI Comparison Orchestration

End-to-end pattern: ask the same question to 4+ AI sites (DeepSeek, Doubao, Kimi, Grok, ChatGPT, etc.) in parallel-ish, then AX-read each reply, with screenshot fallback.

## The four-step pattern per site

1. **Find tab** — HTTP `urllib.request.urlopen("http://localhost:9333/json")`, filter by `type=="page"` and title/url substring match. Prefer the tab with non-default title (has history → user has been using it).
2. **Connect** — `websockets.connect(tab["webSocketDebuggerUrl"], max_size=20*1024*1024)`. Use 19-char hex `tabId` from the same JSON.
3. **Enable domains** — `Page.enable` then `DOM.enable`. **Do NOT enable Runtime.enable alongside DOM.enable** — they collide and Runtime.evaluate returns empty. Runtime is implicitly active once any of these is on.
4. **Locate input** — see Input Element Detection below.

Run sites **serially**, not in parallel. Chrome CDP does not handle concurrent WS connections to different tabs well — they'll fight over resources and some will hang.

## Input element detection (the actual hard part)

Modern AI sites use three different input element patterns. Detect in this order:

```python
# Step 1: Count textareas
r = await cdp.send("Runtime.evaluate", {
    "expression": "({ta: document.querySelectorAll('textarea').length, ce: document.querySelectorAll('[contenteditable=true]').length, url: location.href})",
    "returnByValue": True
})
info = r["result"]["result"]["value"]
```

| Pattern | Sites | How to interact |
|---------|-------|-----------------|
| `<textarea>` × 1 | DeepSeek, Grok, ChatGPT | `DOM.querySelector("textarea")` + `DOM.focus` |
| `<textarea>` × 2+ | Doubao (input + hidden), 豆包 multi-input | **JS-pick**: visible + non-readonly + has `placeholder` (priority 1), else first non-readonly, else last |
| `<div contenteditable="true">` | **Kimi** (`.chat-input-editor`), some Notion-style editors | `document.querySelector('[contenteditable=true]').focus()` — note: `textarea.value` reads empty after input; read `textContent` instead |

**Don't blindly use `querySelector("textarea")` for the multi-textarea case** — it'll grab the wrong one (hidden search box, side panel composer, etc.). The placeholder heuristic catches all current sites.

## Reading the AI reply: AX tree (works for new tabs)

**Discovery: a freshly opened tab → ask → reply can be read by `Accessibility.getFullAXTree` directly, no screenshot needed.** An old tab with conversation history will put the reply in Shadow DOM and AX returns nothing.

```python
# After sending + waiting 25-30s for generation
r = await cdp.send("Accessibility.getFullAXTree", {"depth": 25, "fetchRelatives": True})
nodes = r["result"]["nodes"]
ai_reply = "\n".join(
    n["name"]["value"] for n in nodes
    if n.get("role",{}).get("value") == "StaticText" and len(n.get("name",{}).get("value","")) > 30
)
```

- `StaticText` role + length > 30 chars filters out UI labels and sidebars.
- Sometimes 30 chars is too aggressive (Kimi sometimes has short structured answers); try 15 if empty.
- DeepSeek: ~1000-2000 chars across 20-40 segments.
- Doubao: ~150-300 chars across 2-4 segments (its UI is heavier, most text is in Shadow DOM).
- Grok / Kimi / ChatGPT: variable.

## Fallback chain when AX returns empty

1. **New tab retry** — open a fresh tab to the same URL, ask there, AX often works.
2. **screencapture per tab** — `Page.bringToFront` on each tab (with 1-2s sleep), then `screencapture -x -t png <path>`. Use this for one-shot per-tab captures (compare results visually).
3. **Direct API** — for known providers (DeepSeek API, OpenAI API, etc.) bypass the browser entirely. Use this when the goal is "get an answer" not "test the web UI".

## CDP `Page.captureScreenshot` is unreliable on macOS

Returns 0 bytes or hangs on some Chrome versions (GPU compositing layer issue). **Don't depend on it for verification.** Use `screencapture -x` (macOS native) as the screenshot tool, and only after `Page.bringToFront` to control which window is captured.

## Multi-textarea JS pick pattern

```python
r = await cdp.send("Runtime.evaluate", {
    "expression": """
        (() => {
            const tas = document.querySelectorAll('textarea');
            let target = null;
            // priority 1: visible + non-readonly + has placeholder (the user input box)
            for (let t of tas) {
                if (t.offsetParent !== null && !t.readOnly && t.placeholder) {
                    target = t; break;
                }
            }
            // priority 2: first non-readonly
            if (!target) for (let t of tas) if (!t.readOnly) { target = t; break; }
            // priority 3: last
            if (!target) target = tas[tas.length-1];
            target.focus();
            return {ph: target.placeholder, idx: Array.from(tas).indexOf(target), total: tas.length};
        })()
    """,
    "returnByValue": True
})
```

## Site-specific quirks observed 2026-06-02

| Site | Input | Login needed? | AX read? | Other |
|------|-------|---------------|----------|-------|
| DeepSeek | textarea×1 | optional (works without) | ✅ (new tab) | Send via Enter |
| Doubao | textarea×2 | yes for full features | ✅ (partial) | 2nd textarea is hidden search; use JS pick |
| Kimi | contenteditable div | yes | ❌ (mostly) | New tab returns text via AX, established tab Shadow DOM |
| Grok | textarea×1 | yes (xAI account) | ⚠️ partial | Login redirects to accounts.x.ai; needs cookies in profile |
| ChatGPT | textarea×1 | yes | ❌ Shadow DOM heavy | Use API instead |
| Claude.ai | contenteditable | yes | ❌ Shadow DOM | Use API instead |

## Real multi-ask script

See `scripts/multi_ai_ask.py` for the working implementation. Usage:
```bash
python3 ~/.hermes/scripts/multi_ai_ask.py "Mac Mini 24G跑Hermes..."
```

Outputs a side-by-side comparison with each site's status (✅ success, ⚠️ AX empty + screenshot path, ❌ tab missing), the AX-read text, and a fallback screenshot for visual verification.
