# Ollama API Endpoint Distinction (2026-05-30, updated 2026-06-02)

## 关键发现

Ollama 有两个 API 端点，返回完全不同类型的数据：

| 端点 | 返回 | 用途 |
|------|------|------|
| `https://api.ollama.com/api/tags` | 仅 39 个超大官方模型（无社区模型） | 查官方大模型用 CLI `ollama search` 代替 |
| `http://127.0.0.1:11434/api/tags` | **本地已安装**模型 | 检查本地是否已安装 |

⚠️ 之前误以为 api.ollama.com 返回"所有可 pull 模型"，实际它只返回官方大模型列表，社区模型（smolvlm2-agentic-gui、qwen3-vl:2b 等）不在其中。

## 实测数据（2026-06-02）

**远程库 (`api.ollama.com`) 返回** — 仅 39 个超大官方模型：
```
qwen3.5:397b, qwen3-vl:235b-instruct(437GB), gemma4:31b(58GB),
devstral-small-2:24b(48GB), ...（无任何社区小模型）
```

**本地 Ollama (`127.0.0.1:11434`) 返回** — 实际安装的 2 个模型：
```
qwen2.5:1.5b  | 0.92 GB
qwen3-vl:2b   | 1.76 GB
（smolvlm2-agentic-gui 已从本地消失，可能被 Ollama 自动清理）
```

## 教训

1. 以为 smolvlm2/qwen3-vl:2b 被删除了 → 实际上它们不在远程 API 列表中（远程 API 只返回官方大模型）
2. 以为 screen_trigger_handler 用了不存在的模型 → 需确认本地 127.0.0.1:11434 是否真正有
3. smolvlm2-agentic-gui 从本地消失两次（2026-05-30 和 2026-06-02），可能是 Ollama 自动清理机制

## 正确检查方法

```python
# ✅ 正确：检查本地已安装模型（curl 方式，避免 Python API 超时）
import urllib.request, json
url = "http://127.0.0.1:11434/api/tags"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read())
    for m in data.get('models', []):
        print(m['name'], '|', round(m['size']/(1024**3), 2), 'GB')

# ❌ 错误：检查远程库（不等于本地安装，社区模型不在此列表）
import urllib.request
url = "https://api.ollama.com/api/tags"  # 只返回官方大模型
```

## 搜索社区模型的正确方法

```bash
# ✅ 用 ollama search CLI（搜索社区模型）
ollama search smolvlm2-agentic-gui

# ❌ 不要用 api.ollama.com（无社区模型）
```

## screen_trigger_handler 模型确认

```bash
# 检查 screen_trigger_handler 用的模型
grep "MODEL" /Users/aimac/.hermes/scripts/screen_trigger_handler.py
# 当前：ahmadwaqar/smolvlm2-agentic-gui:latest

# 确认模型是否在本地
curl -s --max-time 8 http://127.0.0.1:11434/api/tags | grep smolvlm2
# 如果无输出，说明模型已从本地消失，需重新 pull
```