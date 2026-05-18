---
name: claude-code-architecture
description: Claude Code源码深度分析——liuup版（513K行TS源码，2026-03-31泄漏）+ Hermes对齐状态
triggers:
  - Claude Code架构分析
  - Claude Code源码学习
  - Multi-Agent实现
  - StreamingToolExecutor
  - Tool Permission系统
  - MCP集成
  - Session Storage设计
  - Sandbox隔离
---

# Claude Code Architecture — 全量源码分析 + Hermes集成

## 来源
https://github.com/liuup/claude-code-analysis（Star 2.6k，Fork 1.6k）
原始泄露：Anthropic npm包未删除sourcemap，1902文件/513,237行TypeScript

---

## 一、架构总览：六层分层

```
CLI引导层 → TUI/REPL交互层 → Query/Agent执行内核 → Tool/Permission层 → Memory/Persistence层 → MCP/Remote/Swarm扩展层
```

主链路：cli.tsx → main.tsx → init.ts/setup.ts → launchRepl() → App+REPL → query() → runTools()/StreamingToolExecutor → sessionStorage/SessionMemory/compact/hooks

---

## 二、启动优化（cli.tsx + main.tsx）

- **快路径分流**：cli.tsx识别--version/--dump-system-prompt/remote-control/daemon/bg/runner，命中则执行并退出，不加载完整应用
- **并行预取**：init()阶段同时启动MDM读取、Keychain预取、GrowthBook拉取，~40ms vs 串行135ms+
- **Trust分离**：trust前只应用安全env var，trust后才initializeTelemetryAfterTrust() + 应用全部env
- **四种运行形态**：REPL/TUI、Headless/SDK、MCP Server、Remote/Bridge，共用同一query执行内核

---

## 三、Memory系统：多层文件化（非数据库）

### 底层存储：MEMORY.md索引 + topic/*.md
- ENTRYPOINT_NAME='MEMORY.md'，MAX_ENTRYPOINT_LINES=200，MAX_ENTRYPOINT_BYTES=25,000
- MEMORY.md是索引文件，不是正文；每条memory独立md文件
- 同步读取（React render路径不能await）+ 硬截断保护

### 四层Memory（各有独立目录/prompt/更新策略）
1. **Auto Memory**：用户/项目级长期记忆，~/.claude/projects/<project>/memory/，默认开启
2. **Session Memory**：当前会话摘要，会话<10K token不启用，>=5K token+3次tool_call才触发摘要提取，subagent执行（只能FileEdit精确路径）
3. **Agent Memory**：绑定特定agent类型，scope分user/project/local，目录结构复用memdir体系
4. **Team Memory**：团队共享repo级知识

### Relevant Memory Recall
- findRelevantMemories()：扫描文件头生成manifest，轻量模型选最多5个，不塞全文
- 被选的是文件名，不是整段正文

---

## 四、Tool系统

### Tool抽象（Tool.ts:362）
Tool是运行时协议对象，不只是函数映射：
- 能力描述：name/description()/prompt()/searchHint
- 输入输出：inputSchema/outputSchema/mapToolResultToToolResultBlockParam
- 安全属性：isConcurrencySafe()/isReadOnly()/isDestructive()/checkPermissions()
- UI表现：renderToolUseMessage()/renderToolResultMessage()
- 运行控制：interruptBehavior()/requiresUserInteraction()

### buildTool()默认值策略（Fail-Closed）
- isConcurrencySafe默认false（并发默认不安全）
- isReadOnly默认false
- toAutoClassifierInput默认''（安全分类器默认短路拦截）

### 权限链（toolExecution.ts）
每次tool调用必经：Zod schema校验 → tool.validateInput() → pre-tool hooks → canUseTool()决策（deny/ask/allow） → tool.call() → post-tool hooks → 格式化为tool_result

### 流式工具执行（StreamingToolExecutor.ts）
- LLM流式输出tool_use block时立即启动工具（不等全部到齐）
- isConcurrencySafe=true：与其他安全工具并发执行
- isConcurrencySafe=false：独占，串行化后续所有工具
- siblingAbortController：任一工具出错立即取消其他并发兄弟
- 结果按接收顺序返回（非完成顺序），保证LLM下一轮tool_result对应关系确定

---

## 五、MCP集成（client.ts）

### 四种传输协议
| 类型 | 适用场景 | 传输层 |
|------|---------|--------|
| stdio | 本地进程（最常用） | StdioClientTransport |
| sse/sse-ide | 远程HTTP长连接 | SSEClientTransport |
| ws/ws-IDE | WebSocket（IDE集成） | WebSocketTransport |
| http/streamable-http | HTTP+claude.ai代理 | StreamableHTTPClientTransport |

