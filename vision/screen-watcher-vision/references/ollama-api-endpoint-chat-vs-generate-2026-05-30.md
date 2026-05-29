# Ollama API 端点对比：/api/generate vs /api/chat

**日期**：2026-05-30
**问题**：screen_trigger_handler 超时（120s 内 Read timed out）
**根因**：错误使用 `/api/generate` 端点

## 实测数据

| 端点 | 1920x1080 截图耗时 | 响应格式 |
|------|-------------------|----------|
| `/api/generate` | **41.6s** | `data['response']` |
| `/api/chat` | **31.7s**（快24%） | `data['message']['content']` |

## payload 格式差异

```python
# ❌ /api/generate（已废弃）
OLLAMA_URL = "http://localhost:11434/api/generate"
payload = {
    "model": MODEL,
    "prompt": prompt,
    "images": [img_b64],
    "stream": False,
    "options": {"num_gpu": 0, "temperature": 0.0}
}
resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
return resp.json().get('response', '').strip()

# ✅ /api/chat（当前使用）
OLLAMA_URL = "http://localhost:11434/api/chat"
payload = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": prompt, "images": [img_b64]}
    ],
    "stream": False,
    "options": {"temperature": 0.0}
}
resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
return resp.json().get('message', {}).get('content', '').strip()
```

## 验证方法

```bash
python3 /tmp/test_ollama_api.py
# 输出：
# /api/generate: status=200, time=41.6s
# /api/chat: status=200, time=31.7s
```

## 影响范围

- `screen_trigger_handler.py` 的 `ask_screen()` 和 `get_scene_type()` 两个函数
- 两函数原本都使用 `/api/generate`，现已统一改为 `/api/chat` + `messages` 格式
- 备份文件：`screen_trigger_handler.py.bak.20260530`

## 结论

Ollama 的 `/api/chat` 是较新且经过优化的端点，处理图像输入时性能显著优于 `/api/generate`。所有新的 Ollama Vision 集成都应使用 `/api/chat` + `messages` 格式。
