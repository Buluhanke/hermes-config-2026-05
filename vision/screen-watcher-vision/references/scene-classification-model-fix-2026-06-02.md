# 场景分类模型切换：smolvlm2 → qwen3-vl:2b（2026-06-02）

## 问题描述

`get_scene_type()` 使用 `smolvlm2-agentic-gui` 做场景分类，但持续输出乱码：

```
RAW: "final_answer(''The i..."
CLEANED: "final_answer(''The i..."
```

导致 `auto_execute()` 永远无法触发（`[AUTO-EXEC-DRY]` 日志始终为 0）。

## 根因分析

smolvlm2-agentic-gui 是 GUI 操作特化微调模型，专为 `click/type/scroll` 结构化 action 设计。
在**纯分类任务**（多选一、无 action 输出）上，会强制将选项包裹在 `final_answer('')` 格式中，
即使 prompt 明确要求"只回答一个英文单词"也无济于事。

qwen3-vl:2b 是通用视觉模型，在场景分类任务上表现正常：`"desktop"` → 直接匹配 whitelist ✅

## 修复方案

修改 `~/.hermes/scripts/screen_trigger_handler.py` 的 `get_scene_type()`：

```python
# 改用 qwen3-vl:2b + 英文 prompt
prompt = (
    "What is shown in this screenshot? Choose ONE from:\n"
    "browser, wechat, desktop, calculator, jingdong, 1688, dingtalk, telegram, other\n"
    "Reply with ONLY the word, nothing else."
)

payload = {
    "model": "qwen3-vl:2b",          # 从 MODEL (smolvlm2) 改为 qwen3-vl:2b
    "prompt": prompt,
    "images": [img_b64],
    "stream": False,
    "options": {"temperature": 0.0}
}

# timeout 60s → 120s（qwen3-vl:2b 响应慢）
```

## 两模型分工

| 函数 | 模型 | 速度 | 用途 |
|------|------|------|------|
| `get_scene_type()` | qwen3-vl:2b | ~46s（慢，但准确）| 场景分类，触发 auto_execute |
| `ask_screen()` | smolvlm2-agentic-gui | 7-10s（快）| GUI 内容分析 + 操作规划 |

注意：`ask_screen()` 仍用 smolvlm2，因为 GUI 操作规划正是 smolvlm2 的强项。

## Trade-off

- 场景分类从"永远失败"变为"46s 后成功"
- 场景分类每 60s 最多 1 次（cooldown 机制），所以影响有限
- qwen3-vl:2b 的高延迟是模型本身特性，非 bug

## 验证方法

```bash
tail -5 ~/.hermes/logs/screen_trigger.log
# 应出现：场景类型: desktop（或其他英文单词）
# 以及：[AUTO-EXEC-DRY] Would execute: wininfo for scene=desktop
```

## 备份

修复前已备份：`~/.hermes/scripts/screen_trigger_handler.py.bak.20260602`