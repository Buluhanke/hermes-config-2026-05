# Config Lifecycle: When Changes Take Effect

## Core Rule

Changes to `config.yaml` (`model.provider`, `model.default`, `api_key`, `providers.*`) **only apply to NEW sessions**. The currently running session continues with whatever provider/model it was started with.

This applies to all channels:
- **CLI / TUI**: current session stays on the old config; exit and start a new one
- **Dashboard**: current session stays; new sessions pick up the new config
- **QQ / Telegram / other gateway bots**: gateway caches the config at startup; `hermes gateway restart` needed for full reload. `/new` reads the cached default, not the changed config.yaml

## How to Switch Immediately

Two options, ordered by recommendation:

### A. Start a new session (recommended)

```
hermes chat --provider minimax --model MiniMax-M2.7
```

Or just exit current session and reconnect — the new session picks up `config.yaml`.

### B. For persistent cross-channel switches

```
hermes config set model.provider minimax
hermes config set model.default MiniMax-M2.7
# then restart gateway for bot channels
hermes gateway restart
```

## Common Pitfalls

- "I changed the api_key but it's still using the old one" → the current session was authenticated at session start. Start a new session.
- "I added a new provider to `providers:` but `hermes model` doesn't show it" → built-in providers appear irrespective of config; custom providers in `custom_providers:` list are model-routable but won't show in the interactive selector.
- "I set `fallback_providers` but the session still fell back to something else" → fallback chain is evaluated at each API call, not at session start. This one DOES apply mid-session.

## Quick Test: Verify New Provider Works

```bash
# Test the new provider directly via CLI
hermes chat --provider minimax --model MiniMax-M2.7 -q "ping" -Q
```

If it fails, the error message tells you the issue (401 = bad key, timeout = wrong endpoint, etc.). The current session is NOT affected by a failed test — safe to experiment.
