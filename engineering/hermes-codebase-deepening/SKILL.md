---
name: hermes-codebase-deepening
description: 源码深化工作流 — 研究 Hermes Agent 源码，理解架构，发现差距，实现功能扩展。模式：源码分析→差距识别→子代理实施→patch落地→语法验证。今天的核心成果：daemon系统 + loop内置planning。
triggers:
  - 读Hermes源码理解某机制
  - 想给Hermes加新功能
  - 比较Hermes和其他Agent实现
  - 在conversation_loop/gateway/tools等核心目录做patch
---

# Hermes 源码深化工作流

## 何时用

- 想理解 Hermes 某个机制是怎么工作的
- 想给 Hermes 添加新功能
- 想对比 Hermes 和 Claude Code 的实现差异
- 想在 `agent/`、`cron/`、`tools/`、`gateway/` 等核心目录做修改

## 标准流程

### 第一步：源码分析（子代理执行）

用 `delegate_task` 分配给子代理，避免主对话被源码刷屏。

**提示词模板：**
```
先读以下文件了解结构：
- `~/.hermes/hermes-agent/<相关文件>`
- `~/.hermes/hermes-agent/<相关文件>`

分析：
- 核心数据结构和函数
- 入口点和调用链
- 关键设计模式
- 与目标的关联

输出：关键发现 + 注入点位置（精确到行号）
```

### 第二步：识别注入点

常见目标位置（conversation_loop.py 为例）：
```
Line 356-424   →  Preflight 压缩阶段（循环前）
Line 424-460   →  pre_llm_call hook 之后（今日Planning注入点）
Line 532       →  while 主循环入口
Line 780-850   →  api_messages 构建阶段（今日planning提示注入点）
```

### 第三步：实施 patch

**原则：最小侵入，精确到行**

```python
# 工具：patch(old_string, new_string)
# 关键：old_string 必须唯一，包含足够上下文
# 验证：patch 后立刻 python3 -m py_compile 检查语法
```

**子代理输出要求：**
1. 精确 old_string（上下文 3 行以上）
2. 完整 new_string
3. 精确插入位置（行号 + 上下文）
4. 撤销方法
5. 语法检查命令

### 第四步：验证

```bash
python3 -m py_compile <修改的文件> && echo "语法检查通过"
```

### 第五步：确认循环导入

修改 `gateway/run.py`、`cron/` 等被多处导入的文件时：
- 确认没有循环导入
- 确认 `__init__.py` 无需更新（大多数自注册工具无需修改 registry）
- 检查 `tools/registry.py` 的 `_module_registers_tools()` 确认自注册机制

---

## 今日成果（2026-05-17）

### ① Daemon 后台任务系统

**背景：** 参考 Claude Code s08（Background Tasks/Daemon），Hermes 原有 cronjob 只能定时跑，无法常驻。

**注入点：** `gateway/run.py` line ~16614，cron tick 循环内

**文件：**
```
cron/daemon_scheduler.py  (630行) — 核心调度引擎
  - DaemonState 状态机：STOPPED/RUNNING/STARTING/FAILED/HEARTBEAT_MISSING
  - tick_daemons()：gateway 60s tick 驱动
  - Per-daemon threading：每 daemon 独立线程
  - 心跳检测：daemon 调用 daemon(action='heartbeat') 续命
  - 自动重启：failed/stopped 的 daemon 在 tick 时自动重启

tools/daemon_tool.py     (539行) — Agent 工具接口
  - 自注册：registry.register(name="daemon", ...)
  - 自动发现：tools/registry.py 的 _module_registers_tools() 无需修改

已修改：
  gateway/run.py — 2行，接入 tick_daemons()
```

**验证语法：**
```bash
python3 -m py_compile cron/daemon_scheduler.py && echo "daemon_scheduler.py OK"
python3 -m py_compile tools/daemon_tool.py && echo "daemon_tool.py OK"
```

### ② Loop 内置 Planning

