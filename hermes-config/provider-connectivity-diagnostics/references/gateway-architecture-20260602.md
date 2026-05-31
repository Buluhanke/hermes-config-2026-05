# Gateway 架构笔记（2026-06-02晚实测）

## config.yaml + auth.json 双来源配置

Gateway 从两个地方读取 provider 配置：

### config.yaml（主模型路由）
- 控制当前 primary model 的 provider/base_url/api_key
- `model.provider: custom` → 从 `custom_providers` 列表匹配
- `model.default`: 模型名（如 llama-3.3-70b）
- 改动后需 gateway 重启生效

### auth.json（credential_pool，各 provider 实际凭证）
- 存各 provider 的实际 base_url + api_key
- 结构：`{"credential_pool": {"provider_name": [{"base_url": "...", "api_key": "...", "last_status": "..."}]}}`
- gateway 运行时动态读取，修改后可能自动生效

**当前状态**：
- config.yaml 主模型指向 `custom` + Cerebras base_url，但 Cerebras key 已失效（401）
- auth.json credential_pool 里 MiniMax 有有效凭证，但主模型没指向它
- fallback 指向 minimax-cn，429时不会切到 DeepSeek

## OpenRouter via Nous Portal Bearer Token

从 nous_auth.json 取出 access_token，调用 OpenRouter：
```
curl -H "Authorization: Bearer $TOKEN" https://openrouter.ai/api/v1/chat/completions \
  -d '{"model":"deepseek/deepseek-v4-flash","messages":[...]}'
```

**注意**：Bearer token 和 OpenRouter API key 是两套。OpenRouter key 存在 .env 的 `OPENROUTER_API_KEY`（sk-or-v1-...格式）。

## gateway.error.log 正确读法

```bash
# 过滤掉 screen_watcher/smolvlm 噪音
tail -200 ~/.hermes/logs/gateway.error.log | grep -v "screen_watch\|smolvlm\|VLM错误" | grep -E "provider=|model=" | tail -20

# 找最新 provider 错误
tail -50 ~/.hermes/logs/gateway.error.log | grep "ERROR agent.conversation_loop" | tail -5
```

## 各 API Key 格式（2026-06-02实测）

| Provider | Key格式 | 长度 | 状态 |
|----------|---------|------|------|
| DeepSeek | sk-7d775eb... | 35 | ❌ 已失效 |
| OpenRouter | sk-or-v1-... | 60+ | ✅ 可用 |
| MiniMax CN | sk-cp-pjty... | 125 | ❌ 额度耗尽 |
| Cerebras | csk-585933... | 41 | ❌ key失效 |
| Groq | gsk_... | - | ❌ 未测试 |

## Hindsight 降级原因

```
WARNING plugins.memory.hindsight: Hindsight retain failed: No module named 'hindsight_client'
```

不是 Docker 容器问题（容器在跑），是 Python 端缺少 hindsight_client 包。
修：`. venv/bin/activate && pip install hindsight_client`
