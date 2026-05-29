# Idle Learning 2026-06-02 Session — Response Normalization Fix

## Session Summary

**Time**: 2026-06-02 06:00
**Learning direction**: C — 理解（执行层链路诊断）
**Duration**: Single idle_learning cycle

## Key Findings

### 1. Network Status
- github.com: **blocked**
- news.ycombinator.com: **blocked**
- HN Firebase API: ✅ **working**
- ddgs CLI: ✅ **working** (but returns empty at 20s timeout, good for quick keyword search only)

### 2. screen_watcher链路状态（实测）
- screen_watcher.py: **运行中** (PID 61102, started before 06:00)
- screen_trigger_handler.py: **运行中** (PID 4817, started 05:59AM)
- dry-run日志: ✅ **正常**（之前修复的 unknown 白名单已生效）
- 日志示例: `[AUTO-EXEC-DRY] Would execute: wininfo for scene=unknown`

### 3. 场景分类持续返回 "unknown" 根因
`get_scene_type()` 已切换到 qwen3-vl:2b，但仍持续返回 "unknown"：

**根因**：qwen3-vl:2b 在 scene classification 任务中输出非单词响应：
- 输出完整描述："This picture shows the home screen of a smartphone..."
- 输出带标点："desktop." → 无法匹配 `"desktop"` key in ACTION_WHITELIST
- 多行输出：第一行是场景，第二行是详细描述

### 4. Response 标准化修复（已实施）
**文件**: `~/.hermes/scripts/screen_trigger_handler.py`
**位置**: line 173-174（在 response 清理逻辑后新增）

```python
# 标准化：只取第一行、小写化、trim掉标点
response = response.split('\n')[0].lower().strip().rstrip('.').rstrip(',')
```

**效果**:
| 原始输出 | 标准化后 |
|---------|---------|
| `desktop.` | `desktop` |
| `This picture shows the home screen...` | `this picture shows the home screen...` |
| `browser,\nThe screenshot shows...` | `browser` |

### 5. HN 热门发现
- **Tiny-vLLM**（jmaczan）: C++/CUDA 写的 Llama 风格推理引擎，教育用
- **LFM2.5-8B-A1B**（Liquid AI）: 38T token 训练，MoE 架构，Mac M4 ~50 tok/s
- **SQLite as durable workflow engine** (244 pts) — interesting for Hermes memory layer
- **Liquid AI LFM2.5-8B-A1B** revealed: 8B MoE trained on 38T tokens

## Immediate Actions Taken

1. **Applied response normalization fix** to `get_scene_type()` in `screen_trigger_handler.py`
2. **Logged findings** to `~/.hermes/memory/idle_learning_log.md`

## Next Session Focus

**Direction D — 执行层**：验证 auto_execute 完整链路
- screen_watcher 存活 ✅
- handler 触发 ✅  
- dry-run 验证 ✅
- 坐标校准 → DRY_RUN=False

## Skill Updates

- `screen-watcher-vision/SKILL.md` updated: added `references/response-normalization-2026-06-02.md`
- `screen-watcher-vision/SKILL.md` patched: added reference to new reference file in the references list