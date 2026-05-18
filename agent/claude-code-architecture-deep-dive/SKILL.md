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
| s07 | Persistent Tasks（文件任务图） | ✅ 已实现（task_system.py） |
| s08 | Background Tasks（Daemon 模式） | ✅ 已实现（daemon_scheduler.py） |
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

---

## 2026-05-18 新增：源码快照深度解析

来源：Anthropic 通过一次源码快照泄漏的 Claude Code 完整代码（2026-03-31）。比之前来源更完整、更准确。

### 规模指标

| 指标 | 数值 |
|------|------|
| TypeScript/TSX 文件数 | 1,884 个 |
| 总行数 | ~512,685 行 |
| 源码目录大小 | 35 MB |
| 主入口 src/main.tsx | 786 KB / 4,683 行 |

### 技术栈全景（补充）

| 类别 | 技术 | 说明 |
|------|------|------|
| 运行时 | Bun | 替代 Node.js，启动更快，内置 bundler 和测试框架 |
| 终端 UI | React + Ink | 在终端中跑 React 组件树 |
| CLI 解析 | Commander.js | 附带 extra-typings 的类型安全 CLI |
| 外部协议 | MCP SDK + LSP | 工具扩展协议 + 语言服务器协议 |
| Feature Flag | GrowthBook + **bun:bundle** | 运行时灰度 + **构建时死代码消除** |
| 代码搜索 | ripgrep | GrepTool 内部调用 |

**最重要的技术决策：Bun 死代码消除**
Claude Code 大量使用 `bun:bundle` 做构建时 feature flag 死代码消除。flag 在打包时就被判断并剔除，而不是运行时的 if/else 分支：

```typescript
// src/tools.ts（节选）
import { feature } from 'bun:bundle'

const SleepTool = feature('PROACTIVE') || feature('KAIROS')
  ? require('./tools/SleepTool/SleepTool.js').SleepTool
  : null
```

这意味着内部开发版和对外发布版是完全不同的二进制，对外版本里根本不含某些实验性功能的代码。

### 核心：StreamingToolExecutor（流式工具执行引擎）

**文件：** `src/services/tools/StreamingToolExecutor.ts`（~300行）

这是 Claude Code 最精妙的工程设计——在 LLM 流式输出的同时，就开始并发执行工具，不等全部 tool_use block 到齐。

```typescript
export class StreamingToolExecutor {
  private tools: TrackedTool[] = []   // 工具执行队列
  private toolUseContext: ToolUseContext
  private siblingAbortController: AbortController  // 兄弟工具出错时中止其他工具
}

type TrackedTool = {
  id: string
  block: ToolUseBlock
  status: 'queued' | 'executing' | 'completed' | 'yielded'
  isConcurrencySafe: boolean
  promise?: Promise<void>
  results?: Message[]
  pendingProgress: Message[]
}
```

**并发控制逻辑：**
```typescript
private canExecuteTool(isConcurrencySafe: boolean): boolean {
  const executingTools = this.tools.filter(t => t.status === 'executing')
  return (
    executingTools.length === 0 ||
    (isConcurrencySafe && executingTools.every(t => t.isConcurrencySafe))
  )
}
```

**核心规则：**
- 只读（并发安全）工具：只要当前正在执行的全是只读工具，就可以立即加入并发执行
- 写入（非并发安全）工具：必须等所有在执行的工具完成，才能独占执行
- 错误传播：兄弟工具联动取消——当一个 BashTool 执行出错时，会通过 `siblingAbortController` 立即取消所有正在并发执行的兄弟工具进程

**结果顺序保证：** `getRemainingResults()` 按工具接收顺序（而非完成顺序）yield 结果。保证了 LLM 下一轮收到的 tool_result 对应关系是确定的。

**对比 Hermes：** Hermes 的 `tool_executor.py` 是"等 LLM 完全输出后，再用 ThreadPoolExecutor 并发执行"。Claude Code 是"看到 tool_use block 就开始执行"，不需要等 LLM 全部输出完毕。这是感知延迟上的关键差距。

### 核心：ReAct Loop（Agent 循环）

**文件：** `src/query.ts:241`（async generator）

