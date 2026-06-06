# Chrome Login State — Cookie Sync vs Profile Launch

## 2026-06-04 attempt: sync Cookies + Login Data to debug profile

**What was tried**: `chrome-debug-launcher.py` now copies these files from the user's real Chrome profile (`~/Library/Application Support/Google/Chrome/Default/`) before starting the Playwright persistent context:

```
Cookies          (SQLite db)
Cookies-journal
Login Data       (encrypted, Chromium/os_crypt)
Login Data-journal
Local Storage/   (directory)
IndexedDB/       (directory)
```

**Result**: Copy succeeds (verified 229KB Cookies, 41KB Login Data, directories). But after launch, sites like Doubao show **not logged in**.

**Root causes** (two distinct problems):

### 1. Login Data is encrypted at rest
`Login Data` (passwords, session tokens) is encrypted using OS X Keychain via `os_crypt`. Playwright's Chromium binary uses its **own keychain** — it cannot decrypt tokens written by the user's real Chrome. This is the fundamental blocker.

### 2. Cookies SQLite WAL race
Even `Cookies` (plain SQLite) fails because Chrome holds a `Cookies-wal` and `Cookies-shm` in-memory while running. Copying just the `.db` file loses the WAL changes, so the session cookie is stale or missing.

**Verification**: After cookie sync, `lsof -i :9333` shows Playwright's `chrome-headless-shell` (not the user's `Google Chrome`). The cookie store belongs to the Playwright profile, not the user's Chrome.

## What actually works

### Option A — Chrome launched with `--remote-debugging-port` (user's real Chrome)
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --remote-debugging-port=9333 \
    --user-data-dir="$HOME/.hermes/chrome-debug" \
    --remote-allow-origins=* \
    about:blank
```
- cookie store IS the user's real Chrome store
- `browser.cdp_url=ws://127.0.0.1:9333` then drives the real Chrome tab
- This is what `ai-site-browser-e2e` now uses after 2026-06-04 fix

### Option B — User manually opens the tabs
If the user opens AI sites in their Chrome first (while Hermes' CDP points at the same Chrome via 9333), those tabs are already logged in.

### Option C — Playwright persistent_context profile IS the user profile
If the user is logged into their real Chrome, and we point Playwright's profile at the SAME `Default` dir, Playwright inherits the session cookies directly (not encrypted — just SQLite). **But**:
- Playwright must be launched with `--no-sandbox` on macOS
- Chrome must be fully quit first (cookie WAL flushed)
- This only works for session cookies, NOT for encrypted `Login Data`

## Recommendation

**Use Option A** (user's real Chrome via `--remote-debugging-port`). Do NOT try to copy cookies — just ensure the Chrome debug instance is running (via `chrome-debug-launcher.py` or manually) and `browser.cdp_url` points to it. The cookie sync code in `chrome-debug-launcher.py` is kept for `Local Storage` and `IndexedDB` (which DO transfer correctly for site-state persistence), but Login Data sync is a dead end.

## Practical check

After launching Chrome debug, always verify login state by navigating to a known logged-in site and checking for user avatar / session state. If not logged in, the user needs to manually log in once in the debug Chrome (that session will persist in the profile dir on next launch).