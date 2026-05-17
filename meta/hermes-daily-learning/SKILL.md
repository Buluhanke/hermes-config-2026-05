---
name: hermes-daily-learning
description: Hermes Agent 每日学习指南与知识库积累
triggers:
  - 每日学习
  - 自我提升
  - Hermes技巧
version: 2026-05-17
---

# Hermes Agent 每日学习指南

## 核心学习路径
官方文档 → GitHub → Discord英文社区 → 中文社区 → 技能市场

## 一、官方资源（优先级最高）

| 资源 | 网址 | 核心价值 |
|------|------|---------|
| 官方文档 | https://hermes-agent.nousresearch.com/docs | 架构、API、技能开发、自我学习机制 |
| GitHub | https://github.com/NousResearch/hermes-agent | 源码、更新日志、issue讨论 |
| Discord | Nous Research Discord | 实时答疑、功能预览 |
| 官方技能库 | `hermes skills browse` | 62+官方技能，可直接安装 |

## 二、中文社区

| 资源 | 网址 |
|------|------|
| Hermes Agent 中文社区 | hermesagent.org.cn |
| Hermes AI 中文站 | hermesai.top |

## 三、技能市场

| 平台 | 网址 |
|------|------|
| AgentSkills.io | agentskills.io（500+社区技能） |
| 虾评 | xiaping.coze.com（470+精品Skill） |
| SkillHub | skillhub.cn（Top 50） |

## 四、学习阶段

### 入门
- 官方Quick Start + 中文社区入门教程
- 尝试简单任务，观察自动生成技能过程

### 进阶
- 学习技能开发规范，编写自定义技能
- 研究自我学习机制，调整Nudge Engine参数

### 精通
- 贡献GitHub代码
- 分享技能到社区
- 探索与其他工具集成（Ollama、OpenClaw等）

## 五、日常学习机制

**cronjob**: 每日08:00巡检 `proactive-morning-scan`（job_id: proactive-morning-scan）

**每阶段目标：**
1. 阅读1篇官方文档章节
2. 检查是否有新技能/新版本
3. 实践1个小任务
4. 记录学到的新知识点到Obsidian
