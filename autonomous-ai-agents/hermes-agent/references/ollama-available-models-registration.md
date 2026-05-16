# Ollama 模型注册 — available_models 缺失

## 问题现象

Ollama 服务正常运行（`ollama list` 显示 qwen3-fast、qwen3:8b 等已安装），`providers.ollama` 段也在 config.yaml 里配置了，但 Hermes 里看不到这些模型，切不到。

## 根因

Hermes 的模型可用列表不是直接读取 `ollama list`，而是通过 `model.available_models` 配置注册的。没有注册就算 Ollama 跑着 100 个模型，Hermes 也当作它们不存在。

```yaml
# providers 段有，但模型不在 available_models → 不可见
providers:
  ollama:
    api_key_env_var: OLLAMA_API_KEY
    base_url: http://192.168.0.4:11434/v1
```

## 修复

在 `model:` 段添加 `available_models`：

```yaml
model:
  default: deepseek-v4-flash
  provider: deepseek
  context_length: 131072
  available_models:
    - name: qwen3-fast
      provider: ollama
      model: qwen3-fast:latest
    - name: qwen3-8b
      provider: ollama
      model: qwen3:8b
```

字段说明：
- `name` — Hermes 内部的模型标识符（用户切换时看到的名字）
- `provider` — 必须和 `providers:` 段里的键名一致
- `model` — Ollama 的实际模型名（`ollama list` 显示的 NAME 列）

## 验证

1. 重启 gateway：`hermes gateway restart`
2. 检查连通性：
   ```bash
   curl -s http://192.168.0.4:11434/v1/models \
     -H "Authorization: Bearer ollama"
   ```
3. 确认模型出现在 Hermes 的模型列表里

## 常见误区

- 只配了 `providers.ollama` 但没配 `available_models` ← **本题根因**
- `available_models` 里的 `provider` 值和 `providers:` 段键名不匹配
- `model` 字段用了 Ollama 模型 ID 但格式不对（如少了 `:latest` 后缀）
