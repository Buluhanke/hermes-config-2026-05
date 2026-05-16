# Ollama 模型状态（2026-05-16 实测纠正）

## M4 24GB 模型可用性（纠正）

| 模型 | 大小 | 状态 | 备注 |
|------|------|------|------|
| **qwen2.5vl:7b** | 6GB | ✅ **可用（主力）** | 速度快，准确度高，6GB M4 24GB 实测通过 |
| ahmadwaqar/smolvlm2-agentic-gui | 2GB | ⚠️ 可用但弱 | 1.8B太小，复杂界面不够用 |
| qwen3-fast:latest | 5.2GB | ✅ 可用 | 文本模型，非视觉 |
| qwen3:8b | 5.2GB | ✅ 可用 | 文本模型，非视觉 |

## 推荐用法

```bash
# 主力视觉模型（qwen2.5vl，要加:7b后缀）
curl -X POST http://127.0.0.1:11434/api/generate -d '{
  "model": "qwen2.5vl:7b",
  "prompt": "描述这张图片",
  "images": ["/tmp/hermes_screen.png"],
  "stream": false
}'

# smolvlm2 备用（轻量但准确度一般）
curl -X POST http://127.0.0.1:11434/api/generate -d '{
  "model": "ahmadwaqar/smolvlm2-agentic-gui",
  "prompt": "描述这张图片",
  "images": ["/tmp/hermes_screen.png"],
  "stream": false
}'
```

**注意**：qwen2.5vl 模型名必须带 `:7b` 后缀，否则报 "model not found"。

## smolvlm2 响应特征（实测）

```
# 纯文本查询
"当前屏幕是什么内容？"
→ "The image shows a web page with various links..."

# 带坐标请求
"找'Safari图标'，返回坐标"
→ "未找到"
   或
→ "(173, 289)"  # 标准坐标格式

# 有时返回 <code> 标签包裹的action
→ "未找到"
<code>
scroll(direction='up', amount=10)
</code>
```

**解析规则**：
1. 优先找 `(数字, 数字)` 格式
2. 次找 `坐标：数字,数字` / `x=数字 y=数字`
3. 如果只有 `<code>` 标签里的内容，说明VLM没找到坐标，执行action再重试
4. "未找到" 不一定是失败，可能是元素真不在当前屏幕

## curl 测试命令

```bash
# 测试 smolvlm2 视觉
curl -X POST http://127.0.0.1:11434/api/generate -d '{
  "model": "ahmadwaqar/smolvlm2-agentic-gui:latest",
  "prompt": "描述这张图片",
  "images": ["/tmp/hermes_screen.png"],
  "stream": false
}' | jq .response

# 测试文本模型（qwen3-fast）
curl -X POST http://127.0.0.1:11434/api/generate -d '{
  "model": "qwen3-fast:latest",
  "prompt": "你好",
  "stream": false
}' | jq .response

# 查看已加载模型
curl -s http://127.0.0.1:11434/api/tags | jq '.models[].name'
```

## 内存问题

M4 24GB 运行 qwen2.5vl:7b 时：
- 首次加载需要 ~12s
- 高并发时 OOM
- smolvlm2 更稳定，优先使用