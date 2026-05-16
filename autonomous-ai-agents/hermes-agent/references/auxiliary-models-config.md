# Auxiliary Models — Configuration & Common Errors

Auxiliary models power secondary tasks: vision, compression, session_search, title_generation, skills_hub, approval, mcp, web_extract, curator.

## Default Behavior: `provider: auto`

All auxiliary tasks default to `provider: auto`, which auto-selects from available credentials (OpenRouter API key > Google API key > others). No manual config needed unless you want explicit control.

```yaml
auxiliary:
  title_generation:
    provider: auto   # default — auto-selects
  compression:
    provider: auto
  vision:
    provider: auto
```

## Common Error: HTTP 403 "model is not available in your region"

**Symptom**: `Auxiliary title generation failed: HTTP 403: This model is not available in your region`

**Cause**: `provider: auto` may select a model (e.g. Google Gemini) that doesn't work in the user's region. When that model is called, you get 403.

**Fix options** (pick one):

### Option A: Remove the offending provider from config
If Google Gemini was auto-selected and causes 403, delete the `providers.google` block from config.yaml. `provider: auto` will skip it and pick the next available credential.

```yaml
# Delete this block from config.yaml:
providers:
  google:
    api_key: GOOGLE_AI_KEY_REDACTED...   # ← remove entirely
    base_url: https://generativelanguage.googleapis.com/v1beta/openai
```

### Option B: Explicitly set auxiliary provider to a working one
### Auxiliary models not working
If `auxiliary` tasks (vision, compression, session_search) fail silently, the `auto` provider can't find a backend. Either set `OPENROUTER_API_KEY` or `GOOGLE_API_KEY`, or explicitly configure each auxiliary task's provider:
```bash
hermes config set auxiliary.vision.provider <your_provider>
hermes config set auxiliary.vision.model <model_name>
```
**Note**: If OpenRouter API key is valid but auxiliary calls fail with "provider not configured", the credential pool entry may be `exhausted` (429 rate limit). See `references/auxiliary-models-config.md` → "Credential Pool Exhaustion" section.

Or for all auxiliary tasks at once:
```bash
hermes config set auxiliary.vision.provider openrouter
hermes config set auxiliary.compression.provider openrouter
# etc.
```

### Option C: Keep auto but ensure OpenRouter key is present
`provider: auto` prioritizes OpenRouter if `OPENROUTER_API_KEY` is in `.env` or `providers.openrouter.api_key` is in config. Make sure that credential is present and valid.

## Where to Configure (Custom Endpoint vs Auxiliary)

| UI Option | What it does | Use when |
|-----------|---------------|----------|
| **Custom endpoint** | Adds a new main model Provider | You want this model as primary or fallback for conversation |
| **Configure auxiliary models** | Sets the model for auxiliary tasks | You got "Auxiliary X failed" error |

The title generation error → use **Configure auxiliary models**.

## Credential Pool Exhaustion (429 Rate Limit)

**Symptom**: Auxiliary calls fail with `provider not configured` or `Fallback to openrouter failed`, but the OpenRouter API key is valid and present.

**Root cause**: The credential in `auth.json`'s `credential_pool.openrouter` has `last_status: exhausted` with `last_error_code: 429`. This happens when OpenRouter's free-tier daily limit (1000 requests/day) is exceeded.

**Diagnosis**:
```bash
cat ~/.hermes/auth.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
for cred in d.get('credential_pool',{}).get('openrouter',[]):
    print('status:', cred.get('last_status'))
    print('error_code:', cred.get('last_error_code'))
    print('error_msg:', cred.get('last_error_message'))
    reset_at = cred.get('last_error_reset_at')
    if reset_at:
        from datetime import datetime
        print('resets_at:', datetime.fromtimestamp(reset_at).strftime('%Y-%m-%d %H:%M:%S'))
"
```

**Fix options**:

1. **Wait for automatic reset** — OpenRouter free tier resets at ~00:00 UTC. Check `last_error_reset_at` in `auth.json`.

2. **Clear exhaustion flag** (allow retry immediately):
   ```bash
   python3 -c "
   import json
   path = '/Users/mac/.hermes/auth.json'
   with open(path) as f: d = json.load(f)
   for c in d.get('credential_pool',{}).get('openrouter',[]):
       c['last_status'] = 'usable'
       c['last_error_code'] = None
   with open(path,'w') as f: json.dump(d,f,indent=2)
   "
   launchctl kickstart -kp gui/$(id -u)/ai.hermes.gateway
   ```
   > Note: The API key is still rate-limited server-side; clearing the flag lets Hermes retry. If the daily limit is hard-exhausted, calls will get 429 again until reset time.

3. **Configure a dedicated auxiliary provider** (avoids pool conflicts):
   ```bash
   hermes config set auxiliary.vision.provider openrouter
   hermes config set auxiliary.vision.model "google/gemma-4-26b-a4b-it:free"
   hermes config set auxiliary.compression.provider groq
   hermes config set auxiliary.compression.model "llama-3.3-70b-versatile"
   ```
   Groq free tier does not share OpenRouter's rate limit pool.

4. **Add a second OpenRouter key** to the credential pool as a hot standby: `hermes auth add`

**Why it affects auxiliary but not main model**: The main model uses `fallback_providers` which reads config directly. Auxiliary uses `provider: auto` which reads from `credential_pool` in `auth.json`. When a pool entry is marked `exhausted`, `provider: auto` skips it and reports "provider not configured" rather than "rate limited".

## Verification

Test that auxiliary calls work:
```bash
curl -s https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer <your-openrouter-key>" | python3 -c "
import json,sys
models = json.load(sys.stdin)['data']
free = [m['id'] for m in models if ':free' in m['id']]
print(f'OpenRouter free models available: {len(free)}')
"
```

## Key Config Path

```
auxiliary.
  title_generation.
    provider: auto | openrouter | google | ...
    model: ''  # empty = provider's default
    base_url: ''
    api_key: ''
    timeout: 30
```

Same structure repeats for: `vision`, `compression`, `session_search`, `skills_hub`, `approval`, `mcp`, `web_extract`, `curator`.