Claude Code 的 Agent Loop 实现了经典的 ReAct 模式（Reasoning + Acting）：

```
用户输入 → 调用 LLM，流式获取响应
  ↓
响应中有 tool_use？
  ├─ 是 → 执行工具 → 将结果追加到对话 → 回到"调用 LLM"
  └─ 否 → 结束，将最终文本响应展示给用户
```

**入口：** `QueryEngine.submitMessage()` → `query()` → `queryLoop()`

**状态机设计：** 每次迭代开始时解构 state 拿到只读引用，迭代内不修改 state；只在"continue sites"（循环末尾）通过 `state = { ...newState }` 整体替换。这保证了每次迭代的状态是清晰快照，避免了跨迭代的意外修改。

**Token Budget 跟踪：** budgetTracker 贯穿全程，配合 taskBudgetRemaining 在跨 compact 边界后也能准确统计总消耗。

### 核心：工具调用权限链

**文件：** `src/services/tools/toolExecution.ts:1,745`

每次工具调用都经过完整权限检查链：

```
runToolUse(block)
  ├─ 1. Zod schema 校验输入参数
  ├─ 2. tool.validateInput()（工具自定义校验）
  ├─ 3. runPreToolUseHooks()     ← 前置 hooks
  ├─ 4. canUseTool() 权限决策
  │       ├─ deny 规则匹配 → 拒绝
  │       ├─ ask 规则匹配  → 弹出用户确认对话框（阻塞）
  │       └─ allow         → 通过
  ├─ 5. tool.call(input, context, ...)
  ├─ 6. runPostToolUseHooks()    ← 后置 hooks
  └─ 7. 格式化为 tool_result 消息块
```

权限规则支持针对特定工具、特定参数模式的细粒度配置，例如：
- `Bash(git *)` — 自动允许所有 git 命令
- `Bash(rm *)` — 所有删除命令必须询问

**对比 Hermes：** Hermes 有 `tool_guardrails.py` + `shell_hooks.py` + 插件 hook，但没有 Zod schema 校验层。权限链深度不如 Claude Code。

### 核心：Compact 对话压缩四种策略

**文件：** `src/services/compact/compact.ts`

| 策略 | 触发场景 | 特点 |
|------|----------|------|
| Session Memory Compaction | 首选 | 不调用 LLM，直接存入 session memory 文件，最快 |
| Microcompaction | 含大量图片/文档时 | 先剥离图片（替换为 [image]），再做轻量压缩 |
| Traditional Compaction | 需高质量摘要 | fork 独立子 agent 做全量摘要，支持自定义指令 |
| Reactive Compaction | 收到 prompt_too_long 错误 | 响应式触发，自动压缩后重试 |

关键常量：
- `COMPACT_MAX_OUTPUT_TOKENS = 20,000` — 摘要最大输出 token
- `POST_COMPACT_TOKEN_BUDGET = 50,000` — 压缩后可用 token 预算

**对比 Hermes：** Hermes 的 `context_compressor.py` (1699行) 已有类似 4 种策略，实现上相当。

### 核心：Hook 生命周期（30+ 事件）

**文件：** `src/utils/hooks/`（多文件）

覆盖 30+ 生命周期事件：PreToolUse / PostToolUse / PostToolUseFailure / SessionStart / SessionEnd / Setup / Stop / SubagentStart / SubagentStop / TaskCreated / TaskCompleted / PreCompact / PostCompact / UserPromptSubmit / PermissionDenied / PermissionRequest / InstructionsLoaded / CwdChanged / FileChanged / TeammateIdle …

Hook 配置支持四种执行类型：Shell 命令 / HTTP 请求 / Agent 委托 / Prompt Hook。

Exit code 语义：0=成功，2=阻塞错误（影响模型下一步行为），其他非零=报告给用户。

**对比 Hermes：** Hermes 的 `shell_hooks.py` (836行) + 插件系统有类似能力，但事件点数量和粒度不如 Claude Code。

### 核心：Task 系统（多 Agent 协作基础设施）

**文件：** `src/utils/tasks.ts:862`

Task 以 JSON 文件形式存储于 `~/.claude/config/tasks/{taskListId}/` 目录，包含：id / subject / status / blocks / blockedBy / owner 等字段。

