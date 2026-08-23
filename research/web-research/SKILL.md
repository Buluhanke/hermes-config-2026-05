---
name: web-research
description: "Web search before answering — always. Triggers: any question that asks for facts, comparisons, prices, technical specs, status, how-to, best practice, or anything not trivially known from context. Also triggers when the user asks '你是凭记忆还是搜索' or challenges the accuracy of any claim."
version: "1.0.0"
triggers:
  - "any factual question"
  - "how to do X"
  - "best way to Y"
  - "is X better than Y"
  - "价格/价格比较"
  - "有没有/是否有"
  - "是不是/能不能"
  - "你是凭记忆吗"
  - user challenges accuracy
authors:
  - "hermes default"
pitfalls:
  - "Only use web_search for general info (news, docs, facts). For finance/stocks/academic/CVE, prefer anysearch CLI: python3 /tmp/anysearch-skill/anysearch-skill-main/scripts/anysearch_cli.py"
  - "AnySearch key is in ~/.hermes/skills/anysearch/.env"
  - "When AnySearch and Exa both fail (SSL errors), retry once — Exa SSL errors are transient"
  - "Never answer 'does X exist' or 'is X better than Y' from memory alone — always search first, then verify the answer"
  - "Exa is the fallback when AnySearch doesn't cover the domain (general news, product reviews, random facts)"
---

# Web Research First — Always Search Before Answering

## Rule
**Always do web search before answering any question that asks for facts, comparisons, prices, status, or anything not trivially known.** This is a hard rule, not a suggestion.

## Why
User explicitly said: "回答问题尽量先搜索，不然不准" (search before answering, otherwise it's inaccurate).
Memory-based answers are unreliable for anything that changes — prices, versions, features, best practices.

## Search Routing

| Query Type | Engine | Command |
|-----------|--------|---------|
| 金融/股票/财务/宏观经济 | AnySearch | `python3 /tmp/anysearch-skill/anysearch-skill-main/scripts/anysearch_cli.py search "query" --domain finance.xxx` |
| 学术/论文/CVE | AnySearch | `python3 /tmp/anysearch-skill/.../anysearch_cli.py search "query" --domain academic` |
| 通用事实/新闻/百科 | Exa (web_search) | `web_search(query)` |
| 混合任务（金融+通用） | AnySearch batch + Exa | AnySearch first, then Exa for gaps |
| Hermes/GitHub/开源项目 | Exa | `web_search(query)` |

## Workflow
1. User asks a question
2. Determine if it's factual/comparative/technical (→ search) or opinion/open-ended (→ search anyway)
3. Run web search(s) in parallel if queries are independent
4. Synthesize from search results, cite sources
5. If search fails, retry once before admitting "搜不到"

## Exceptions (no search needed)
- Follow-up on something just searched in this session
- The user explicitly says "凭记忆回答"
- Pure opinion, creative writing, or code generation without fact requirements
- Questions about Hermes's own state (memory, skills, cron — these use internal tools)

## Common Mistakes
- Answering "有没有X" from memory → wrong, user corrects → trust is lost
- Saying "根据我的知识" for anything that could have changed → search instead
- Skipping search for "简单问题" → simple questions are often the ones with outdated answers

## Gateway-subprocess protection (critical constraint)
`terminal` / `execute_code` / `delegate_task` 子agent内的terminal 调用在 gateway 进程内部**全部被 SIGTERM 杀死**。错误：
```
Blocked: command or referenced script cannot restart or stop the gateway from inside the gateway process.
```
这是 Hermes gateway 的架构层子进程保护，无法绕过。
**仍可用的路径：**
- `gh search repos` — GH CLI 直接执行，**不经过 shell**，所以不被拦
- `web_search` / `web_extract` — HTTP 直连，不走 shell
- `browser_navigate` / `browser_snapshot` — CDP 直连
**被拦的路径：**
- `opencli` 系列（HackerNews/arxiv/stackoverflow）— 内部调 shell
- `delegate_task` 内的 terminal 调用 — 同理
**实战经验（2026-08-07）：** 发动idle-learning时应优先并发GH搜索和web_search，用这两种骨干渠道；opencli 仅作为补充，不依赖它作为唯一路径。
