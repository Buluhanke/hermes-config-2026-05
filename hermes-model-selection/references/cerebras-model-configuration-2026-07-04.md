# Cerebras 模型配置指南

## 问题描述 (2026-07-04)

用户想使用 Cerebras 提供的模型，但发现 Hermes 无法正确识别 `cerebras/gpt-oss-120b` 这样的配置。

## 根因分析

Cerebras 实际上不直接开发这些模型，而是提供 OpenAI、Google、Z.AI 等公司模型的 API 端点。因此：

1. **`cerebras` 不是 Hermes 支持的 provider 名称**
2. **GPT-OSS-120B 是 OpenAI 开发的模型**
3. **Cerebras 只是提供了 API 访问服务**

## 正确配置方法

### 方法 1：通过 OpenRouter 访问（推荐）

```yaml
model:
  default: openai/gpt-oss-120b
  provider: openrouter
  base_url: https://openrouter.ai/api/v1
```

**优点**：
- 无需额外 API key
- OpenRouter 已配置
- 自动负载均衡

### 方法 2：通过 Cerebras 官方 API

```yaml
model:
  default: gpt-oss-120b
  provider: openai-api  # 使用 OpenAI 兼容格式
  base_url: https://api.cerebras.ai/v1
```

**要求**：
- 需要 `CEREBRAS_API_KEY` in `.env`
- 使用 OpenAI 兼容格式

## 验证命令

```bash
# 检查 OpenRouter 是否有该模型
curl -s -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  "https://openrouter.ai/api/v1/models" | grep -i gpt-oss-120b

# 检查 Cerebras 官方 API
curl -s -H "Authorization: Bearer $CEREBRAS_API_KEY" \
  "https://api.cerebras.ai/v1/models" | grep -i gpt-oss-120b
```

## 常见误区

### ❌ 错误配置
```yaml
# 错误：Hermes 不识别 cerebras provider
provider: cerebras
model: cerebras/gpt-oss-120b
```

### ✅ 正确配置
```yaml
# 正确：通过 OpenRouter 访问
provider: openrouter
model: openai/gpt-oss-120b
```

## 模型归属说明

| 模型 ID | 实际开发者 | 提供商 | 访问方式 |
|---|---|---|---|
| `gpt-oss-120b` | OpenAI | Cerebras | OpenRouter / Cerebras API |
| `gemma-4-31b` | Google | Cerebras | OpenRouter / Cerebras API |
| `zai-glm-4.7` | Z.AI | Cerebras | OpenRouter / Cerebras API |

## 推荐策略

对于日常使用：
1. **优先使用 OpenRouter** - 无需额外配置
2. **需要特殊功能时用 Cerebras 官方 API** - 如需要特定优化
3. **避免直接使用 `cerebras` provider** - Hermes 不支持