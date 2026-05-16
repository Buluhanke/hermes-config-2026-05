# Custom Provider Credential Pool Failure Modes

## Symptom

API calls fail with `HTTP 404: model 'MiniMax-M2.7-highspeed' not found` pointing to `http://127.0.0.1:11434/v1` (Ollama), even though:
- `config.yaml` correctly configures a custom provider (e.g., `aicodee`) with the right endpoint
- The model name is correct for the intended provider

## Root Cause

When a `custom_providers` credential's API key is invalid/expired, Hermes's credential pool may fall back to another credential in the pool with a **different base URL** (e.g., `custom:local-(localhost:11434)` pointing to local Ollama). The fallback is not to an equivalent endpoint — it's to an entirely different service that doesn't have the requested model.

Evidence in `auth.json`:
```json
"credential_pool": {
  "custom:aicodee": [{ "base_url": "https://v2.aicodee.com/v1", "last_status": "ok" }],
  "custom:local-(localhost:11434)": [{ "base_url": "http://localhost:11434/v1" }]
}
```

When `aicodee` key fails auth, the pool returns the Ollama credential instead. Ollama doesn't know `MiniMax-M2.7-highspeed` → 404.

## Diagnostic Steps

1. **Check `auth.json` credential pool** — look for multiple credentials per provider:
```bash
cat ~/.hermes/auth.json | python3 -m json.tool | grep -A 20 "credential_pool"
```

2. **Test the custom provider endpoint directly** with the API key:
```bash
curl -s -X POST https://v2.aicodee.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"model":"MiniMax-M2.7-highspeed","messages":[{"role":"user","content":"Hi"}],"max_tokens":5}'
```
If you get `"无效的令牌"` (invalid token) or `"invalid token"` — the API key is expired/revoked.

3. **Check which credential was actually used** — the error message shows the Endpoint URL. If it's not your intended provider's URL, a fallback occurred.

## Fix

1. Obtain a fresh API key from the custom provider
2. Update the credential. On macOS with Keychain integration, the key may be stored in the Keychain. Use `hermes auth add` or update via the provider's dashboard
3. Restart the gateway: `hermes gateway restart`

## Prevention

- Periodically test custom provider endpoints: a `"last_status": "ok"` in auth.json means the key was valid at last check, but providers can revoke keys at any time
- If a custom provider is mission-critical, configure a `fallback_model` in `config.yaml` using a different provider family (openrouter, etc.) so fallback goes to a comparable endpoint rather than a random pooled credential

## Restart After Credential Update

**Critical: the gateway does NOT hot-reload credentials.** After updating an API key in `auth.json`, you MUST restart the gateway:

```bash
hermes gateway restart
```

In a **multi-machine setup**, restart the gateway on the FAILING machine — not the machine you're currently SSH'd into or chatting from:

```bash
# On the failing machine (aimac@192.168.0.4 in this setup)
launchctl kickstart -ks gui/<uid>/ai.hermes.gateway

# To find uid: id -u aimac → typically 502 on macOS GUI sessions
launchctl kickstart -ks gui/502/ai.hermes.gateway
```

**How to identify the failing machine:** the error path tells you — `/Users/aimac/.hermes/` = Mac mini (aimac), `/Users/mac/.hermes/` = Mac Pro (mac).
