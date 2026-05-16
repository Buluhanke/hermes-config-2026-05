# Hermes Gateway on macOS: launchd, Environment Variables, and Process Proliferation

## The Problem Pattern

On macOS, a Hermes gateway installed as a launchd service (`~/Library/LaunchAgents/ai.hermes.gateway.plist`) can develop a distinctive failure mode:

1. Provider authentication fails repeatedly (e.g., aicodee `MINIMAX_API_KEY` not found)
2. Gateway crashes/exits
3. launchd's `KeepAlive: SuccessfulExit: false` restarts it immediately
4. Crash → restart → crash → restart → **multiple zombie processes accumulate**
5. Each process consumes ~100-200MB RSS, draining system memory
6. System falls into swap, model inference slows from <1s to 60-80s

**Symptoms:**
```
WARNING gateway.run: Primary provider auth failed: Unknown provider 'aicodee' — trying fallback
```

Then in `ps aux` you see multiple `hermes gateway run` and `ollama launch` processes with different PIDs but the same start time pattern.

## Root Cause: launchd Does Not Load .env Files

macOS launchd processes do **not** source `.env` files. Environment variables must be explicitly declared in the plist's `EnvironmentVariables` dict.

If `MINIMAX_API_KEY` is only in `~/.hermes/.env`, the launchd process sees it as empty → provider auth fails.

## Diagnosis Checklist

```bash
# 1. Check for multiple gateway processes
ps aux | grep 'hermes.*gateway' | grep -v grep

# 2. Check launchd service
launchctl list | grep hermes

# 3. Check if env var reaches the process
launchctl getenv MINIMAX_API_KEY

# 4. Verify .env has the key
grep MINIMAX_API_KEY ~/.hermes/.env

# 5. Check gateway error log
grep -i 'auth failed\|aicodee\|401\|failed' ~/.hermes/logs/gateway.error.log | tail -20
```

## Fix: Add Environment Variables to plist

```bash
# Read current plist
plutil -convert xml1 -o - ~/Library/LaunchAgents/ai.hermes.gateway.plist

# Edit to add EnvironmentVariables dict entries, e.g.:
#   <key>MINIMAX_API_KEY</key>
#   <string>YOUR_API_KEY-key-here</string>

# Then reload
launchctl unload ~/Library/LaunchAgents/ai.hermes.gateway.plist
launchctl load ~/Library/LaunchAgents/ai.hermes.gateway.plist
```

Or reconstruct the plist with the required env vars:

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>HERMES_HOME</key>
    <string>/Users/aimac/.hermes</string>
    <key>MINIMAX_API_KEY</key>
    <string>YOUR_API_KEY-key-here</string>
    <key>VIRTUAL_ENV</key>
    <string>/Users/aimac/.hermes/hermes-agent/.venv</string>
    <key>PATH</key>
    <string>/Users/aimac/.hermes/hermes-agent/.venv/bin:...</string>
</dict>
```

## Reading Masked .env Values on macOS

Hermes Agent may mask sensitive values in `.env` when displaying them:

```bash
# This shows *** — value is masked by display tools
cat ~/.hermes/.env
grep MINIMAX ~/.hermes/.env

# Use od -c to read the raw unmasked value
grep MINIMAX ~/.hermes/.env | od -c
```

The raw key appears after `=` and before `\n`. Extract it:

```bash
grep MINIMAX ~/.hermes/.env | od -c | awk '{print $2}' | tr -d '\n'
```

**Never assume the masked display value is real.** Always use `od -c` to verify before updating plists or configs.

## SSH Access to Remote Macs

When SSHing to a Mac mini, specify the identity file explicitly:

```bash
ssh -i ~/.ssh/hermes_agent aimac@192.168.0.4 "command"
```

Common targets:
- Mac mini: `aimac@192.168.0.4`
- Mac Pro (local): `aimac@192.168.0.2`

## Also Clean Up Broken Cron Jobs

Skills that register cron jobs don't always clean them up on deletion. Broken cron entries waste resources:

```bash
# List cron jobs
crontab -l

