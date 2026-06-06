# 2026-06-05 — self_heal_watchdog.sh exit-1 debugging transcript

## Symptom
`launchctl print gui/$(id -u)/ai.hermes.self-heal-watchdog` reported
`last exit code = 1`, but the script's log file showed all 6 health checks
completing normally. launchd marked the plist as failed on every tick.

## Initial misdiagnosis
- v1.2 had `nohup ... hermes_cli.main gateway run` in the script.
- v1.2 also moved from `StartInterval` to `StartCalendarInterval` to dodge
  launchd's "minimum runtime = 10s" check, and added `--dry-run`.
- Both changes looked correct. `bash watchdog.sh --dry-run` returned 0.

## Root cause (3 bugs stacked)

1. **`log()` function returned the truth value of `[[ ]] && cmd`**:
   ```bash
   log() {
       msg="[$(ts)] $*"
       echo "$msg" >> "$LOG"
       [[ "$DRY_RUN" == "true" ]] && echo "$msg"   # ← returns 1 when DRY_RUN=false
   }
   ```
   When `DRY_RUN=false`, `[[ false == "true" ]]` returns 1; the `&&` chain
   returns 1 (not 0). Since `log "── watchdog 周期完成 ──"` was the last
   line of the script, the script exited 1.

2. **`[ ! -w "$FACT_DB" ] 2>/dev/null`** — the `2>/dev/null` redirect
   inside `[ ]` is illegal bash; bash silently discards it. Doesn't cause
   the exit-1 itself but contributes to "where IS the bug?" confusion
   when reading the script.

3. **v1.2 put `pkill ... gateway` + `nohup ... gateway run` IN the
   watchdog** — the "restart if down" branch was the original source of
   the issue. v1.2 attempted to keep the restart logic (under `|| true`
   and `disown`) but the spawn could still fail (port not bound in
   5s = launchd 5s hard timeout) and the watchdog would mark itself
   broken instead of "gateway is broken".

## Fix (v1.3)

```bash
log() {
    msg="[$(ts)] $*"
    echo "$msg" >> "$LOG"
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "$msg"
    fi
    return 0   # ← explicit 0, never inherit [[ ]] truth
}

# Detect branch — no longer restarts anything:
if [ "$GATEWAY_OK" -eq 0 ]; then
    log "⚠️  Gateway 异常（无进程或端口无响应）— 需手动或脚本重启（不自动启）"
fi
```

## Verification protocol
```bash
# 1. Syntax
bash -n /Users/aimac/.hermes/scripts/self_heal_watchdog.sh

# 2. Real-run 3x stability
for i in 1 2 3; do
    bash /Users/aimac/.hermes/scripts/self_heal_watchdog.sh >/dev/null 2>&1
    echo "run $i exit=$?"
done
# Expect: exit=0  exit=0  exit=0

# 3. Reload plist (load is NOT idempotent — must unload first)
launchctl unload ~/Library/LaunchAgents/ai.hermes.self-heal-watchdog.plist
launchctl load   ~/Library/LaunchAgents/ai.hermes.self-heal-watchdog.plist

# 4. Wait for next scheduled fire (StartCalendarInterval Minute=0,10,20,...)
sleep 12

# 5. Confirm launchd sees the new exit code
launchctl print gui/$(id -u)/ai.hermes.self-heal-watchdog | grep "last exit code"
# Expect: last exit code = 0
```

## Take-away
The watchdog is now detect-only. Restarts are owned by:
- `chrome_keepalive.sh` for Chrome 9333
- `gateway_keepalive` (if/when added) for hermes_cli gateway
- Manual user action for everything else

This is the **separation of concerns** pattern: a script whose job is
"tell me when something is broken" should not itself be the thing that
fixes things — otherwise fix-failures look like watcher-failures.
