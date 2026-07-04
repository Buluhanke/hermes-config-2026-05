# Tips 补充 — 2026-07-02 第二轮采集

**来源**: https://hermes-agent.nousresearch.com/docs/guides/tips/ (后半部分)
**状态**: 已验证 (cron idle 学习实际用过)

## 记忆与 Skills

### 13. Memory vs Skills: 放什么

**官方原文**: "Memory is for facts: your environment, preferences, project locations, and things the agent has learned about you. Skills are for procedures: multi-step workflows, tool-specific instructions, and reusable recipes. Use memory for 'what,' skills for 'how.'"

**本机用法**: 新的 memory tool 支持 operations 批量操作（v0.17 升级），一个 call 做多条增删改。等下次 memory tool 可用时验证。

### 14. 何时创建 Skill

**官方原文**: "If you find a task that takes 5+ steps and you'll do it again, ask the agent to create a skill for it. Say 'save what you just did as a skill called deploy-staging.' Next time, just type /deploy-staging and the agent loads the full procedure."

### 15. 管理 Memory 容量

Memory 有上限（~2,200 chars MEMORY.md, ~1,375 chars USER.md）。超限时 agent 自动合并。用户可以说"clean up your memory"。

### 16. "remember this for next time" 命令

用户说"remember this for next time"，agent 会存关键点。也可以指定"save to memory that our CI uses GitHub Actions with the deploy.yml workflow"。

**⚠️ 注意**: Memory 是 frozen snapshot — 会话中的改变要到下次会话才出现在 system prompt 中。agent 会立即写盘，但 prompt 缓存不会在会话中段失效。

## 性能与成本

### 17. 不要破坏 Prompt Cache

Provider 缓存 system prompt 前缀。保持 system prompt 稳定（同 context files、同 memory），后续消息享受 cache hit 降低费用。避免会话中间换模型/system prompt。

### 18. `/compress` 压缩巨量上下文

**官方原文**: "When you notice responses slowing down or getting truncated, run /compress. This summarizes the conversation history, preserving key context while dramatically reducing token count. Use /usage to check where you stand."

**本机用法**: 这是真正的 productivity hack — 长任务后 /compress 可继续工作而不丢上下文。

### 19. `delegate_task` 并行子代理

**官方原文**: "Need to research three topics at once? Ask the agent to use delegate_task with parallel subtasks. Each subagent runs independently with its own context, and only the final summaries come back — massively reducing your main conversation's token usage."

### 20. `execute_code` 做批量操作

比一个一个跑 terminal 命令快。一次写完一个脚本统一执行。

### 21. `/model` 切换模型

**官方原文**: "Use /model to switch models mid-session. Use a frontier model (Claude Sonnet/Opus, GPT-4o) for complex reasoning and architecture decisions. Switch to a faster model for simple tasks like formatting, renaming, or boilerplate generation."

**补充**: `hermes setup --portal` 一站式获取 300+ 模型（Claude, GPT-5, Gemini）。

### 22. `/usage` 查 token 消耗 / `/insights` 看 30 天模式

## 通讯技巧

### 23. `/sethome` 设置 Home Channel

Cron job 结果和定时任务输出送达这里。没有 home channel agent 无处发送主动消息。

### 24. `/title` 为会话命名

`/title auth-refactor` 或 `/title research-llm-quantization`。命名后可 `hermes sessions list` 找到，`hermes -r "auth-refactor"` 恢复。

### 25. DM Pairing 团队访问

队友 DM 机器人时获得一次性配对码。用 `hermes pairing approve telegram XKGH5N7P` 批准。

### 26. `/verbose` 控制工具活动显示

Messaging 平台用 "new" 只看新 tool call；CLI 用 "all" 看全貌。

### 27. 消息平台的会话重置

平台会话空闲 24h 后自动重置，或每天 4 AM 重置。可在 config.yaml 每个平台调。

## 安全

### 28. Docker 隔离不可信代码

`TERMINAL_BACKEND=docker` + `TERMINAL_DOCKER_IMAGE=hermes-sandbox:latest`

### 29. Windows 编码坑

`with open("f.txt", "w", encoding="utf-8")` 显式指定 utf-8。PowerShell `$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)`

### 30. Command Approval 安全网

Hermes 检查每个命令的危险模式（递归删除、SQL drop、curl|sh 等）。Docker/Modal 容器后端中跳过安全检查（容器 === 安全边界）。

### 31. 消息机器人的 Allowlist

永远不要 `GATEWAY_ALLOW_ALL_USERS=true`。用 `TELEGRAM_ALLOWED_USERS` / `DISCORD_ALLOWED_USERS` / `GATEWAY_ALLOWED_USERS`。

## 价值评级

| 技巧 | 实用度 | 说明 |
|---|---|---|
| `/compress` 压缩上下文 | ⭐⭐⭐⭐⭐ | 持续工作的关键 hack |
| `delegate_task` 并行子代理 | ⭐⭐⭐⭐⭐ | 多任务并行，不占主上下文 |
| `execute_code` 批量操作 | ⭐⭐⭐⭐ | 替代一个一个跑 terminal |
| `/title` 命名会话 | ⭐⭐⭐⭐ | 告别"一堆 unnamed session" |
| `/model` 切换模型 | ⭐⭐⭐⭐ | 复杂用 frontier，简单用快模型 |
| `/usage` / `/insights` | ⭐⭐⭐ | token 可见性 |
| `/sethome` 设 home channel | ⭐⭐⭐ | cron 结果送达 |
| Memory vs Skills 区分 | ⭐⭐⭐ | 减少错误放置 |
| Docker 隔离 | ⭐⭐⭐ | 安全场景 |
