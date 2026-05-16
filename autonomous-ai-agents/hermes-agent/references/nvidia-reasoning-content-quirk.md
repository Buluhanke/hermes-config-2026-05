# NVIDIA API 返回格式特殊处理

## 问题现象

调用 `https://integrate.api.nvidia.com/v1/chat/completions` 使用 `nvidia/llama-3.3-nemotron-super-49b-v1.5` 时：

- HTTP 200 正常
- 响应中 `choices[0].message.content` 为 `null`
- 实际回复内容在 `choices[0].message.reasoning_content` 字段

```json
{
  "choices": [{
    "message": {
      "content": null,
      "reasoning": "模型思考过程...",
      "reasoning_content": "这里是实际的回复文本"
    }
  }]
}
```

## 判断是否需要此处理

不是所有 NVIDIA 模型都这样——只有 **reasoning 模型**（带思考链的模型）会把回复放到 `reasoning_content`：
- `nvidia/llama-3.3-nemotron-super-49b-v1.5` ✅ 需要
- 其他非 reasoning 模型（标准 llama 等）❌ 不需要，正常取 `content`

## 在 Hermes 中的影响

Hermes Agent 目前**未对此做特殊处理**，意味着使用 NVIDIA nemotron 模型时：
- 直接对话可能正常（模型可能自己填了 `content`）
- 但 tool calling / structured output 可能失败（因为 `content` 为 `null`）

如果用 NVIDIA 配合 Hermes，建议用非 reasoning 模型如 `meta/llama-3.1-8b-instruct`。

## 验证命令

```python
import requests
r = requests.post(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
    json={"model": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
          "messages":[{"role":"user","content":"1+1等于几？"}], "max_tokens": 20},
    timeout=20
)
data = r.json()
content = data["choices"][0]["message"].get("content") or data["choices"][0]["message"].get("reasoning_content")
print(content)
```
