---
name: llm-wiki-maintenance
description: |
  LLM Wiki 维护宪章 — Karpathy LLM Wiki 模式的 Hermes 实现。
  Use when: 用户说"这个记一下"、"存到笔记里"、"以后查"、
  或者 Hermes 主动判断某条信息值得持久化到知识库时触发。
  本skill定义了 Hermes 如何维护 Obsidian 知识库的根本原则。
license: MIT
metadata:
  author: karpathy-llm-wiki (adapted for Hermes)
  version: "1.0.0"
---

# LLM Wiki 维护宪章

## 核心理念

> **LLM Wiki 不是 RAG。**
> - RAG：每次从原始文档重新检索，无积累
> - Wiki：知识只编译一次，持久保存，交叉引用已存在，
>   矛盾会被标记，综合分析已反映所有已读内容
>
> Wiki 是一个**持久复合的产物**，每新增一个来源、每回答一个问题，都让它更丰富。

## 三层架构

### Layer 1: 原始来源（Raw Sources）
- 位置：`~/Obsidian/迅龙贸易/sources/`
- 内容：网页截图、PDF、聊天记录截图、文档
- **原则**：不可变。Hermes 只读取，不修改
- 命名规范：`YYYY-MM-DD_来源平台_主题.扩展名`

### Layer 2: Wiki 页面（The Wiki）
- 位置：`~/Obsidian/迅龙贸易/wiki/`
- 内容：Hermes 根据 sources 生成的摘要、实体页、概念页、对比页
- **原则**：Hermes 全权拥有此层，负责创建、更新、维护交叉引用
- 页面类型：
  - `entity/` — 供应商、产品、联系人实体
  - `concept/` — 概念、流程、行业知识
  - `comparison/` — 对比分析表
  - `source-summary/` — 原始来源摘要

### Layer 3: Schema（工作宪章）
- 本文件即 Schema
- 定义：wiki 结构、工作流程、维护规范
- **与用户共同演化**

## 核心操作

### Ingest（摄入新来源）
1. 用户说"记一下"或 Hermes 主动判断信息有价值
2. 将原始内容存入 `sources/`
3. Hermes 生成摘要存入 `wiki/source-summary/`
4. 更新相关实体页（可能涉及 3-5 个已有页面）
5. 更新 `index.md` 索引
6. 追加 `log.md` 记录

### Query（查询）
1. 搜索相关 wiki 页面
2. 读取相关页面的摘要和引用
3. 综合回答，标注来源
4. **重要**：如果回答质量高，将回答本身存入 wiki（探索性内容 → 持久知识）

### Lint（健康检查）
定期执行（建议配合 cron 每日一次）：
- 检查矛盾页面（同一事实说法不一）
- 标记过时内容（被新来源更新）
- 找出孤立页面（无导入链接）
- 补充缺失的交叉引用
- 发现可 web 搜索填补的空白

## 索引与日志

### `index.md`
内容导向，每个页面一条记录，含链接、一句话摘要、元数据。

### `log.md`
按时间顺序的只追加记录，格式：`## [YYYY-MM-DD] [操作类型] [主题]`

## 适不适合存入 wiki

**值得存入：**
- 供应商报价单和交期（长期参考）
- 行业知识（义乌快递、政策、工艺）
- 老板偏好和习惯（"老板要什么档次"）
- 流程经验（"1688询价标准流程"）
- 教训（"XX供应商踩过坑"）

**不值得存入：**
- 一次性信息（今天的天气）
- 完全通用无需记忆的内容
- 纯临时任务状态

## 分工原则

- **人类**：筛选来源、引导分析方向、问好问题、思考意义
- **Hermes**：其他一切——读取、总结、编写、更新、交叉引用

## 与 Obsidian 的结合

- Obsidian 是 IDE，Hermes 是程序员，wiki 是代码库
- Graph View 是检查 wiki 健康度的最佳工具
