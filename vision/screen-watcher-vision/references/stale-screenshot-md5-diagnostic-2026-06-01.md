# Stale Screenshot + MD5 Diagnostic — 2026-06-01

## Symptom
- `ls -lt current.png` shows timestamp from May 31 (stale)
- `ps aux | grep screen_watcher` shows process alive
- But MD5 of current.png keeps changing every 10 seconds

## Root Cause
screencapture writes new content but macOS filesystem metadata update may lag or batch.

## Diagnostic Flow (Updated)
1. `ls -lt current.png` — check mtime (may be stale even when working)
2. `md5 current.png` twice with 10s gap — **MD5 changing = watcher is writing new content**
3. `ps aux | grep screen_watcher` — check process alive
4. If process dead → restart: `pkill screen_watcher && terminal(background=true) python3 ~/.hermes/scripts/screen_watcher.py`
5. If process alive + MD5 same → real stale, restart
6. If process alive + MD5 changing → **completely normal, no action needed**

## Key Insight
**MD5 change > mtime as diagnostic signal**

mtime can freeze on macOS screencapture even while content is being updated.
Always use MD5 comparison as the truth test.
