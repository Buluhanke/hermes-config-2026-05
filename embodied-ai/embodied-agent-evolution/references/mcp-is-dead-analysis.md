# MCP Is Dead — Quandri Engineering Analysis

**来源**: https://www.quandri.io/engineering-blog/mcp-is-dead
**HN分数**: 21pts
**日期**: 2026-05-30 抓取

## 核心结论

MCP 三大问题：
1. **吞噬 Context Window** — 77个工具 = 21K tokens = 占 Claude 200K 上下文的 10.5%
2. **低可靠性** — 进程隔离导致 mid-session tool death、MCP server 崩溃
3. **架构重叠** — 与现有 CLI/API 功能重复，但只存在于 LLM 对话中

## 数据支撑

### Tool Definition Sizes（Quandri Stack）

| MCP Server | Tools | Est. Chars | Est. Tokens |
|------------|-------|------------|-------------|
| Linear | 42 | ~51,229 | ~12,807 |
| Notion | 14 | ~16,156 | ~4,039 |
| Slack | 12 | ~15,168 | ~3,792 |
| Postgres | 9 | ~1,755 | ~438 |
| **Total** | **77** | **~84,308** | **~21,077** |

### Context Window Usage

| Model | Context Window | Tool Definitions Usage |
|-------|---------------|----------------------|
| Claude (200K) | 200,000 tokens | **10.5%** |
| GPT-4o (128K) | 128,000 tokens | **16.5%** |

### Biggest Tools by Size

| Tool | Chars | ~Tokens |
|------|-------|---------|
| linear/save_issue | 2,479 | ~619 |
| slack/search_public | 1,614 | ~403 |
| linear/list_issues | 1,588 | ~397 |
| notion/fetch | 1,379 | ~344 |
| slack/send_message | 1,248 | ~312 |

## MCP vs Skills 对比

| Aspect | MCP | Skills |
|--------|-----|--------|
| Loading time | All tool definitions loaded on connect | Only loaded when needed |
| Context consumption | Always occupied | Only when in use |
| Scalability | Context pressure grows with each server | Not proportional to skill count |
| Reliability | Process isolation, mid-session tool death | No extra process layer |
| Composability | Locked to server return format | Pipes, jq, grep freely combinable |
| Debugging | Only reproducible inside conversation | Reproduce immediately in terminal |

## 对 Hermes auto_execute 的意义

**ACTION_WHITELIST 正是 Skills 模式的体现**：
- 按场景加载动作（browser/wechat/1688/dingtalk/telegram）
- 不为每个 app 引入完整 MCP server
- 避免为每个 app 引入完整 MCP server，保持轻量

**备选原则**：MCP 只用于需要严格权限隔离的生产级 DB 场景。

## CLI vs MCP Token 对比（Linear Issue Lookup）

```
CLI approach:
→ Prompt (curl command): ~150 tokens
→ Response: ~100 tokens

MCP approach:
→ Tool definitions (always loaded): ~12,800 tokens
→ Tool call + response: ~400 tokens
```

## 何时用 MCP vs CLI/Skills

| Scenario | Recommendation | Why |
|----------|---------------|-----|
| Local dev / personal DB | CLI + Skills | Light and fast, easy to recover from mistakes |
| Production DB / shared team | MCP | Safety guardrails essential, query validation at server level |