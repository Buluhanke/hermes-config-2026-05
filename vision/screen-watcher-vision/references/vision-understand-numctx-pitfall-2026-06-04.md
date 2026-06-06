# vision_understand.py + ollama VLM num_ctx 陷阱（2026-06-04 实测）

## 背景
vision_understand.py 是新增的纯 ollama VLM 语义理解工具，与 screen_trigger_handler.py 共享 ollama + qwen3-vl:2b。**同样的 VLM，截然不同的延迟** — 根源在 num_ctx。

## vision_understand.py

**位置**：`~/.hermes/skills/vision/scripts/vision_understand.py`

**用法**：
```bash
python3 ~/.hermes/skills/vision/scripts/vision_understand.py <image>           # 默认中文 prompt
python3 ~/.hermes/skills/vision/scripts/vision_understand.py <image> -p "..."   # 自定义问题
python3 ~/.hermes/skills/vision/scripts/vision_understand.py --screen           # 截全屏再理解
python3 ~/.hermes/skills/vision/scripts/vision_understand.py <image> -m moondream  # 换模型
python3 ~/.hermes/skills/vision/scripts/vision_understand.py <image> --bench   # +耗时
```

**功能**：自动 ensure_model（缺则 ollama pull）→ base64 编码图片 → POST /api/generate → 输出回答。

## ⚠️ ollama VLM 的 num_ctx 陷阱（必须复用的关键发现）

**screen_trigger_handler** 修过的 bug（2026-06-01 修复，见 SKILL.md 主文档）：

| 调用 | 设了 num_ctx | 延迟 | 内存 |
|------|-------------|------|------|
| screen_trigger_handler.get_scene_type() | 1024 | ~3s | 2.7GB |
| screen_trigger_handler.ask_screen() | 4096 | ~5s | 2.7GB |
| **vision_understand.py（无 num_ctx）** | **未设（默认 262144）** | **23-30s** | **20GB+** |

**实测对比**（同一张 1.3MB 终端截图，模型 qwen3-vl:2b）：

| 工具 | 耗时 | num_ctx |
|------|------|---------|
| vision_understand.py | 23-30s | 默认 262144 |
| screen_trigger_handler.ask_screen | ~5s | 4096 |
| screen_trigger_handler.get_scene_type | ~3s | 1024 |

**根因**：Ollama 默认 num_ctx = 262144（模型全量上下文大小）。Qwen3-VL 这种长上下文 VLM 在 full ctx 下 KV cache 巨大，推理慢且吃 20GB 内存。

## 修复（vision_understand.py 待办）

**问题代码**（vision_understand.py 的 chat_with_image()）：
```python
body = json.dumps({
    "model": model,
    "prompt": prompt,
    "images": [img_b64],
    "stream": False,
    # ❌ 缺 "options": {"num_ctx": 1024}
}).encode()
```

**应改为**：
```python
body = json.dumps({
    "model": model,
    "prompt": prompt,
    "images": [img_b64],
    "stream": False,
    "options": {
        "temperature": 0.0,
        "num_ctx": 1024,   # ← 关键：单图理解 1024 足够
    }
}).encode()
```

**预期收益**：30s → 3s，内存从 20GB 降到 2.7GB。

**为何 vision_understand.py 没修**：本次任务是验证 Vision OCR 桥和 moondream 对比，num_ctx 修复是顺带发现但本 session 没动。下次 touch vision_understand.py 时**第一件事**就是加 num_ctx。

## 复用规则（所有 ollama VLM caller）

任何调 ollama VLM 的 Python 代码必须**显式设 num_ctx**：
- 单图理解 / 短回答：**num_ctx=1024**
- 多图 / 长 prompt 场景分类：**num_ctx=4096**（screen_trigger_handler 实战值）
- 永远不要用默认 262144

**验证命令**：
```bash
ollama ps   # 看加载模型的 CONTEXT SIZE 列
# 如果显示 CONTEXT SIZE 是 262144 而代码期望 4096 → num_ctx 没生效
```

## moondream 实测结论

详见同目录下 `moondream-cascade-2026-06-07.md`。**核心：moondream 在中文 screen-watcher 场景不可用**（忽略中文 prompt、可能缓存/幻觉、不区分相似图）。
