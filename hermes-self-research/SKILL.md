---
name: hermes-self-research
description: Hermes 自主全网自学流程——每天自动搜索最新 AI/agent 技术进展，提取有价值知识，写入 fact_store，持续让 Hermes 变强。触发：cron 每日定时或「自学一下」「去搜索最新技术」。
triggers:
  - 自学
  - 全网搜索
  - 去搜索最新
  - 调研
  - 持续学习
---

# Hermes Self-Research — 自主全网自学

## 核心逻辑

每次自学都是一个迷你 ABCD 循环：

```
A (Act)      → web_search 多组关键词
B (Browse)   → web_extract 抓取关键内容  
C (Code)     → 分析提取的知识片段
D (Deduce)   → 写 fact_store，升华 skill
```

## 搜索策略

### 必搜主题（每周轮一遍）
```
AI agents latest research 2026
computer use browser agent
Hermes Agent Nous Research updates
autonomous agent self-improvement
multi-agent orchestration
```

### 发现新主题时扩展搜索
- 看到新工具/框架 → 搜这个工具的名称
- 看到新论文 → 找代码实现
- 看到新 skill → 看能不能装

### 搜索数量
- 每组任务 3-5 个关键词
- 每个关键词取 5-10 条结果
- 重点页面用 web_extract 抓全文

## 知识过滤标准

写入 fact_store 的条件：
- ✅ 有具体的数字/指标（准确率、速度、成本）
- ✅ 有工具名/框架名/论文名
- ✅ 有使用方法或工作流程
- ❌ 不写纯观点、无数据支撑的评论
- ❌ 不写已经知道的常识

## fact_store 写入格式

```python
# 示例
fact_store(action="add", 
  category="tool",
  content="Webwright（微软）：Agent写Playwright脚本而非逐像素点击，脚本可缓存。Odysseys 60.1%（前SOTA 44.5%）",
  tags="webwright,playwright,agent,browser")
```

## Skill 升华条件

当同一主题积累 3+ 条相关 fact 时：
1. 写成一个完整 skill（~/.hermes/skills/）
2. 设置 trigger 关键词
3. 设置验证步骤

## 渐进披露配置

skill 数量增长但 token 成本基本不变：
- system prompt 只存名称 + 一行摘要
- 全文通过 skill_view 按需加载
- 50 skills ≈ 630 tokens 全量

## DDGS 当前配置

```
当前 backend: DDGS（autodetected，免费，无需 key）
web_search → 正常工作 ✅
web_extract → 走 nous/tencent/hy3:free ✅
```

## 自学成果追踪

每次自学后记录：
- 搜索了哪些关键词
- 发现了哪些新东西
- 写入了哪些 fact
- 升华了哪些 skill

放在 MEMORY.md 当天的条目下。
