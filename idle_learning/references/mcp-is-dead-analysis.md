# MCP Is Dead 分析 — Quandri Engineering

**来源**：[MCP is dead | Quandri Engineering](https://www.quandri.io/engineering-blog/mcp-is-dead)（2026-05-30 HN 21pts）

## 核心数据

### 工具定义大小（Quandri Stack 真实测量）

| MCP Server | 工具数 | Chars | ~Tokens |
|------------|--------|-------|---------|
| Linear | 42 | ~51,229 | ~12,807 |
| Notion | 14 | ~16,156 | ~4,039 |
| Slack | 12 | ~15,168 | ~3,792 |
| Postgres | 9 | ~1,755 | ~438 |
| **Total** | **77** | **~84,308** | **~21,077** |

### Context Window 占用

| Model | Context Window | 工具定义占用 |
|-------|---------------|------------|
| Claude (200K) | 200,000 tokens | **10.5%** |
| GPT-4o (128K) | 128,000 tokens | **16.5%** |

### 最大工具（按 size）

1. `linear/save_issue`: 2,479 chars → ~619 tokens
2. `slack/search_public`: 1,614 chars → ~403 tokens
3. `linear/list_issues`: 1,588 chars → ~397 tokens
4. `notion/fetch`: 1,379 chars → ~344 tokens

## 三大问题

### 问题1：吞噬 Context Window
- 工具定义常驻内存，77个工具=21K tokens（Claude 200K的10.5%）
- 每增加一个 MCP server，上下文压力线性增长
- **Skills 模式**：按需加载，只有在用时才占用 context

### 问题2：低可靠性
- 需要启动和维护独立进程
- 外部 server 往返延迟（every tool call）
- **Mid-session tool death**：MCP server 进程崩溃
- 权限不透明（不清楚每个工具实际有什么权限）

### 问题3：架构重叠
- MCP 只存在于 LLM 对话中，对人类不可直接调试
- CLI/API 已有能力（grep/pipes/jq 自由组合），MCP 被锁在 server return format 里
- **训练数据**：CLI 已从 man pages/StackOverflow 学来，MCP 需要额外工具定义

## MCP vs Skills 模式对比

| Aspect | CLI/API | MCP | Skills |
|--------|---------|-----|--------|
| Loading time | N/A | All at once | Only when needed |
| Context consumption | N/A | Always occupied | Only when in use |
| Scalability | N/A | Grows with each server | Not proportional to count |
| Composability | Pipes/jq/grep | Locked format | Flexible |
| Debugging | Terminal | Conversation only | Per skill |

## 数据库场景建议

| Scenario | Recommendation | Why |
|----------|---------------|-----|
| Local dev / personal DB | Skills + CLI | Light and fast, easy recovery |
| Production / shared team DB | MCP | Safety guardrails, query validation |

## 对 Hermes 的意义

1. **auto_execute ACTION_WHITELIST 正是 Skills 模式**：按场景加载动作，非全量 MCP
2. **避免引入完整 MCP server 链路**：保持轻量，context 友好
3. **生产级 DB 场景才考虑 MCP**：需要严格权限隔离时才用
4. **MCP 架构问题印证了 Hermes 当前选择**：hermes-rpa + screen_trigger_handler 的轻量架构是对的

## HN 评论补充

- HN 评论指出 MCP 的"token eating"问题在工具数量增多时指数级恶化
- Anthropic 内部已在研究 MCP 的替代方案
- 某些团队开始用"Tool Schema Registry"替代 MCP 的全量加载