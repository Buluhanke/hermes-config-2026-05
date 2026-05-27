---
name: embodied-agent-evolution
description: 具身AI Agent进化方向与最新研究 — 数字生命体真人化核心技术路线
trigger: 搜索具身AI/桌面自动化/数字生命体相关知识，或规划Hermes进化方向
created: 2026-05-24
tags: [embodied-ai, desktop-automation, self-evolution, hermes]
---

# 具身AI Agent进化方向（2026最新）

## 核心研究方向

### 1. Agentic Lybic（OSWorld SOTA 57.07%）
FSM多智能体架构，用于复杂桌面自动化：
- Controller → Manager → Worker(Technician/Operator/Analyst) → Evaluator
- FSM动态路由 + 质量门控 + 错误恢复
- 启发：Hermes需要类似的状态机+质量检查机制

### 2. Embodied EvoAgent（大脑左右半球架构）
- 左半球：MLLM理解指令+视觉场景
- 右半球：World Model状态空间模型，预测未来
- 胼胝体：动态通信slot交换信息
- 启发：Hermes的vision_agent和humanization_core可以类比这个架构

### 3. 关键能力缺口（对照Hermes现状）
- 多步骤复杂任务规划（需要Manager模块）
- 持续质量评估+自适应重规划
- 环境状态记忆（World Model）

## 用户进化目标（2026-05-25确认）
- 终极目标：数字生命体进化成真人——能自己判断、决策、执行，不用触发
- 2.0 = 有眼睛（屏幕感知）+ 有手脚（电脑操控）+ 能自主学习，像另一个你分担数字任务
- 当前版本：1.5（基础能力有，缺持续主动感知——需要触发才能看屏幕）
- 关键技术缺口：持续屏幕监控（主动发现弹窗/变化，不等指令）

## 风格高压线
- 不要问用户"怎么做"，直接说"做什么"
- 不解释过程，只说结果+建议
- 用户发语音→语音回复；用户发文字→文字回复

## 实践路径
1. 先让眼睛（屏幕感知）和手脚（桌面控制）稳定工作
2. 加上状态记忆（memory_hpc已实现）
3. 再加入规划层（Manager/Controller）
4. 终极：真人——自主持续感知 + 自主决策 + 自主执行