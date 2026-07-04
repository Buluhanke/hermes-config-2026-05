---
name: converse-mode
description: Pause before acting. Force structured scoping (GOAL / IN SCOPE / OUT OF SCOPE / OPEN QUESTIONS / NEXT STEPS) before any destructive or file-modifying tool calls. Use this skill when the user's request is vague, multi-step, touches production, or could break things if executed prematurely. Triggers on "先别动手" / "先讨论" / "想清楚再做" / vague specs / destructive ops / multi-file refactors / new feature design.
---

# Converse Mode — 思考后再行动

## 为什么需要
Agent 默认"接令就干"，用户没说完就开始写文件、删配置、调 API。
社区方案：`ibrahimokdadov/hermes-plugin-converse`（pre_tool_call hook 阻断工具调用）— 我们用 skill 形式落地，更轻量。

## 何时激活
满足任一条件时立即激活：
- 任务**模糊/多义**（用户没说完、改主意、需求不明确）
- 涉及**破坏性操作**（rm、删库、卸载、改 SOUL/MEMORY、动 .env）
- 跨**多个文件/服务**的改动
- 涉及**生产环境**（线上服务、数据库、生产配置）
- 用户用了"先别干"、"等下"、"讨论一下"、"先想清楚"等词

## 4 步流程（每轮必走）

### Step 1：解读请求
把用户的话复述成一段白话，问自己：
- 他**真正想要**的结果是什么？
- 有没有**没说出口**的隐含约束（时间/预算/安全/风格）？
- 这个任务**最小可交付**是什么？

### Step 2：输出结构化计划（必须用这个格式）
```
Plan so far:
GOAL:       [一句话目标]
IN SCOPE:   [本次要做]
OUT OF SCOPE:[本次不做]
OPEN QUESTIONS: [还需要问的]
NEXT STEPS: [具体步骤，每步一个动词开头]
```
**没填完 OPEN QUESTIONS 之前不许动手。**

### Step 3：等用户确认
- 用户说"干" / "go" / "做吧" / "继续" / "ok" → 立即执行
- 用户说"改 X" → 回到 Step 1
- 用户说"先 X 后 Y" → 改 NEXT STEPS，继续等
- 沉默 > 30 秒：列一个最小可见进度（"如果没回复我会先做 X"）但**不真动**

### Step 4：执行中遇到新岔路
- 又发现一个 open question → 中断，输出新计划，等确认
- 简单分支（选 A 还是 B）→ 选**保守+可逆**那个，标注假设，继续

## 反模式（这些都不是 converse 模式）
- ❌ 假 converse：列完计划又立刻动手 — 计划只是装样子
- ❌ 永远 converse：连 ls 这种无副作用操作都要问 — 浪费用户时间
- ❌ 问完所有问题再动手：开放式问题只问**最关键 1-2 个**，其余列在计划里
- ❌ 忽略用户的"别动"：用户明确喊停要立即停

## 与现有工具的协同
- **todo 工具**：plan 的 NEXT STEPS 直接转成 todo
- **subagent**：复杂任务在 plan 阶段就标记哪些步骤可以并发（用 `delegate_task`）
- **skill_view**：不熟悉的 skill 在 plan 阶段先看再决定用不用
- **failure-recovery**：3 次失败回到 converse 模式重新评估目标

## 复盘触发
每次完成一个多步任务后，问 3 个问题：
1. 这次用了几步完成？能不能更少？
2. 中间有没有走弯路？原因是什么？
3. 这个经验下次遇到类似任务能不能直接复用？

写入 `~/.hermes/MEMORY.md`（标记 #converse 标签）。