**背景：** 参考 Claude Code s03（Planning mode），复杂任务执行前无拆解。

**注入点：**
- `agent/conversation_loop.py` line ~466 — Planning 检测逻辑
- `agent/conversation_loop.py` line ~731 — Planning 提示注入

**代码逻辑：**
```python
_COMPLEX_TASK_KEYWORDS = [
    "研究", "调研", "分析", "比较", "调查",
    "实现", "开发", "构建", "找出", "评估", "审核",
    "写一个", "做一个", "帮我做", "帮我", "全面", "系统",
    "review", "implement", "build", "create", "design",
]

# 长度 > 100 且含关键词 → 注入 Planning 提示
```

**触发效果：** 模型先输出 `**计划已制定** + 步骤列表`，再执行

**验证语法：**
```bash
python3 -m py_compile agent/conversation_loop.py && echo "语法检查通过"
```

### ③ 审计结论（重要）

**错误自动恢复 Hermes 已有**，且比 Claude Code 更强：
- `agent/error_classifier.py` — 完整错误分类
- `agent/agent_runtime_helpers.py` — `recover_with_credential_pool()`
- `agent/conversation_loop.py` line ~1895 — 调用恢复逻辑
- 覆盖场景：billing(402)/rate_limit(429)/auth(401/403)/image_too_large
- 上下文溢出 → preflight 压缩

**不要重复造轮子。**

---

## Hermes vs Claude Code 关键架构对比（2026-05-18）

### 规模对比

| 指标 | Claude Code | Hermes |
|---|---|---|
| 语言 | TypeScript (Bun) | Python |
| 入口文件 | main.tsx 4,683行 | cli.py 14,379行 / run_agent.py 4,094行 |
| 核心循环 | query.ts 1,729行 (async generator) | conversation_loop.py 4,058行 (同步while) |
| 工具执行 | StreamingToolExecutor ~300行 | tool_executor.py 920行 (ThreadPool) |
| 对话压缩 | compact.ts 200+行 | context_compressor.py 1,699行 |
| Hooks | hooks.ts 200+行 | shell_hooks.py 836行 |
| 代码总量 | ~512K 行 | ~50K 行 |

### Hermes 已经做得更好的

| 功能 | Hermes 实现 | Claude Code 对应 |
|---|---|---|
| **错误自动恢复** | 完整错误分类 + 凭证池 + 降级 | 基础重试 |
| **Checkpoint** | 文件修改前快照 | 无 |
| **Daemon系统** | daemon_scheduler + daemon_tool | 无（Claude Code 只有 cron） |
| **Loop内置Planning** | conversation_loop 两处注入 | Claude Code 需要手动 /plan |

### P0 差距（已完成：StreamingToolExecutor）

**1. 流式工具执行 ✅ 已实现（2026-05-18）**
- Claude Code: `StreamingToolExecutor`，LLM边输出token边启动工具
- Hermes: `agent/streaming_tool_executor.py`（329行新建）
- 改动：`agent/chat_completion_helpers.py` 注入 `streaming_tool_callback`，`_call_chat_completions` 和 `_call_anthropic` 均支持
- 注入点：OpenAI path 在 tool name 首次出现时；Anthropic path 在 `input_json_delta` 累积后 JSON 解析成功时

**关键 bug：RLock 死锁**
- 根因：`_run_tool` 在 ThreadPoolExecutor 线程中执行 `_invoke_tool` 后，尝试获取 `self._lock` 更新状态；但 `add_tool`（主线程）已持有同一把锁，导致子线程等待主线程释放 → 死锁
- 修复：`threading.Lock()` → `threading.RLock()`
- 验证：单工具测试通过，并发读工具 0.16s < 0.25s 串行基准 ✓

**并发规则**：
- 只读工具（grep/read_file/glob 等）可并行，写工具（terminal/edit_file/write_file 等）独占
- 任意工具出错立即 sibling abort 取消其他并发兄弟
- 结果按提交顺序返回，与 LLM 输出顺序对齐