# Remove broken entries (grep -v keeps the ones you want)
(crontab -l | grep -v watchdog.sh) | crontab -
(crontab -l | grep -v auto-model-router) | crontab -
```

## ⚠️ Proxy Environment Variables in launchd (Critical for China/GFW)

**Problem pattern:**
- System proxy is configured and running (`networksetup -getwebproxy 'Wi-Fi'` shows `127.0.0.1:7897`)
- Proxy process (Clash/Surge/V2Ray) is actively listening on that port
- `curl -x http://127.0.0.1:7897 https://...` works from terminal
- **But** Hermes gateway requests to Google/Gemini API still timeout

**Root cause:** `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` are shell-level environment variables set per-session by the proxy app. macOS launchd does **not** inherit these from the system proxy settings. The launchd plist must explicitly declare them.

**Diagnosis:**
```bash
# Verify system proxy is configured
networksetup -getwebproxy 'Wi-Fi'

# Verify proxy process is listening
lsof -iTCP:7897 -sTCP:LISTEN -n

# Test proxy is reachable via -x flag
curl -s --max-time 5 -x http://127.0.0.1:7897 https://generativelanguage.googleapis.com/v1/models

# Check if env vars reach the launchd process (empty = not set)
launchctl getenv HTTP_PROXY
```

**Fix:** Add proxy env vars to the plist via Python:
```python
import plistlib
path = '/Users/aimac/Library/LaunchAgents/ai.hermes.gateway.plist'
with open(path, 'rb') as f:
    plist = plistlib.load(f)
env = plist.get('EnvironmentVariables', {})
env['HTTP_PROXY'] = 'http://127.0.0.1:7897'
env['HTTPS_PROXY'] = 'http://127.0.0.1:7897'
env['ALL_PROXY'] = 'http://127.0.0.1:7897'
env['https_proxy'] = 'http://127.0.0.1:7897'
env['http_proxy'] = 'http://127.0.0.1:7897'
plist['EnvironmentVariables'] = env
with open(path, 'wb') as f:
    plistlib.dump(plist, f)
```

Then restart:
```bash
launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway
sleep 3 && launchctl list | grep hermes
tail -5 ~/.hermes/logs/gateway.log
```

**Note:** The port (7897) and proxy type (HTTP vs SOCKS5) must match your actual proxy app's configuration. Clash Verge commonly uses 7897 HTTP, Surge uses 6153, etc.

**⚠️ Must also set `NO_PROXY`** — without it, all traffic (including local network requests to e.g. Ollama on `192.168.0.4:11434`) will be routed through the proxy, causing failures.

**Essential NO_PROXY entries for China/domestic APIs:**
```xml
<key>NO_PROXY</key>
<string>localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,api.deepseek.com,v2.aicodee.com,open.bigmodel.cn</string>
```

**Why:** DeepSeek (`api.deepseek.com`), MiniMax/AICODEE (`v2.aicodee.com`), and Zhipu/GLM (`open.bigmodel.cn`) are domestic Chinese API endpoints. If they go through an overseas proxy, they'll be slower and may fail. Add any other domestic API domains you use.

**Mac mini vs Mac Pro — do it on each machine:** The plist lives on each machine independently. If you fix it on Mac Pro but Mac mini's gateway runs via launchd too, you must SSH in and do the same edit there.

**Verification** — after setting NO_PROXY, confirm domestic APIs bypass the proxy:
```bash
# These should return fast (~0.1-0.2s) — not going through proxy
curl -s --noproxy '*' -o /dev/null -w "%{time_total}s\n" https://api.deepseek.com/v1/models
curl -s --noproxy '*' -o /dev/null -w "%{time_total}s\n" https://v2.aicodee.com/v1/models

# Compare with proxy route — should be slower or different IP
curl -s -x http://127.0.0.1:7897 -o /dev/null -w "%{time_total}s\n" https://api.deepseek.com/v1/models
```

### Clash DNS / fake-ip on macOS — may not be actively listening

Clash config may declare a DNS listener with fake-ip mode:
```yaml
dns:
  enable: true
  listen: :53
  enhanced-mode: fake-ip
```

