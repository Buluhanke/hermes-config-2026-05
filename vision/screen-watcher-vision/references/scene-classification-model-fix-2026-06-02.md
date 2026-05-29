# 场景分类模型实测（2026-05-30 更新）

## 结论（已验证，正确）

`get_scene_type()` 使用 `smolvlm2-agentic-gui` ✅

| 测试项 | qwen3-vl:2b | smolvlm2-agentic-gui |
|--------|-------------|---------------------|
| 900x506 缩略图响应时间 | 60s+ 超时 | **17.9s** ✅ |
| scene classification 输出 | 未测（超时） | "browser" ✅ |
| 结论 | 不适合实时场景分类 | 适合 |

## 实测命令

```bash
python3 /tmp/test_scenetype.py
# 输出：Scene type: 'browser', Time: 17.9s
```

## 测试脚本

```python
# /tmp/test_scenetype.py
import sys
sys.path.insert(0, '/Users/aimac/.hermes/scripts')
from screen_trigger_handler import get_scene_type
import time
start = time.time()
result = get_scene_type('/tmp/test_idle_screen.png')
elapsed = time.time() - start
print(f"Scene type: '{result}', Time: {elapsed:.1f}s")
```

## 已执行的修复（2026-05-30）

`~/.hermes/scripts/screen_trigger_handler.py` 的 `get_scene_type()`：
- 模型：`qwen3-vl:2b` → `ahmadwaqar/smolvlm2-agentic-gui:latest`
- timeout：`120s` → `30s`
- temperature：`0.0` → `0.1`
- prompt：直接内联，不再用独立变量

备份：`~/.hermes/scripts/screen_trigger_handler.py.bak.20260530_0616`

## 历史（仅供追踪）

- 2026-06-02：曾切换到 qwen3-vl:2b（误判为正确）
- 2026-05-30 实测推翻：smolvlm2 17.9s 成功，qwen3-vl:2b 60s+ 超时