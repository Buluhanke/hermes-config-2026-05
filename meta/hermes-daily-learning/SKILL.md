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
| AgentSkills.io | agentskills.io（500+社区技能，可直接导入） |
| 虾评 | xiaping.coze.com（470+精品Skill，有排行榜和评测） |
| SkillHub | skillhub.cn（Top 50） |

导入社区技能：`hermes skills import <name>`，观察 Hermes 如何在使用中自动优化。

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

## 六、GitHub 优质项目研究法

研究新项目时的标准流程：

```
1. git clone --depth=1 <repo> 到 /tmp
2. ls 查看结构，找 SKILL.md / README.md / scripts/
3. 读 SKILL.md（描述核心价值）+ README（前100行了解能力）
4. 扫关键脚本（cdp-proxy.mjs 等核心实现）
5. 识别：对 Hermes 的价值（直接可用 / 思路借鉴 / 架构参考 / 存档）
6. 判断优先级：Tier1（直接可用）/ Tier2（思路借鉴）/ Tier3（存档）
```

**"对我们有什么用处？"** 这个问题是过滤标准——不是所有项目都要深究。

### 本次研究存档

| 仓库 | 价值 | Tier |
|------|------|------|
| claude-code (freestylefly) | 架构参考：12阶段渐进式构建 | Tier1 |
| awesome-selfhosted | 榜单设计思路可用 | Tier2 |
| agent-browser-runtime | Docker 架构不适用，思路存档 | Tier2 |
| eze-is/web-access | 浏览器 Skill，CDP Proxy，本地书签/历史检索，站点经验积累 | Tier2 |
| Tencent/TencentDB-Agent-Memory | 记忆分层架构（L0→L1→L2→L3），Mermaid符号化压缩，33-61% token节省 | Tier1 |
