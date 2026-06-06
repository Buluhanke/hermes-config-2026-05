# 模型审计实测结果 — 2026-06-03

> 触发场景：用户从"做加法"转向"做减法"，先盘点 9 个 provider 的真实可用性。
> 测试方法：`1+1=几?只回数字` 最小 prompt + system="直接答,不要解释"，temperature=0，max_tokens=20-50。

## 三档分类

### 🟢 真能打（6 个 — 推荐用）

| 模型 | 协议/URL | 参数 | 上下文 | 速度 | 用途 |
|---|---|---|---|---|---|
| MiniMax-M3 | v2enby anthropic | 旗舰 | 8K | 快 | **主用**（当前就在跑） |
| `nvidia/nemotron-3-super-120b-a12b:free` | OR OpenAI | 120B | **1M** | ~2s | 复杂推理 fallback（reasoning 分离） |
| `nvidia/nemotron-3-nano-30b-a3b:free` | OR OpenAI | 30B | 256K | **~1s** | 快速推理 |
| `moonshotai/kimi-k2.6:free` | OR OpenAI | — | 262K | ~1s | 中文长文 |
| `google/gemma-4-26b-a4b-it:free` | OR OpenAI | 26B | 262K | ~1.8s | 通用 |
| `z-ai/glm-4.5-air:free` | OR OpenAI | — | 131K | ~2s | 中文 |

### 🟡 凑合能用（2 个 — 兜底层）

| 模型 | 限制 |
|---|---|
| `gemini-2.5-flash-lite` (官方) | Pro/3.x/3.1 全 quota 满，flash-lite 是唯一能用的 Gemini |
| `glm-4.5-air` (智谱官方) | glm-4.5/4.6/5/5.1 全部 1113 余额不足，只有 4.5-air 还能用 |

### 🔴 失效 / 别碰（13+ 个 — 从 config 删）

| 失败对象 | 错误码 | 原因 |
|---|---|---|
| DeepSeek | 401 | key 过期（`****f076` 失效） |
| Groq | SSL EOF | Mac 网络代理 / 协议问题 |
| Cerebras | SSL EOF | 同上 |
| `openai/gpt-oss-120b:free` | 503 | 上游 provider 故障 |
| `openai/gpt-oss-20b:free` | 503 | 同上 |
| `meta-llama/llama-3.3-70b-instruct:free` | 429 | OR 上游限流 |
| `qwen/qwen3-coder:free` | 429 | OR 上游限流 |
| `nousresearch/hermes-3-llama-3.1-405b:free` | 429 | OR 上游限流 |
| `qwen/qwen3-next-80b-a3b-instruct:free` | 429 | OR 上游限流 |
| `google/gemma-4-31b-it:free` | 503 | OR 上游故障 |
| `gemini-2.5-pro` | 429 | quota 满 |
| `gemini-3-pro-preview` | 429 | quota 满 |
| `gemini-3.1-pro-preview` | 429 | quota 满 |
| `gemini-pro-latest` | 429 | quota 满 |
| `gemini-2.5-flash` | empty content | safety 拦（沙盒 prompt 触发） |
| `gemini-3-flash-preview` | empty content | safety 拦 |
| `gemini-3.5-flash` | empty content | safety 拦 |
| `gemini-flash-latest` | empty content | safety 拦 |
| 智谱 `glm-4.5` / `4.6` / `4.7` / `5` / `5-turbo` / `5.1` | 1113 | 资源包余额不足 |

## OR 免费模型完整列表（21 个，按 ctx 排序）

```
qwen/qwen3-coder:free                            1048K  (代码特化, 1M ctx, 当前 429)
nvidia/nemotron-3-super-120b-a12b:free           1000K  ✅ 推荐
poolside/laguna-xs.2:free                         262K
poolside/laguna-m.1:free                          262K
moonshotai/kimi-k2.6:free                         262K  ✅ 推荐
google/gemma-4-26b-a4b-it:free                    262K  ✅ 推荐
google/gemma-4-31b-it:free                        262K  (503)
qwen/qwen3-next-80b-a3b-instruct:free             262K  (429)
nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free 256K
nvidia/nemotron-3-nano-30b-a3b:free               256K  ✅ 推荐 (reasoning)
openai/gpt-oss-120b:free                          131K  (503)
openai/gpt-oss-20b:free                           131K  (503)
z-ai/glm-4.5-air:free                             131K  ✅ 推荐
meta-llama/llama-3.3-70b-instruct:free            131K  (429)
meta-llama/llama-3.2-3b-instruct:free             131K
nousresearch/hermes-3-llama-3.1-405b:free         131K  (429)
nvidia/nemotron-nano-12b-v2-vl:free               128K
nvidia/nemotron-nano-9b-v2:free                   128K
liquid/lfm-2.5-1.2b-thinking:free                  32K
liquid/lfm-2.5-1.2b-instruct:free                  32K
cognitivecomputations/dolphin-mistral-24b-venice-edition:free  32K
```

## Gemini 完整模型列表（38 个，已过滤 generateContent 能力）

旗舰：`gemini-3.1-pro-preview` (1M ctx, quota 满) / `gemini-3-pro-preview` / `gemini-2.5-pro` (quota 满)
快：`gemini-2.5-flash` / `gemini-2.5-flash-lite` (✅ 唯一能用) / `gemini-flash-latest`
多模态：`gemini-3-pro-image-preview` / `nano-banana-pro-preview`
深度研究：`deep-research-pro-preview-12-2025` / `deep-research-max-preview-04-2026`
机器人：`gemini-robotics-er-1.5/1.6-preview`
其他：`antigravity-preview-05-2026` / `gemini-2.5-computer-use-preview-10-2025`

## 智谱 GLM 实际能列出的模型
```
glm-4.5 / glm-4.5-air  / glm-4.6 / glm-4.7 / glm-5 / glm-5-turbo / glm-5.1
```

## v2enby anthropic 协议提示
- endpoint: `https://api.minimaxi.com/anthropic/v1/messages`
- header: `x-api-key: <key>`, `anthropic-version: 2023-06-01`
- 模型名: `MiniMax-M2.7` / `MiniMax-M3` (刚切到 M3)
- 已知错误: `429 usage limit exceeded (2056)` — 用户触达每日/每分钟额度上限，等几小时或换 OR fallback

## 关键修复点（等用户拍板）
1. `config.yaml` 的 `model.default` 还是 `MiniMax-M2.7`，需改成 `M3`
2. `config.yaml` 缺 `fallback_providers`，加 `[openrouter, gemini-flash-lite]`
3. `.env` 里失效的 key 可清理（DeepSeek / Groq / Cerebras）
4. `self_optimization.py` 已有 patch（移除 DeepSeek 健康检查），验证一下还在

## 复现命令
```bash
python3 ~/.hermes/skills/free-model-scanner/scripts/audit_all_providers.py
```

输出格式：每 provider 一段，每模型一行 (✅/❌ + 耗时 + 回复 + reasoning + 错误码)。
