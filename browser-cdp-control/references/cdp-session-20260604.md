# CDP Session Notes

## 2026-06-04: Foreground Chrome + Real Profile — Breakthrough

**Problem**: Copying Chrome profile to `chrome-debug/` breaks cookies — all session cookies are `encrypted_value` (Keychain-encrypted), Playwright chromium has a different Keychain identity and cannot decrypt them. The `chrome-debug-launcher.py` had been using Playwright's `launch_persistent_context` which creates a headless shell, not the real Chrome.app binary.

**Solution**: Use the user's foreground Chrome directly:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --user-data-dir="/Users/aimac/Library/Application Support/Google/Chrome/Default" \
  --remote-debugging-port=9222 \
  --no-first-run --no-default-browser-check \
  --disable-blink-features=AutomationControlled \
  --new-window about:blank 2>/dev/null &
```

All 6 AI sites (豆包, ChatGPT, DeepSeek, Gemini, ChatGLM, Grok) are already logged in — no re-login needed. Same binary, same Keychain.

## `browser.cdp_url` Dirty Data Bug (2026-06-04)

**Symptom**: `browser_navigate` returns "404 Not Found" or "ERR_BLOCKED_BY_CLIENT" even when `curl localhost:9222/json/version` works fine.

**Root cause**: `hermes config set` cannot delete keys — it only writes empty-string over them. Repeated calls accumulate `server: ''` / `cdp_url: ''` empty-string fields. YAML parser gets confused by adjacent empty fields and the value silently fails to parse.

**Fix**: Python exact-line removal (NOT sed):
```python
import pathlib
cfg = pathlib.Path('/Users/aimac/.hermes/config.yaml')
lines = cfg.read_text().splitlines()
cleaned = [l for l in lines if not (
    any(k in l and l.strip().endswith("''") 
         for k in ['server:', 'cdp_url:', 'engine:'])
)]
cfg.write_text('\n'.join(cleaned) + '\n')
```

**Then verify**:
```bash
curl -s http://127.0.0.1:9222/json/version   # must return Chrome version
browser_navigate https://www.doubao.com       # must return fully rendered page
```

## mcp-chrome-stdio Failure Pattern

**Symptom**: `ECONNREFUSED 127.0.0.1:12306`

**Root cause**: mcp-chrome-stdio has a separate stdio-config.json that must match the running Chrome debug port.

**Workaround**: Bypass entirely. Chrome debug port 9222 is directly accessible via HTTP+WebSocket. No bridge needed.

## Critical: Chrome CDP Does NOT Support JSON-RPC 2.0

❌ WRONG (causes `-32600` errors):
```python
msg = {"jsonrpc": "2.0", "id": 1, "method": "Page.bringToFront"}
```

✅ CORRECT:
```python
msg = {"id": 1, "method": "Page.bringToFront"}  # No jsonrpc field
```

## Key Tab IDs (session reference)

| Site | Tab ID | Notes |
|------|--------|-------|
| DeepSeek chat | 9F5ACAD89DE94001ECF1E57DEE0E3C19 | ✅ AX tree works |
| Grok | 5E2311C0CA3F45EAEB6EEB3699AA608A | ✅ AX tree works |
| ChatGPT | 5A2213186C845F0F292E171EFD802B97 | ✅ AX tree works |
| 豆包 | D926D91C4D3022D003F1698B0FD2783C | ✅ AX tree works |
| ChatGLM | C12511A3F357953BA732CC110CA9CD6F | ✅ AX tree works |