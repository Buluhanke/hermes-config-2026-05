# 2026-06-04 — `vision_understand.py` 实测复现 num_ctx 坑

## 复现
今天写了一个独立 vision 理解工具 `~/.hermes/skills/vision/scripts/vision_understand.py`，默认模型 `qwen3-vl:2b`，调 `/api/generate` 端点。

**没设 num_ctx** → 重蹈 `vision-understand-numctx-pitfall-2026-06-04.md`（2026-06-01 已发现）的覆辙。

实测：
| 跑次 | 实际耗时 | 应有耗时（设了 num_ctx=4096） |
|---|---|---|
| 1 | 30.2s | ~3-8s |
| 2 | 23.0s | ~3-8s |

默认 262144 num_ctx → Ollama 给 qwen3-vl:2b 分配 20GB KV cache → 慢 + 内存炸。

## 修复（patch vision_understand.py 必加）

`/api/generate` payload 必须显式 num_ctx：
```python
body = json.dumps({
    "model": model,
    "prompt": prompt,
    "images": [img_b64],
    "stream": False,
    "options": {"num_ctx": 4096},  # ← 必加，单图理解够用
}).encode()
```

**4096 是分界点参考**：
- 场景分类（单字输出）→ `num_ctx=1024`
- 屏幕内容理解（数句）→ `num_ctx=4096`
- 永远不要用默认 262144

## 关联资源
- 原 pitfall 文档（2026-06-01 发现）: `references/ollama-numctx-memory-optimization-2026-06-01.md`
- screen-watcher-vision 已修: `get_scene_type` 用 1024，`ask_screen` 用 4096
- 任何**新写的** ollama VLM caller 都必须显式 num_ctx

## 顺手发现 — moondream 行为
对比测试时发现：
- `moondream` 强制中文 prompt 仍输出英文（忽略指令）
- `moondream` 两张不同图返回**完全一样的描述**（疑似 ollama 缓存/模型层幻觉）
- 结论：纯英文场景可备选，中文场景别用

memory 已固化（合并到"视觉+主链+反过度工程"条目）。