**2. 权限模型深度**
- Claude Code: Zod校验→tool自检→pre hooks→canUseTool→post hooks（6层）
- Hermes: Guardrails + PreToolHooks + 插件（3层）
- 改动：`agent/tool_guardrails.py` 扩展为完整权限链

### P1 差距（已完成：Task System + Hooks）

**3. Async Generator 架构**
- Claude Code: `async function* yield` 驱动全链路
- Hermes: 回调(callback)驱动
- 改动：`run_conversation()` 改为 async generator
- 状态：conversation_loop 已改造（流式注入完成，generator 改造进行中）

**4. 多Agent Task系统 ✅ 已实现（2026-05-18）**
- Claude Code: 文件锁+原子claim+级联清理 (`src/utils/tasks.ts`)
- Hermes: `agent/task_system.py`（605行新建）
- 已集成：`tools/delegate_tool.py`，子 agent 执行时 claim/update/release task
- Hook 触发：`task_created` / `task_blocked` / `subagent_start` / `subagent_complete`

**5. Hooks 扩展 ✅ 已实现（2026-05-18）**
- Claude Code: 30+ 生命周期事件
- Hermes: `hermes_cli/plugins.py` VALID_HOOKS 从 18 → 36 个
- 新增：`task_created` / `task_blocked` / `subagent_start` / `subagent_complete` / `pre_compact` / `post_compact` / `permission_denied` / `permission_granted` / `tool_call_failure` / `budget_exceeded` / `user_prompt_submit` / `teammate_idle` / `cwd_changed` / `file_changed` / `instructions_loaded` / `on_setup` / `on_stop` / `on_stop_failure`

### 源码规模参考（用于评估改动成本）

```
Hermes 核心文件：
  cli.py                          14,379 行
  run_agent.py                     4,094 行
  agent/conversation_loop.py        4,058 行
  agent/tool_executor.py             920 行
  agent/context_compressor.py        1,699 行
  agent/shell_hooks.py                836 行
  model_tools.py                      899 行
  toolsets.py                         866 行

Claude Code 对应：
  src/main.tsx                      4,683 行
  src/query.ts                      1,729 行
  src/services/tools/toolExecution.ts 1,745 行
  src/services/tools/StreamingToolExecutor.ts ~300 行
  src/services/compact/compact.ts    200+ 行
  src/utils/tasks.ts                  862 行
```

---

## 常见源码位置速查（更新）

| 功能 | 文件 | 关键行/备注 |
|------|------|-------------|
| 主循环入口 | agent/conversation_loop.py | 532, while 主循环 |
| Preflight压缩 | agent/conversation_loop.py | 356-424 |
| API调用+错误恢复 | agent/conversation_loop.py | ~1880-1930 |
| 工具执行引擎 | agent/tool_executor.py | 920行，ThreadPoolExecutor，8 workers |
| 流式工具执行 | agent/streaming_tool_executor.py | 329行新建，RLock并发控制 |
| 工具注册 | tools/registry.py | 42-70 |
| 工具定义 | model_tools.py | 899行，discover_builtin_tools() |
| 对话压缩 | agent/context_compressor.py | 1699行，4种策略 |
| Hooks | agent/shell_hooks.py | 836行，JSON协议 |
| Hooks(扩展) | hermes_cli/plugins.py | VALID_HOOKS 36个 |
| Skill加载 | agent/skill_commands.py | 斜杠命令解析 |
| Task系统 | agent/task_system.py | 605行新建，文件锁+原子claim |
| Cron调度 | gateway/run.py | ~16600 |
| Daemon调度 | cron/daemon_scheduler.py | 630行 |
| 错误分类 | agent/error_classifier.py | 345行 |
| 凭证池恢复 | agent/agent_runtime_helpers.py | 537行 |
| Checkpoint | agent/checkpoint.py | 文件快照管理 |
| CLI入口 | cli.py | 14379行 |
| Agent入口 | run_agent.py | 4094行 |
| chat completion | agent/chat_completion_helpers.py | 2055行，streaming_tool_callback |
| delegate_tool | tools/delegate_tool.py | 2796行，task_id集成 |

