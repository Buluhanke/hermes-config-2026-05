# Remote Hermes Agent Diagnostics (macOS target)

## SSH Access

**aimac (192.168.0.4) — always use identity file, password auth is disabled:**
```bash
# Via SSH config alias (preferred)
ssh macmini "command"

# Direct with identity file
ssh -i ~/.ssh/hermes_agent aimac@192.168.0.4 "command"
```
> `hermes_agent` is NOT a GitHub key — it's for SSHing into aimac (macmini 192.168.0.4) and aimacmini (192.168.0.17).

**When SSH fails but Dashboard works:** "Connection closed by port 22" = sshd is down, but Hermes processes may still be alive. Use the Dashboard HTTP API as a health probe:
```bash
curl -s --connect-timeout 5 http://<IP>:9119/api/status
# {"detail":"Unauthorized"} = Hermes gateway is running (auth is working)
# Full JSON = full status including platform connections
```

## Common Remote Fixes

**hermes CLI broken on aimac (venv binary missing):**
```bash
ssh macmini "ls ~/.hermes/hermes-agent/venv/bin/hermes"  # if empty, binary is gone
ssh macmini "bash ~/.hermes/hermes-agent/scripts/install.sh"
# May timeout at "Node.js dependencies" step — binary is usually installed before that
```

**Git conflict during install on aimac (`git stash` fails "needs merge"):**
```bash
ssh macmini "cd ~/.hermes/hermes-agent && git reset --hard HEAD && git status"
# Then re-run the install script
```

## Key Paths on Remote Mac

| Purpose | Path |
|---------|------|
| Gateway logs | `~/.hermes/logs/gateway.log` |
| Error logs | `~/.hermes/logs/gateway.error.log` |
| Agent logs | `~/.hermes/logs/agent.log` |
| Errors summary | `~/.hermes/logs/errors.log` |
| Config | `~/.hermes/config.yaml` |
| Ollama API | `http://localhost:11434/api/ps` |

## macOS Diagnostics (Linux commands that DON'T work on Mac)

macOS is **not Linux**. Many common Linux commands are missing or have different flags:

| Linux command | macOS replacement | Example |
|---------------|-------------------|---------|
| `free -h` | `top -l 1` (look at PhysMem line) | `top -l 1 \| head -20` |
| `ps aux --sort=-%mem` | `top -l 1 -o mem` | `top -l 1 -o mem \| head -15` |
| `pstree -p` | Not available | Use `ps aux \| grep PID` |
| `nproc` | `sysctl -n hw.ncpu` | `sysctl -n hw.ncpu` |
| `iostat` | Not built-in | Use Activity Monitor or `ioreg` |
| `vmstat` | `vm_stat` | `vm_stat` |

## Memory Diagnostics

```bash
# Quick memory check
top -l 1 | grep PhysMem

# Detailed VM stats (includes swap)
sysctl -a | grep -E 'swap|vm.compressor' | head -20

# Check swap usage
sysctl -n vm.swapusage
```

**Memory pressure signs:**
- `PhysMem: 22G used (X wired, Y compressor), Z unused` — low Z means pressure
- `vm.swapusage: used = X free = Y` — swap being used = memory pressure
- High `vm.compressor.swapper.swapouts_pressure` = active paging

## Network Reachability (Critical for China-hosted VMs)

Chinese cloud/hosted VMs often block Google AI, OpenAI, and other Western APIs. **Always check reachability from the remote machine before diagnosing model/config issues.** Symptom: "No response from provider for 180s" with valid API key and config.

```bash
# Test Google AI (blocked in China = timeout → 200 means accessible)
ssh -i ~/.ssh/hermes_agent aimac@<IP> \
  "curl -s -o /dev/null -w '%{http_code}' --max-time 10 \
   'https://generativelanguage.googleapis.com/v1/models?key=\$GOOGLE_API_KEY'"

# Test OpenAI (often blocked too)
ssh -i ~/.ssh/hermes_agent aimac@<IP> \
  "curl -s -o /dev/null -w '%{http_code}' --max-time 10 \
   'https://api.openai.com/v1/models'"

# Test OpenRouter (usually accessible from China)
ssh -i ~/.ssh/hermes_agent aimac@<IP> \
  "curl -s -o /dev/null -w '%{http_code}' --max-time 10 \
   'https://openrouter.ai/api/v1/models'"
```

**Symptom pattern that confirms this problem:**
- Model times out with "No response from provider for 180s"
- Fallback also fails (if fallback model name is invalid)
- API key correct, config correct, but nothing works
- **Fix:** Switch remote machine to OpenRouter-only or local Ollama

## One-Line Health Check

```bash
top -l 1 | grep "Load Avg"
sysctl -n machdep.cpu.brand_string   # CPU model
sysctl -n hw.ncpu                    # Core count
```

## Finding Gateway Process

```bash
ps aux | grep -E 'hermes|gateway' | grep -v grep
```

Look for:
- `hermes_cli.main gateway run` — main gateway process
- `hermes` — agent process
- `ollama launch` — ollama launch helper

**Multiple gateway/agent processes** = resource contention, restart needed.

## Testing Ollama

```bash
# Health check
curl http://localhost:11434/api/health

# Loaded models (empty = none loaded)
curl -s http://localhost:11434/api/ps | python3 -m json.tool

# Simple generation test (measure time)
time curl -s -X POST http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5","prompt":"Hi","stream":false}'

# V1 endpoint test
curl -s -X POST http://127.0.0.1:11434/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen2.5","messages":[{"role":"user","content":"Hi"}],"stream":false}'
```

Ollama itself fast (~2-3s) but Hermes slow = problem in Hermes/gateway layer, not Ollama.

## Common Issues Found

### Multiple Hermes processes
Symptoms: Slow responses, duplicate log entries, resource contention.
Fix: `launchctl list | grep hermes` to find launchd-managed, then restart.

### Memory pressure
Symptoms: Slow model inference, high swap usage, compressor activity.
Fix: Close other apps, restart gateway, check for memory leaks.

### auto-model-router skill broken
Symptoms: `benchmark.py` not found errors in model-router-cron.log.
Fix: Reinstall skill or disable the cron job.

## One-Line Health Check

```bash
ssh -i ~/.ssh/hermes_agent aimac@<IP> \
  "top -l 1 | grep 'Load Avg\|PhysMem'; curl -s http://localhost:11434/api/ps; tail -5 ~/.hermes/logs/gateway.log"
```
