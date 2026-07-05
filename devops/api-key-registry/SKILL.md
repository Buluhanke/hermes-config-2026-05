---
name: api-key-registry
description: Hermes API key inventory and provider management
---

# API Key 管理清单

## 存储原则
- 所有 key 存在 `~/.hermes/.env`，config.yaml 用 `${XXX_API_KEY}` 引用，不硬编码
- key 内容不得写入 memory（触发威胁检测），只记录 key 名称和用途

## 现有 Key 一览（2026-07-06）

| EnvVar | 前缀 | Provider | 用途 | 状态 |
|--------|------|----------|------|------|
| `MINIMAX_M3_API_KEY` | sk-290... | custom:123.56.67.77:9100 | MiniMax M2.7 代理首选 | ✅ config 有 |
| `GROQ_API_KEY` | gsk_GHs6o... | groq | Llama 3.3 70B 极速328t/s | ✅ config 有 |
| `GEMINI_API_KEY` | AQ.Ab... | gemini | Gemini 2.5 Flash 免费 | ✅ config 有 |
| `GLM_API_KEY` | 22a17c2d... | glm | GLM-4 Flash 智谱免费 | ✅ config 有 |
| `ZAI_API_KEY` | 同GLM | zai | Z.AI GLM-4-Flash 备用 | ✅ config 有 |
| `NOUS_API_KEY` | sk-nous... | nous | Nous Portal Step 3.7 免费 | ✅ config 有 |
| `OPENROUTER_API_KEY` | sk-or... | openrouter | OR Qwen3 Coder/Nemotron/397B | ✅ config 有 |
| `NVIDIA_API_KEY` | nvapi-9Sxl... | openrouter | NV Qwen3.5 397B/Nemotron | ✅ config 有 |
| `OLLAMA_API_KEY` | dc1af... | ollama-cloud | Ollama Cloud Gemma4 31B | ✅ config 有 |
| `AGNES_API_KEY` | sk-94t... | custom:apihub.agnes-ai.com | Agnes 2.0 最终兜底 | ✅ config 有 |
| `CEREBRAS_API_KEY` | csk-5859... | openrouter | Cerebras Gemma4 via OR | ✅ config 有 |
| `DEEPSEEK_API_KEY` | sk-55e... | deepseek | DeepSeek v4（已从chain移除） | ⚠️ 有key但不在chain |
| `BOCHA_API_KEY` | sk-280... | bocha | 未加入fallback | 🔵 待定 |
| `EXA_API_KEY` | 767362d8... | exa | 搜索用，非模型 | — |
| `FIRECRAWL_API_KEY` | fc-2de... | firecrawl | 网页提取 | — |
| `SERPER_API_KEY` | cd64fc17... | serper | 搜索（2000次/月免费） | ✅ 已添加 2026-07-06 |
| `BAIDU_API_KEY` | qBU5Xn... | baidu | 未使用 | — |
| `AICODEE_API_KEY` | sk-290... | aicodee | 未加入fallback | 🔵 待定 |

## 新增 Provider 标准化流程

```
1. 测连通性：curl 测试 key 有效性
2. 写 .env：hermes config set XXX_API_KEY "key值"
3. 加 config.yaml fallback_providers[] entry（request_timeout_seconds: 15-20）
4. 同步 fallback_chain：hermes config set model.fallback_chain "...,newprovider/model,..."
5. 验证：grep fallback_chain ~/.hermes/config.yaml
6. 重启 gateway：bash /tmp/restart_gateway.sh
```

## 注意事项
- Groq 有两个 key：旧 key（gsk_uqn2...）已废弃，新 key（gsk_GHs6oR3z...）为当前有效 key
- GLM_API_KEY 和 ZAI_API_KEY 是同一个 key（智谱/国内版）
- OPENAI_API_KEY 当前指向 $CEREBRAS_API_KEY（疑似配置错误，需确认）
- DEEPSEEK_API_KEY 有 key 但 deepseek 已从 fallback_chain 移除（用户决定）

## Fallback Chain 顺序（2026-07-06，12条）

```
1.  custom:123.56.67.77:9100/MiniMax-M2.7-highspeed  (代理首选)
2.  groq/llama-3.3-70b-versatile                     (极速328t/s)
3.  gemini/gemini-2.5-flash                         (Google免费)
4.  glm/glm-4-flash                                 (智谱免费)
5.  ollama-cloud/gemma4:31b                         (Ollama云免费)
6.  nous/stepfun/step-3.7-flash:free                (Nous免费)
7.  openrouter/qwen/qwen3-coder:free                (OR免费)
8.  openrouter/google/gemma-4-31b-it                (OR免费)
9.  openrouter/nvidia/nemotron-3-super-120b-a12b   (OR付费)
10. openrouter/qwen/qwen3.5-397b-a17b              (OR付费)
11. zai/glm-4-flash                                 (Z.AI备用)
12. custom:apihub.agnes-ai.com/agnes-2.0-flash      (最终兜底)
```

## 速度参考（2026-07 benchmark）
- Groq Llama 3.3 70B: 328 t/s（最快）
- Gemini 2.5 Flash: 快
- MiniMax M2.7: 极快（有上下文缓存优势）
- OR 付费型号: 慢（限速）
