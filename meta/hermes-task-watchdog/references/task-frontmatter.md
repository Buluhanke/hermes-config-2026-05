# Task Frontmatter Specification

Each task file in `~/.hermes/tasks/` should begin with a YAML frontmatter block delimited by `---` lines.

## Fields

- **任务** (string, required): Short description of the task.
- **状态** (string, required): One of `进行中`, `完成`, `失败`, `已取消`. The watchdog only acts on `进行中` and `完成`.
- **创建时间** (string, optional): Timestamp when the task was created, format `YYYY-MM-DD HH:MM`.
- **步骤** (list, optional): Checklist of steps, each line starting with `- [ ]` (pending) or `- [x]` (done).
- **结果** (string, optional): Filled in when task completes.

## Example

```yaml
---
任务：更新 Hermes 技能库
状态：进行中
创建时间：2026-06-26 09:00
步骤：
- [ ] 审查今日对话
- [ ] 更新相关技能
- [ ] 添加参考文件
结果：
---
```

## Notes

- Keep the frontmatter concise; avoid extra keys unless needed by other tools.
- If the file does not start with `---` or lacks a closing `---`, treat the whole file as content (no frontmatter).
- The watchdog skips files without valid frontmatter or missing required fields.