## 重要原则

1. **先读再改**：永远先用子代理读懂源码，再动手
2. **最小侵入**：找最少的改动点，能 hook 就不新建
3. **语法验证**：每次 patch 后立刻 py_compile
4. **循环导入检查**：gateway/cron/agent 三者之间的导入关系要清晰
5. **自注册优先**：新工具尽量用 `registry.register()` 自注册，避免改 registry.py

## 会话恢复工作流（2026-05-18 新增）

当用户说"继续之前的工作"时，按以下顺序检查：

### 第一步：定位最近会话
```
session_search(limit=3)  → 找到最近会话ID
session_search(query="<相关关键词>")  → 精确定位目标会话
```

### 第二步：识别工作状态
- 查看会话 summary 中的"未完成"部分
- 用 git status 检查是否有未提交的改动
- 用 tail -30 ~/.hermes/logs/agent.log 确认系统运行状态
- 检查 ps aux | grep hermes 确认进程状态

### 第三步：验证文件存在性
```bash
# 检查是否已建目标文件
ls -la ~/.hermes/hermes-agent/agent/task_system.py
ls -la ~/.hermes/hermes-agent/agent/streaming_tool_executor.py

# 检查是否已集成到核心文件
grep -r "StreamingToolExecutor\|TaskSystem" ~/.hermes/hermes-agent/run_agent.py
```

### 第四步：确认系统正常运行
```bash
ps aux | grep hermes | grep -v grep  # Hermes进程
tail -5 ~/.hermes/logs/agent.log      # 最新日志
tail -5 ~/.hermes/logs/gateway.log    # Gateway状态
```

### 关键教训
- **工作可能在会话截断前已完成**：summary 说"未开始"不代表没做，要验证文件是否存在
- **已完成的改动会自动commit**：StreamingToolExecutor + TaskSystem 在截断前已完成实装，只是未提交
- **向老板汇报时不说过程**：直接说结果（✅ 已完成/✅ 已提交）

---

## 已验证技术要点（2026-05-18）

### StreamingToolExecutor 并发规则
- 只读工具 frozenset：grep / glob / read_file / search_files / web_search 等
- 写工具由 `_is_write_tool()` 判定：terminal / edit_file / write_file 等
- `interruptible_streaming_api_call` 是**同步函数**（`def`，非 `async def`）
- Anthropic path 无 `content_block_stop` 事件，靠 `input_json_delta` 累积后 JSON 解析成功判断 block 完成
- `streaming_tool_callback` 签名：`callable(tool_call_id, function_name, arguments)`，在 `chat_completion_helpers.py` 中被 try/except 包裹，**异常不传播且无日志**（2026-05-18 发现）

### ⚠️ 潜在风险：streaming_tool_callback 异常静默
- 位置：`agent/chat_completion_helpers.py` line ~1456-1464
- 问题：`except Exception: pass` 吃掉了所有异常，无日志，无重试
- 影响：工具执行失败时用户看不到错误，只能从日志推断
- 建议：如需调试，临时改 `except Exception as e: logger.warning(...)`

### RLock 死锁 bug 与修复
- 症状：单元测试卡住，未打印 "after add_tool"
- 根因：`add_tool` 在主线程持有 `self._lock`，调用 `ThreadPoolExecutor.submit(_run_tool)` 后，`_run_tool`（子线程）执行完 `_invoke_tool` 后尝试获取 `self._lock` 更新状态，但锁已被主线程持有 → 死锁
- 修复：`threading.Lock()` → `threading.RLock()`（同一线程可重复获取）
- 教训：在有 ThreadPoolExecutor 的类中，如果子线程会更新共享状态，锁必须用 RLock

