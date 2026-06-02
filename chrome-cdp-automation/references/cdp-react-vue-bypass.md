# CDP React/Vue Bypass — Full Writeup

## The problem

Modern SPAs (React, Vue, Angular, Svelte) listen for `input` events, not the `.value` property. When you do `element.value = "x"` in DevTools, the DOM updates but the framework's internal state does not, because:

- React's onChange/onInput only fires on real user input events
- The form's submit handler may also check the controlled component's state, not the DOM
- Buttons stay disabled because the framework thinks the user "hasn't typed anything yet"

`page.fill()` in Playwright tries to set `.value` and dispatch synthetic events, but it doesn't always trigger all the framework's hooks. `element.value = "x"` via `Runtime.evaluate` is even worse — no events at all.

## The fix: `Input.dispatchKeyEvent` with `char` events

`Input.dispatchKeyEvent` simulates real keyboard at the browser-OS boundary. There are three event types per physical keystroke:

- `keyDown` — physical key press
- `char` — character input (this is what causes the focused input to receive the text)
- `keyUp` — physical key release

### Working pattern (verified, no double-character bug)

```python
for ch in text:
    # keyDown: NO text, otherwise React double-counts
    await cdp.send("Input.dispatchKeyEvent", {
        "type": "keyDown",
        "key": ch,
        "code": f"Key{ch.upper()}" if ch.isalpha() else ch,
        "windowsVirtualKeyCode": ord(ch.upper()) if ch.isalpha() else ord(ch),
        "text": "",
        "unmodifiedText": "",
    })
    # char: this inserts the character
    await cdp.send("Input.dispatchKeyEvent", {
        "type": "char",
        "text": ch,
        "unmodifiedText": ch,
        "key": ch,
    })
    # keyUp: no text
    await cdp.send("Input.dispatchKeyEvent", {
        "type": "keyUp",
        "key": ch,
    })
    await asyncio.sleep(0.05)  # human typing speed
```

### The double-character bug

If you put `text=ch` in the keyDown event, React processes BOTH the keyDown and the char as input, resulting in `用3句话` becoming `用用33句句话话`. This was verified on DeepSeek (2025-06-02).

`text=""` (empty string, not absent) in keyDown is mandatory. You can omit the `text` field entirely from keyDown — both work — but never put the character there.

## Why this beats Playwright's `page.type()`

Playwright's `page.type()` does essentially the same thing under the hood, but:

- Playwright needs its own browser instance, which means importing cookies (requires Chrome closed + pycryptodome for cookie value decryption)
- Playwright loses login state, requires manual cookie import
- Raw CDP reuses your existing Chrome with all logins intact

## Submit pattern (for AI chat sites)

```python
# 1. Focus the textarea via DOM domain (more reliable than Runtime.focus)
r = await cdp.send("DOM.getDocument", {})
root_id = r["result"]["root"]["nodeId"]
r = await cdp.send("DOM.querySelector", {"nodeId": root_id, "selector": "textarea"})
ta_node = r["result"]["nodeId"]
await cdp.send("DOM.focus", {"nodeId": ta_node})
await asyncio.sleep(0.2)

# 2. Send Enter via Input.dispatchKeyEvent
for t in ["keyDown", "keyUp"]:
    await cdp.send("Input.dispatchKeyEvent", {
        "type": t, "modifiers": 0, "timestamp": 0,
        "text": "\r", "unmodifiedText": "\r",
        "key": "Enter", "code": "Enter",
        "keyCode": 13, "windowsVirtualKeyCode": 13,
        "location": 0, "isKeypad": False, "isAutoRepeat": False
    })
```

### Why `text: "\r"` in the Enter keyDown

Some frameworks check for `e.key === "Enter"` AND a printable character (to distinguish from other Enter types). The `\r` carriage return is what keyboards actually produce for the main Enter key.

## Other gotchas discovered

- **`/devtools/browser` WS endpoint returns HTTP 404.** Use `http://localhost:9333/json` (HTTP, not WS) to enumerate tabs, then connect directly to `ws://localhost:9333/devtools/page/<tabId>`.
- **Chrome CDP does NOT support JSON-RPC 2.0.** Do not include `jsonrpc: "2.0"` in your messages. Format is `{"id": N, "method": "...", "params": {}}`.
- **`id` must be unique per session.** Using `0` for multiple requests breaks the response correlation. Monotonically increment from 1.
- **CDP sends unsolicited events** (Page.loadEventFired, Page.frameNavigated, etc.). Your recv loop must skip these and only consume responses matching your `id`.
- **`Page.captureScreenshot` sometimes returns 0 bytes** on Chrome with hardware acceleration issues. Fall back to `subprocess.run(["screencapture", "-x", "-t", "png", path])` for macOS native screen capture.
- **DOM.querySelector returns nodeId=0 if the selector doesn't match.** This is NOT the same as an error — check for `nodeId > 0` before using.
- **DOM.enable is required** for `DOM.focus` and `DOM.querySelector`. Enable it before use, especially if you've also enabled Runtime.

## Performance numbers (Mac Mini M4, 24GB)

- Tab list via HTTP: ~10ms
- Accessibility tree (full page): ~50ms, 200-2000 nodes depending on complexity
- Runtime.evaluate simple expression: ~5ms
- Each `Input.dispatchKeyEvent`: ~3-5ms round-trip
- 50-char message typed char-by-char: ~2.5s
- screencapture full screen: ~200ms
- Total end-to-end (ask DeepSeek + get reply + read it): ~30-40s including 25s AI generation wait
