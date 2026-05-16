# Full Hermes Machine Migration (macOS → macOS)

Migrate an entire Hermes Agent installation from one Mac to another — including config, skills, sessions, memory, API keys, platform credentials, and source code. One machine is decommissioned; the other becomes the full replacement.

## Prerequisites (Source Machine)

- SSH access from source to target (passwordless key-based auth)
- Target machine already has Hermes installed (git-based or pip-based)
- Both machines on same network or accessible via SSH

## SSH Authentication Pitfall

If `.ssh/config` has a Host alias with the identity file (e.g. `Host macmini` with `IdentityFile ~/.ssh/hermes_agent`), **DO NOT** use the raw IP address for rsync/SSH — it will bypass the config entry and fail with "Permission denied" and "Too many authentication failures".

```bash
# ✓ CORRECT — uses ~/.ssh/config host alias
ssh macmini "hostname"

# ✓ CORRECT — explicit identity file with raw IP
ssh -i ~/.ssh/hermes_agent aimac@192.168.0.4 "hostname"

# ✗ WRONG — raw IP without -i bypasses .ssh/config
rsync -avz ~/.hermes/ aimac@192.168.0.4:~/.hermes/    # ← auth failure!
```

## Step 1: Backup Target Machine

The target machine likely has its own platform credentials (QQ bot with different app_id, WeCom, etc.) and additional API keys. These must be preserved:

```bash
ssh macmini "cp ~/.hermes/.env ~/.hermes/.env.backup.$(date +%Y%m%d_%H%M%S)"
ssh macmini "cp ~/.hermes/config.yaml ~/.hermes/config.yaml.backup.$(date +%Y%m%d_%H%M%S)"

# Extract unique credentials for later merge
ssh macmini "grep -v '^#' ~/.hermes/.env.backup.* | grep -v '^$' | sort"
```

## Step 2: Rsync Core Data

Transfer everything from source to target, excluding large/cache directories:

```bash
rsync -avz \
  --exclude 'hermes-agent/' \    # 1.8G source code — sync separately via git
  --exclude 'logs/' \
  --exclude '.git/' \
  --exclude '.gitkeep' \
  -e 'ssh -i ~/.ssh/hermes_agent' \
  ~/.hermes/ aimac@192.168.0.4:~/.hermes/
```

**What gets transferred:**
- `config.yaml` — main config (overwrites target)
- `.env` — API keys (overwrites target)
- `skills/` — all installed skills
- `sessions/` — conversation history
- `state.db` — memory store
- `auth.json` — credential pools
- `cron/` — cron job definitions
- `channel_directory.json`, `gateway_state.json`, etc.

## Step 3: Sync Hermes Source Code

Ensure target's hermes-agent checkout matches source:

```bash
# Check current commits on both machines
ssh macmini "cd ~/.hermes/hermes-agent && git log --oneline -1"
cd ~/.hermes/hermes-agent && git log --oneline -1

# Update target to match source (handle local changes)
ssh macmini "cd ~/.hermes/hermes-agent && git stash && git checkout <SOURCE_COMMIT_SHA> && git stash drop"
```

## Step 4: Patch Custom Tools

If source had custom patches (e.g. bocha search backend in `tools/web_tools.py`), rsync the patched files:

```bash
rsync -avz -e 'ssh -i ~/.ssh/hermes_agent' \
  ~/.hermes/hermes-agent/tools/web_tools.py \
  target_user@target_ip:~/.hermes/hermes-agent/tools/web_tools.py
```

## Step 5: Restore Target-Unique Credentials

The source `.env` overwrote the target's. Add back any unique keys that only existed on target:

```bash
ssh macmini "cat >> ~/.hermes/.env << 'EOF'
KEY_THAT_WAS_ON_TARGET_ONLY=value
ANOTHER_UNIQUE_KEY=value
EOF"
```

Check the backup file from Step 1 to find what's missing. Common unique keys include:
- Different QQ bot credentials (`QQ_APP_ID`, `QQ_CLIENT_SECRET`)
- WeCom (企业微信) credentials (`WECOM_BOT_ID`, `WECOM_SECRET`)
- Provider keys that weren't on source (`CEREBRAS_API_KEY`, etc.)

## Step 6: Reconcile Config Sections

The source config.yaml may be missing some sections that existed on target. Common ones to check:

- **`display.platforms.wecom`** — WeCom display config may only exist on target
- **`custom_providers`** — local Ollama endpoint, aicodee (v2), etc.
- **Additional provider entries** — Cerebras, ollama-launch, etc.

Use Python YAML to surgically restore these:

