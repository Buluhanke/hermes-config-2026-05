# Ollama API Endpoint Distinction (2026-05-30)

## 关键发现

Ollama 有两个 API 端点，返回完全不同类型的数据：

| 端点 | 返回 | 用途 |
|------|------|------|
| `https://api.ollama.com/api/tags` | 远程库模型列表 | 判断可以 pull 什么模型 |
| `http://127.0.0.1:11434/api/tags` | **本地已安装**模型 | 检查本地是否已安装 |

两者完全不同的数据！用远程库判断本地是否安装会导致误判。

## 实测数据

**远程库 (`api.ollama.com`) 返回** — 大量超大模型：
```
qwen3.5:397b, qwen3-vl:235b-instruct, gemma4:31b, devstral-small-2:24b, ...
(这些是 ollama.com/library 上可以 pull 的模型，不等于本地已安装)
```

**本地 Ollama (`127.0.0.1:11434`) 返回** — 实际安装的 4 个模型：
```
ahmadwaqar/smolvlm2-agentic-gui:latest  ✅ GUI 专用视觉模型（1.85GB）
qwen3-vl:2b                            ✅ 通用视觉（1.9GB）
qwen2.5:1.5b                           ✅ 小型文本模型
nomic-embed-text:latest                ✅ 嵌入模型
```

## 教训

之前误以为"ollama API 返回的模型列表就是本地安装的"，导致：
1. 以为 smolvlm2/qwen3-vl:2b 被删除了（远程库没有它们）
2. 以为 screen_trigger_handler 用了不存在的模型
3. 实际上它们一直在本地正常运行

## 正确检查方法

```python
# ✅ 正确：检查本地已安装模型
import urllib.request
import json

url = "http://127.0.0.1:11434/api/tags"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read())
    for m in data.get('models', []):
        print(m['name'])

# ❌ 错误：检查远程库（不等于本地安装）
import urllib.request
url = "https://api.ollama.com/api/tags"
# 这个返回的是 ollama.com/library 上所有的模型，不是本地已安装
```

## screen_trigger_handler 模型确认

```bash
grep "MODEL" /Users/aimac/.hermes/scripts/screen_trigger_handler.py
# MODEL = "ahmadwaqar/smolvlm2-agentic-gui:latest"
# screen_trigger_handler.py 用的是 smolvlm2，确认在本地 127.0.0.1:11434 中存在 ✅
```