# Provider Authentication Troubleshooting Guide

## Common Failure Patterns

### HTTP 401: Missing Authentication header
- **Symptom**: "Provider authentication failed. Check the configured credentials"
- **Root causes**:
  1. API key expired or invalid
  2. Wrong provider configuration in config.yaml
  3. Environment variables not set
  4. Provider switched but old key still referenced

### Troubleshooting Steps

#### Step 1: Check gateway logs
```bash
tail -20 ~/.hermes/logs/gateway.log
# Look for "HTTP 401" or "AuthenticationError"
```

#### Step 2: Verify provider configuration
```bash
hermes config show
# Check current model.provider and model.default
```

#### Step 3: Test API connectivity
```bash
# For GLM (智谱)
curl -s -H "Authorization: Bearer ${GLM_API_KEY}" \
  -H "Content-Type: application/json" \
  "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
  -d '{"model":"glm-4-flash","messages":[{"role":"user","content":"test"}]}'

# For ZAI
curl -s -H "Authorization: Bearer ${ZAI_API_KEY}" \
  -H "Content-Type: application/json" \
  "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
  -d '{"model":"glm-4.5-flash","messages":[{"role":"user","content":"test"}]}'
```

#### Step 4: Check environment variables
```bash
env | grep -E "(ZAI|GLM|OPENROUTER|NVIDIA)"
# Should show API keys, not "not set"
```

#### Step 5: Update configuration
```bash
# Switch to working provider
hermes config set model.provider <working_provider>
hermes config set model.default <working_model>
```

## Case Study: 2026-07-05 ZAI Authentication Failure

**Problem**: ZAI provider authentication failed, fallback to GLM also failed
**Root cause**: Both ZAI and GLM API keys were expired/unset
**Solution**: 
1. Switched provider to GLM (which had valid key in .env)
2. Updated config: `model.default=glm-4-flash provider=glm`
3. Verified GLM API connectivity with curl
4. Required manual gateway restart: `hermes gateway restart`

## Prevention

- Regular API key rotation (check expiry dates)
- Monitor gateway logs for authentication errors
- Keep fallback providers configured and tested
- Document working provider configurations in memory

## Reference Commands

```bash
# Check all configured providers
grep -A 20 "providers:" ~/.hermes/config.yaml

# Check fallback chain
grep -A 10 "fallback_chain:" ~/.hermes/config.yaml

# Test individual provider connectivity
curl -s -H "Authorization: Bearer $API_KEY" "$API_BASE_URL/v1/models" | jq .
```