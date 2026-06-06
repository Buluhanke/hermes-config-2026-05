# Foreground Chrome vs Debug Chrome — Separate Instances (2026-06-04)

## The Core Confusion

Users say "用前台已经登录的 Chrome" thinking there's one Chrome with login state. Actually there are two:

| Property | Foreground Chrome | Debug Chrome |
|---|---|---|
| **user-data-dir** | `~/Library/Application Support/Google/Chrome/Default/` | `~/.hermes/chrome-debug/` |
| **Keychain identity** | `Chrome Safe Storage` (钥匙串) | Separate `chrome-debug` Safe Storage |
| **CDP debug port** | ❌ None (default Chrome doesn't set it) | ✅ 9333 |
| **Who controls it** | User (human) | Hermes agent |
| **Cookie decryption** | ✅ Can decrypt its own cookies | ❌ Cannot decrypt foreground Chrome's cookies |

## The Cookie Encryption Problem

Chromium encrypts cookies with a master key stored in **macOS Keychain** under the Chrome's own Safe Storage identity. When you copy `Cookies` from foreground → debug:

- The **encrypted blob** copies correctly
- The **Keychain key** does NOT copy (it stays in the foreground Chrome's Keychain entry)
- Debug Chrome tries to decrypt with its own Keychain identity → fails → all `encrypted_value` cookies are ignored

**Result**: Even perfect file-level sync = no login state in debug Chrome.

This applies to ALL browsers that use Chromium's Keychain encryption (Chrome, Edge, Brave, Arc, etc.).

## Why `browser_navigate` Got 404 / ERR_BLOCKED_BY_CLIENT

Two problems:

1. **404**: The CDP WebSocket target (`/devtools/page/1F39A0FF...`) was from a **stale tab** (inherited from a previous session). Chrome had navigated away. The WS connection was live but pointing at a tab that no longer existed at that URL.

2. **ERR_BLOCKED_BY_CLIENT**: uBlock Origin extension (`dhdgffkkebhmkfjojejmpbldmpobfkfo`) installed in the debug profile was blocking the navigation request.

**Fix for future sessions**: Always re-list tabs via `curl localhost:9333/json` before connecting. If a known URL returns 404, open a fresh tab via `Target.createTarget`.

## Two Ways to Get Login State into CDP

### Option A: Inherit Foreground Profile Directly (preferred if feasible)

```bash
# Kill ALL Chrome first — Chrome refuses to run two instances
pkill -9 -f "Google Chrome"

# Launch Chrome WITH debug port, using the REAL user profile
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --args --remote-debugging-port=9333 \
  --user-data-dir=$HOME/Library/Application\ Support/Google/Chrome/Default
```

**Pros**: Full login state, no cookie decryption issue
**Cons**: Kills user's foreground Chrome (disruptive if they have tabs open)

### Option B: Two-Profile Debug Chrome (what we've been doing)

Launch debug Chrome at `~/.hermes/chrome-debug` with cookie sync on every launch.

**Problem**: Cookies are encrypted → not usable across Keychain boundaries. 
**Partial workaround**: Login state for some sites that store tokens outside cookies (e.g. Google, which uses `chrome://settings/manageProfile`).

### Option C: Use Frontend Chrome's Existing Tabs

If user already has AI site open in foreground Chrome, don't kill it. Instead:
1. Ask user to open the AI site in foreground Chrome
2. Use `computer_use` to read the screen (for simple tasks)
3. Use AI API directly for complex tasks

## Diagnostic Checklist

```bash
# Is foreground Chrome running?
ps aux | grep -E "[G]oogle Chrome" | grep -v Helper | grep -v chrome-debug

# Is debug Chrome running?
lsof -iTCP:9333 -n -P | grep Google

# Which profile is debug Chrome using?
ps aux | grep "user-data-dir" | grep chrome-debug

# Can we see tabs?
curl -s localhost:9333/json | python3 -c "
import json,sys
for t in json.load(sys.stdin):
    if t['type'] == 'page':
        print(t['id'][:16], t.get('title','')[:30], t['url'][:60])
"
```

## Session Summary (2026-06-04)

- User confirmed: "算了，还是用前台登陆好的chrome浏览器吧"
- Found: Only ONE Chrome instance running (PID 39205), using `~/.hermes/chrome-debug` profile
- Foreground Chrome profile (`~/Library/.../Default/`) has NO debug port
- Cookie sync copies 26 doubao cookies but all are `encrypted_value` — useless without Keychain key
- `browser_navigate` failed: 404 (stale tab) + ERR_BLOCKED_BY_CLIENT (uBlock Origin)
- Proposed Option A (use foreground profile directly) — user hasn't responded yet

## Next Step for Option A

If user approves: kill all Chrome → relaunch with `--user-data-dir=$HOME/Library/Application Support/Google/Chrome/Default` → full login state available on CDP 9333.