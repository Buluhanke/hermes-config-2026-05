# Stuck / Hung GUI Updater — full diagnostic + fix (kk, 2026-07-17)

## Symptom
Desktop app "一直没成功" updating. App window gone, no chat. Relaunch doesn't help.
The failure is the **updater itself freezing**, not the app or your model/creds.

## Reproduction recipe (what I saw)
1. App self-triggers update (user clicked "Check for Updates" / update overlay).
   `apps/desktop/electron/main.ts` `applyUpdates()` spawns:
   ```
   /Users/kk/.hermes/hermes-setup --update --branch main \
     --target-app /Users/kk/.hermes/hermes-agent/apps/desktop/release/mac-arm64/Hermes.app
   ```
   ...then quits after a dwell to release the venv shim. Updater is supposed to
   rebuild + relaunch the app when done.
2. Updater is a **Cocoa GUI binary**. It entered its run loop and never advanced.
   Observed 40+ minutes later:
   - `%CPU = 0.0`, `STAT = Ss`
   - `pgrep -P <PID>` → no children
   - `lsof -p <PID>` → no TCP/network connections, no tty
   - `sample <PID> 3` → entire stack is `NSApplication run → nextEventMatchingMask → _DPSBlockUntilNextEventMatchingListInMode → mach_msg` (idle event loop)
3. `.hermes-update-in-progress` held `<PID>\n<epoch>` — looks "in progress" but PID is dead.
4. Watchdog `hermes-desktop-watchdog` (job 2965c4f50530) skips relaunch while the
   marker exists → permanent stuck state until manual intervention.

## Confirm it's the same bug (copy-paste)
```bash
ps -o pid,etime,%cpu,stat,command -p "$(head -1 ~/.hermes/.hermes-update-in-progress)" 2>/dev/null
pgrep -P "$(head -1 ~/.hermes/.hermes-update-in-progress)"
lsof -nP -p "$(head -1 ~/.hermes/.hermes-update-in-progress)" 2>/dev/null | grep -iE 'TCP|ESTABLISHED'
pgrep -f "mac-arm64/Hermes.app" >/dev/null && echo UP || echo DOWN
```

## Fix
```bash
PID=$(head -1 ~/.hermes/.hermes-update-in-progress)
kill -9 "$PID"
rm -f ~/.hermes/.hermes-update-in-progress
open /Users/kk/.hermes/hermes-agent/apps/desktop/release/mac-arm64/Hermes.app
sleep 8
pgrep -f "hermes-setup --update" >/dev/null && echo "WARN respawned" || echo "OK no updater"
tail -6 ~/.hermes/logs/desktop.log   # expect: "Hermes backend is ready. Finalizing desktop startup"
```

## Was a real update needed?
Usually no. Check before assuming a rebuild:
```bash
git -C ~/.hermes/hermes-agent status -sb
git -C ~/.hermes/hermes-agent log -1 --format="%h %ci %s"
cat ~/.hermes/desktop-build-stamp.json
ls -lT ~/.hermes/hermes-agent/apps/desktop/release/mac-arm64/Hermes.app
```
If checkout == origin/main and bundle mtime/contentHash are sane → just relaunch.

## Notes
- Update is user-triggered only (IPC `hermes:updates:apply`, menu `checkForUpdatesItem`).
  No auto-update-on-startup, so relaunching won't re-trigger the loop.
- To perform a real update without the fragile GUI path: `hermes update` (CLI).
- `sample` tool: /usr/bin/sample, usage `sample <pid> <seconds> -mayDie`.
