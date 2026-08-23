# Launch Chrome CDP without stealing focus (macOS, verified 2026-08-23, Chrome 151)

Use case: a dedicated CDP Chrome (separate from the user's daily Chrome) driven via raw websocket in
the BACKGROUND — the user keeps using their computer, no window pops front, no mouse/keyboard hijack.
The 1688 sourcing refactor (raw CDP on :9222) is the canonical trigger.

## The ONLY launch that does not steal focus

```bash
open -n -g -j -a "Google Chrome" --args \
  --remote-debugging-port=9222 --remote-allow-origins='*' \
  --user-data-dir="$HOME/chrome-cdp-profile" \
  --no-first-run --no-default-browser-check about:blank
```

Flags (all required — each solves a distinct failure mode):
- `-n`  force a NEW independent Chrome instance. Without it, `open -a` hands `--args` to the user's
        ALREADY-RUNNING default Chrome, which ignores them and never binds the port.
- `-g`  launch in background (never activated / never becomes frontmost).
- `-j`  launch hidden (no window shown).
- `--args`  passes the rest to Chrome (open's own arg parsing stops at `--args`).

Verify BOTH:
1. `curl -s -m5 http://127.0.0.1:9222/json/version` returns Browser info.
2. `osascript -e 'tell app "System Events" to get name of first application process whose frontmost is true'`
   returns something OTHER than "Google Chrome" (proves no focus steal).

## Failures tried — do NOT use these

- `--no-startup-window` (plain binary launch): process starts but NO window exists → user can't log in.
  Use only when you truly never need a window.
- `--start-minimized` (plain binary launch): window exists but Chrome STILL takes frontmost on launch
  (verified: frontmost became "Google Chrome"). Violates the no-focus rule.
- `open -a "Google Chrome" --args ...` WITHOUT `-n`: reuses default Chrome pid, --args ignored, port never binds.
- `terminal(background=true)` with a plain binary + `&`: Hermes rejects `&`; in raw shells `&` detaches
  but the process inherits no launchd session and the port may not survive restart. Prefer `open -n -g -j`.

## One-time login (the only time the window should appear)

The hidden instance has no visible window, so login must be done once manually:
```bash
zsh ~/.hermes/scripts/reveal_cdp_1688_login.sh   # reveals the 9222 Chrome window via System Events
```
User logs into 1688; state persists in `$HOME/chrome-cdp-profile`. After that, close/minimize — CDP keeps
running, no further reveals needed.

## Raw-websocket driving (no Playwright)

1. Connect browser WS from `/json/version` → `webSocketDebuggerUrl`.
2. `Target.createTarget({url, background:true})` → `targetId`.
3. `Target.attachToTarget({targetId, flatten:true})` → `sessionId`. On Chrome 151 this WORKS (verified
   2026-08-23). If you see `-32001 Session not found`, fall back to page-level WS from `/json`
   (match `id`, use `webSocketDebuggerUrl`) and omit `sessionId`.
4. `Runtime.enable` + `Page.enable`, then `Runtime.evaluate({expression, returnByValue:true})`.
5. No `jsonrpc` field in frames. Use a per-`id` message queue (don't `recv()` once per send — races
   with CDP events and picks the wrong reply).
6. `Target.closeTarget({targetId})` to tear down the tab when done.

DO NOT use `playwright.sync_api.chromium.connect_over_cdp(...)`. On Chrome 151
`browser.setDownloadBehavior` / `context.setDownloadBehavior` throws a CDP error ("not allowed"), so
Playwright-over-CDP is unreliable here. Raw websocket is the path.

Client reference: `~/.hermes/skills/1688-search-cn-gb-region-skill/scripts/cdp_client.py`
(`CDPBrowser` / `CDPTab`: background-tab create + `navigate` + `eval`/`eval_fn` + auto-close).
NOTE: that skill dir is user-owned — port changes there need `hermes curator adopt 1688-search-cn-gb-region-skill`.