**However, on macOS, this DNS server may not actually be running on port 53** (check with `lsof -i :53 -P`). If nothing is listening on port 53, Clash is NOT intercepting DNS queries, and all apps resolve DNS through the normal system DNS (223.5.5.5, etc.).

**Diagnostic:**
```bash
# Check if Clash DNS is actually listening
lsof -i :53 -P 2>/dev/null

# Test DNS resolution through 127.0.0.1:53
time nslookup google.com 127.0.0.1 2>/dev/null || echo "port 53 not listening"

# Check actual DNS servers in use
scutil --dns | grep 'nameserver\[' | head -5
```

**Clinical relevance:** Even though Clash appears fully configured with fake-ip DNS, an app's "卡住" (hanging) may not be caused by Clash at all if:
- TUN mode is disabled (`tun.enable: false`)
- System proxy is disabled (`networksetup -getwebproxy` shows Enabled: No)
- Port 53 DNS is not actually listening
- App is connecting directly to its own CDN/server

**Verification** — after adding proxy env vars and restarting the gateway, verify Google API is reachable:
```bash
# Test proxy connectivity directly (via -x flag, bypassing env)
curl -x http://127.0.0.1:7897 -s -o /dev/null -w "HTTP %{http_code}\n" \
  --max-time 10 "https://generativelanguage.googleapis.com/v1beta/openai/models" \
  -H "Authorization: Bearer GOOGLE_AI_KEY_REDACTED[your-key]"

# Expected: HTTP 200 (NOT timeout or 403/000)
# If timeout: proxy not running on that port
# If 403 region: proxy node IP still detected as China — switch to JP/US node
```

**跨机器容易遗漏**：launchd + 代理的修复需要在**每台机器**分别做。Mac mini 修过不代表 Mac Pro 也修了。检查方法是 `launchctl getenv HTTP_PROXY` 看 launchd 进程能否读到。

## Ollama Memory Management

When multiple `ollama` models are loaded simultaneously, they consume significant RAM. To reduce memory pressure:

```bash
# List models (use full app path — ollama CLI may not be in SSH PATH)
/Applications/Ollama.app/Contents/Resources/ollama list

# Check what's actually running in VRAM
curl -s http://localhost:11434/api/ps | python3 -m json.tool

# Delete unused models to free RAM
/Applications/Ollama.app/Contents/Resources/ollama rm gemma4:latest gpt-oss:20b hermes3:latest qwen3.5:9b

# Kill all ollama processes if needed (e.g. hung runner processes)
pkill -9 -f 'ollama'
```

**Typical model sizes** (affects how many fit in RAM):
- qwen2.5 7B: ~4.7 GB
- qwen3.5 9B: ~6.6 GB
- gemma4 8B: ~9.6 GB
- gpt-oss 20B: ~13 GB

**Deletion workflow** — keep only what's actually used:
1. Check `ollama list` for all installed models
2. Check `~/.hermes/config.yaml` for configured models in `ollama-launch` provider
3. Delete everything not in use (saves 20-35 GB typically)
```

## Key Paths on the Mac mini (192.168.0.4)

| Item | Path |
|------|------|
| launchd plist | `~/Library/LaunchAgents/ai.hermes.gateway.plist` |
| .env | `~/.hermes/.env` |
| Gateway logs | `~/.hermes/logs/gateway.log`, `gateway.error.log` |
| Ollama models | `~/.ollama/models/` |
| Skills | `~/.hermes/skills/` |
| Config | `~/.hermes/config.yaml` |

## Prevention

1. **Always add env vars to plist** when setting up a launchd-based service — don't rely on `.env`
2. **Check for crash loops** — if `launchctl list | grep hermes` shows `-15` signal or frequent restarts, something is wrong
3. **Use `hermes gateway restart`** (via `/restart` slash command) rather than manual process killing — it handles graceful shutdown
4. **Add proxy env vars to plist if in China/GFW environment** — system proxy settings are not inherited by launchd processes; if external API calls time out despite proxy being running, add `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY` to the plist
5. **Verify connectivity with `-x` flag** — `curl -x http://127.0.0.1:PORT URL` bypasses shell env and tests whether the proxy itself is reachable
