---
name: claude-code-architecture
description: Claude Code architecture deep-dive — Hermes integration reference
triggers:
  - Claude Code analysis
  - StreamingToolExecutor implementation
  - Task system design
  - Hook lifecycle expansion
---

# Claude Code Architecture — Hermes Integration Notes

## StreamingToolExecutor (最大工程亮点)
LLM边流式输出tool_use block，边启动对应工具执行，不等LLM完全结束。
- queued → executing → completed → yielded
- 只读工具可并发，写入工具须独占
- sibling_abort_controller: 任一工具出错取消所有并发兄弟

## Hooks (30+ events)
Hermes已从18扩展到36：task_created/task_blocked/subagent_start/subagent_complete/pre_compact/post_compact/permission_denied等

## Hermes 已对齐
- context_compressor.py: 4种压缩策略 ✓
- task_system.py: 文件锁+原子claim+级联清理 ✓
- Hooks: 36事件 ✓
- delegate_tool.py: task_list_id接入 ✓

## 待实现
- StreamingToolExecutor: 需改conversation_loop.py为LLM边输出边启动工具
