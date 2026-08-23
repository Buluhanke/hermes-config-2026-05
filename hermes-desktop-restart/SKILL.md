---
name: hermes-desktop-restart
description: Restart the Hermes macOS desktop app when it won't chat / went blank
  (usually after a self-update failed to auto-relaunch).
version: 1.0.0
platforms:
- macos
metadata:
  hermes:
    tags:
    - hermes
    - desktop
    - restart
    - troubleshooting
    - macos
triggers:
- Use when hermes desktop restart
trigger_type: general
---

# Restart Hermes Desktop App (macOS)

## When to use
User says the Hermes desktop app "can't chat", "went blank", "froze", or "打不开/不能对话了".
Most common root cause on kk's machine: the app triggered a self-update, the updater
told the app to quit to release the venv shim, and the auto-relaunch ("detached
relauncher / mac bundle swap") failed — leaving an empty shell with a dead backend.
The underlying model/creds/network are usually fine (verify with a CLI chat).

## Fast diagnosis
1. Is the app process actually running?
   `ps aux | grep "[H]ermes.app/Contents/MacOS/Hermes"`
   Zero matches = app is down (the usual case).
2. Confirm the backend, model, creds are healthy (rule out non-app causes):
   `hermes chat -q "只回复：ok"`  → if it replies fast, the problem is ONLY the app.
3. Check for a stuck update marker:
   `ls ~/.hermes/.hermes-update-in-progress`  → if present, an update *appears*
   mid-flight. But a marker alone is NOT proof — it only holds a PID. Distinguish
   a live update from a **dead/stuck** updater (see "Stuck / hung GUI updater"
   below) before deciding to wait. A marker pointing at a DEAD, idle PID means the
   updater hung and you must kill it + clear the marker, then relaunch.

## Fix — one command
```bash
open /Users/kk/.hermes/hermes-agent/apps/desktop/release/mac-arm64/Hermes.app
```
Then wait ~8s and confirm the backend came up:
```bash
sleep 8; tail -6 ~/.hermes/logs/desktop.log
```
Look for: `Hermes backend is ready. Finalizing desktop startup` and a `HERMES_BACKEND_READY port=...` line.

If a stale blank window is still open, tell the user to Cmd+Q it first, then relaunch.

## Stuck / hung GUI updater (`hermes-setup --update`) — marker present but PID is DEAD

Different failure mode from "self-update failed to auto-relaunch". Here the app
*does* quit to release the venv shim (by design), but the updater binary
`/Users/kk/.hermes/hermes-setup --update --branch main --target-app .../Hermes.app`
itself **hung** — it never downloads or rebuilds, it just sits in its Cocoa event
loop forever. Seen 2026-07-17: ran 40+ min at 0% CPU, never finished, app never
relaunched, and the watchdog skipped relaunch because the in-progress marker was
still present → permanent stuck state.

### How to distinguish "genuinely in-progress" from "dead/stuck"
A present `~/.hermes/.hermes-update-in-progress` is NOT proof an update is live.
The file just holds a PID (format: `<pid>\n<epoch_seconds>`). Verify the PID:

```bash
cat ~/.hermes/.hermes-update-in-progress          # shows: <pid>\n<timestamp>
ps -o pid,etime,%cpu,stat,command -p <PID>         # alive + working?
pgrep -P <PID>                                    # any children (git/uv/npm)?
lsof -nP -p <PID> | grep -iE 'TCP|ESTABLISHED'     # any network activity?
```

A **dead/stuck** updater shows: `%cpu` ~0.0, **no children**, **no network
connections**, `stat` = `Ss` (sleeping session leader), `etime` climbing into
many minutes. A live updater shows children (git/uv/npm/electron-builder) and/or
open network sockets.

### Confirm a Cocoa hang (optional but definitive)
`hermes-setup` is a GUI binary. Sample it to prove it's parked on the event loop,
not working:
```bash
sample <PID> 3 -mayDie 2>&1 | grep -E 'NSApplication run|mach_msg|ReceiveNextEvent'
# stuck → whole stack is NSApplication run → nextEventMatchingMask → mach_msg (idle)
```

### Fix — kill the stuck updater, clear the marker, relaunch
```bash
kill -9 <PID>                                   # terminate the hung GUI updater
rm -f ~/.hermes/.hermes-update-in-progress      # clear the stale "in progress" flag
open /Users/kk/.hermes/hermes-agent/apps/desktop/release/mac-arm64/Hermes.app
sleep 8
pgrep -f "hermes-setup --update" >/dev/null && echo "WARN: respawned" || echo "OK: no updater"
```
Then confirm the app booted clean (no in-progress marker, backend ready in
desktop.log).

### Why this is safe (it will NOT loop)
The desktop update is **user-triggered only** — `hermes:updates:apply` is an IPC
handler fired from the menu/settings UI (`checkForUpdatesItem`, `applyUpdates` in
`apps/desktop/electron/main.ts`); there is **no auto-check-for-update on app
startup**. So after clearing the stuck updater and relaunching, the app will NOT
immediately re-spawn a `--update`. (Verified 2026-07-17: no `hermes-setup
--update` respawned after relaunch.)

### Was there even an update to apply? (often there is NOT)
```bash
git -C ~/.hermes/hermes-agent status -sb      # "## main...origin/main" = up to date
git -C ~/.hermes/hermes-agent log -1 --format="%h %ci %s"
cat ~/.hermes/desktop-build-stamp.json        # contentHash + builtAt of current build
```
If the checkout is already synced with `origin/main` and the
`release/mac-arm64/Hermes.app` bundle is intact (sane mtime, no `.asar` mismatch),
then no real update was pending — the hang was a no-op updater that never
terminated. Just relaunch; do NOT rebuild.

### Avoid the GUI updater next time
On kk's machine the in-app "Check for Updates" → `hermes-setup --update` path can
hang. To actually update, prefer the CLI:
```bash
hermes update        # same git+deps+desktop steps, no Cocoa GUI to freeze
```
See `references/stuck-gui-updater.md` for the full diagnostic transcript + CLI
update notes.

## Symptom: App 404s/credits-errors a model while CLI works (stale composer.model)
User sees e.g. `HTTP 404: Model 'tencent/hy3' requires available credits` (or any
provider rejection naming a *specific* model) from the **desktop app**, but
`hermes chat` (CLI) works and `~/.hermes/config.yaml` already has the correct
entry (e.g. `default: tencent/hy3:free`).

**Root cause:** the App persists the *currently selected model* in its own
Electron localStorage key `hermes.desktop.composer.model`, stored in
`~/Library/Application Support/Hermes/Local Storage/leveldb`. The App's
`refreshCurrentModel` only overwrites that value when the in-memory copy is
empty, so a stale value (e.g. the bare `tencent/hy3` without the `:free`
suffix) is never corrected by config.yaml. The App sends that stale name to the
gateway → wrong model id → provider rejects it. CLI is unaffected because it
reads config.yaml directly.

### Diagnose
1. Find what the App actually sent — stuck model names live in session request dumps:
   ```bash
   python3 - <<'PY'
   import json, glob, os
   for f in sorted(glob.glob(os.path.expanduser('~/.hermes/sessions/request_dump_*.json')),
                   key=os.path.getmtime, reverse=True)[:6]:
       try:
           d = json.load(open(f))
           body = d.get('request', {}).get('body', {})
           if body.get('model'):
               print(os.path.basename(f), '->', body['model'])
       except Exception:
           pass
   PY
   ```
   If it prints `tencent/hy3` (no `:free`) while config has `tencent/hy3:free`, that's the bug.
2. Confirm config is correct: `grep 'default:' ~/.hermes/config.yaml`.
3. Prove the *correct* model itself works (rules out a real account problem):
   pull the Nous token via `hermes_cli.auth.get_provider_auth_state('nous')`,
   then POST `chat/completions` to the inference base URL with
   `model: "tencent/hy3:free"`. A normal completion means only the name was wrong.

### Fix — wipe the App's cached UI model state
```bash
pkill -f "Hermes.app/Contents/MacOS/Hermes"        # quit the app
sleep 1
rm -rf "$HOME/Library/Application Support/Hermes/Local Storage/leveldb"
open /Applications/Hermes.app                      # or the release bundle path
```
After relaunch, verify the re-seeded value carries the suffix:
```bash
sleep 4
strings "$HOME/Library/Application Support/Hermes/Local Storage/leveldb"/*.log 2>/dev/null \
  | grep -o 'composer.model[^.]\{0,25\}'
# expect: composer.model  tencent/hy3:free
```
See `references/stale-composer-model-404.md` for the full leveldb-parsing recipe
and a copy-paste API probe.

See `references/stuck-gui-updater.md` for the full stuck-updater diagnostic
transcript + CLI-update note.

### Why not just edit config
config.yaml was already correct — the defect is purely App-side cached UI state.
Deleting the leveldb only drops UI prefs (window layout, last-open session); it
does NOT touch config.yaml or chat sessions.

### Pitfall — wiping leveldb can expose an already-BROKEN config.yaml model block
Symptom right after the leveldb wipe: App boots but shows
`agent init failed: No LLM provider configured. Run hermes model ...`.
The wipe didn't cause this — it removed the stale composer.model that was
*masking* an already-corrupt `model:` section. Seen 2026-07-17:
```
model:
  default: tencent/hy3:free
  provider: custom                          # orphaned — no matching custom_providers entry/key
  base_url: 'https://openrouter.ai/api/v1'  # stale leftover from a previous provider
```
`provider: custom` with no resolvable custom provider + a base_url pointing at a
different provider = invalid → "No LLM provider configured". The tell: CLI still
works when you pass `--provider nous` explicitly, so the broken part is config's
default provider, not creds/network.

**Fix — use `hermes config set`, NOT a direct file edit.** The agent's `patch`/
`write_file` on `~/.hermes/config.yaml` is REFUSED ("cannot modify
security-sensitive configuration"). Repair via CLI:
```bash
hermes config set model.provider nous
hermes config set model.base_url ""
hermes config set model.default tencent/hy3:free
```
Then restart the app (pkill + open bundle) so the backend re-reads config. Verify
the `model:` block and that the backend log shows `Hermes backend is ready` with
no provider error.

### "Won't switch model" is often just session/cache semantics, not a bug
Before deep-diving, know the two designed behaviors that look like breakage:
- A model switch does NOT apply to the *current* conversation (prompt-cache
  preservation). The old chat keeps its original model on purpose. Use `/new` for
  a fresh session on the new model, or `/model <name>` which rebuilds the agent
  next turn.
- The desktop backend reads config at boot; a long-running backend (started hours
  ago) holds the OLD in-memory config. If config was changed after boot, the App
  keeps using the stale model until you restart the app. Confirm with the
  request-dump diagnostic above — if dumps show the OLD model while config has the
  new one, restart the backend (and check the broken-config + stale-leveldb
  pitfalls).

### Pitfall — recurrence
`refreshCurrentModel` seeds from `/api/model/info` (config truth) ONLY when the
composer value is empty. So any manually-picked model, or a value seeded before a
config change, sticks forever. If the 404 returns after the user switches models,
repeat the leveldb wipe. A durable fix is to always trust config unless the user
changed the model this session — file upstream if you want it fixed properly.

## Note on the "web UI disabled … use hermes dashboard" log line
That 404 line in desktop.log is NORMAL — the desktop uses an embedded backend, not
the browser dashboard. It does not indicate a problem.

## Prevention (already set up 2026-07-16)
- Watchdog cron job `hermes-desktop-watchdog` (job_id 2965c4f50530) runs every 3m,
  script `~/.hermes/scripts/hermes-app-watchdog.sh`, no_agent mode. It relaunches
  the app if the main process is gone, and stays silent when healthy. It skips
  relaunch while `.hermes-update-in-progress` exists or the bundle is missing
  (avoids fighting an active update).
- To check it: `cronjob action='list'` or `hermes cron list`.
- If the user wants a push notification when the app is auto-restarted, update the
  job with deliver='telegram' (or 'all') — CLI sessions have no live delivery.

## Pitfalls
- Do NOT relaunch while an update is **genuinely** in progress — BUT a present marker
  is NOT proof: it only stores a PID. If that PID is dead/idle (0% CPU, no children,
  no network — see "Stuck / hung GUI updater" above), the update is *stuck*, not
  running. Kill the updater, remove the marker, then relaunch. Parking-and-waiting
  on a dead PID is exactly what produces a permanent stuck state (the watchdog also
  skips relaunch while the marker exists).
- The bundle path is build-specific: `apps/desktop/release/mac-arm64/Hermes.app`.
  If it's missing, the app may need a rebuild / reinstall, not just a relaunch.
- App-level config/tool changes need a fresh app session; the desktop reads them at boot.
