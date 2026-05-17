---
name: voyager
description: Minecraft终身学习Agent，GPT-4驱动，Skill Library持续扩充
version: 1.0.0
category: autonomous-ai-agents
---

# Voyager

## When to Use
当需要在Minecraft中实现自主探索、任务规划和技能获取时使用。适合研究具身AI学习和持续学习能力的场景。

## Core Features
- **终身学习架构**：通过"学徒-熟练-专家"三阶段逐步提升技能
- **Skill Library**：从零构建可复用的技能库，积累环境交互经验
- **GPT-4驱动**：使用GPT-4作为核心推理引擎，支持复杂任务分解
- **自动课程学习**：根据环境反馈自动调整学习路径
- **代码生成执行**：生成Python/JS代码操作游戏环境并验证

## Quick Start
```bash
# Voyager基于Mineflayer构建
pip install minerl

# 启动 Voyager
python -m voyager

# 设置API Key
export OPENAI_API_KEY=your_key
```

## Pitfalls
- 需要OpenAI API配额，成本较高
- Minecraft版本兼容性（推荐1.17.1）
- 技能库膨胀后检索效率下降
- 网络延迟影响实时交互
