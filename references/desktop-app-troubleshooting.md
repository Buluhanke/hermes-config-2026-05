# Hermes desktop app (Electron) troubleshooting on macOS

## Symptom: "the app can't chat anymore / won't respond"

Do NOT assume model/config/credentials are broken. The most common cause is
an **app-shell failure** (Electron process died or is a stale window with a
dead backend), while the underlying agent stack is completely healthy.

### Diagnosis order — isolate the layer BEFORE touching config

1. **Check the app process is actually running.**
   ```bash
   ps aux | grep -iE "Hermes\.app|hermes serve" | grep -v grep
   ```
   If empty → the app isn't running at all (the window you see may be a stale
   shell whose backend already exited). This alone is often the whole answer.

2. **Prove the agent stack is healthy with a CLI chat** — this bypasses the
   desktop app entirely (same model, provider, creds, network):
   ```bash
   hermes chat -q "只回复：你好"
   ```
   A fast, correct reply means model + Nous/OAuth creds + network are FINE and
   the problem is isolated to the desktop app. (Note: macOS has no `timeout`
   binary by default — don't wrap the command in `timeout`; just run it with a
   generous tool-level timeout.)

3. **Read the desktop logs** (in `~/.hermes/logs/`):
   - `desktop.log` — Electron boot / backend spawn / update lifecycle. Look for
     `launched updater ... exiting desktop to release venv shim` followed by NO
     subsequent successful boot → the app quit for an update and never came back.
   - `gui.log` — websocket / renderer. `ws closed ... client_disconnect` lines
     are NORMAL reconnects, not errors.
   - `errors.log` — real backend errors. Most `check_fn ... returned False`
     WARNINGs are benign (tools gated off because their deps/creds aren't set).

4. **Check the config only if steps 1–3 point at it** (they usually don't):
   ```bash
   grep -E "^(model|auxiliary|delegation):" -A6 ~/.hermes/config.yaml
   ```

### The classic root cause: update quit the app, relaunch failed

macOS "update-then-restart" is **best-effort**. The updater tells the running
app to quit so it can release the venv shim / swap the bundle, then a detached
relauncher is supposed to re-open the new bundle. The documented failure mode
(all over `apps/desktop/electron/update-relaunch.ts`) is exactly
**"quit and never came back"** — the app exits and no window returns. The
window you were looking at becomes a dead shell.

Confirm it was a clean update (no stuck lock) by checking for a leftover marker:
```bash
ls -la ~/.hermes/.hermes-update-in-progress   # absent = update finished cleanly
```
Absent marker + no running process = update completed, only the final relaunch
step was skipped.

### Fix: just relaunch the bundle

```bash
open /Users/<user>/.hermes/hermes-agent/apps/desktop/release/mac-arm64/Hermes.app
```
Then verify boot succeeded:
```bash
sleep 8
ps aux | grep -iE "Hermes\.app|hermes serve" | grep -v grep   # expect processes
tail -6 ~/.hermes/logs/desktop.log   # expect "Hermes backend is ready. Finalizing desktop startup"
```
If the old dead window is still visible, `Cmd+Q` it fully first, then `open`.

Benign log line to NOT worry about: `web UI disabled ... use hermes dashboard`
— the desktop app uses an embedded `hermes serve` backend, not the browser
dashboard, so that 404 on the dashboard-token read is expected.

## Prevention options (offer these, don't silently apply)

- **A — one-liner recovery (zero cost).** Keep the `open ...Hermes.app` command
  handy; recovery is one command, no diagnosis needed once you recognize the
  pattern.
- **B — watchdog.** A cron/launchd job that checks for the Hermes process every
  few minutes and re-`open`s the bundle if absent. Trades a background job for
  never seeing the empty-shell state.
- **C — decouple updates from the app.** Update manually (`hermes update` from
  the CLI, or the menu's "Check for Updates") instead of relying on the in-app
  auto-restart path, so you never hit the "window vanished mid-session" case.
  As of this session the desktop app had NO periodic auto-update timer —
  `checkForUpdates` is a manual menu item — so the update was triggered
  explicitly/at boot, not on a background schedule.

Recommended combo: A + C (manual updates + know the one-line restart).

## Notes

- Sessions/backends are separate processes from the Electron shell, so
  restarting the app does NOT lose chat history.
- Token expiry is a red herring to rule out fast: `hermes status` shows
  `Access exp` / `Key exp` for Nous Portal; if those are in the future, the
  creds are fine and you're chasing the wrong layer.
