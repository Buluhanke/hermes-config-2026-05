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

## 常见源码位置速查

| 功能 | 文件 | 关键行 |
|------|------|--------|
| 主循环入口 | agent/conversation_loop.py | 532 |
| Preflight压缩 | agent/conversation_loop.py | 356-424 |
| API调用+错误恢复 | agent/conversation_loop.py | ~1880-1930 |
| 工具注册 | tools/registry.py | 42-70 |
| Cron调度 | gateway/run.py | ~16600 |
| Daemon调度 | cron/daemon_scheduler.py | 630行 |
| 错误分类 | agent/error_classifier.py | 345 |
| 凭证池恢复 | agent/agent_runtime_helpers.py | 537 |
| 状态存储 | agent/state/ | AppState.tsx |

## 重要原则

1. **先读再改**：永远先用子代理读懂源码，再动手
2. **最小侵入**：找最少的改动点，能 hook 就不新建
3. **语法验证**：每次 patch 后立刻 py_compile
4. **循环导入检查**：gateway/cron/agent 三者之间的导入关系要清晰
5. **自注册优先**：新工具尽量用 `registry.register()` 自注册，避免改 registry.py

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
