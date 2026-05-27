# FreeLLMAPI — 本地LLM聚合代理

## 基础信息

- **项目**: tashfeenahmed/freellmapi (5378 stars, TypeScript)
- **代理端口**: `:3001` (OpenAI-compatible)
- **管理UI**: `:5173`
- **数据库**: `~/freellmapi/server/data/freeapi.db` (SQLite)
- **启动命令**: `cd ~/freellmapi && npm run dev`
- **进程管理**: background=true + notify_on_complete=true

## 支持的免费平台

| 平台 | 免费模型 | API Key环境变量 |
|------|---------|----------------|
| Groq | llama-3.3-70b, mistral-nemo | GROQ_API_KEY |
| Cerebras | llama-3.3-70b, mistral-nemo | CEREBRAS_API_KEY |
| SambaNova | llama-3.3-70b | SAMBANOVA_API_KEY |
| OpenRouter | 200+模型，部分免费 | OPENROUTER_API_KEY |
| Cloudflare | llama-3.1, mistral | CLOUDFLARE_API_KEY |
| HuggingFace | inference-api | HUGGINGFACE_API_KEY |
| Mistral | mistral-nemo | MISTRAL_API_KEY |
| GitHub | gpt-4o-mini | GITHUB_TOKEN |
| NVIDIA | llama-3.1-nemo | NVIDIA_API_KEY |
| Cohere | command-r-plus | COHERE_API_KEY |
| Z-AI | 免费额度 | ZAI_API_KEY |

## 添加API Key的方法

### 方法1: 管理UI (推荐)
1. 打开 `http://localhost:5173`
2. Navigation到 Keys 管理页面
3. 选择平台，填入API Key

### 方法2: API调用
```bash
curl -X POST "http://localhost:3001/api/keys" \
  -H "Content-Type: application/json" \
  -d '{"provider":"groq","api_key":"GRSK_REDACTED"}'
```

### 方法3: 直接写数据库
```bash
sqlite3 ~/freellmapi/server/data/freeapi.db \
  "INSERT INTO api_keys(provider, api_key) VALUES('groq','GRSK_REDACTED');"
```

## Hermes配置

FreeLLMAPI是OpenAI-compatible格式，Hermes配置示例：

```yaml
providers:
  free_llm:
    name: free-llm-api
    api_key: not-needed
    base_url: http://localhost:3001/v1
    models:
      default: auto
```

## 已知问题: LLM平台自动化注册

### 问题描述
通过浏览器自动化注册Groq/Cerebras等平台时，**邮件验证**环节无法绕过。

### 失败原因
1. **Groq**: 邮箱注册后发送验证链接 → 需在163/QQ邮箱点击 → Hermes无法登录用户邮箱
2. **GitHub OAuth**: 跳转到GitHub登录页 → 需要已有GitHub会话cookie → 无会话则需邮箱验证
3. **Google OAuth**: 同GitHub问题

### 可行的注册方式
- **SMS验证**: 部分平台支持手机号（+86）注册，Mac mini可接收短信（18006816283）
- **自助完成**: 用户去各平台官网注册（5分钟），把key给Hermes录入

### 推荐注册顺序（免费额度）
1. Groq (groq.com) — 注册最简单
2. Cerebras (cerebras.ai)
3. SambaNova (sambanova.ai)
4. Cloudflare (cloudflare.com/ai)

## 验证key是否有效
```bash
curl -s -X POST "http://localhost:3001/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```

## 架构特点

- **故障转移**: 主平台不可用时自动切换
- **30分钟粘性会话**: 同一会话期间固定使用一个平台
- **加密存储**: API keys用ENCRYPTION_KEY (AES-256-GCM) 加密
- **99模型**: 聚合14个平台的免费额度
