---
name: cursor-rules
description: .cursorrules文件写法规范
version: 1.0.0
---

# Cursor Rules — 项目规范文件写法

## When to Use
- 初始化新项目时建立团队编码规范
- 多LLM协作项目中统一响应格式
- 需要AI编程工具深度理解项目上下文时

## Core Features
- **项目规则**：语言/框架/目录结构约定
- **LLM响应格式**：输出模板、注释风格、代码块规范
- **文件约定**：命名规则、import顺序、模块组织
- **任务指令**：迭代方式、评审节点、提交规范

## Quick Start
```bash
# 在项目根目录创建
touch .cursorrules

# 基础结构示例
# 语言与框架
- framework: React + TypeScript
- styling: Tailwind CSS

# 响应格式
- 用中文注释解释复杂逻辑
- 代码块标注语言类型
- 重要决策附带WHY说明

# 文件约定
- 组件放components/，hooks放hooks/
- 测试文件与源码同目录
- 配置文件用 YAML/JSON
```

## Pitfalls
- 规则过细导致AI忽略关键指令
- 未同步更新导致规范与实际脱节
- 禁止性规则过多（"不要用"）降低AI创造力
- 缺少实际代码示例让AI误解意图
