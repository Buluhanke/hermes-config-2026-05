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

## 权威源直取（第一步必做，先于 web_search）

每天自学**先跑结构化拉取脚本**，直接吃全网最前沿，再用 web_search 补充。不要只靠关键词碰运气。

```bash
python3 ~/.hermes/scripts/frontier_sources.py --days 2
```

三个源（2026-11-22 实测可用）：
- **arXiv API**（https 端点，双端点重试）：cs.AI/cs.CL/cs.LG 最近论文，命中 agent/memory/harness/self-improv 等关键词高亮
- **Papers with Code**（paperswithcode.co/api/v1）：最新论文+代码源
- **Awesome-AI4AI**（走 `gh api`）：每周更新的 1148 篇策划论文+高引榜单，抓最新条目和高引行

Hugging Face `daily_papers` 若直连报 SSL 握手失败/EOF，直接跳过用它——Papers with Code 已覆盖同类论文+代码信息，不必为它重试。网络恢复后可以再加回来作为第四源。

脚本零依赖（stdlib + gh CLI），输出精简 markdown；加 `--json` 出结构化数据，`--source arxiv|pwc|ai4ai` 单拉。
从三源里挑有数字/框架名/方法的条目，按下方标准写 fact_store。

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
