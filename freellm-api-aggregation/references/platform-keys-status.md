# 各平台API Key状态（2026-05-26实测）

## 已配置的Key
| 平台 | Key格式 | 状态 |
|------|---------|------|
| OpenRouter | YOUR_API_KEY-v1-17... | 待测 |
| Groq | GRSK_REDACTED...832C | ❌ Forbidden |
| Cerebras | cYOUR_API_KEY...cyme | 待测 |
| Nvidia NIM | NVIDAPI_REDACTED...ylA- | 待测 |
| Google (3个) | GOOGLE_AI_KEY_REDACTED... | 待测 |
| GitHub | ghp_lx...APKi | 待测 |
| ZenmuX | YOUR_API_KEY-v1-f1... | ⚠️ 平台不在支持列表 |

## 支持的model格式
```
groq/llama-3.3-70b-versatile
cerebras/qwen-3-235b-a22b-instruct-2507
openrouter/qwen/qwen3-coder:free
nvidia/meta/llama-3.1-70b-instruct
google/gemini-2.5-flash
```

## 各平台注册限制
- **Groq**: 邮件验证（必须点链接）→ Hermes无法独立完成
- **Cerebras**: 需测试
- **SambaNova**: 需测试
- **Nvidia**: 需测试
- **OpenRouter**: 支持邮箱注册
- **Cloudflare**: Workers AI免费额度，需测试
