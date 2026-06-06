# 2026-06-04 全 Provider 实测结果

## 方法
脚本 `~/.hermes/scripts/scan_free_models.py` 默认会因为 macOS Python SSL 证书不全而静默返回 `ERR_`（连 HTTP status 都没有），关键修复：

```python
import os, certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
# 再调 scan_free_models.load_env() 和各 scan_xxx()
```

不注入这两行，`load_env()` 加载 key 都成功但 urllib 立刻挂，**用户看到的现象是"key 配了但扫描一个都没有"** —— 极容易误判为 provider 全死。

## OpenRouter — 21 个 :free 模型（全可达，0 限流）
按价值排序：

| 模型 ID | 上下文 | 用途 |
|---|---|---|
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | 256K | 推理，多模态 |
| `poolside/laguna-xs.2:free` | 262K | 通用 |
| `poolside/laguna-m.1:free` | 262K | 通用 |
| `moonshotai/kimi-k2.6:free` | 262K | **中文长文首选** |
| `google/gemma-4-26b-a4b-it:free` | 262K | 通用 |
| `google/gemma-4-31b-it:free` | 262K | 通用 |
| `nvidia/nemotron-3-super-120b-a12b:free` | 1000K | **1M ctx 推理王** |
| `liquid/lfm-2.5-1.2b-thinking:free` | 33K | 小/快 |
| `liquid/lfm-2.5-1.2b-instruct:free` | 33K | 小/快 |
| `nvidia/nemotron-3-nano-30b-a3b:free` | 256K | 推理 |
| `nvidia/nemotron-nano-12b-v2-vl:free` | 128K | 视觉 |
| `qwen/qwen3-next-80b-a3b-instruct:free` | 262K | 通用 |
| `nvidia/nemotron-nano-9b-v2:free` | 128K | 轻量 |
| **`openai/gpt-oss-120b:free`** | 131K | **OpenAI 开源旗舰** |
| `openai/gpt-oss-20b:free` | 131K | 轻量版 gpt-oss |
| `z-ai/glm-4.5-air:free` | 131K | **中文通用** |
| `qwen/qwen3-coder:free` | 1049K | **编码王 480B** |
| `cognitivecomputations/dolphin-mistral-24b-venice-edition:free` | 33K | 无审查 |
| `meta-llama/llama-3.3-70b-instruct:free` | 131K | 通用 |
| `meta-llama/llama-3.2-3b-instruct:free` | 131K | 小/快 |
| `nousresearch/hermes-3-llama-3.1-405b:free` | 131K | Hermes 底座 |

## NVIDIA build.nvidia.com — 119 个模型全免费档（月 1000 credits）
endpoint: `https://integrate.api.nvidia.com/v1/models`，header `Authorization: Bearer $NVIDIA_API_KEY`。
高价值候选：
- `qwen/qwen3.5-397b-a17b` — 397B 旗舰
- `qwen/qwen3.5-122b-a10b` — 122B
- `qwen/qwen3-coder-480b-a35b-instruct` — 编码王
- `nvidia/nemotron-3-super-120b-a12b` — 120B 推理
- `openai/gpt-oss-120b` — OpenAI 开源
- `meta/llama-4-maverick-17b-128e-instruct` — Llama 4
- `nvidia/llama-3.3-nemotron-super-49b-v1.5` — 49B 强推理
- `nvidia/nemotron-3-nano-30b-a3b` — 30B 快
- `deepseek-ai/deepseek-v4-pro` / `deepseek-ai/deepseek-v4-flash`
- `moonshotai/kimi-k2.6`
- `google/gemma-4-31b-it`
- `meta/llama-3.3-70b-instruct`

**全套包含**：yi-large、jamba-1.5-large、gemma-2/3 全系、granite 3.0、starcoder2、deepseek-coder、codegemma、llama-3.1/3.2/3.3/4 全系、mistral、mixtral、phi-3、qwen2/2.5/3/3.5/coder、nemotron-3/4 系列。

**与 OpenRouter 重叠度**：高（gpt-oss/qwen3/llama-3.3/nemotron/kimi/gemma 全两边都有），但 NVIDIA 走的是 NVIDIA 自己的额度，OR 走的是 OR 自己的额度 — 同一时间一边挂另一边大概率能用，是天然的 cross-failover。

## Nous Portal — 1 个 :free 模型
- `stepfun/step-3.7-flash:free`
- 此外还有 deepseek 全系（v3.1/v3.2/v4/r1/chat）非 free 档可用

## 死的
- **DeepSeek 直连** (`https://api.deepseek.com/models`)：401，key `DEEPSEEK_API_KEY` 在 .env 但失效。需重新签发或换号。
- **Cerebras** (`https://api.cerebras.ai/v1/models`)：403 + `error code: 1010`（Cloudflare 拦截），key `CEREBRAS_API_KEY` 在但可能没绑到该 IP/CDN。**不是 key 失效，是网络层 ban**。
- Groq：本次没扫（脚本没覆盖），但 2026-06-03 审计时已标 SSL 断。

## 给 future session 的复用建议
1. **任何"哪些模型还能用"的盘点问题，先跑 SSL 修复版脚本**，别重新写。
2. **用户当前选择**（本次对话明确表态）：不接 fallback 链。**不要自作主张列执行令**。本表只作为参考。
3. **千万别再单独写扫描脚本** —— 本次对话已经确认 `scan_free_models.py` + SSL 修复的组合拳能扫到 140+ 模型。
