# When `browser_navigate` is broken — the CDP fallback ladder

## Symptom (2026-06-05)
```
browser_navigate(url="https://claude.ai")
→ {"success": false, "error": "[Errno 2] No such file or directory:
   '/Users/aimac/.hermes/hermes-agent/node_modules/.bin/agent-browser'"}
```

`agent-browser` is actually installed (in `node_modules/.bin/`), but the
`browser_navigate` tool is hard-coded to look at the wrong relative path
under `hermes-agent/`. The tool is dead for the rest of the session —
it does not auto-recover, and the path is baked in at import time.

## Quick checks
```bash
ls /Users/aimac/.hermes/hermes-agent/node_modules/.bin/ | grep agent-browser
# should show: agent-browser
# if absent: real install issue (npm i -g agent-browser or use npx)
# if present: the tool's path is wrong; fall back to CDP
```

## Fallback ladder (verified 2026-06-05)

### Tier 1: `browser_cdp` + `Target.createTarget` (best for new tabs)
```python
browser_cdp(method="Target.createTarget", params={"url": "https://claude.ai"})
# Returns: {"result": {"targetId": "<36-char UUID>"}}
```
Then attach via:
```python
sess = browser_cdp(method="Target.attachToTarget",
                   params={"targetId": TARGET_ID, "flatten": True})
```
The session_id from that response is what you pass for `sessionId` on later
calls; the target_id works as `target_id` on page-level calls.

### Tier 2: `browser_cdp` + `Page.navigate` (best for existing tabs)
```python
browser_cdp(method="Page.navigate",
           params={"url": "https://claude.ai"},
           target_id=EXISTING_TAB_ID)
```

### Tier 3: cua-driver launch_app (last resort)
```python
mcp_cua_driver_launch_app(
    additional_arguments=[
        "--remote-debugging-port=9333",
        "--user-data-dir=/Users/aimac/.hermes/chrome-debug",  # may be ignored on macOS
        "--remote-allow-origins=*",
        "https://claude.ai",
    ],
    name="Google Chrome",
)
```
**Caveats**:
- The `--user-data-dir` flag is **ignored on macOS** by cua-driver. The
  new Chrome uses the system default profile. That's actually a bonus
  here — the user's foreground Chrome login state is in the system
  default profile, so any site they've logged into will be logged in.
- The new Chrome **takes over port 9333** silently. The old Chrome on
  9333 (your debug instance) is pre-empted and its tab state is lost
  for automation purposes. Foreground Chrome is unaffected.
- **Do not `pkill Google Chrome` to "clean up"** — you'll drop the
  user's tabs and login state. Close CDP tabs explicitly via
  `Target.closeTarget` or just leave the new Chrome alive.

## Related gotcha: CDP supervisor `returnByValue` deserialization

When you go through `browser_cdp`, calls like `Runtime.evaluate` with
`returnByValue: True` (Python bool) sometimes fail with:
```
CDP error: {'code': -32602, 'message': 'Invalid parameters',
            'data': 'Failed to deserialize params.returnByValue - BINDINGS:
                     bool value expected at position NNN'}
```
The wrapper's BINDINGS deserializer is buggy. Two workarounds:

1. **Drop `returnByValue`** — you get the full result dict, read
   `r["result"]["result"]["value"]` yourself. Cleaner anyway.
2. Pass the field as the string `"true"` / `"false"` (Hermes sometimes
   does this internally). Less reliable.

This burned 4 retries in one session before the diagnosis. Always
prefer option 1.

## When this session happened
- 2026-06-05, while expanding the AI site roster from 6→12
- The user wanted Claude/Perplexity/Kimi/Tongyi/Copilot/Poe logged in
- `browser_navigate` failed → `Target.createTarget` × 5 worked in seconds
- The user logged in once per tab; cookies persist in the Chrome profile
  across restarts

## Verdict
`browser_navigate` is a thin wrapper that's brittle. **Default to
`browser_cdp` for all tab-level operations** in any script you intend to
keep working across sessions. The direct CDP path is more verbose but
robust.
