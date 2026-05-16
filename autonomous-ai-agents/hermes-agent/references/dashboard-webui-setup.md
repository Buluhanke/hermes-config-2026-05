# Hermes Dashboard / Web UI Setup

## Architecture

The Hermes web UI consists of **two separate processes**:

| Process | Port | Managed by launchd? | Purpose |
|---------|------|---------------------|---------|
| **Dashboard backend** (`hermes dashboard`) | 9119 | No (manual) | Serves API + static built files |
| **Vite dev server** (`npm run dev`) | 5173 | No (manual) | Dev frontend (proxies /api → 9119) |

The **gateway** (`hermes gateway run`) is a third separate process. It IS launchd-managed and unrelated to the dashboard.

## Common Pitfalls

### 1. Web UI shows 500 on every action

**Cause:** Dashboard backend not running. Vite dev server on 5173 proxies to `127.0.0.1:9119` — if that backend is down, all API calls fail.

**Fix:**
```bash
# Start dashboard backend
~/.hermes/hermes-agent/venv/bin/hermes dashboard --host 127.0.0.1 --port 9119

# Verify it's up
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9119
# Should return 200
```

### 2. `cp: node_modules/@nous-research/ui/dist/fonts: No such file or directory`

**Cause:** `predev` script (sync-assets) runs before `npm install` finishes populating `node_modules/`. Race condition, not a real missing dependency.

**Fix:**
```bash
cd ~/.hermes/hermes-agent/web
npm install          # run first, wait for completion
npm run dev -- --host  # then start dev server
```

### 3. `Chat unavailable: The ptyprocess package is missing`

**Cause:** Dashboard embedded chat (CHAT menu) requires `ptyprocess` to spawn a PTY for the agent. This package is not in the hermes venv — it's needed by the Dashboard backend (which runs under Homebrew Python, NOT the venv).

**Fix — install for Homebrew Python**:
```bash
/opt/homebrew/Cellar/python@3.13/3.13.3_1/Frameworks/Python.framework/Versions/3.13/bin/pip3 install ptyprocess --break-system-packages -q && echo "OK"
```

Refresh the Dashboard page after installation.

### 4. Third-party Web UIs conflict with built-in dashboard

**`nesquena/hermes-webui`** and similar tools may bind to ports 9119 or 5173, causing conflicts. Use the built-in dashboard instead.

## Production Build (recommended for auto-start)

Dev server is not suitable for production. Build first:

```bash
cd ~/.hermes/hermes-agent/web
npm install
npm run build    # outputs to ../hermes_cli/web_dist/
```

Then `hermes dashboard` serves both API and built static files — no separate Vite process needed.

## Auto-start on Boot

Dashboard is independent from gateway (which IS launchd-managed). Options:

- **Recommended:** Build web (`npm run build`) then `hermes dashboard` self-serves static files
- Write a separate launchd plist for dashboard
- **Do NOT** run `nesquena/hermes-webui` and `hermes dashboard` simultaneously — they conflict

## Verification Commands

```bash
# Check dashboard API
curl -s http://127.0.0.1:9119/api/status | python3 -c "import sys,json; d=json.load(sys.stdin); print('Gateway:', d.get('gateway_state'), 'Platforms:', list(d.get('gateway_platforms',{}).keys()))"

# Check gateway (separate process, launchd-managed)
ps aux | grep hermes.gateway | grep -v grep
```
