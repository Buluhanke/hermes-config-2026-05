# Chrome Debug Login State — Why File Copy Does NOT Work (2026-06-04)

## ⚠️ The original claim (now falsified)

`references/chrome-cookie-sync-strategy.md` previously stated copying raw SQLite files from the user's real Chrome to the debug profile "works." **This is wrong.** After live testing on 2026-06-04, Doubao shows **not logged in** after sync despite 229KB Cookies + 41KB Login Data being copied successfully.

## Why cookie file copy fails

### 1. Login Data is encrypted at rest (os_crypt — the hard blocker)

`Login Data` (passwords, session tokens, auth cookies) is encrypted using OS X Keychain via Chrome's `os_crypt`. Playwright's own Chromium binary uses its **own keychain** — it cannot decrypt tokens written by the user's real Chrome.

This is the fundamental blocker for session transfer. It is not a timing issue, not a file format issue.

### 2. Cookies SQLite WAL race

Even `Cookies` (plain SQLite) fails because Chrome holds a WAL (Write-Ahead Log) in-memory while running. Copying just the `.db` file loses the WAL changes, so the session cookie is stale or missing.

**Symptom**: Copy succeeds (229KB file), but after launch the site shows logged out because the WAL page that contains the latest session cookie was not flushed to the main db file.

## What actually works

### Option A — Chrome launched with `--remote-debugging-port` (user's real Chrome, not Playwright)

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --remote-debugging-port=9333 \
    --user-data-dir="$HOME/.hermes/chrome-debug" \
    --remote-allow-origins=* \
    about:blank
```

- cookie store IS the user's real Chrome store (same process, same encryption key)
- `browser.cdp_url=ws://127.0.0.1:9333` in `~/.hermes/config.yaml` then drives the real Chrome tab
- This is the only approach that reliably preserves login state

### Option B — User manually opens the tabs first

If the user opens AI sites in their Chrome first (while Hermes' CDP points at the same Chrome via 9333), those tabs are already logged in and stay that way.

### Option C — Playwright persistent_context profile IS the user profile (session cookies only)

If the user is logged into their real Chrome at `~/Library/Application Support/Google/Chrome/Default`, and Playwright launches with `--user-data-dir` pointing at that SAME directory (not a copy), Playwright inherits the session cookies directly — the SQLite is readable, not encrypted. **But**:

- Chrome must be fully quit first (cookie WAL flushed)
- `--no-sandbox` required on macOS
- This only works for session cookies, NOT encrypted Login Data
- Risk: Playwright may corrupt the profile if it crashes

## Practical check after launching Chrome debug

Always verify login state by navigating to a known logged-in site and checking for user avatar. If not logged in, the user needs to manually log in once in the debug Chrome.

## Corrected chrome-debug-launcher.py behavior

The cookie sync code in `chrome-debug-launcher.py` is kept for `Local Storage` and `IndexedDB` (which DO transfer correctly for site-state persistence like UI preferences, not login sessions). Login Data sync is a dead end and should be removed from the sync list — but is kept for backwards compatibility with the `Local Storage`/`IndexedDB` sync.