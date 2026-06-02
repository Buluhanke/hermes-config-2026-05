# AI Site DOM Selectors — Verified 2026-06-02

Selectors for reading AI reply text via `Runtime.evaluate` + `querySelector`, Tier 1 approach.

## Why Tier 1 over AX tree

- AX tree breaks on old tabs with conversation history (Shadow DOM boundary)
- `Runtime.evaluate` + CSS selector returns actual text directly, no tree walking
- Works on both fresh and old tabs
- No screenshot, no OCR, no post-processing

## Decision chain

```
Try Tier 1 selector → empty? → Try Tier 2 (AX tree, fresh tab only) → empty? → screenshot + vision_analyze
```

## Tier 1 verified selectors

### DeepSeek — `querySelector('.ds-markdown')`
```javascript
// Verified 2026-06-02 — returns full reply, ~1000-2000 chars
(() => {
    const els = document.querySelectorAll('.ds-markdown');
    if (els.length === 0) return {err: 'no .ds-markdown'};
    return {full: els[els.length-1].innerText};
})()
```
- `.ds-markdown` is a regular DOM element — the AI reply is mounted as its child, outside Shadow DOM
- Use `[els.length-1]` to get the LAST occurrence (the latest reply in a multi-turn conversation)

### Doubao — no confirmed selector (Tier 2 fallback)
- AX tree partial success: 2-4 segments, ~150-300 chars on fresh tab
- Site uses heavy Shadow DOM — selector TBD
- Workaround: `screencapture` + `vision_analyze`

### ChatGLM (智谱清言) — no confirmed selector
- Same Shadow DOM pattern as Doubao
- Test selector: `.output-item`, `.message-content`, `[role="article"]`
- AX tree on fresh tab works partially

### ChatGPT — no selector available
- Heavy Shadow DOM: `guest-mode`, `chat-stream` elements are inside closed Shadow DOM
- Login required
- Tier 3: screenshot + vision_analyze (most reliable)

### Gemini — no selector
- Site is a webview iframe (`<webview>` element) — CDP cannot access its DOM directly
- `Accessibility.getFullAXTree` on the outer page returns iframe node, not inner content
- Workaround: target the iframe's tab directly via `Target.createTarget` to the iframe URL

### Grok — selector TBD (blocked by Cloudflare)
- Cloudflare challenge page blocks all automation
- Needs authenticated session + Cloudflare clearance cookie
- Selector (preliminary, unverified): `.markdown-body`, `.prose`

## Completion signal: bodyLen growth (NOT stop button)

Modern AI sites render "停止生成" inside private Shadow DOM — neither CDP nor AX can see it.

**Robust signal**: `document.body.innerText.length` monotonic growth.

```python
# Polling loop
prev_len = 0
stable_cycles = 0
while True:
    r = await cdp.send("Runtime.evaluate", {
        "expression": "document.body.innerText.length",
        "returnByValue": True
    })
    curr_len = r["result"]["result"]["value"]
    if curr_len > prev_len:
        stable_cycles = 0
        prev_len = curr_len
    else:
        stable_cycles += 1
        if stable_cycles >= 5:  # 5 cycles × 2s = 10s stable = done
            break
    await asyncio.sleep(2)
```

## Input selectors

### All sites — robust textarea finder
```javascript
(() => {
    const tas = document.querySelectorAll('textarea');
    let target = null;
    for (let t of tas) {
        if (t.offsetParent !== null && !t.readOnly && t.placeholder) {
            target = t; break;
        }
    }
    if (!target) for (let t of tas) if (!t.readOnly) { target = t; break; }
    if (!target) target = tas[tas.length - 1];
    if (target) target.focus();
    return {placeholder: target?.placeholder, idx: Array.from(tas).indexOf(target), total: tas.length};
})()
```

### Kimi — contenteditable
```javascript
document.querySelector('.chat-input-editor')?.focus();
// Read reply via textContent, NOT value (contenteditable stores in textContent)
```

## Summary table

| Site | Selector | Method | Notes |
|------|----------|--------|-------|
| DeepSeek | `.ds-markdown` | Tier 1 | ✅ Full reply, verified |
| Doubao | TBD | Tier 2 AX | Shadow DOM heavy |
| ChatGLM | TBD | Tier 2 AX | Partial via AX on fresh tab |
| ChatGPT | none | Tier 3 screenshot | Shadow DOM blocks all |
| Gemini | none | iframe targeting | Webview, needs special handling |
| Grok | TBD | blocked | Cloudflare blocks first |
| Kimi | `.chat-input-editor` | contenteditable | textContent read |