**并发安全：** 所有修改操作都在 proper-lockfile 的文件锁保护下执行，最多重试 30 次，重试间隔指数退避。

**原子 Claim：** `claimTask()` 实现原子性的任务认领——多个 agent 竞争同一 task 时，只有一个能成功。

**级联清理：** 删除 task 时自动清理所有其他任务中对该 task 的 blocks/blockedBy 引用。

### 关键文件速查表

| 文件 | 行数 | 职责 |
|------|------|------|
| src/main.tsx | 4,683 | CLI 入口、React/Ink 渲染、并行预取 |
| src/query.ts | 1,729 | Agent Loop 核心（queryLoop） |
| src/Tool.ts | 792 | Tool 类型定义与工具查找 |
| src/tools.ts | 390 | 工具注册、池化、feature gate |
| src/services/tools/toolExecution.ts | 1,745 | 工具权限检查、hooks、实际执行 |
| src/services/tools/StreamingToolExecutor.ts | ~300 | 流式并发工具执行引擎 |
| src/utils/tasks.ts | 862 | Task 系统（文件锁 + 原子 claim） |
| src/services/compact/compact.ts | 200+ | 对话压缩服务（四种策略） |
| src/utils/thinking.ts | ~200 | Thinking 模式配置与 ultrathink 触发 |

### Hermes vs Claude Code 关键差距速查

| 优先级 | 差距 | Claude Code 方案 | Hermes 当前 |
|--------|------|-----------------|------------|
| **P0** | 流式工具执行 | LLM边输出token边启动工具 | ✅ 已实现（streaming_tool_executor.py） |
| **P0** | 权限模型深度 | Zod校验→tool自检→pre hooks→canUseTool→post hooks | Guardrails + invoke_tool |
| **P1** | Async Generator架构 | `async function* yield` 驱动全链路 | 回调(callback)驱动 |
| **P1** | 多Agent Task系统 | 文件锁+原子claim+级联清理 | ✅ 已实现（task_system.py） |
| **P2** | Hook生命周期 | 30+ 事件点 | ✅ 已扩展（18→36个事件） |
| **P2** | Skill MCP自动化 | MCP工具自动注册为skill | 无 |
| **P3** | 构建时Feature Flag | bun:bundle 死代码消除 | 无（运行时判断） |

> ✅ 标注项：2026-05-18 已提交 commit 5501f5b6b

### 架构亮点总结（可借鉴的设计哲学）

1. **Async Generator 驱动整个架构** — yield 事件给 UI 层，return 终止状态，线性可读性 + 真正流式处理
2. **流式工具执行** — 看到 tool_use block 就开始执行，不等 LLM 全部输出完毕
3. **权限模型是硬编码的必经路径** — 安全是设计出发点，不是事后补丁
4. **构建时特性隔离** — bun:bundle 让实验代码在发布版中完全消失
5. **多 Agent 是一等公民** — Task 系统的文件锁、原子 claim、兄弟 abort 机制
6. **扩展性贯穿始终** — MCP / Hooks / Skill / Plugin 四层扩展

### 待观察（⚠️）
- 远程控制/遥测开关
- Undercover 模式（公开仓库自动隐藏 AI 身份）
- KAIROS（自主 Agent 模式）

## 关键文件位置

```
/tmp/claude-code-study/          # 克隆的 Claude Code 源码
```
~/.hermes/hermes-agent/agent/streaming_tool_executor.py  # 2026-05-18 新建，流式工具执行引擎
~/.hermes/hermes-agent/agent/task_system.py             # 2026-05-18 新建，Task协作系统
~/.hermes/hermes-agent/cron/daemon_scheduler.py         # 2026-05-17 新建，Daemon调度
~/.hermes/hermes-agent/tools/daemon_tool.py             # 2026-05-17 新建，Daemon工具
```

## 参考文档

- `/tmp/learn-coding-agent-study/README_CN.md` — 中文完整分析
- `/tmp/learn-coding-agent-study/docs/zh/` — 5份专题报告（遥测/代号/卧底/远程/路线图）
- `references/hermes-agent-source-data-2026-05-18.md` — Hermes 源码关键数据实地读取（2026-05-18 本次分析）
