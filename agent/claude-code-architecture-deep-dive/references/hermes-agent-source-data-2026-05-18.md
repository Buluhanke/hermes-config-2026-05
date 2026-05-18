# Hermes Agent 源码关键数据（2026-05-18）

来源：本次会话实地读取 `/Users/aimac/.hermes/hermes-agent/` 核心文件

## 核心文件规模

| 文件 | 行数 | 职责 |
|------|------|------|
| cli.py | 14,379 | CLI 入口，Rich + prompt_toolkit，命令分发 |
| run_agent.py | 4,094 | AIAgent class，client 创建，消息处理 |
| agent/conversation_loop.py | 4,058 | 主对话循环，消息构建，错误恢复，压缩触发 |
| agent/context_compressor.py | 1,699 | 对话压缩，4种策略，token 预算 |
| agent/tool_executor.py | 920 | 并发工具执行，ThreadPoolExecutor，8 workers |
| agent/shell_hooks.py | 836 | Shell hook 桥接，JSON 协议，权限检查 |
| model_tools.py | 899 | 工具编排，handle_function_call()，异步循环 |
| toolsets.py | 866 | 工具集定义，_HERMES_CORE_TOOLS 列表 |
| agent/error_classifier.py | 345 | 错误分类，billing/rate_limit/auth/image |
| hermes_state.py | 2,966 | SQLite session 存储，FTS5 搜索 |

## agent/tool_executor.py 核心结构

```python
_MAX_TOOL_WORKERS = 8  # 最大并发线程数

execute_tool_calls_concurrent(agent, assistant_message, messages, effective_task_id)
  → _run_tool() worker function
  → agent._invoke_tool(function_name, function_args, ...)
  → concurrent.futures.ThreadPoolExecutor(max_workers=8)
  → contextvars.copy_context() 传播 ContextVars
  → agent._touch_activity() 心跳保活

# 工具执行前检查链：
1. checkpoint_mgr（文件快照）
2. get_pre_tool_call_block_message()（插件 block）
3. agent._tool_guardrails.before_call()（权限 guardrails）
4. agent._guardrail_block_result()（block 结果）
```

**与 Claude Code 的关键差异：**
- Hermes：等 LLM 完全输出 → ThreadPoolExecutor 并发执行
- Claude Code：StreamingToolExecutor，LLM 边输出 token 边启动工具

## agent/conversation_loop.py 核心结构

```python
run_conversation(agent, user_message, system_message, conversation_history, task_id)
  → 预检：sanitize、stream_callback、task_id、retry counters
  → 消息初始化：messages = list(conversation_history)
  → 系统提示：agent._cached_system_prompt（首次构建，后续复用）
  → 构建 user_msg，加入 messages
  → while(api_call_count < max_iterations):
      → api_messages = build_api_messages(messages, ...)
      → response = _interruptible_api_call(api_messages, ...)
      → if response.tool_calls:
          → execute_tool_calls_concurrent() 或顺序执行
          → messages.append(tool_result_messages)
          → api_call_count++
      → else:
          → return response.content
  → 压缩检查：context_compressor.compress_if_needed()
  → post-turn hooks
```

**关键设计：**
- 同步 while 循环（Claude Code 是 async generator）
- 回调驱动（Claude Code 是 yield 事件驱动）
- preflight 压缩在循环前
- 错误恢复内嵌在循环内（credential pool fallback）

## agent/context_compressor.py 核心结构

```python
# 4种压缩策略（与 Claude Code 完全对应）
1. Session Memory Compaction — 直接存文件，不调 LLM
2. Microcompaction — 剥离图片后轻量压缩
3. Traditional Compaction — LLM 全量摘要
4. Reactive Compaction — 收到 prompt_too_long 后自动触发

# 关键常量
_MIN_SUMMARY_TOKENS = 2000
_SUMMARY_RATIO = 0.20
_SUMMARY_TOKENS_CEILING = 12_000
_IMAGE_TOKEN_ESTIMATE = 1600  # 与 Claude Code 相同
```

## agent/shell_hooks.py 核心结构

```python
# Wire 协议
stdin: JSON {hook_event_name, tool_name, tool_input, session_id, cwd, extra}
stdout: JSON {decision: "block"/"allow", reason: str} 或 {context: str}

# 支持事件（部分）
- pre_tool_call: 返回 block 可以阻止工具执行
- pre_llm_call: 返回 context 可以注入上下文
- post_tool_call: 工具执行后通知
- on_error: 错误发生时通知

# Exit code 语义
0: 成功
2: 阻塞错误（影响模型行为）
其他: 报告给用户，不影响模型
```

## Hermes 权限链（当前实现）

```
tool_executor._run_tool()
  → checkpoint_mgr.ensure_checkpoint()（写文件前快照）
  → get_pre_tool_call_block_message()（插件预检）
  → agent._tool_guardrails.before_call()（权限 guardrails）
    → tool_dispatch_helpers._is_destructive_command()
    → tool_result_classification 分类
  → agent._invoke_tool()
    → tools.registry.registry[function_name].handler()
    → maybe_persist_tool_result()（大结果写磁盘）
```

**对比 Claude Code（6层）：**
Claude Code 多一层 `canUseTool()` 细粒度权限决策，且支持参数模式匹配（如 `Bash(git *)` 自动允许）。

## Skill 系统（当前实现）

```python
# agent/skill_commands.py
skill_preprocessing.py → 解析 /command args
skill_utils.py → 技能加载工具
skill_commands.py → 注册斜杠命令

# 执行模式
inline: 在当前会话直接执行，共享对话历史
fork: 在独立子 agent 中运行，完全隔离

# 加载路径
~/.hermes/skills/         # 用户自定义
内置 skills/              # repo 内置
optional-skills/          # 可选技能
MCP managed               # MCP 工具生成
```
