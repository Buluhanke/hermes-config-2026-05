# OpenRouter Credential Pool Exhaustion — 诊断与处理

## 症状

`errors.log` 中出现：
```
WARNING resolve_provider_client: openrouter requested but OpenRouter credential pool has no usable entries (credentials may be exhausted)
Fallback to openrouter failed: provider not configured
```

同时 `auth.json` 中 OpenRouter 条目显示：
```json
{
  "last_status": "exhausted",
  "last_error_code": 429,
  "last_error_reason": "Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day",
  "last_error_reset_at": 1777939200.0
}
```

**影响范围**：auxiliary 模型（vision、web_extract 等）使用 `provider: auto` 时走 OpenRouter，免费额度耗尽后这些任务静默失败。主模型（aicodee/MiniMax）不受影响，QQ/微信消息收发正常。

## 诊断命令

```bash
# 1. 检查 auth.json 中 OpenRouter credential 状态
cat ~/.hermes/auth.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
creds = d.get('credential_pool',{}).get('openrouter',[])
for c in creds:
    print(f'status={c[\"last_status\"]} code={c[\"last_error_code\"]} reason={c[\"last_error_reason\"]} reset_at={c[\"last_error_reset_at\"]}')
"

# 2. 检查当前时间与重置时间
python3 -c "from datetime import datetime; ts=1777939200.0; print('重置时间:', datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'), '当前:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))"

# 3. 直接测试 OpenRouter 免费模型可用性
curl -s "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"minimax/minimax-m2.5:free","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content','无响应'))"
```

## 错误码区分

| last_error_code | last_error_reason 包含 | 含义 |
|-----------------|----------------------|------|
| 429 | `free-models-per-day` | OpenRouter 账户免费额度耗尽（每天1000次） |
| 429 | `Provider returned error` | 上游 provider（meta-llama, qwen 等）自身的限额 |
| 401/403 | — | API Key 无效或被拒绝 |

**minimax/minimax-m2.5:free** 在 OpenRouter 免费额度耗尽时仍可能可用，疑似独立分配。

## 处理方案

### 方案 1：等待自动重置（推荐）
免费额度每天 UTC 0 点重置（约 13 小时）。auxiliary 任务失败不影响消息收发。

### 方案 2：充值解锁
给 OpenRouter 账户充值 $10+ 解锁 1000次/天 的免费模型请求。

### 方案 3：配置 auxiliary 备用 provider
```bash
# 方案 A: 指定 OpenRouter 付费模型
hermes config set auxiliary.vision.provider openrouter
hermes config set auxiliary.vision.model "google/gemma-4-26b-a4b-it"

# 方案 B: 使用 Groq（需配置 GROQ_API_KEY）
hermes config set auxiliary.vision.provider groq
hermes config set auxiliary.vision.model "llama-3.3-70b-versatile"

# 方案 C: 使用 Ollama 本地模型
hermes config set auxiliary.vision.providerollama
hermes config set auxiliary.vision.model "qwen3-fast:latest"
```

### 方案 4：重置 credential 状态
如果已充值或问题已解决，手动清除 exhausted 状态：
```bash
# 编辑 auth.json，将 openrouter 条目的 "last_status" 改为 "ok"，删除 "last_error_*" 字段
# 然后重启 gateway: launchctl kickstart -kp gui/$(id -u)/ai.hermes.gateway
```

## 验证修复

```bash
# 检查 credential 状态已恢复
cat ~/.hermes/auth.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
c = d['credential_pool']['openrouter'][0]
print(f\"status={c['last_status']} usable={c.get('usable',True)}\")
"

# 重启 gateway 使配置生效
launchctl kickstart -kp gui/$(id -u)/ai.hermes.gateway
```