```python
import os, yaml

path = os.path.expanduser("~/.hermes/config.yaml")
with open(path) as f:
    config = yaml.safe_load(f)

# Restore WeCom display config
if "display" not in config:
    config["display"] = {}
if "platforms" not in config["display"]:
    config["display"]["platforms"] = {}
config["display"]["platforms"]["wecom"] = {
    "enabled": True,
    "extra": {
        "dm_policy": "open",
        "group_policy": "open",
        "websocket_url": "wss://openws.work.weixin.qq.com"
    }
}

# Restore custom providers
config["custom_providers"] = [
    {"name": "aicodee (v2)", "api_key_env_var": "AICODEE_API_KEY",
     "base_url": "https://v2.aicodee.com/v1", "model": "MiniMax-M2.7-highspeed"},
    {"name": "Local (localhost:11434)", "base_url": "http://localhost:11434/v1",
     "model": "hermes3:latest"},
]

# Restore missing provider sections
if "cerebras" not in config.get("providers", {}):
    config.setdefault("providers", {})["cerebras"] = {
        "api_key_env_var": "CEREBRAS_API_KEY",
        "base_url": "https://api.cerebras.ai/v1",
        "models": ["llama-3.3-70b", "llama-3.1-8b"]
    }

with open(path, "w") as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
```

**⚠️ Pitfall:** Inline Python via SSH (`python3 -c '...'`) does NOT expand `~`. Always use `os.path.expanduser("~/.hermes/config.yaml")` or the absolute path.

## Step 7: Restart Gateway

```bash
ssh macmini "~/.hermes/hermes-agent/venv/bin/hermes gateway restart"
```

## Step 8: Verification Checklist

Run this verification on the target machine:

```bash
ssh macmini "
echo '=== Status ==='
~/.hermes/hermes-agent/venv/bin/hermes status 2>&1 | head -10

echo '=== Model ==='
python3 -c \"import yaml; c=yaml.safe_load(open('/Users/aimac/.hermes/config.yaml')); m=c.get('model',{}); print('Model:', m.get('default'), '/ Provider:', m.get('provider'))\"

echo '=== Platforms ==='
python3 -c \"import yaml; c=yaml.safe_load(open('/Users/aimac/.hermes/config.yaml')); print('Platforms:', list(c.get('platforms',{}).keys()))\"

echo '=== Skills ==='
ls /Users/aimac/.hermes/skills/ 2>/dev/null | wc -l

echo '=== Memory DB ==='
ls -lh /Users/aimac/.hermes/state.db 2>/dev/null | awk '{print \$5}'

echo '=== Hermes commit ==='
cd /Users/aimac/.hermes/hermes-agent && git log --oneline -1

echo '=== Custom patches (bocha) ==='
grep -c 'bocha' /Users/aimac/.hermes/hermes-agent/tools/web_tools.py 2>/dev/null

echo '=== Env vars ==='
grep -v '^#' /Users/aimac/.hermes/.env | grep -v '^$' | wc -l

echo '=== Gateway running ==='
launchctl list | grep hermes | grep gateway
"
```

## What To Check After Migration

| What | How |
|------|-----|
| Model is correct | `model.default` in config.yaml |
| Fallback works | `fallback_model` and `fallback_providers` |
| All platforms connected | `hermes status` or `launchctl list` |
| Skills intact | Count matches source |
| Memory survives | `state.db` size > 0 |
| Custom patches active | grep for patch signature in web_tools.py |
| Gateway process running | launchd list shows `ai.hermes.gateway` with exit code 0 |

## Pitfalls

- **rsync with raw IP bypasses .ssh/config** — always use host alias or `-i` flag
- **Inline Python via SSH doesn't expand `~`** — use `os.path.expanduser()` or absolute paths
- **Target's hermes-agent may have local changes** — `git stash` before checkout
- **Mac mini had a worktree** (`hermes-agent-2026.4.23`) — gateway might use the main checkout not the worktree; check `ps aux | grep hermes_cli | grep gateway` to see which venv/PID is active
- **`hermes gateway restart` may fail if launchd process is detached** — if `launchctl list` shows `status = -9`, use `kill <PID> && sleep 2 && launchctl start ai.hermes.gateway`
- **Memory was full (2,082/2,200 chars)** — may need to prune memory entries after migration to make room for new operational context
- **Venv shebang paths are hardcoded per-user** — After rsync, all `venv/bin/*` files have `#!/Users/<old_user>/...` as shebang. The `python3 -> python -> python3.11` symlinks can become circular. **Fix sequence:**
  1. Fix python symlinks: `rm venv/bin/python3.11 && ln -s /Users/<new_user>/.local/bin/python3.11 venv/bin/python3.11 && rm venv/bin/python venv/bin/python3 && ln -s python3.11 venv/bin/python && ln -s python3.11 venv/bin/python3`
  2. Fix all shebangs: `sed -i '' 's|/Users/<old_user>/|/Users/<new_user>/|g' venv/bin/*`
  3. Fix venv activate script: `sed -i '' 's|VIRTUAL_ENV=/Users/<old_user>/|VIRTUAL_ENV=/Users/<new_user>/|g' venv/bin/activate`
  4. Reinstall the package: `cd venv/bin && ./python3 -m pip install -e ~/.hermes/hermes-agent`
  5. Verify: `hermes --version` returns correctly
- **Exclude config.yaml and auth.json during rsync** if the target machine has its own model config and platform credentials. These must be preserved independently. Use: `--exclude='config.yaml' --exclude='config.yaml*' --exclude='auth.json' --exclude='auth.json.backup*' --exclude='.env' --exclude='channel_directory.json'`
