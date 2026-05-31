# 2026-05-31 Fallback Chain 全量同步测试结果

## 测试时间
2026-05-31 16:15 CST（当前 session 使用 deepseek-v4-flash via DeepSeek）

## 当前主模型
- Provider: custom:v2.aicodee.com（config 配置）
- 实际：deepseek-v4-flash via DeepSeek（session 手动切换）

## 测试结果

| Provider | 模型 | 测试方式 | 结果 |
|----------|------|---------|------|
| DeepSeek 直连 | deepseek-v4-flash | 直调 API | ✅ 200 OK |
| MiniMax CN | MiniMax-M2.7 | 直调 API | ❌ 404（URL 指向 /anthropic 端点） |
| Api.groq.com（自定义） | llama-3.3-70b-versatile | 直调 API | ❌ 401 Invalid API Key（key 截断） |
| Api.cerebras.ai（自定义） | zai-glm-4.7 | 直调 API | ✅ 200（模型列表可查） |
| Api.cerebras.ai（自定义） | gpt-oss-120b | 模型列表 | ✅ Cerebras 平台可用 |
| V2.aicodee.com（自定义） | MiniMax-M2.7-highspeed | 直调 API | ❌ 401（key 截断） |

## Cerebras 可用模型
```
zai-glm-4.7
gpt-oss-120b
```

## 备用列表更新后（5条）
1. MiniMax-M2.7 → minimax-cn
2. deepseek-v4-flash → deepseek
3. llama-3.3-70b-versatile → custom:Api.groq.com
4. zai-glm-4.7 → custom:Api.cerebras.ai
5. MiniMax-M2.7-highspeed → custom:V2.aicodee.com

## 关键发现

### 自定义 Provider 在 Fallback 中的引用格式
```yaml
# 自定义 provider 用 custom:<ProviderName> 格式（大小写敏感）
- model: llama-3.3-70b-versatile
  provider: custom:Api.groq.com
```

### config.yaml 中的 Key 截断问题
config.yaml 中 custom_providers 的 api_key 字段存储的是截断值：
- V2.aicodee.com: `sk-290...6e18`（完整 key 在 .env 的 AICODEE_API_KEY）
- Api.groq.com: `gsk_vt...jo9o`（.env 中无 GROQ_API_KEY，只有 config 中有）
- Api.cerebras.ai: 完整 `csk-585933myftrtrrvj85kk8p6wnndcvrfn69jyxxmwvpv6r22h`

### MiniMax URL 问题
.env 中的 MINIMAX_CN_BASE_URL = `https://api.minimaxi.com/anthropic`
这是 Anthropic 兼容端点，测试返回 404。
标准端点应为 `https://api.minimaxi.com/v1/text/chatcompletion_v2`

## 环境信息
- config.yaml: `~/.hermes/config.yaml`（受保护文件，patch/write_file 不可写）
- .env: `~/.hermes/.env`（DEEPSEEK_API_KEY, AICODEE_API_KEY, MINIMAX_CN_API_KEY 等）
- 用户约束：「不能删除任何一个api和模型配置」+「key在config里也要同步，不能有残缺」
