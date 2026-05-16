# Ollama Endpoint + Remote API Model = 404

## 典型错误

```
API call failed: HTTP 404 — model 'MiniMax-M2.7-highspeed' not found
Endpoint: http://localhost:11434/v1
```

**根因**：config 中 `base_url` 指向 Ollama 监听地址（`localhost:11434`），但 `model` 字段填的是需要远程 API 的模型（MiniMax、DeepSeek 等）。

Ollama 是**本地开源模型服务**，只认它自己 pull 过的模型（llama、qwen、mistral 等）。它不认识 `deepseek-v4-flash`、`MiniMax-M2.7-highspeed` 这类远程 API 模型名，所以返回 404。

## 快速诊断

```bash
grep -n "11434\|ollama" ~/.hermes/config.yaml
```

关注这两种模式（都是错的）：
```yaml
# 错法1：主 model 段指向 Ollama
model:
  provider: custom
  base_url: http://localhost:11434/v1   # ← Ollama
  model: MiniMax-M2.7-highspeed        # ← 远程模型，Ollama 不认

# 错法2：delegation 段指向 Ollama
delegation:
  provider: custom
  base_url: http://localhost:11434/v1  # ← Ollama
  model: deepseek-v4-flash             # ← 远程模型，Ollama 不认
```

## 正确配置（远程 API 模型）

远程模型（DeepSeek、MiniMax、OpenRouter 等）应指向对应 API 端点：

```yaml
# DeepSeek 正确配置
model:
  default: deepseek-v4-flash
  provider: deepseek
  base_url: https://api.deepseek.com/v1
  api_key: ''          # key 放 .env 的 DEEPSEEK_API_KEY

delegation:
  model: deepseek-v4-flash
  provider: deepseek
  base_url: https://api.deepseek.com/v1
  api_key: ''
```

## 如果想用本地 Ollama 模型

确保：
1. Ollama 服务在运行：`curl -s http://localhost:11434/api/tags` 有返回
2. 模型已 pull：`ollama pull qwen2.5:latest`
3. config 中的 model 名与 Ollama 模型名匹配（带 `:latest` tag）

```yaml
# Ollama 本地模型正确配置
model:
  default: qwen2.5:latest
  provider: ollama
  base_url: http://localhost:11434/v1
  api_key: ''

delegation:
  model: qwen2.5:latest
  provider: ollama
  base_url: http://localhost:11434/v1
  api_key: ''
```

## 修复后验证

```bash
# 确认没有残留 11434 指向远程模型
grep -n "11434" ~/.hermes/config.yaml

# 重启 gateway
hermes gateway restart

# 验证新模型可用
hermes chat -q "hi" --model deepseek-v4-flash
```

## 相关坑

- **v2.aicodee.com MiniMax Relay**：这个 endpoint 不稳定（实测 401），优先用原生 DeepSeek。
- **fallback_providers 里的 custom endpoint**：如果 custom provider 的 base_url 是 Ollama 地址，但 model 名是远程模型名，同样会 404。清理 fallback 里无效的 custom 端点。
