# Dashboard launchd Debugging — Session Findings (2026-05-07)

## `launchctl error -1` — what it really means

`launchctl list | grep dashboard` shows status `-1` → **process failed to start**.

`launchctl error -1` returns "unknown error code" → **this is a macOS API error code lookup that is uninformative**. Do NOT trust it to tell you why the process failed.

**Correct debug step**: Always read the stderr log first:
```bash
tail -20 ~/.hermes/logs/dashboard.error.log
```
Common errors: "npm is not available" (PATH missing npm), "address already in use" (crash loop), Python tracebacks.

## Port 9119 bound but not accessible locally

**Symptoms**:
- `netstat -an | grep 9119` shows `ESTABLISHED` connections but NO `LISTEN` on 127.0.0.1
- `curl http://127.0.0.1:9119` → connection refused
- `lsof -nP -iTCP:9119 -sTCP:LISTEN` → nothing
- Chrome Helper processes (PID 835) connected to 192.168.0.4:9119 from remote machine

**Root cause**: The `hermes dashboard` process is running but bound to the LAN interface (192.168.0.x) instead of 127.0.0.1, OR a previous crashed process hasn't fully released the port. Remote Chrome sessions (from another machine on LAN) are connected to it, making it appear alive.

**Fix**: Kill the dashboard process and restart with `--host 127.0.0.1` explicitly:
```bash
kill $(ps aux | grep 'hermes dashboard' | grep -v grep | awk '{print $2}')
sleep 2
launchctl load -w ~/Library/LaunchAgents/ai.hermes.dashboard.plist
```

## The crash loop mechanism

```
dashboard starts
  → _build_web_ui() called
    → npm not in PATH → returns False (soft failure)
      → dashboard exits with error
        → launchd sees process died → KeepAlive: true → restarts
          → port 9119 not fully released → bind() fails → "address already in use"
            → dashboard exits → launchd restarts → [loop]
```

**Two fixes needed simultaneously**:
1. `HERMES_WEB_DIST=/path/to/hermes_cli/web_dist` — skips `_build_web_ui()` entirely
2. Full `PATH` in plist EnvironmentVariables — so npm would be found even if build were triggered

Without (1): dashboard keeps trying to build and failing.
Without (2): even with HERMES_WEB_DIST, the PATH problem may cause other issues.

## Correct plist for ai.hermes.dashboard

See `references/dashboard-webui-autostart-macos.md` for the complete working plist. Key fields:

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>HERMES_HOME</key><string>/Users/mac/.hermes</string>
    <key>HERMES_WEB_DIST</key><string>/Users/mac/.hermes/hermes-agent/hermes_cli/web_dist</string>
    <key>PATH</key><string>/Users/mac/.npm-global/bin:/usr/local/bin:...</string>
    <!-- proxy vars if needed -->
</dict>
```

## Correct reload sequence

```bash
# Unload first (stops launchd from auto-restarting during kill)
launchctl unload ~/Library/LaunchAgents/ai.hermes.dashboard.plist

# Kill manually (process may have stale port binding)
kill $(ps aux | grep 'hermes dashboard' | grep -v grep | awk '{print $2}') 2>/dev/null

sleep 2

# Reload (launchd starts fresh)
launchctl load -w ~/Library/LaunchAgents/ai.hermes.dashboard.plist

sleep 5
netstat -an | grep 9119  # should show LISTEN on 127.0.0.1:9119
```
