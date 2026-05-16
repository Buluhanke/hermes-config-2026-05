# 模型连通性检测参考

## 快速检测命令

### 1. hermes doctor（推荐第一步）
```bash
hermes doctor
```
检查配置完整性和认证状态。

### 2. 测试各 Provider API 连通性

**aicodee (MiniMax):**
```bash
curl -s "https://v2.aicodee.com/v1/models" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); [print(m['id']) for m in d.get('data',[])]"
```

**Gemini:**
```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$GOOGLE_API_KEY" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); [print(m['name']) for m in d.get('models',[])]"
```

**OpenRouter:**
```bash
curl -s "https://openrouter.ai/api/v1/models" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); [print(m['id']) for m in d.get('data',[])]"
```

### 3. 快速连通性探测（不需 API key）
```bash
# 检查基础连接
curl -s --connect-timeout 5 https://v2.aicodee.com/v1/models -o /dev/null -w "%{http_code}"

# 检查 DNS 解析
dig +short v2.aicodee.com
```

## 常见错误判断

| HTTP 状态码 | 含义 | 处理方式 |
|------------|------|---------|
| 200 | ✅ 可用 | 模型列表正常返回 |
| 401 | ❌ API Key 无效 | 检查 key 是否正确 |
| 403 | ❌ 权限不足 | 检查 key 是否有该模型权限 |
| 429 | ⚠️ 限速 | 稍后重试 |
| 500/503 | ⚠️ 服务端问题 | 检查 provider 状态 |
| 超时 | ❌ 网络不通 | 检查 VPN/防火墙 |

### 3. 测试实际模型调用（流式响应处理）

```bash
# OpenRouter 免费模型测试
curl -s --max-time 15 "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"minimax/minimax-m2.5:free","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'

# Ollama 本地模型测试（流式 NDJSON，需取最后一行）
curl -s --max-time 15 "http://<IP>:11434/api/chat" \
  -d '{"model":"qwen3-fast:latest","messages":[{"role":"user","content":"hi"}],"max_tokens":20}' \
  | tail -1 | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(d.get('message',{}).get('content','无'))"
```

### 4. Ollama 连通性检测

Ollama 的 `/v1/models` 端点对 Python 3.11+ SSL 有兼容问题，用 `/api/tags` 代替：
```bash
curl -s --max-time 5 "http://<IP>:11434/api/tags" \
  -H "Authorization: Bearer ollama" \
  | python3 -c "import json,sys; [print(m['name']) for m in json.load(sys.stdin).get('models',[])]"
```

## OpenRouter 免费模型特别说明

2026年5月测试结果：
- OpenRouter 免费模型整体受 `free-models-per-day` 配额限制，大多数模型返回 429
- **例外**：`minimax/minimax-m2.5:free` 在配额耗尽时仍可能可用（疑似独立分配）
- **重置时间**：每天 UTC 0 点（约 13 小时一周期）
- 诊断：`auth.json` 中 `last_status: exhausted` + `last_error_code: 429` + `last_error_reason: "Rate limit exceeded: free-models-per-day"`

详见 `references/openrouter-exhaustion-diagnostic.md`

## 常见错误判断

| HTTP 状态码 | 含义 | 处理方式 |
|------------|------|---------|
| 200 | ✅ 可用 | 模型列表正常返回 |
| 401 | ❌ API Key 无效 | 检查 key 是否正确 |
| 403 | ❌ 权限不足 | 检查 key 是否有该模型权限 |
| 429 | ⚠️ 限速 | 稍后重试 |
| 500/503 | ⚠️ 服务端问题 | 检查 provider 状态 |
| 超时 | ❌ 网络不通 | 检查 VPN/防火墙 |

## 完整模型可用性报告格式

报告给用户时应包含：
1. ✅ **可用** — 模型名称 + 实测响应时间
2. ⚠️ **可用但慢** — 模型名称 + 超时情况
3. ❌ **不可用** — 模型名称 + 错误原因（401/403/超时）
4. ❓ **未知** — 无法探测，需用户提供 key
