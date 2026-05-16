# Multi-Machine Hermes Config Sync

> **⚠️ See also:** `references/full-machine-migration-macos.md` for full migration (decommissioning one machine, moving everything — sessions, memory, skills, source code, platform configs). This doc covers ongoing sync between active machines.

Synchronizing Hermes Agent model configuration between multiple machines (e.g., MacBook Pro + Mac mini).

## Key Facts

- **API keys are not device-bound** — Deepseek, Google, OpenRouter, and most provider API keys work from any IP/machine. No origin restriction. Calls from two different machines look like two concurrent sessions to the provider.
- **Single key, two machines, same rate limit** — The only shared resource is the API quota. For a single user using one machine at a time, this is invisible.
- **Copy model config only** — Don't copy the entire `config.yaml`. Each machine has machine-specific sections (platforms, terminal backend, launchd plists, cron jobs, command allowlists).

## Sync Procedure

### 1. Read Source Config

On the source machine, identify the sections to copy:
- `model` — main model selection
- `fallback_model` — global fallback for any model switch failure
- `fallback_providers` — ordered fallback chain
- `delegation` — subagent model
- `auxiliary.*` — vision, compression, session_search, etc.
- `compression.threshold` — must match compression model's context
- `credential_pool_strategies` — only the target provider's entry

### 2. Write a Python YAML Update Script

Use Python's `yaml` library (from Hermes' venv or system) to surgically update only the model-related keys while preserving everything else:

```python
import yaml, os

TARGET = os.path.expanduser("~/.hermes/config.yaml")

with open(TARGET) as f:
    config = yaml.safe_load(f)

KEY = "YOUR_API_KEY"  # DeepSeek API key (从源机 .env 读取，不是从 config.yaml)

# Model — 内置 provider 不要写 api_key
config["model"] = {
    "default": "deepseek-v4-flash",
    "provider": "deepseek",
    "base_url": "https://api.deepseek.com",
    # 不要加 api_key — 内置 deepseek provider 走 .env 的 DEEPSEEK_API_KEY
}

# Fallback model — 同样不要写 api_key
config["fallback_model"] = {
    "provider": "deepseek",
    "model": "deepseek-v4-flash",
    "base_url": "https://api.deepseek.com",
}

# Fallback providers (just one entry)
config["fallback_providers"] = [
    {"model": "deepseek-v4-flash", "provider": "deepseek"}
]

# Delegation — 同样不要 api_key
config["delegation"]["model"] = "deepseek-v4-flash"
config["delegation"]["provider"] = "deepseek"
config["delegation"]["base_url"] = "https://api.deepseek.com"
# config["delegation"].pop("api_key", None)  # 去掉之前可能残留的 api_key

# All auxiliary tasks
for key, sub in config.get("auxiliary", {}).items():
    if isinstance(sub, dict):
        sub["provider"] = "deepseek"
        sub["model"] = "deepseek-v4-flash"
        sub.pop("api_key_env_var", None)  # remove old env-var based auth

# Compression threshold (fix warning)
config["compression"]["threshold"] = 0.13

# Credential pool strategy
config["credential_pool_strategies"]["deepseek"] = "fill_first"

with open(TARGET, "w") as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
```

### 3. Deploy to Target Machine

Also copy the `.env` entries for the new provider(s). For built-in providers (deepseek, google, etc.), the API key MUST be in `.env`, not in `config.yaml`:

```bash
# Copy the Python update script
scp -i ~/.ssh/hermes_agent /tmp/update_config.py user@target:/tmp/

# Add/update env vars on target (built-in providers read from .env, not config.yaml)
ssh -i ~/.ssh/hermes_agent user@target 'grep -q "DEEPSEEK_API_KEY" ~/.hermes/.env \
  && sed -i "" "s/^DEEPSEEK_API_KEY=.*/DEEPSEEK_API_KEY=YOUR_API_KEY/" ~/.hermes/.env \
  || echo "DEEPSEEK_API_KEY=YOUR_API_KEY" >> ~/.hermes/.env'

# Run config update script on target
ssh -i ~/.ssh/hermes_agent user@target 'python3 /tmp/update_config.py'

# Verify both config and .env
ssh -i ~/.ssh/hermes_agent user@target "python3 -c 'import yaml; c=yaml.safe_load(open(\\\"~/.hermes/config.yaml\\\")); print(c.get(\\\"model\\\",{}).get(\\\"default\\\"))'"
ssh -i ~/.ssh/hermes_agent user@target 'grep DEEPSEEK_API_KEY ~/.hermes/.env'
```

### 4. Restart Gateway

```bash
# On target machine:
launchctl load ~/Library/LaunchAgents/ai.hermes.gateway.plist

# Or via SSH:
ssh user@target 'launchctl load ~/Library/LaunchAgents/ai.hermes.gateway.plist'
```

Verify the gateway restarted with a new PID:
```bash
ssh user@target 'launchctl list | grep hermes'
```

## Alternative: GitHub-Based Full Config Sync

Some users prefer to sync **everything** — config.yaml (including API keys) + skills + memories — via a git remote. This is simpler for one-person setups but has caveats.