### 关键工程细节
- 工具描述超2048字符强制截断（OpenAPI衍生MCP服务曾有15-60KB描述）
- 并发连接控制：本地默认3，远端默认20
- 认证缓存防雪崩：某server认证失败后15分钟内直接短路返回needs-auth
- GET请求不加超时（SSE是长连接）
- AbortSignal.timeout()在Bun中有内存泄漏（每请求~2.4KB残留），用setTimeout+clearTimeout替代
- memoize连接：同一server配置只建一次连接

---

## 六、Sandbox（bashPermissions.ts + Shell.ts + sandbox-adapter.ts）

### 四层结构
1. shouldUseSandbox()决定某命令是否进沙箱
2. convertToSandboxRuntimeConfig()把settings语义翻译为sandbox runtime配置
3. bashPermissions.ts把沙箱自动放行和显式deny/ask规则揉在一起
4. Shell.ts + cleanupAfterCommand()执行隔离+宿主机清理

### shouldUseSandbox()判断逻辑
- 全局开关关闭 → 不进
- dangerouslyDisableSandbox + 策略允许 → 不进
- 无command → 不进
- 命中excludedCommands → 不进（**但这是便利特性，不是安全边界**）
- 其他 → 进

### excludedCommands是便利特性非安全边界
源码注释："NOTE: excludedCommands is a user-facing convenience feature, not a security boundary."

---

## 七、Multi-Agent：三种并存

### 1. 普通subagent
- 通过AgentTool调用runAgent()
- 继承父会话完整context和已渲染system prompt字节（**不是为了逻辑正确性，而是prompt cache命中率稳定性**）
- fork child默认后台运行

### 2. Coordinator Mode
- 主线程角色变为coordinator
- "You are Claude Code, an AI assistant that orchestrates software engineering tasks across multiple workers"
- 持续派出worker，worker负责research/implementation/verification，主线程综合结果

### 3. Swarm/Teammates
- 显式创建team，有team_name/lead/teammate roster/inbox/mailbox/共享task list
- 支持in-process/tmux/iTerm2三种backend
- 拓扑约束：teammate不能无限嵌套teammate；in-process teammate不能再启动background agent

---

## 八、Session Storage / Transcript / Resume

### 存储模型：append-only JSONL事件流
- 每session一个sessionId.jsonl
- progress不是transcript message（避免恢复时截断真实对话链）
- subagent transcript单独sidechain文件，不与主链混写
- 主链去重（UUID），sidechain保真，远端只跟主链走

### 写入：内存队列 + 批量flush
- drainWriteQueue()批量flush，不每次同步writeFile
- 文件权限0o600，目录0o700

### Metadata：同日志写入 + 尾部重挂
- metadata周期性重挂到EOF（session列表页只读头尾64KB窗口）
- reAppendSessionMetadata()：先从tail吸收外部SDK改过的新值，再重挂

### 远端ingress
- 主transcript message本地append同时，增量PUT到远端
- Last-Uuid乐观并发控制，409时吸收服务端最新UUID重试
- 同一session远端append必须串行化

---

## 九、Compact（会话压缩，四种策略）
1. **Session Memory Compaction**：首选，直接存入session memory文件，不调LLM
2. **Microcompaction**：大量图片/文档时，先剥离图片再轻量压缩
3. **Traditional Compaction**：fork独立subagent做全量摘要
4. **Reactive Compaction**：收到prompt_too_long错误时响应式触发

---

## 十、Hooks（30+生命周期事件）
Tool/ Session/ Agent/ Task/ Compact/ 权限/ 其他

---

## 十一、Feature Flag（bun:bundle死代码消除）
构建时就剔除，对外版本二进制不含实验性功能代码

---

## 十二、关键设计哲学

1. **Append-only日志 > 可变快照**：transcript/metadata都走追加
2. **文件化Memory > 数据库**：用户可直接打开目录查看markdown文件
3. **Fail-Closed**：新工具默认不安全、必须显式声明
4. **并行预取+懒加载**：启动阶段最大化并发
5. **prompt cache稳定性 > 逻辑等效**：fork child直接用父会话已渲染prompt字节
6. **透明即安全**：所有持久化内容用户可直接查看审计

---

## Hermes对齐状态（截至2026-05-18）

✅ 已完成：
- StreamingToolExecutor（写读互斥+sibling abort）
- Hook扩展（18→36个事件）
- Task系统（文件锁+原子claim+级联清理）
- delegate_tool接入Task System
- chat_completion_helpers.py已注入streaming_tool_callback

📋 进行中：
- 流式工具执行端到端集成
- conversation_loop的async generator改造

📋 待办：
- MCP工具自动注册为Hermes skill
- Session Storage透明化设计
- 权限链强化（deny规则+auto-allow）
- Feature Flag架构
