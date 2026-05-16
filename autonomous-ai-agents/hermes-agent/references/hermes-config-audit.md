# Hermes Config Audit — Common Misconfigurations

Config issues frequently found during manual audits. Run after any model/provider change.

## 1. Errant `model:` field under `model:` block

**Symptom**: `model.default` says one thing (e.g. `MiniMax-M2.7-highspeed`) but `model.model` is set to something completely different (e.g. `google/gemma-3-27b-it:free`).

**Cause**: Manual editing or a buggy merge left a stray `model:` key inside the `model:` config block.

**Fix**: Remove the errant line. The `model:` block should only contain `api_key`, `base_url`, `default`, `context_length`, `provider` — NOT a second `model:` assignment.

```yaml
# WRONG (two model: keys):
model:
  api_key: ...
  default: MiniMax-M2.7-highspeed
  model: google/gemma-3-27b-it:free   # ← remove this
  provider: custom

# CORRECT:
model:
  api_key: ...
  default: MiniMax-M2.7-highspeed
  context_length: 65536
  provider: custom
```

## 2. `credential_pool_strategies.latency_based_routing: true` — NO-OP

**Symptom**: Config has `latency_based_routing: true` but routing behavior doesn't change.

**Cause**: This config key is not implemented. No code reads it.

**Fix**: Remove the entire `credential_pool_strategies:` block. Failure threshold and health check interval are valid but the routing one does nothing.

## 3. Redundant `model_catalog:` block

**Symptom**: Config has both a `model_catalog:` section and an `openrouter:` top-level key.

**Cause**: `model_catalog` enables the built-in model directory feature (fetched from `hermes-agent.nousresearch.com`). The `openrouter:` top-level key is a separate feature. Having both is unnecessary and adds confusion.

**Fix**: Remove `model_catalog:`. It is optional metadata, not functional configuration.

## 4. `custom_providers` vs `providers.ollama` confusion

Ollama on a remote host (e.g. Mac mini) can be configured two ways:

**Correct way** (if you want it as a named provider in fallback_providers):
```yaml
providers:
  ollama:
    api_key: ollama
    base_url: http://192.168.0.4:11434/v1
```

**Also valid** (for inline custom endpoint, no provider name needed):
```yaml
custom_providers:
  - name: ollama-local
    base_url: http://192.168.0.4:11434/v1
    api_key: ollama
    model: qwen2.5:latest
```

**Pitfall**: Adding Ollama to `custom_providers` AND `providers` simultaneously causes credential pool confusion. Pick one.

## 5. `HERMES_MODEL` overrides config file (env var OR in config.yaml)

**Symptom**: Changing `model.default` in config.yaml has no effect. `/model` slash command switches don't stick.

**Cause**: `HERMES_MODEL` takes precedence over `model.default`. It can be set in two places:

### 5a. Shell environment variable
```bash
echo $HERMES_MODEL   # check if set
```

### 5b. Directly in config.yaml (less obvious)
A top-level `HERMES_MODEL: some-model` key in `~/.hermes/config.yaml` also causes the override, just like an env var. This is not visually obvious — it looks like any other config key.

**Fix**:
- Shell env: `unset HERMES_MODEL`
- Config.yaml: Remove or comment out the `HERMES_MODEL:` line
- Then restart gateway: `hermes gateway restart`

**Pitfall**: Even if `model.default` is set correctly, a `HERMES_MODEL` entry in config.yaml silently locks the model. `/model` switches appear to succeed but the session still uses the locked model on next turn.

## 6. `auxiliary.*.context_length` exceeding model's real context

**Symptom**: 413 "Request payload too large" even though compression is enabled and `threshold: 0.13` looks correct. Compression attempts fail repeatedly and sessions auto-reset.

**Cause**: `auxiliary.compression.context_length` (and other `auxiliary.*.context_length` fields) was set to `819200` — far exceeding the actual model's context limit (e.g. deepseek-v4-flash = 131072). The compression model can't hold the context it's being asked to compress.

