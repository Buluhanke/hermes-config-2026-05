---
name: freellm-api-aggregation
description: FreeLLMAPI本地代理聚合多平台免费LLM额度
triggers:
  - 聚合免费LLM API
  - FreeLLMAPI配置
  - 多平台API key管理
  - 注册免费AI平台
---

# FreeLLMAPI 聚合平台技能

## 核心知识

### 关键路径
- 服务端口: :3001 (代理)  :5173 (管理UI)
- 数据库: ~/freellmapi/server/data/freeapi.db
- 日志: ~/.hermes/logs/freellmapi.log

### API Keys 管理

**正确端点**: `POST http://localhost:3001/api/keys`

**正确Payload**:
```json
{
  "platform": "groq",
  "key": "GRSK_REDACTED",
  "label": "groq"
}
```

**支持的platform**（从源码确认）:
```
google, groq, cerebras, sambanova, nvidia, mistral,
openrouter, github, cohere, cloudflare, zhipu, ollama,
kilo, pollinations, llm7, huggingface
```

### 验证key是否生效
```bash
# 检查数据库中的key
sqlite3 ~/freellmapi/server/data/freeapi.db "SELECT platform, label, enabled FROM api_keys;"

# 测试调用
curl -X POST http://localhost:3001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"groq/llama-3.3-70b-versatile","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'

# 查看日志
tail -20 ~/.hermes/logs/freellmapi.log
```

### 常见问题

**"Invalid API key" 但key存在**
- key格式正确但平台拒绝（被封/未激活/地区限制）
- 直接用curl测试平台是否接受该key
- Groq对中国IP可能返回Forbidden

**两套 Key 体系导致认证失败（2026-05-27）**
freellmapi 有两套独立的 key 机制，理解错会导致长时间调试：

| Key | 位置 | 用途 |
|-----|------|------|
| `FREELLMAPI_KEY` | `~/.hermes/.env` | gateway 等客户端调用 freellmapi 的 Bearer token |
| `unified_api_key` | `freeapi.db settings 表` | freellmapi 内部用于调用上游真实 API provider |

- 客户端请求时 header: `Authorization: Bearer {FREELLMAPI_KEY}`
- freellmapi 内部代理到上游（aicodee/groq等）时，用的是 DB 里的 unified key
- 两套 key 值不同（DB 存 `freellmapi-138b...`，`.env` 存 `local-proxy-no-key-needed`），但彼此独立工作
- **如果 freellmapi 返回 "Invalid API key"**：检查的是 DB 里的 unified key，不是 `.env` 里的 `FREELLMAPI_KEY`
- 验证命令：
  ```bash
  # 查 DB unified key
  sqlite3 ~/freellmapi/server/data/freeapi.db "SELECT value FROM settings WHERE key='unified_api_key';"
  # 查 .env FREELLMAPI_KEY
  grep FREELLMAPI_KEY ~/.hermes/.env
  ```

**Health checker显示"0 keys"**
- 服务未正确加载数据库
- kill所有旧进程 → 重新npm run dev

### 进程管理
- 用 `background=true` 启动
- 多workspace用concurrently（server + client）
- 旧进程残留 → 先kill再启动

### 2026-05-27 重要更新：入口路径变更
项目结构已变更，旧入口 `src/index.ts` 失效。

**当前有效入口**: `server/src/index.ts`

启动命令:
```bash
cd /Users/aimac/freellmapi && npx tsx server/src/index.ts
```

**进程卡死诊断流程**:
1. `lsof -i :3001` — 无端口监听但进程存在 → 进程已崩溃
2. kill旧进程 → 检查入口路径是否正确
3. 用 `tsx server/src/index.ts` 启动（不是 `tsx src/index.ts`）

**健康检查端点行为**: `/health` 返回前端HTML而非JSON，说明路由配置有变，但不影响核心 `/v1/chat/completions`

### v2.aicodee.com 诊断
- 连接错误 ≠ Token错误：网络不通时返回连接失败，Token无效时返回 `{"type":"new_api_error","message":"无效的令牌"}`
- 区分瞬时网络抖动 vs Token过期：前者重试可恢复，后者需更换Key

### 平台注册能力
| 平台 | Hermes能否独立注册 | 备注 |
|------|-------------------|------|
| Groq | ❌ | 邮件验证必点链接 |
| Cerebras | 待测 | 可能是邮箱验证 |
| SambaNova | 待测 | — |
| Nvidia | 待测 | — |
| OpenRouter | 可能❌ | 邮箱验证 |
| Cloudflare | 待测 | Workers AI |

## 参考资料
- `references/platform-keys-status.md` — 各平台key状态和可用模型
