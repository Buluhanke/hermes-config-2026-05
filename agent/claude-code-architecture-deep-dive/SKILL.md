---
name: claude-code-architecture-deep-dive
description: Claude Code 官方 CLI 架构深度研究 — 12阶段渐进式Agent构建方法论、buildTool工厂、上下文压缩、多Agent协作协议。来源：freestylefly/claude-code + sanbuphy/learn-coding-agent
triggers:
  - 学习Claude Code架构
  - 设计Agent系统
  - 工具注册模式
  - 上下文压缩方案
  - 多Agent协作
---

# Claude Code 架构深度研究

## 概述

来源：Anthropic 官方 Claude Code CLI 源码研究（freestylefly/claude-code + sanbuphy/learn-coding-agent）

这是目前最完整的生产级 AI Agent 架构研究，包含 12 阶段递进式 Agent 构建方法论。

## 核心技术发现

### 1. Agent 循环架构（最核心）

```
Entry → Query Engine → Tool Dispatch → State → Loop
```

- `src/main.tsx`：REPL 入口，~4683 行
- `src/query.ts`：主 Agent 循环，~785KB（最大文件）
- `src/queryEngine.ts`：Headless/SDK 查询生命周期引擎

### 2. 12 阶段渐进式 Agent 构建

| 阶段 | 机制 | Hermes 可借鉴 |
|------|------|--------------|
| s01 | 基础 while-true 循环 | ✅ 已有主循环 |
| s02 | Tool Dispatch（buildTool 工厂） | 🔴 需要：标准化工具注册 |
| s03 | Planning（Plan mode + TodoWrite） | ⚠️ 部分：task 分解 skill |
| s04 | Sub-Agents（fork 新 messages[]） | ⚠️ 部分：delegate_task |
| s05 | Knowledge on Demand（懒加载 Skill） | ✅ 已有 skills 系统 |
| s06 | Context Compaction（3层压缩） | 🔴 需要：实现压缩 |
| s07 | Persistent Tasks（文件任务图） | ⚠️ 部分：已有 todo |
| s08 | Background Tasks（Daemon 模式） | 🔴 需要：后台任务 |
| s09 | Agent Teams（异步邮箱） | 🔴 需要：多 Agent 协作 |
| s10 | Team Protocols（SendMessage 协商） | 🔴 需要：Agent 间通信协议 |
| s11 | Autonomous Agents（Coordinator 模式） | 🔴 需要：自主决策模式 |
| s12 | Worktree Isolation（git worktree 隔离） | ⚠️ 部分：hermes 多工作区 |

### 3. 工具系统（buildTool 模式）

核心：`src/Tool.ts`（~29KB）+ `src/tools.ts`（~17KB）

```typescript
// 核心工厂模式
const tool = buildTool({
  name: 'BashTool',
  description: '...',
  inputSchema: z.object({ command: z.string() }),
  execute: async (args, context) => { ... }
})
```

- Zod schema 做输入验证
- AsyncLocalStorage 做上下文隔离
- StreamingToolExecutor 做工具执行生命周期观察

### 4. 上下文压缩（3层策略）

1. **autoCompact**：自动压缩对话历史
2. **snipCompact**：选择性裁剪中间消息
3. **contextCollapse**：上下文折叠

### 5. 关键工程模式

| 模式 | 实现位置 | 用途 |
|------|----------|------|
| AsyncGenerator Streaming | query.ts | API → 消费者全链路流式 |
| Builder + Factory | Tool.ts | 标准化工具定义 |
| Branded Types | src/types/ | 防止字符串混淆（如 SystemPrompt） |
| Feature Flags + DCE | feature() from bun:bundle | 编译时死代码消除 |
| Discriminated Unions | Message types | 类型安全消息处理 |
| Observer + State Machine | StreamingToolExecutor | 工具执行生命周期 |
| Snapshot State | FileHistoryState | 文件操作 undo/redo |
| Ring Buffer | error logs | 有界内存错误记录 |
| Fire-and-Forget Writes | transcript | 非阻塞持久化 |
| Lazy Schema | Zod deferred | 延迟 Zod schema 求值 |

### 6. 状态管理

- `src/state/AppState.tsx`（~23KB）
- `src/state/AppStateStore.ts`（~22KB）
- Redux-like store + React hooks
- AsyncLocalStorage 做 per-agent 上下文隔离

### 7. MCP 支持

完整 Model Context Protocol 实现：
- stdio / SSE / HTTP / WebSocket 传输
- MCP 认证、配置管理
- ~25 个服务文件

### 8. 遥测系统

- OpenTelemetry + Datadog
- 环境指纹采集
- 20+ 功能开关（KAIROS, VOICE_MODE, WEB_BROWSER_TOOL, COORDINATOR_MODE 等）
- 远程控制：每小时轮询 `/api/claude_code/settings`

## Hermes Agent 差距分析（2026-05-17 实地验证）

### 已有（✅）
- 主 Agent 循环
- Skills 系统（懒加载知识）
- Task 分解
- delegate_task 子 Agent
- 状态存储
- 基础 MCP 支持
- **错误自动恢复（凭证池）** ✅ 比 Claude Code 更强

### 缺失/需要加强（🔴）
1. **标准化 buildTool 工厂** — 工具注册不规范
2. **上下文压缩** — 有基础 preflight 压缩，但无语义分块+重要性权重
3. **后台任务/Daemon** — ✅ 今日已实现（daemon_scheduler.py + daemon_tool.py）
4. **多 Agent 团队协作** — 无异步邮箱/共享任务板
5. **Agent 间通信协议** — SendMessageTool 缺失
6. **自主决策模式（Coordinator）** — 全部任务依赖用户触发
7. **多工作区隔离** — git worktree 级别隔离

### 今日已落地（✅ 2026-05-17）
1. **Daemon 后台任务系统** — `cron/daemon_scheduler.py` (630行) + `tools/daemon_tool.py` (539行)
   - 接入 gateway tick 循环（`gateway/run.py`）
   - Agent 可用 `daemon(...)` 工具注册/启停/查看后台任务
   - 持久化到 `~/.hermes/daemons/daemons.json`
2. **Loop 内置 Planning** — `agent/conversation_loop.py` 两处 patch
   - 复杂任务启发式检测（100字符 + 关键词匹配）
   - 自动注入 `**计划已制定** + 步骤列表` 提示
   - 撤销：`cron/__init__.py`（如有修改则还原）

### awesome-selfhosted 元信息（2026-05-17）
- **两仓库架构**：`awesome-selfhosted-data` (YAML) → bot → `awesome-selfhosted` (README.md)
- **不接受直接 PR**：编辑须提交到 `awesome-selfhosted-data`
- **结论**：对 Hermes 无直接可用项目（Tier1: Ollama/LocalAI/Khoj 已研究，Tier2: Langfuse/Opik 可用但非紧急，Tier3: sish 最实用）

### 待观察（⚠️）
- 远程控制/遥测开关
- Undercover 模式（公开仓库自动隐藏 AI 身份）
- KAIROS（自主 Agent 模式）

## 关键文件位置

```
/tmp/claude-code-study/          # 克隆的 Claude Code 源码
/tmp/learn-coding-agent-study/   # 克隆的学习资料
~/.hermes/hermes-agent/cron/daemon_scheduler.py  # 今日实现
~/.hermes/hermes-agent/tools/daemon_tool.py      # 今日实现
```

## 参考文档

- `/tmp/learn-coding-agent-study/README_CN.md` — 中文完整分析
- `/tmp/learn-coding-agent-study/docs/zh/` — 5份专题报告（遥测/代号/卧底/远程/路线图）
