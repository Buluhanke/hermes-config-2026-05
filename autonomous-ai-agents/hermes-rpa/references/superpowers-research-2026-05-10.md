# Superpowers 调研记录

**日期**: 2026-05-10
**仓库**: github.com/obra/superpowers（184k stars）

## 结论：与当前任务无关，不需要装

Superpowers 是一个**代码开发方法论框架**，给 Claude Code / Codex / Cursor 这类 coding agent 用的。

| 维度 | 内容 |
|------|------|
| 定位 | 代码开发流程标准化（brainstorm → TDD → code review → finish branch） |
| 适用场景 | 帮人写代码更规范，不是操控桌面/浏览器 |
| Stars | 184k |
| 平台 | Claude Code / Codex CLI / Gemini CLI / OpenCode / Cursor |

## 为什么没用

- **目标不匹配**：我们追求的是"类人化操控整台电脑"，Superpowers 解决的是"AI 写代码更规范"
- **场景不同**：它是 coding agent 专用，Hermes 是通用助手
- **无可借鉴点**：workflow 思路和 Hermes 的 `delegate_task` + `kanban-orchestrator` 有重叠，但这些 skill 已经在 Hermes 里了

## 有两个可借鉴的技能

1. **`systematic-debugging`**（4步溯源法）—— 调试难问题时可以用这个思路
2. **`subagent-driven-development`** —— 多任务并行调度的思路，Hermes 已有类似实现

如需在 Claude Code 里玩可以装，但对 Hermes 没有意义。
