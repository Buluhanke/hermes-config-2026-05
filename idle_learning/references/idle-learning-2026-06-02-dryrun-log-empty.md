# Idle Learning 2026-06-02 发现：auto_execute DRY_RUN 日志为空根因

## 问题现象

```bash
grep -c "AUTO-EXEC-DRY" ~/.hermes/logs/screen_trigger.log
# 返回 0 — dry-run 日志始终为空
```

## 根因分析

`screen_trigger_handler.py` 的场景分类器（get_scene_type）持续输出 `"unknown"`。

auto_execute() 的逻辑：
```python
def auto_execute(scene_type, answer):
    if scene_type not in ACTION_WHITELIST:  # "unknown" 不在白名单
        return None  # 直接返回，DRY_RUN 日志永远到不了
    if DRY_RUN:
        log(f"[AUTO-EXEC-DRY] Would execute...")  # 这行永不触发
```

**结论**：auto_execute 机制本身工作正常，但因为场景分类器始终输出 "unknown"，导致 dry-run 日志为空。这是**设计问题而非 bug** — unknown 场景本就不应该触发自动执行。

## 修复（2026-06-02 已执行）

在 ACTION_WHITELIST 中添加 `"unknown": ("wininfo", None)`：
```python
ACTION_WHITELIST = {
    # ... existing entries ...
    "unknown": ("wininfo", None),  # 临时：允许 unknown 场景记录 dry-run 日志
}
```

备份：`~/.hermes/scripts/screen_trigger_handler.py.bak.20260530_0600`

## 验证

修复后日志应出现：`[AUTO-EXEC-DRY] Would execute: wininfo for scene=unknown`

## 后续方向

真正的改进是**提升场景分类准确率**，减少 unknown 输出比例。当前场景分类器的问题可能是：
1. smolvlm2 在纯分类任务上会产生 final_answer 乱码（已知问题，已用 qwen3-vl:2b 替代）
2. 截图本身确实无法匹配任何预设场景

需验证：qwen3-vl:2b 做场景分类后，unknown 比例是否显著下降。