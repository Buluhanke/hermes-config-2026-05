---
name: handoff
description: "会话交接 当前对话压缩成handoff文档。Use when 会话太长要交接给下一个会话"
argument-hint: What will the next session be used for?
disable-model-invocation: true
triggers:
- Use when handoff
trigger_type: general
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to the temporary directory of the user's OS - not the current workspace.

Include a "suggested skills" section in the document, which suggests skills that the agent should invoke.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.
