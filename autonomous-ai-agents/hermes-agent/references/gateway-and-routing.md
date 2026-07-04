# Hermes 网关配置与智能路由参考

本文档记录网关配置、端口设置和智能路由模型轮询的权威信息。

## 网关端口

**默认监听端口：8642**

网关启动后监听 `127.0.0.1:8642`，这是唯一的 API 端口。

### 验证网关状态

```bash
# 健康检查（无需认证）
curl http://127.0.0.1:8642/health

# 预期响应
{"status": "ok", "platform": "hermes-agent", "version": "0.17.0"}
```

### API 端点

所有 API 调用需要认证，使用配置中的 API key：

```bash
curl http://127.0.0.1:8642/v1/models \
  -H "Authorization: Bearer <YOUR_API_KEY>"

curl http://127.0.0.1:8642/v1/chat/completions \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"model":"<model_name>","messages":[...],"max_tokens":5}'
```

### 配置位置

- 主配置：`~/.hermes/config.yaml`
- 凭据：`~/.hermes/.env`
- 日志：`~/.hermes/logs/gateway.log`

## 智能路由模型配置

智能路由通过 `fallback_chain` 配置，按顺序尝试多个模型，实现故障转移和负载均衡。

### 配置示例 (config.yaml)

```yaml
model:
  default: qwen/qwen3.5-397b-a17b
  provider: custom:nv-qwen3.5-397b
  fallback_chain: >-
    qwen/qwen3.5-397b-a17b,
    nvidia/nemotron-3-super-120b-a12b,
    qwen/qwen3-coder:free,
    gemini-2.5-flash,
    gpt-oss-120b,
    deepseek-chat,
    glm-4-flash,
    openrouter/free,
    agnes-2.0-flash
```

### Custom Providers 配置

```yaml
custom_providers:
  - name: nv-qwen3.5-397b
    base_url: https://integrate.api.nvidia.com/v1
    model: qwen/qwen3.5-397b-a17b
    api_key: ${NVIDIA_API_KEY}
  
  - name: nv-nemotron-120b
    base_url: https://integrate.api.nvidia.com/v1
    model: nvidia/nemotron-3-super-120b-a12b
    api_key: ${NVIDIA_API_KEY}
  
  - name: or-qwen3-coder
    base_url: https://openrouter.ai/api/v1
    model: qwen/qwen3-coder:free
    api_key: ${OPENROUTER_API_KEY}
```

### 2026-06-28 实测模型连通性

所有 9 个模型均验证可用，按响应速度排序：

| 排名 | 模型 | Provider | 响应时间 | 特点 |
|------|------|----------|----------|------|
| 1 | gpt-oss-120b | Cerebras | 2.7s | 极速免费 ⭐ |
| 2 | qwen/qwen3-coder:free | OpenRouter | 2.8s | 免费 |
| 3 | gemini-2.5-flash | Google | 2.8s | 免费额度 |
| 4 | deepseek-chat | DeepSeek | 2.9s | 强推理 |
| 5 | glm-4-flash | 智谱 | 2.9s | 免费 |
| 6 | openrouter/free | OpenRouter | 2.9s | 自动路由 |
| 7 | agnes-2.0-flash | Agnes AI | 2.9s | 最终兜底 |
| 8 | nvidia/nemotron-3-super-120b-a12b | NVIDIA | 3.0s | 大模型 |
| 9 | qwen/qwen3.5-397b-a17b | NVIDIA | 3.2s | 主力，大上下文 |

### API Key 需求

| Provider | 环境变量 | 获取方式 |
|----------|----------|----------|
| NVIDIA | `NVIDIA_API_KEY` | build.nvidia.com |
| OpenRouter | `OPENROUTER_API_KEY` | openrouter.ai |
| Google Gemini | `GEMINI_API_KEY` | makersuite.google.com |
| DeepSeek | `DEEPSEEK_API_KEY` | platform.deepseek.com |
| 智谱 GLM | `GLM_API_KEY` | open.bigmodel.cn |
| Cerebras | `CEREBRAS_API_KEY` | cloud.cerebras.ai |
| Agnes AI | `OPENROUTER_API_KEY` | apihub.agnes-ai.com |

## 常见故障排查

### 端口占用问题

```bash
# 检查 8642 端口监听状态
lsof -i :8642

# 预期输出
python3.1  891 aimac   39u  IPv4  0x...  0t0  TCP 127.0.0.1:8642 (LISTEN)
```

### 网关无法启动

查看日志：
```bash
tail -50 ~/.hermes/logs/gateway.log
tail -50 ~/.hermes/logs/gateway.error.log
```

常见原因：
1. 端口被占用 → `kill -9 <PID>`
2. API key 缺失 → `hermes setup`
3. 配置文件错误 → `hermes config check`

### 模型调用失败

```bash
# 测试单个模型
hermes ask --model '<model_name>' '1+1=?'

# 检查配置
hermes config show | grep -A3 "Model:"
```

### 认证错误 (HTTP 401)

确认 `.env` 中有对应的 API key：
```bash
cat ~/.hermes/.env | grep <PROVIDER>_API_KEY
```

## 性能优化建议

1. **首选快速模型**：`gpt-oss-120b`（Cerebras）实测最快（2.7s）
2. **推理任务**：`deepseek-chat`（2.9s，强推理能力）
3. **大上下文**：`qwen/qwen3.5-397b-a17b`（3.2s，397B 参数）
4. **成本控制**：全部使用免费额度内的模型组合

## 切换智能路由配置

```bash
# 查看当前配置
hermes config show | grep -A5 "fallback_chain"

# 编辑配置
hermes config edit

# 修改后重启网关
hermes gateway restart
```

## 相关文档

- 官方配置文档：https://hermes-agent.nousresearch.com/docs/user-guide/configuration
- Provider 配置：https://hermes-agent.nousresearch.com/docs/integrations/providers
- 网关文档：https://hermes-agent.nousresearch.com/docs/user-guide/gateway/