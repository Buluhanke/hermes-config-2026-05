# Ollama Vision 模型测试方法论

在 cron 环境/后台自动化环境下测试 Ollama 视觉语言模型（VLM）的经验总结。

## 核心原则

### 1. 使用直接 API 调用，避免 ollama Python SDK

`ollama.chat()` 和 `ollama.generate()` Python API 在 cron 环境有已知问题：
- 长时间等待模型加载时，HTTP 连接超时（`context canceled` 错误）
- stream=True 会提前关闭链接
- 超时无法单独控制（继承 urllib 默认 30s?）

**✅ 正确做法**：直接用 `urllib.request` 或 `curl` 调用 REST API
**✅ 正确做法**：直接用 `urllib.request` 或 `curl` 调用 REST API，**必须用 `/api/chat`**（不能用 `/api/generate`，性能差24%且易超时）

```python
import urllib.request, base64, json

with open('/tmp/image.jpg', 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()
payload = {
    "model": "qwen3-vl:2b",
    "messages": [{"role": "user", "content": "Describe this image", "images": [img_b64]}],
    "keep_alive": -1,    # 保持模型在内存
    "options": {"temperature": 0.1},
    "stream": False       # 非流式，获取单次响应
}

req = urllib.request.Request(
    "http://localhost:11434/api/chat",  # ⚠️ 必须用 /api/chat
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"}
)

# 必须用长超时（模型首次加载可能 > 60s）
with urllib.request.urlopen(req, timeout=600) as resp:
    data = json.loads(resp.read())
    print(data['message']['content'])
```

### 2. 图像大小限制

不同 VLM 对输入图像的分辨率容忍度不同：

| 模型 | 最大安全分辨率 | 实测结果 |
|------|--------------|---------|
| smolvlm2-agentic-gui | 2048px ✅ | 全分辨率正常 |
| qwen3-vl:2b | 500px ✅ / 1024px ❌ | 500px 19.3s, 1024px 超时 |
| gemma4:e2b | 未测试 | — |

**建议**：测试新 VLM 时，从 500px JPEG（~40KB）开始，逐步加大。

### 3. 模型预热策略

首次加载可能有 5-15s 加载耗时（取决于模型大小）：

```bash
# 预加载：发一个简单的文本请求，keep_alive=-1
curl -s --max-time 120 -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3-vl:2b", "messages": [{"role":"user","content":"Hello"}], "keep_alive": -1}'
# 然后发视觉请求（通常快 5-10s）
```
```

验证模型是否在内存：
```bash
curl -s http://localhost:11434/api/ps
```

### 4. Pull 模型时的超时处理

大模型下载在 cron 环境可能超时（300s 不够）：
- 检查 `~/.ollama/models/blobs/` 下是否有对应大小的 blob 文件
- 检查 `~/.ollama/models/manifests/registry.ollama.ai/<namespace>/<model>/<tag>` 是否有 manifest
- 如果 manifest + blobs 都存在，直接调用即可（下载已完成但 Python pull() 超时了）

```bash
# 检查是否已下载完成
ls -lt ~/.ollama/models/blobs/ | head -5
ls ~/.ollama/models/manifests/registry.ollama.ai/library/qwen3-vl/
cat ~/.ollama/models/manifests/registry.ollama.ai/library/qwen3-vl/2b
```

### 5. Ollama 日志检查

```bash
cat ~/.ollama/logs/server.log | grep -E "error|warn|fail|timeout|cancel" | tail -20
```

常见错误模式：
- `client connection closed before server finished loading, aborting load` → 客户端超时，增大 timeout
- `context canceled` → 同上
- `requested context size too large for model` → `num_ctx` 超过模型最大上下文

## 实测数据（M4 24GB）

见 `references/smolvlm2-agentic-gui-variants.md`。
