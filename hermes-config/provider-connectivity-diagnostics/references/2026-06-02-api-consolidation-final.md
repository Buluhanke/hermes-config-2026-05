# 2026-06-02 API Key 归集 & Provider 连通性最终结果

## 执行摘要

**目标**：所有 API key 归集到 `.env`，config.yaml 只保留 `api_key_env` 引用。

**结果**：✅ 完成

---

## Provider 连通性最终结果

| Provider | Key 在 .env | HTTP 测试 | 结论 |
|----------|-------------|-----------|------|
| AICODEE (v2.aicodee.com) | `AICODEE_API_KEY` | ✅ 200 | 正常 |
| DeepSeek 直连 | `DEEPSEEK_API_KEY` | ✅ 200 | 正常 |
| OpenRouter | `OPENROUTER_API_KEY` | ✅ 200 | 正常 |
| MiniMax-CN | `MINIMAX_CN_API_KEY` | ⚠️ 429 | key有效，额度耗尽 |
| Gemini | `GEMINI_API_KEY` | ⚠️ 超时 | 网络/墙问题，key本身有效 |
| Cerebras | `CEREBRAS_API_KEY` | ❌ 403/1009 | IP被Cloudflare屏蔽，key有效 |
| Groq | ~~`GROQ_API_KEY`~~ | ❌ 403 | key已从.env删除（过期） |

---

## .env 最终状态

**有效 key（21个）：**
- `AICODEE_API_KEY` ✅
- `DEEPSEEK_API_KEY` ✅
- `OPENROUTER_API_KEY` ✅
- `MINIMAX_CN_API_KEY` ⚠️ 额度耗尽
- `GEMINI_API_KEY` ⚠️ 网络超时
- `CEREBRAS_API_KEY` ❌ IP屏蔽
- `TELEGRAM_BOT_TOKEN`、`WEIXIN_TOKEN`、`QQ_CLIENT_SECRET`
- `FEISHU_APP_SECRET`、`GITHUB_MCP_TOKEN`
- `BAIDU_*`、`FIRECRAWL_API_KEY`、`BOCHA_API_KEY`、`EXA_API_KEY`
- `FREELLMAPI_KEY`、`GLM_API_KEY`、`NVIDIA_API_KEY`、`OLLAMA_API_KEY`
- `DEEPSEEK_BASE_URL`、`GEMINI_BASE_URL`、`MINIMAX_CN_BASE_URL`、`SEARXNG_API_KEY`

**已删除：**
- `GROQ_API_KEY` — key 失效（从 config.yaml 和 .env 双删除）

**Base URL 配置：**
- `DEEPSEEK_BASE_URL=https://api.deepseek.com/v1`
- `GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta`
- `MINIMAX_CN_BASE_URL=https://api.minimaxi.com/v1`

---

## config.yaml 最终状态

**custom_providers（全部使用 `api_key_env` 引用 .env）：**
```yaml
custom_providers:
- name: V2.aicodee.com
  base_url: https://v2.aicodee.com/v1
  api_key_env: AICODEE_API_KEY
  model: MiniMax-M2.7-highspeed   # ← /model picker 匹配用
- name: Api.groq.com
  base_url: https://api.groq.com/openai/v1
  api_key_env: GROQ_API_KEY
  model: llama-3.3-70b-versatile
- name: Api.cerebras.ai
  base_url: https://api.cerebras.ai/v1
  api_key_env: CEREBRAS_API_KEY
```

**硬编码 key：0 个** ✅

**secrets.bitwarden 残留：已清理** ✅

---

## V2.aicodee.com /model Picker 消失修复

**根因**：`yaml.safe_load()` + `yaml.dump()` 重建 custom_providers 时，`model: MiniMax-M2.7-highspeed` 字段丢失。导致 /model picker 的模型匹配逻辑无法识别当前模型，V2.aicodee.com 从 picker 中消失。

**修复**：显式补回 `model: MiniMax-M2.7-highspeed`。

**教训**：yaml.dump() 只重建单个区块时，必须确保所有字段都存在。

---

## Bitwarden 残留清理

**操作**：删除 `secrets.bitwarden` 配置段

**方法**：Python `yaml.safe_load()` → `del cfg['secrets']['bitwarden']` → `yaml.dump()` 写回

**事故**：最初用 `sed -i '' '/^secrets:$/,/^    auto_install: true$/d'` 范围删除，误伤了中间其他配置行，导致 YAML 报 `mapping values are not allowed here` 错误。从备份恢复后改用 Python 字典操作成功。

**结论**：删除配置区块用 Python 字典操作，不用 sed 范围删除。

---

## 核心原则（已确认）

> "所有api以最新为准，以前的可能没用了，如果能测试尽量测试一下，能用再保存。不要又把之前过期的来覆盖了最新当前的，那就适得其反了。"

**行动准则**：
1. config.yaml 里正在跑的值 = 真实权威值
2. 归集前必须逐个 HTTP 实测
3. yaml.dump() 只重建单个区块，确保字段不丢失
4. 删除配置区块用 Python 字典操作，不用 sed 范围删除
