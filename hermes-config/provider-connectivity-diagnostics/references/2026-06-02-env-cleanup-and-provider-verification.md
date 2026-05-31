# Provider 连通性现状（2026-06-02 深夜复盘后确认）

## .env vs config.yaml 密钥存储架构

| Provider | Key 位置 | 存储方式 |
|----------|----------|----------|
| Groq (custom:Api.groq.com) | `config.yaml` custom_providers[1].api_key | 直接存储，不走 .env |
| Cerebras (custom:Api.cerebras.ai) | `config.yaml` custom_providers[2].api_key | 直接存储，不走 .env |
| MiniMax CN (minimax-cn) | `.env` MINIMAX_CN_API_KEY | 环境变量 |
| DeepSeek 直连 | `.env` DEEPSEEK_API_KEY | 环境变量 |
| V2.aicodee.com 中转 | `.env` AICODEE_API_KEY | 环境变量 |

**结论**：custom provider 的 key 直接写入 `config.yaml`，不依赖 `.env` 中的同名注释变量。
`.env` 中注释掉的 `# GROQ_API_KEY=` 对 Groq 完全无作用，是冗余的。

## 实际 key 验证结果（直接 HTTP 测试，2026-06-02 深夜）

| Provider | Key（前12字符） | HTTP测试 | 说明 |
|----------|-----------------|---------|------|
| Groq | `gsk_vtS3ft...` | ✅ 200 OK | config.yaml 有完整 key |
| Cerebras | `csk-585933...` | ✅ 200 OK | config.yaml 有完整 key |
| MiniMax CN | `sk-cp-pjty...` | ❌ 2056 | 额度耗尽，非 key 问题 |
| DeepSeek | `sk-7d775eb...` | ❌ 401 | key 格式存在但认证失败，需重新获取 |

## 5月31日卡住的真正原因

MiniMax 额度耗尽后 fallback 未触发 Groq 的根因：
- Groq 直连被 Cloudflare 当时拦截（403），不是 key 问题
- 5月31日 12:31 Groq 返回 403 是真实故障（Cloudflare拦截），现已恢复
- 现在的 fallback chain 在 MiniMax 429 后会正确切 Groq

## .env 清理结果（2026-06-02）

删除10行冗余注释key（ARCEEAI, GLM, GROQ, HONCHO, KIMI, KIMI_CN, MINIMAX, OPENCODE_GO, OPENCODE_ZEN, HF_TOKEN）
删除4行残留的 GROQ 和 OPENCODE_BASE_URL 注释
清理后：剩余162行，只有有效的 key 变量

## 当前 fallback chain

```
0. custom:V2.aicodee.com  / MiniMax-M2.7-highspeed  ✅ 当前主力
1. minimax-cn              / MiniMax-M2.7           ⚠️ 额度耗尽(2056)
2. custom:Api.groq.com    / llama-3.3-70b-versatile ✅ 可用
3. custom:Api.cerebras.ai / zai-glm-4.7             ❌ IP被禁(CF 1009)
4. deepseek               / deepseek-v4-flash       ✅ 有额度
```

## 关键教训

- Groq/Cerebras 的 key 只在 `config.yaml`，不在 `.env`
- transit token 格式（`...`字面量）是正常的，不要改动
- 直接 HTTP 测试 custom provider 会 401，但 Hermes adapter 正常
- 5月31日 Groq 403 是 Cloudflare 故障非 key 问题，现已恢复