### Task System 关键实现
- 存储路径：`~/.claude/config/tasks/{taskListId}/`
- 文件锁：proper-lockfile，最多重试30次，指数退避
- 原子 claim：`claim_task()` 先读后写，全在锁内
- 级联清理：`delete_task()` 自动清理其他任务中对自身的 blocks/blockedBy 引用
- hook 调用：fire-and-forget（`invoke_hook` 在新线程执行），避免循环依赖

### Hook 扩展（VALID_HOOKS 18→36）
- 不要在 `plugins.py` 中直接 import `task_system`（循环依赖）
- 通过 `shell_hooks.invoke_hook()` 在新线程中调用，保持解耦
- 新增 hook 均已注入：task_created / task_blocked / subagent_start / subagent_complete / pre_compact / post_compact / permission_denied / permission_granted / tool_call_failure / budget_exceeded / user_prompt_submit / teammate_idle / cwd_changed / file_changed / instructions_loaded / on_setup / on_stop / on_stop_failure

---

## cc-haha 架构精髓（可迁移到 Hermes）

> 来源：NanmiCoder/cc-haha (11k stars, Claude Code 泄露源码修复版)

### 核心思想：分层解耦

cc-haha 实现 Computer Use 的方式：**不改原始接口和安全机制，只换底层实现**。

```
Layer 1 — MCP 工具定义（24个schema）← 不改
Layer 2 — 安全关卡（9层）← 不改
Layer 3 — 会话上下文 ← 不改
Layer 4 — CLI集成 ← 不改
Layer 5 — Python桥接 ← 替换底层
Layer 6 — 执行层（pyautogui/mss）← 替换底层
```

**对应 Hermes 的思路**：换 skill 执行层不换 skill 协议，换 model provider 不换调用接口。

### Python Bridge 跨语言通信

cc-haha 用 JSON RPC 连接 TypeScript (Bun) 和 Python (pyautogui/mss)：
- venv 隔离管理，带引导流程（检查/创建venv → 检查pip → 安装依赖）
- 所有屏幕控制指令走这个桥

**对 Hermes 的意义**：Hermes 的 computer use 也可以这样解耦——Python 执行控制，TS 只做调度。

### 9层安全关卡体系（可直接复用思路）

| 关卡 | 作用 |
|------|------|
| Kill Switch | 硬编码 `return true` 绕过灰度 |
| TCC权限 | Accessibility + Screen Recording |
| 全局互斥锁 | 文件锁防止并发 |
| 前台应用检查 | 当前应用必须在白名单 |
| 权限等级 | read < click < full 三级 |
| 像素验证 | 对比截图防变化 |
| 系统快捷键拦截 | 阻止⌘Q等 |

### 应用分类系统（191个 Bundle ID）

55个浏览器 / 102个终端 / 34个交易 / 完全禁止类。权限等级和白名单映射可直接迁移到 Hermes computer use 能力中。

---

## Plugin 热重载（待实现）

### 现状

Hermes 已有 `/reload-skills` 和 `/reload-mcp`，但**没有 `/reload-plugins`**。

plugin manager 有 `stop()/start()` 方法（`hermes_cli/plugins.py`），只差 CLI 入口。

### 待加功能

1. **`/reload-plugins` 命令**：仿 `reload-skills`，调用 `get_plugin_manager().stop()` + `start()`
2. **Plugin 目录文件监控**：仿 `_check_config_mcp_changes()`，监控 `~/.hermes/plugins/` 目录，新加/删除插件时自动重载

### 注入点

- 命令注册：`hermes_cli/commands.py` 的 `COMMAND_REGISTRY`
- 处理逻辑：`cli.py` 的 `process_command()`，elif 分支加在 `reload-skills` 后面
- 文件监控：参考 `_check_config_mcp_changes()` (cli.py line 9371)，对 `~/.hermes/plugins/` 做 stat 监控
