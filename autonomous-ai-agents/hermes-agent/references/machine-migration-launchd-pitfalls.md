# Machine Migration: macOS launchd Pitfalls (Hackintosh → Native Mac)

## Session context

Hermes was cloned from a Hackintosh Mac (black苹果) to a native Mac mini M4 (aimac, 192.168.0.4). The migration revealed several launchd configuration issues that are specific to machine migrations or fresh setups from cloned data.

## Key findings

### 1. venv path: `.venv` vs `venv` — check before writing plists

The install method determines the venv directory name. Some installs create `.venv`, others create `venv`. **Always verify before writing or auditing plists.**

```bash
ls ~/.hermes/hermes-agent/.venv 2>/dev/null && echo ".venv EXISTS" || echo ".venv NOT found"
ls ~/.hermes/hermes-agent/venv  2>/dev/null && echo "venv  EXISTS" || echo "venv  NOT found"

# Canonical answer — resolves the symlink:
readlink -f ~/.hermes/hermes-agent/venv/bin/python   # or .venv/bin/python
```

On aimac (192.168.0.4): venv exists at `~/.hermes/hermes-agent/venv` (NOT `.venv`).
The python resolves to e.g. `/opt/homebrew/Cellar/python@3.13/...` — this is fine.

Both `ai.hermes.gateway.plist` AND `ai.hermes.dashboard.plist` must reference the same correct path.

### 2. Dashboard plist needs full EnvironmentVariables (same as gateway)

A common migration/setup issue: the dashboard plist was created with minimal or no `EnvironmentVariables` dict. Symptoms:

- Dashboard crashes, `launchctl list` shows status `-1` (startup failure)
- Error log: `ModuleNotFoundError: No module named 'fastapi'` — even though fastapi IS installed in the venv
- Cause: plist pointed to wrong python (or no venv env vars), process used system python which lacks fastapi
- Web UI returns HTTP 200 but all operations return 500

**Required dashboard plist EnvironmentVariables** (same structure as gateway plist):
```xml
<key>EnvironmentVariables</key>
<dict>
    <key>HERMES_HOME</key>
    <string>/Users/aimac/.hermes</string>
    <key>VIRTUAL_ENV</key>
    <string>/Users/aimac/.hermes/hermes-agent/venv</string>
    <key>PATH</key>
    <string>/Users/aimac/.hermes/hermes-agent/venv/bin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:...</string>
    <key>HTTP_PROXY</key>
    <string>http://127.0.0.1:7897</string>
    <key>HTTPS_PROXY</key>
    <string>http://127.0.0.1:7897</string>
</dict>
```

Also install fastapi/uvicorn in the venv:
```bash
~/.hermes/hermes-agent/venv/bin/pip install fastapi uvicorn --quiet
```

### 3. Correct launchd restart: `remove` before `load`

**`launchctl unload` does NOT kill the managed process** — it only unregisters the job from launchd while leaving the child process running. The process becomes an orphan.

**Correct sequence after editing a plist:**
```bash
# Full termination then reload:
launchctl remove ai.hermes.gateway
launchctl remove ai.hermes.dashboard
sleep 2
launchctl load ~/Library/LaunchAgents/ai.hermes.gateway.plist
launchctl load ~/Library/LaunchAgents/ai.hermes.dashboard.plist
sleep 3
launchctl list | grep hermes
ps aux | grep hermes_cli | grep -v grep  # verify correct Python
```

**Why this matters after migration:** The old gateway process (from the previous Mac, PID 28502) was still running with Python 3.11 from a stale venv. Even after `unload`+`load`, the old process survived because `unload` only unregisters — it doesn't SIGKILL. Only `remove` terminates cleanly.

**Verification after restart:**
```bash
# Check correct Python is in use (should be homebrew 3.13 on aimac)
ps aux | grep hermes_cli | grep -v grep
# Should show: /opt/homebrew/Cellar/python@3.13/.../Python

# Verify gateway is using proxy (connected to clash port)
lsof -p $(pgrep -f "hermes.*gateway" | head -1) | grep 7897
# Should show: TCP localhost:XXXXX->localhost:7897 (ESTABLISHED)

# Verify QQ bot reconnected
tail -5 ~/.hermes/logs/gateway.log | grep -i qqbot
# Should show: "WebSocket connected" + "qqbot connected"
```

### 4. Web UI build: npm install && npm run build

After migration or hermes-agent update, the pre-built web UI may be stale or missing:
```bash
cd ~/.hermes/hermes-agent/web && npm install && npm run build
```

The built files go to `hermes_cli/web_dist`. Dashboard serves these statically; no Vite dev server needed for production.

### 5. Quick process age check: lsof proxy connections

When debugging whether a running gateway process is fresh or a stale orphan from before the migration, use `lsof` to check if it has active proxy connections — a new process will have ESTABLISHED connections to the Clash proxy port, while an old process from before the proxy was configured will not:

```bash
lsof -p $(pgrep -f "hermes.*gateway" | head -1) | grep 7897
# New process (with proxy env vars): shows TCP localhost:XXXXX->localhost:7897 (ESTABLISHED)
# Old orphan process: no output (no proxy connections)
```

This quickly distinguishes new vs old without relying on PID comparison. Combined with `tail ~/.hermes/logs/gateway.log` modification time, you can confirm the new process is actually writing fresh logs.

### 6. Old plist cleanup

Remove any leftover plists from the source machine that were installed in system-level directories:

```bash
sudo rm -f /Library/LaunchDaemons/com.hermes.dashboard.plist /Library/LaunchAgents/com.hermes.dashboard.plist
```

These system-level plists may have different paths or configurations and can conflict with the user-level plists in `~/Library/LaunchAgents/`.

## Related

- `references/launchd-environment-variables-macos.md` — comprehensive guide to launchd + env vars + proxy on macOS
- `references/full-machine-migration-macos.md` — full migration procedure between Macs
