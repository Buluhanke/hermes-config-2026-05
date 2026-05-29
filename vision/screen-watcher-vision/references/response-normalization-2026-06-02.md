# Response 标准化增强（2026-06-02）

## 问题

`get_scene_type()` 使用 `qwen3-vl:2b` 做场景分类，但模型可能输出：
- 完整描述而非单词："This picture shows the home screen of a smartphone..."
- 带标点："desktop." → 无法匹配 `"desktop"` key in ACTION_WHITELIST
- 多行输出：第一行是场景，第二行是详细描述

## 修复

在 `~/.hermes/scripts/screen_trigger_handler.py` 的 `get_scene_type()` response 清理逻辑中加入：

```python
# 原有清理（line 168-172）
response = data.get('message', {}).get('content', '').strip()
response = response.split('</think>')[-1].strip()
response = response.split('<code>')[-1].strip()
response = response.rstrip('</code>').rstrip(')').strip()

# 新增标准化（line 173-174）
response = response.split('\n')[0].lower().strip().rstrip('.').rstrip(',')
```

## 效果

| 原始输出 | 标准化后 |
|---------|---------|
| `desktop.` | `desktop` |
| `This picture shows the home screen of a smartphone...` | `this picture shows the home screen of a smartphone...` |
| `browser,\nThe screenshot shows Chrome...` | `browser` |

## 验证

```bash
tail -5 ~/.hermes/logs/screen_trigger.log
# 应出现：场景类型: desktop（或其他英文单词，无标点）
# 以及：[AUTO-EXEC-DRY] Would execute: wininfo for scene=desktop
```

## 相关文件

- `references/scene-classification-model-fix-2026-06-02.md` — 模型切换 smolvlm2 → qwen3-vl:2b
- `references/smolvlm2-structured-json-2026-05-29.md` — smolvlm2 输出格式分析