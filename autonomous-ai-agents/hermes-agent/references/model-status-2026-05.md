# 模型可用性实测结果 — 2026-05-06（更新）

## 2026-05-06 中文支持测试

| Provider | 模型 | 中文 | 状态 |
|---|---|---|---|
| Groq | llama-3.1-8b-instant | ✅ | ✅ 正常 |
| Google Gemini | gemini-2.5-flash | ✅ | ✅ 需proxy |
| Google Gemini | gemini-2.5-flash-lite | ✅ | ✅ 需proxy |
| Google Gemini | gemini-3-flash-preview | ✅ | ✅ 需proxy |
| Google Gemini | gemini-3.1-flash-lite-preview | ✅ | ✅ 需proxy |
| NVIDIA | meta/llama-3.3-70b-instruct | ✅ | ✅ 正常 |
| NVIDIA | meta/llama-3.1-70b-instruct | ✅ | ✅ 正常 |
| NVIDIA | meta/llama-3.1-8b-instruct | ✅ | ✅ 正常 |
| NVIDIA | mistralai/mistral-nemotron | ✅ | ✅ 正常 |
| NVIDIA | nvidia/llama-3.1-nemotron-nano-8b-v1 | ⚠️ | ❌ 乱码 |
| NVIDIA | nvidia/nemotron-4-340b-instruct | — | ❌ 404 |
| NVIDIA | deepseek-ai/deepseek-v4-flash | — | ❌ 连接失败 |

## 当前可用免费模型汇总

| 平台 | 状态 | 备注 |
|---|---|---|
| ✅ DeepSeek (deepseek-v4-flash) | 主模型 | 中文完美，131K context，速度稳定 |
| ✅ Groq (llama-3.1-8b-instant) | fallback首选 | 速度快，免费额度充足 |
| ✅ Google Gemini (gemini-2.5-flash) | fallback补充 | 需本地代理 127.0.0.1:8899，gemini-2.0-flash 已 429 |
| ✅ NVIDIA (llama-3.3-70b-instruct) | fallback补充 | 免费额度，模型名需带厂商前缀 |
| ❌ V2.aicodee.com (MiniMax-M2.7-highspeed) | 已失效 | HTTP 401 令牌无效，2026-05-06 确认 |
| ❌ OpenRouter | 账户异常 | HTTP 401 "User not found" |
| ❌ Ollama (Mac mini) | 连接超时 | 服务未运行 |

## 当前 fallback_providers 配置

```yaml
fallback_providers:
- model: deepseek-v4-flash
  provider: deepseek
- model: llama-3.1-8b-instant
  provider: groq
- model: gemini-2.5-flash
  provider: gemini
- model: gemini-2.5-flash-lite
  provider: gemini
- model: gemini-3.1-flash-lite-preview
  provider: gemini
- model: meta/llama-3.3-70b-instruct
  provider: nvidia
- model: meta/llama-3.1-70b-instruct
  provider: nvidia
```

> ⚠️ Gemini 的 provider name 是 `gemini`（指向本地代理 http://127.0.0.1:8899）。
> NVIDIA 模型名需包含厂商前缀（如 `meta/llama-3.3-70b-instruct`），不可裸写 `llama-3.3-70b-instruct`。

## Google Gemini 双Auth问题与本地代理方案

### 问题根因
Google Gemini 的 OpenAI 兼容端点**必须同时**：
1. URL 带 `?key=<API_KEY>` 参数
2. Header 带 `Authorization: Bearer <API_KEY>`

标准 OpenAI 兼容只读 Bearer header，不支持双轨认证。需要本地代理中转。

### 代理脚本
`scripts/gemini-proxy.py`（已保存到技能目录），监听 `http://127.0.0.1:8899`。

### 代理启动问题排查（2026-05-06 实测补充）

**常见故障：代理启动失败**

1. **缺失 GEMINI_API_KEY 环境变量**
   - 症状：端口无监听，连接被拒绝
   - 原因：只有 `GOOGLE_API_KEY` 但无 `GEMINI_API_KEY`
   - 修复：在 `.env` 添加 `GEMINI_API_KEY=你的key`（和 GOOGLE_API_KEY 同值）
   - 注：`scripts/gemini-proxy.py` 已支持自动 fallback 读取 `GOOGLE_API_KEY`

2. **端口 8899 已被占用**
   - 症状：`OSError: [Errno 48] Address already in use`
   - 原因：之前启动的代理进程未退出或僵尸进程残留
   - 修复：`lsof -ti:8899 | xargs kill -9` 后重新启动

3. **启动后 Gemini 模型返回 429**
   - gemini-2.0-flash 已耗尽免费额度（429）
   - gemini-2.5-flash 和 gemini-2.5-flash-lite 仍正常（200 OK）

### 启动命令（含 key）
```bash
# 方式1：设好环境变量再启动
export GEMINI_API_KEY=你的key
python3 ~/.hermes/skills/autonomous-ai-agents/hermes-agent/scripts/gemini-proxy.py &

# 方式2：用 Hermes terminal(background=true) 启动
export GEMINI_API_KEY=GOOGLE_AI_KEY_REDACTED-c_NwtpJxg30znXLoifMM && python3 scripts/gemini-proxy.py
```

### 启动顺序
**proxy 必须先于 gateway 启动**：
1. 启动 gemini-proxy（后台）
2. 重启 hermes gateway

### Config provider 配置
```yaml
providers:
  gemini:
    api_key: fake
    base_url: http://127.0.0.1:8899/v1
```

## 各 Provider 详情

### Groq — ✅ 可用
- **Key**: `GRSK_REDACTED`
- **模型**: `llama-3.1-8b-instant`
- **特点**: 速度快，免费额度充足，**首选备用模型**

### Google Gemini — ✅ 需代理
- **Key**: `GOOGLE_AI_KEY_REDACTED-c_NwtpJxg30znXLoifMM`
- **可用模型**: gemini-2.5-flash, gemini-2.5-flash-lite, gemini-3-flash-preview, gemini-3.1-flash-lite-preview, gemini-flash-latest, gemma-4-26b-a4b-it
- **限制**: 大部分模型已用完免费额度（429），当前只有上述6个可用
- **方案**: 本地 gemini-proxy.py 代理

### NVIDIA — ✅ 可用
- **Key**: `NVIDAPI_REDACTED-jzqJQ39yolRppWt503ZLDh49gsvEGjPZ50TiA0nwQ3mZeNI`
- **可用模型**: meta/llama-3.3-70b-instruct, meta/llama-3.1-70b-instruct, meta/llama-3.1-8b-instruct, mistralai/mistral-nemotron
- **坑**: 部分模型回复在 `reasoning_content` 而非 `content` 字段
- **坑**: 模型名需带厂商前缀，裸写模型名会 404

### V2.aicodee.com (MiniMax) — ❌ Key 失效
- **症状**: HTTP 401 "无效的令牌"

### OpenRouter — ❌ 账户异常
- **症状**: HTTP 401 "User not found"

### Ollama (Mac mini) — ❌ 连接超时
- **端点**: `http://192.168.0.4:11434/v1`
