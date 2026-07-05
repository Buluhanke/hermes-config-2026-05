# Fallback Chain — 2026-07-05 快优先模式

## 配置快照（落地后实时值）

**`fallback_chain`**（共 11 条，快/免费 → 慢/付费）：

```
custom:123.56.67.77:9100/MiniMax-M2.7-highspeed,   ← 首选代理（用户主力）
gemini/gemini-2.5-flash,                             ← Google 免费额度
glm/glm-4-flash,                                      ← 智谱免费
ollama-cloud/gemma4:31b,                              ← Ollama 云免费
nous/stepfun/step-3.7-flash:free,                    ← Nous Portal 免费
openrouter/qwen/qwen3-coder:free,                    ← OR 免费
openrouter/google/gemma-4-31b-it,                     ← OR Gemma 免费
openrouter/nvidia/nemotron-3-super-120b-a12b,        ← OR 付费（Nemotron）
openrouter/qwen/qwen3.5-397b-a17b,                   ← OR 付费（Qwen3.5 397B）
zai/glm-4-flash,                                     ← Z.AI 备用路由
custom:apihub.agnes-ai.com/agnes-2.0-flash           ← 最终兜底
```

**Timeout 关键参数**：
- `model.stream_chunk_timeout_seconds: 25`
- `agent.api_max_retries: 0`（失败立即切）
- `agent.gateway_timeout: 300`（5分钟上限）
- `agent.restart_drain_timeout: 60`

## 格式规范

`fallback_chain` 每条格式：`provider/model`（与 `fallback_providers[].provider` 标签对应）。

⚠️ 以前用 `openrouter` 作为 provider 名但模型格式用 `qwen-qwen3-coder`（连字符）是错的。应使用 `openrouter/qwen/qwen3-coder:free`。

## 验证命令

```bash
grep 'fallback_chain:' ~/.hermes/config.yaml
```

## 关联

- 配置改动：execute_code python3 重写 config.yaml（Workaround A）
- 重启方式：`bash /tmp/restart_gateway.sh`（launchd kickstart）
- Broker socket 路径：`/tmp/hermes-restart-broker.sock`（broker 不在时用脚本法）
