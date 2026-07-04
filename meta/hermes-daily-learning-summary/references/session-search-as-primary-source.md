# session_search 作为 cron 每日总结的主数据源

**场景**: daily-summary cron job 需要在 cron 会话中总结 24h 学习成果。
**问题**: `memory` tool 在 cron 会话不可用，`fact_store` 可能 0 新增。
**方案**: `session_search` 永远可用——用它回溯过去 24h 对话。

## 标准工作流（2026-07-02 已验证）

```python
from hermes_tools import session_search

# 1. 搜索过去 24h 的关键学习信号
result = session_search(query="学到 总结 发现 注意 记忆 更新 教训",
                        limit=10, sort="newest")

# 2. 读最近 3 个 session 的 bookend（goal→match→resolution）
for session in result['data']['session']:
    print(session['session_id'], session['snippet'][:100])
    # bookend_start 显示任务目标
    # messages 显示实际完成的内容

# 3. 读 MEMORY.md 确认哪些已落地
mem = read_file("~/.hermes/MEMORY.md")

# 4. 对比 → 只输出 MEMORY.md 未覆盖的新知识
```

## Pitfalls

- **session_search 默认 FTS5 只能搜今天的 session**——用 `sort="newest"` + `limit=10` 覆盖最近 24h
- **scroll mode** 需要 session_id + around_message_id，别试图直接 scroll
- **browse mode** (无参调用) 返回最近 session 标题列表，适合先扫一遍再精搜
- **role_filter** 默认 `user,assistant` — 一般够用；调试 tool 行为时才加 `tool`

## 数据源优先级（cron 会话）

1. `session_search` (最新鲜，24h 内所有对话)
2. `read_file("~/.hermes/MEMORY.md")` (已固化的系统记忆)
3. `read_file("~/.hermes/logs/daily_learning_*.md")` (每日学习日志)
4. fact_store / agent.log (兜底)
