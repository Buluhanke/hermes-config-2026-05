---
name: browser-automation
description: "Use when needing to automate Chrome browser actions: navigate, click, type, scroll, screenshot, extract page data, or interact with web pages via CDP. Covers both the browser-use Python REPL mode and raw CDP techniques. Does NOT cover browser CDP control via hermes browser tools (use browser-navigate/click/type/snapshot for those)."
license: MIT
version: 1.0.0
author: hermes-digital-resident
validated: 2026-07-08
---

# Browser Automation — CDP Python REPL + Raw CDP

This skill covers browser automation via `browser-use`/`browser-harness` (Python heredoc REPL) and raw CDP via `browser_cdp` tool.

## Two Browser Automation Systems (Know Which You're Using)

| System | Tool | Connects to |
|--------|------|-------------|
| Hermes native browser tools | `browser_navigate`, `browser_click`, etc. | Chrome via CDP port 9222 |
| browser-use Python REPL | `browser-use << 'PY'` | Hermes's own chrome-profile-mirror |

**Critical**: `browser-use`/`browser-harness` daemon connects to **`~/.hermes/chrome-profile-mirror`** — Hermes's own Chrome, NOT the user's real Chrome.

## System 1: browser-use / browser-harness Python REPL

### Installation & Fix

Homebrew version is **broken** (Python 3.14 asyncio conflict):
```bash
brew uninstall browser-use 2>/dev/null
uv tool install --python 3.11 browser-use
```
Always use `~/.local/bin/browser-use` or `browser-harness` (same package).

### Core Workflow

```bash
browser-use << 'PY'
print(page_info())           # dict: url, title, w, h, sx, sy, pw, ph
PY

browser-use << 'PY'
goto_url("https://example.com")
PY
```

Python context persists — variables survive across calls.

### Actual Available API (discovered 2026-07-08)

```python
# Navigation
goto_url(url)               # Navigate to URL
new_tab(url)                # Open new tab  
close_tab()                 # Close current tab
switch_tab(index)           # Switch by tab index
list_tabs()                 # Returns [(index, url), ...]

# Inspection
page_info()                 # dict: url, title, w, h, sx, sy, pw, ph
current_tab()               # Current tab info

# Interaction  
click(element)               # CSS selector or text match
click_at_xy(x, y)           # Pixel coordinates
type_text(text)             # Type into focused element
fill_input(selector, text)  # Fill input by CSS selector
press_key(key)              # Keyboard key (Enter, Escape, etc.)
dispatch_key(keys)          # Key combo (Ctrl+a, etc.)
scroll(direction, amount)   # up/down, pixels

# Waiting
wait_for_element(selector, state='visible', timeout=30000)
wait_for_load(timeout=30000)
wait_for_network_idle(timeout=30000)
wait(text, timeout=30000)

# Capture
capture_screenshot()         # Returns path string, not bytes

# CDP (advanced)
cdp                         # Raw CDP session object
iframe_target()             # iframe helper
```

### CDP WebSocket Bypass (when daemon fails with HTTP 404)

Daemon can't find page target → use explicit WS URL:

```bash
PAGE_WS=$(curl -s http://127.0.0.1:9222/json/list | \
  python3 -c "import sys,json; p=[x for x in json.load(sys.stdin) if x['type']=='page']; print(p[0]['webSocketDebuggerUrl'])")
BU_CDP_WS="$PAGE_WS" browser-use << 'PY'
print(page_info())
PY
```

### Verify Daemon Is Working

```bash
browser-use doctor 2>&1 | grep -E "ok|FAIL"
# Should show: [ok] chrome running, [ok] daemon alive
```

## System 2: Hermes Native Browser Tools

Use these for CDP-level control via `browser_cdp` tool:
- `browser_navigate` → load URL
- `browser_snapshot` → AX tree / DOM
- `browser_click ref` → click by element ref
- `browser_type ref text` → type into element
- `browser_scroll direction` → scroll
- `browser_vision question` → screenshot + VLM analysis
- `browser_console expression` → JS eval in page

For raw CDP commands: `browser_cdp method=<method> params=<json> target_id=<id>`

## Chrome Profile Isolation (Critical Warning)

| Chrome instance | Path | Used by |
|----------------|------|---------|
| Hermes mirror | `~/.hermes/chrome-profile-mirror` | browser-use daemon |
| User's real Chrome | `~/Library/Application Support/Google/Chrome/` | NOT accessible |

**To use user's real Chrome with cookies/logins:**
1. User manually starts Chrome: `open -a "Google Chrome" --args --remote-debugging-port=9222`
2. User clicks "Allow" in the Chrome popup
3. Use `BU_CDP_WS` bypass above with user's Chrome WS URL

## Troubleshooting

| Problem | Fix |
|---------|-----|
| asyncio RuntimeError on startup | `uv tool install --python 3.11 browser-use` |
| CDP WS HTTP 404 | Use explicit `BU_CDP_WS` bypass above |
| "command not found" | Use `~/.local/bin/browser-use` |
| Element click fails | Try CSS selector: `click("button.submit")` |
| screenshot returns path | Normal — returns path like `/Users/aimac/.config/browser-harness/tmp/shot.png` |

## References

- Raw CDP Python access: `references/cdp-python.md` (in browser-use skill dir)
- Multi-session: `references/multi-session.md` (in browser-use skill dir)
- browser-use GitHub: https://github.com/browser-use/browser-use
- browser-harness GitHub: https://github.com/browser-use/browser-harness