### Setup (Source Machine)

```bash
cd ~/.hermes
git init
git remote add origin <your-private-repo-url>
# Ensure .gitignore excludes sessions/, logs/, .env (if keys are in config.yaml)
git add -A && git commit -m "initial hermes config" && git push origin main
# Set up hourly auto-backup in cron (see hermes-git-backup-script.md)
```

### Key Decision: Where to Put API Keys

**Option A — Keys in `.env` (gitignored), config.yaml references via env vars (recommended):**
- `.env` stays local, never pushed → safest
- `config.yaml` uses `api_key_env_var` for standard providers and `key_env` for `custom_providers`
- On new machine: clone repo, manually create `.env` with keys
- Use `.env.example` (git-tracked, template) to avoid forgetting keys

```yaml
# config.yaml — no plaintext keys
providers:
  openrouter:
    api_key_env_var: OPENROUTER_API_KEY
custom_providers:
- key_env: GROQ_API_KEY     # ← use key_env, not api_key
  base_url: https://api.groq.com/openai/v1
  model: llama-3.1-8b-instant
  name: Api.groq.com
```

> **Note:** `custom_providers` uses `key_env` (not `api_key_env_var`) to reference env vars. This is a different field name than the standard `providers` section. See Hermes `hermes_cli/config.py` function `_normalize_custom_provider_entry()`.

**Option B — Keys in `config.yaml` (pushed to GitHub):**
- GitHub's secret scanning will block the push — you must click the unblock URL for each detected secret
- Each API key pattern (OpenRouter, Google, NVIDIA, etc.) triggers a separate scan, each needs its own unblock
- If you later update the old commit (e.g., amending), the push is blocked again and needs a new unblock
- Files >100MB are also blocked (e.g., `bin/node` at 108MB) — add `bin/` to `.gitignore`
- **Not recommended** unless you fully understand and accept the security risk

### New Machine Recovery (Option A)

```bash
git clone <repo-url> ~/.hermes
# Install Hermes
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
# Copy .env.example → .env and fill in all keys
cp ~/.hermes/.env.example ~/.hermes/.env
# Edit .env with real API keys
hermes gateway restart
```

All config (model, providers, skills, memories, cron) is already in place from the clone. Only `.env` needs manual setup.

### What's Tracked vs Gitignored

| Tracked in git | Gitignored |
|---|---|
| config.yaml | .env (API keys/secrets) |
| skills/ | sessions/ |
| memories/ | logs/ |
| channel_directory.json | bin/ (node binaries) |
| cron/jobs.json | hermes-agent/ (source code) |
| scripts/ | auth.json |
| .env.example | checkpoints/ |
| gateway_state.json | *.db, *.sqlite |

## Pitfalls

- **`custom_providers` uses `key_env`, not `api_key_env_var`** — When referencing env vars in `custom_providers`, use `key_env: GROQ_API_KEY` (not `api_key_env_var`). The `_normalize_custom_provider_entry()` function in `hermes_cli/config.py` only recognizes the `key_env` field name. Standard `providers` section uses `api_key_env_var`. Don't mix them up.
- **Don't `launchctl kickstart -k` on detached processes** — if a gateway process has been marked exit -9 by launchd, kickstart won't restart it. Use `launchctl load` (which does unload+load) instead.
- **Preserve machine-specific sections** — platforms (WeCom/QQ/Weixin), terminal backend, command allowlists, cron, and Ollama provider should NOT be overwritten.
- **⚠️ Deepseek 是内置 provider，key 必须走 .env + api_key_env_var** — 不要把 `api_key` 直接写在 `model` 段或 `providers.deepseek.api_key` 里。正确做法：
  ```yaml
  # config.yaml - model section 不要有 api_key
  model:
    default: deepseek-v4-flash
    provider: deepseek
    base_url: https://api.deepseek.com

  # providers 段可加可不加（内置 provider 会自动识别）
  providers:
    deepseek:
      api_key_env_var: DEEPSEEK_API_KEY
      base_url: https://api.deepseek.com

  # .env 里放真正的 key
  DEEPSEEK_API_KEY=YOUR_API_KEY
  ```
  如果误把 key 写在 `model.api_key` 或 `providers.deepseek.api_key`，Hermes 会报 "Set DEEPSEEK_API_KEY environment variable" 错误，因为内置 provider 只认 `api_key_env_var`。从 `.env` 移走 key 也会触发同一错误。
- **AICODEE key ≠ Deepseek key** — 这两个 provider 用的 API key 完全不同，不要混淆。AICODEE key 是 `YOUR_API_KEY...`（用在 MinMax-M2.7-highspeed 的 `model.api_key` 段），Deepseek key 是另一个值（`YOUR_API_KEY...`）。Copy 配置时要各自查各自 `.env` 的实际值。
- **yaml.dump ordering** — Python's yaml.dump may reorder keys. Use `sort_keys=False` to preserve config readability.
- **Python YAML 脚本修改后可能丢失部分配置** — 如果用 Python `yaml.dump` 写回，要验证所有非模型部分（platforms、command_allowlist、custom_providers 等）是否完好。建议写完后用 diff 对比。