**Fix**: Set all `auxiliary.*.context_length` fields to match the actual model context:
```bash
# Verify current values
grep -n "context_length" ~/.hermes/config.yaml

# Fix each auxiliary context_length to the real model limit
hermes config set auxiliary.vision.context_length 131072
hermes config set auxiliary.compression.context_length 131072
hermes config set auxiliary.web_extract.context_length 131072
# ... for all auxiliary.*.context_length entries
```

**Also check**: `compression.` top-level block should NOT have nested `compression:` sub-keys (see #7 below).

## 7. `hermes config set` creates nested keys on dot-paths

**Symptom**: Running `hermes config set compression.compression.context_length 131072` creates a redundant nested structure instead of setting the value at the correct level.

**Cause**: `hermes config set` creates intermediate parent keys as plain dicts. If the YAML already has a `compression:` block, the command creates `compression: {compression: {context_length: ...}}` — a nested `compression` sub-dict under the top-level `compression` key.

**Bad result** (wrong — nested):
```yaml
compression:
  enabled: true
  threshold: 0.13
  compression:        # ← incorrectly created nested block
    context_length: 131072
```

**Correct structure** (what it should be):
```yaml
compression:
  enabled: true
  threshold: 0.13
  target_ratio: 0.2
  protect_last_n: 20
  hygiene_hard_message_limit: 400
# auxiliary.*.context_length lives under auxiliary:, not here
```

**Fix**: Manually edit `~/.hermes/config.yaml` to remove the spurious nested block. Then set auxiliary context lengths correctly via direct YAML edit or `hermes config set auxiliary.<task>.context_length <value>` (not `compression.compression.*`).

**Rule**: If `hermes config set` creates an unexpectedly deep/nested path, read the file and patch manually. Never assume the path created matches the intended structure.

## 8. Ollama unreachable silently breaks model selection

**Symptom**: `model.default` points to an Ollama model (e.g. `qwen3-fast:latest`) but Ollama is unreachable (network timeout). Every request immediately fails with no fallback attempted.

**Cause**: The `model.default` + `model.provider` were set to Ollama but the Ollama service on the remote host is not running or not reachable.

**Fix**: Either start Ollama on the remote host, or switch to a reachable provider:
```bash
hermes config set model.default deepseek-v4-flash
hermes config set model.provider deepseek
hermes gateway restart
```

**Prevention**: After any model/provider change, always verify:
```bash
curl -s --connect-timeout 3 http://<ollama-host>:11434/v1/models \
  -H "Authorization: Bearer ollama"
```

## 9. `model.base_url` and `model.api_key` inside `model:` block override provider-level config

**Symptom**: `model.provider` is set to `ollama` (or another named provider) but requests go to a wrong URL or fail with 404/401. The `providers.<name>.base_url` is correct but routing ignores it.

**Cause**: Legacy or manually edited config left `model.base_url` and/or `model.api_key` fields inside the `model:` block. These fields take precedence over `providers.<name>.base_url` and `providers.<name>.api_key_env_var`, silently redirecting traffic to the wrong endpoint.

**Bad pattern**:
```yaml
model:
  default: qwen3-fast:latest
  provider: ollama              # ← wants to use providers.ollama.base_url
  base_url: http://192.168.0.4:11434/v1   # ← THIS overrides providers.ollama.base_url
  api_key: 625283c246484ba4...  # ← THIS overrides providers.ollama.api_key_env_var
```

**Fix**: Remove `model.base_url` and `model.api_key` from the `model:` block. When `model.provider` is set to a named provider (ollama/deepseek/aicodee/etc.), routing should use `providers.<provider>.base_url`. Only use `model.base_url`/`model.api_key` when `model.provider: custom` with a fully inline custom endpoint (no separate `providers:` entry).

```yaml
# Correct for named provider routing:
model:
  default: qwen3-fast:latest
  provider: ollama              # uses providers.ollama.base_url
  context_length: 131072
  # NO base_url here
  # NO api_key here

providers:
  ollama:
    api_key_env_var: OLLAMA_API_KEY
    base_url: http://localhost:11434/v1
```

**Rule**: If `model.provider` is NOT `custom`, the `model:` block must NOT contain `base_url` or `api_key`. Those fields belong only in `providers.<name>` or in `custom_providers` (when using an unnamed inline endpoint).

## 10. `model.provider: custom` with no `providers.custom` or `custom_providers` entry

**Symptom**: Config has `model.provider: custom` but no `providers.custom:` section and no relevant `custom_providers:` entry. Model requests fail silently or route to wrong endpoint.

**Fix**: Change `model.provider` to the actual provider key name (e.g. `ollama`, `deepseek`, `aicodee`) that exists in `providers:`. Only use `provider: custom` when you have an inline custom endpoint defined in `custom_providers:` (a provider with no separate entry in `providers:`).

Quick structural audit (no external calls):
```bash
python3 - <<'PYEOF'
import yaml, sys, os
path = os.path.expanduser("~/.hermes/config.yaml")
with open(path) as f:
    c = yaml.safe_load(f)

issues = []

# 1. Duplicate model: key inside model: block
m = c.get("model", {})
if "model" in m and m["model"] != m.get("default"):
    issues.append(f"model.model='{m['model']}' != default='{m.get('default')}' — remove model: line inside model block")

# 2. Invalid credential_pool_strategies keys
cps = c.get("credential_pool_strategies", {})
if cps.get("latency_based_routing"):
    issues.append("credential_pool_strategies.latency_based_routing is invalid — remove")

# 3. Redundant model_catalog (only if causing issues)
if "model_catalog" in c and c["model_catalog"].get("enabled", True) is False:
    pass  # disabled is fine
elif "model_catalog" in c:
    issues.append("model_catalog is present — if Dashboard shows unknown providers, set enabled: false")

# 4a. HERMES_MODEL env var check
hm_env = os.environ.get("HERMES_MODEL")
if hm_env:
    issues.append(f"HERMES_MODEL={hm_env} env var overrides config — unset to use config file")

# 4b. HERMES_MODEL in config.yaml (silently overrides /model and model.default)
hm_config = c.get("HERMES_MODEL")
if hm_config:
    issues.append(f"HERMES_MODEL={hm_config} found in config.yaml — this silently locks the model, comment it out")

# 6. auxiliary.*.context_length exceeding safe limits
aux = c.get("auxiliary", {})
model_ctx = c.get("model", {}).get("context_length", 131072)
for task, cfg in aux.items():
    if isinstance(cfg, dict) and "context_length" in cfg:
        aux_ctx = cfg["context_length"]
        if aux_ctx > model_ctx * 2:
            issues.append(f"auxiliary.{task}.context_length={aux_ctx} exceeds safe limit ({model_ctx} x 2) — reduce to {model_ctx}")

# 7. Nested compression.compression block (hermes config set pitfall)
comp = c.get("compression", {})
if isinstance(comp, dict) and "compression" in comp and isinstance(comp.get("compression"), dict):
    issues.append("compression.compression nested block found — remove it; auxiliary.*.context_length lives under auxiliary:, not here")

# 8. model.default pointing to ollama but ollama not reachable
default = c.get("model", {}).get("default", "")
provider = c.get("model", {}).get("provider", "")
if provider == "ollama" and ":" in default:
    issues.append(f"model.provider=ollama + model.default={default} — verify Ollama is running on remote host before relying on this")

if issues:
    print("ISSUES FOUND:")
    for i in issues:
        print(f"  ⚠ {i}")
else:
    print("No common config issues found.")
PYEOF
```

## Fallback Provider Cleanup

OpenRouter free models go offline frequently. The auto-update script at `scripts/auto_update_openrouter_free.sh` keeps the list current. Run manually or wait for the 3am launchd job.

Manual validation:
```bash
curl -s -o /dev/null -w "%{http_code}" https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
# 200 = OK, 401 = bad key
```
