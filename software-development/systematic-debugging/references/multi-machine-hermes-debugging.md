# Multi-Machine Hermes Gateway Debugging

## The Core Pitfall

When Hermes runs on multiple machines (e.g., Mac Pro + Mac mini), the error output tells you **which machine's gateway is failing**. The error path in the message is the key:

```
/Users/aimac/.hermes/  →  Mac mini (user: aimac, hostname: aimac.local)
/Users/mac/.hermes/    →  Mac Pro (user: mac, hostname: Mac-Pro.local)
```

**Symptom:** Current conversation works fine, but user reports errors. The errors are coming from a DIFFERENT machine's gateway.

## Diagnostic Sequence

1. **Read the error path** — immediately tells you which machine is failing
2. **Check SSH connectivity** — SSH keys may be broken even if the gateway is still running
3. **If SSH fails but gateway is up** — use the messaging platform (QQBot, Telegram, etc.) to send restart commands to the remote gateway
4. **If messaging platform also connects to the failing gateway** — the platform connection itself may be down; user needs local access

## Example from This Session

- User reported errors with path `/Users/aimac/.hermes/sessions/request_dump_...`
- The current conversation worked fine (running on Mac Pro's gateway)
- I spent 30+ minutes investigating Mac Pro's config before realizing the error was from Mac mini
- Root cause: Mac mini's gateway had a stale API key and was routing to Ollama instead of aicodee
- Fix: Restart Mac mini's Hermes Gateway to reload fresh credentials

## Restart Commands (macOS LaunchAgent)

On the failing machine, as the correct user:

```bash
# Stop
launchctl kickstart -k gui/<uid>/ai.hermes.gateway

# Start
launchctl start ai.hermes.gateway

# Or one-shot
launchctl kickstart -ks gui/<uid>/ai.hermes.gateway
```

To find the user's uid: `id -u <username>`

## Key Insight

The gateway process can be running (PID exists) with stale config. A restart forces re-reading:
- `~/.hermes/auth.json` (API keys, credential pool)
- `~/.hermes/config.yaml` (provider/model configuration)
- Environment variables via launchd

Just because `ps aux | grep hermes` shows a running process doesn't mean it's using current credentials.
