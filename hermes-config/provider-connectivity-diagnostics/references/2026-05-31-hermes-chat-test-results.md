# 2026-05-31 — 全量备用链连通性测试

## 测试方法

使用 `hermes chat -q "ping" -m "<model>" --provider "<provider>"` 逐个调用。
直接 HTTP 测试不适用于 transit token 格式的 provider。

## 测试结果

| 顺序 | 模型 | Provider | 结果 | 耗时 |
|------|------|----------|------|------|
| 1 | MiniMax-M2.7-highspeed | custom:V2.aicodee.com | ✅ pong | 9s |
| 2 | MiniMax-M2.7 | minimax-cn | ✅ pong | 6s |
| 3 | llama-3.3-70b-versatile | custom:Api.groq.com | ✅ pong | 10s |
| 4 | zai-glm-4.7 | custom:Api.cerebras.ai | ✅ pong | 11s |
| 5 | deepseek-v4-flash | deepseek | ✅ (此前已验证) | — |

## 结论

全部 5 条备用链通过 Hermes 测试。所有 transit token 格式的 key（含 `...`）正常。

## 背景信息

- 当前会话模型：deepseek-v4-flash via deepseek
- 主模型配置：MiniMax-M2.7-highspeed via custom:V2.aicodee.com
- 用户明确指示：不删除任何 API 或模型配置，所有 provider 必须加入备用列表
- 备用链顺序按用户要求排列
