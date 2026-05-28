# v2.aicodee.com API 聚合网关

## 平台概况

**v2.aicodee.com** 是一个第三方 API 聚合网关（"极速AI"），基于 New API 架构搭建。它将 30+ AI 模型供应商的接口统一成 OpenAI/Anthropic 兼容格式，通过单一入口提供服务。

## 支持的 API 端点

| 端点 | 对应官方 API |
|------|-------------|
| `/v1/chat/completions` | OpenAI Chat |
| `/v1/responses` | OpenAI Responses API |
| `/v1/responses/compact` | OpenAI Responses (compact) |
| `/v1/messages` | Anthropic Messages |
| `/v1/embeddings` | 文本向量化 |
| `/v1/rerank` | Cohere Rerank |
| `/v1/images/generations` | 图片生成 |
| `/v1/audio/speech` | TTS 语音合成 |
| `/v1/audio/transcriptions` | ASR 语音转文字 |
| `/v1beta/models` | Beta 模型列表 |

## 聚合的 30+ 供应商

可以看到的 Logo 列表（非完整）：
MoonshotAI / OpenAI / Grok / Zhipu / Volcengine / Cohere / Claude / Gemini / Suno / Minimax / Wenxin / Spark / Qingyan / DeepSeek / Qwen / Midjourney / AzureAI / Hunyuan / Xinference

## API Key 行为差异

| 凭据类型 | base_url | `/v1/models` 返回 | 说明 |
|---------|----------|-------------------|------|
| AICODEE_API_KEY | `https://v2.aicodee.com/v1` | 4 个 MiniMax 模型 | M2.1, M2.5, M2.5-highspeed, M2.7-highspeed |
| AICODEE_API_KEY | `https://v2.aicodee.com/v1` | — | 实际可调用模型比 model list 多（需试错） |
| StepFun Step Plan API Key | `https://v2.aicodee.com` | 0 个模型 | Step Plan 的 token 体系 /v1/models 不返回数据 |
| StepFun Step Plan API Key | `https://v2.aicodee.com/v1` | 取决于配额 | 需配合具体模型名调用 chat completions |

**关键发现**：
- AICODEE_API_KEY 以 `/v1` 结尾的 base_url 能通过 `/v1/models` 看到 4 个 MiniMax 模型
- StepFun 的 API key 在 `/v1/models` 返回空列表，但实际可能可用（token-based 调度）
- 同一网关不同 key 看到的模型集不同，受 key 的套餐/额度限制

## Hermes 配置要点

### aicodee-relay provider（当前在用）

```yaml
custom_providers:
  - api_key_env_var: AICODEE_API_KEY
    base_url: https://v2.aicodee.com/v1
    model: MiniMax-M2.7-highspeed  # 用户配置只指定了 1 个
    name: aicodee-relay
```

实际端点可用模型：MiniMax-M2.1, M2.5, M2.5-highspeed, M2.7-highspeed（共 4 个）
Hermes model catalog 显示为 "aicodee-relay (4 models)"，但 config 只配了 1 个。

### StepFun provider

```yaml
custom_providers:
  - api_key_env_var: STEPFUN_API_KEY  # 或明文 key
    base_url: https://v2.aicodee.com    # 无 /v1 后缀
    model: MiniMax-M2.7-highspeed
    name: V2.aicodee.com
```

Hermes model catalog 显示为 "V2.aicodee.com (0 models)"，因为 /v1/models 返回空列表。
需要手动指定 model name 使用。

## 与 credential_pool 的关系

v2.aicodee.com 相关的 provider 名称（在 auth.json credential_pool 中可见）：
- `custom:aicodee` — 直接 aicodee 线路
- `custom:aicodee-relay` — aicodee 中继（当前主 provider）
- `custom:v2.aicodee.com` — v2 线路
- `custom:minimax-relay-(v2.aicodee.com)` — MiniMax 通过 aicodee 中继

更新 key 时这 4 个 provider 共 7 条 credential 需要一起更新。
