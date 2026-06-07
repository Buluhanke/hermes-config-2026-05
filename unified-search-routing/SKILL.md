---
name: unified-search-routing
description: 统一搜索路由 — 所有 hermes agent 调搜索/提取 URL 的唯一入口。封装 anysearch(最强通用聚合搜索) + last30days(过去30天社媒舆情/趋势) + fetch_url v2(Trafilatura 本地提取) 三个引擎,通过 ~/.hermes/scripts/search.py 按查询意图自动路由,带 DiskCache 24h 缓存 + 三层降级。
version: 3.0.0
created: 2026-06-06
updated: 2026-06-07
author: hermes
tags:
  - search
  - routing
  - core
  - anysearch
  - last30days
  - fetch_url
  - trafilatura
  - diskcache
  - cache
trigger_keywords:
  - 搜索/查一下/搜一下/搜个
  - 找资料/找信息/查资料
  - research / lookup / find
  - 最近的舆情/大家怎么看
  - 评测/推荐/价格/参数/怎么/什么
  - 抓页面/读 URL 全文/提取网页
---

# Unified Search Routing — hermes 统一搜索入口

**所有 hermes agent（包括 cron / subagent / 主 agent）调搜索引擎的唯一入口。** 不要直接调 anysearch_cli.py 或 last30days.py——直接调 `search.py` 走自动路由。

## 一句话总结

> `python3 ~/.hermes/scripts/search.py "你的查询"` —— 自动按意图路由到 **anysearch**（通用/事实/参数） 或 **last30days**（过去 30 天舆情/口碑/趋势），并在模糊地带同时跑两个引擎并联补全。URL 提取走 `fetch_url.py`（**Trafilatura 主提取**，不是 html2text），缓存走 **DiskCache**（不是 JSON 文件），全部免费、零付费后端。

**当用户说"升级联网搜索"/"找更强免费方案"/"全网对比"时（进化触发词）**：先跑 `web_search "best free <组件类> 2026"` 4-6 个候选实测替换，不是打补丁（修补 ≠ 进化，详见 §"进化方法论"）。

## 为什么用 search.py 而不是直接调底座

| 调法 | 风险 |
|---|---|
| ❌ `anysearch_cli.py search "..."` | 漏掉社媒舆情（Reddit/X/HN/YouTube 都没） |
| ❌ `last30days.py "..."` | 漏掉通用实时搜索（技术/参数/价格/事实/官方文档） |
| ❌ `web_search` 内置工具 | 质量/新鲜度/去重都不如两个专用引擎 |
| ❌ 装新的搜索引擎 | 重复造轮（已踩坑：SearXNG 自建死胡同） |
| ✅ **`search.py "..."`** | 自动路由 + 并联补充 + 兜底（任何 search 任务都从这一行开始） |

## 路由规则（2026-06-05 QQ 用户拍板的 v2 版）

```
query
 ├─ 含强信号词"舆情/口碑/最近/过去30天/社媒/reddit/hn/twitter" → last30days 主 + anysearch 补充
 ├─ 含强信号词"什么/怎么/推荐/评测/价格/技术/参数/事实/对比" → anysearch 主 + last30days 补充
 └─ 模糊地带（无强信号）→ anysearch 主 + last30days 并联
                              │
                              └─ anysearch 挂了 → agg_search.py (ddgs) 兜底
```

**强信号词完整列表在 search.py 的 `route()` 函数里**（中文按子串匹配、大小写不敏感）。

## 标准调用

```bash
# 默认 5 条结果
python3 ~/.hermes/scripts/search.py "RTX 5090 价格"

# 指定 10 条
python3 ~/.hermes/scripts/search.py "Claude Sonnet 4.7 评测" 10

# 舆情类（自动走 last30days 主路 + anysearch 补充）
python3 ~/.hermes/scripts/search.py "最近大家对 Hermes Agent 怎么看"

# 模糊类（两个引擎并联）
python3 ~/.hermes/scripts/search.py "Mac mini M5 跑 LLM"
```

**返回结构**：主路结果 + 分隔线 + 补充路结果，stdout 直接读，无需 JSON 解析。

## 两个底座引擎的能力边界

### anysearch（通用聚合搜索）— 强在"找事实/参数/技术文档"

| 能力 | 触发 | 例子 |
|---|---|---|
| 通用 web 搜索 | `search "..."` | "Python 3.13 GIL 移除" |
| 垂直域搜索 | `list_domains` 看支持 → `search "Stock:NVDA"` | Stock/CVE/DOI/IATA/patent |
| 批量并行 | `batch_search --queries '[...]'` | 5 个独立查询一起跑 |
| URL 内容抽取 | `extract "https://..."` | 把网页转成 markdown |

**支持 freshness 过滤**：`--freshness day|week|month|year`
**支持内容类型过滤**：`--content_types web,news,code,doc,academic,data,image,video,audio`
**底层**：`https://api.anysearch.com`（JSON-RPC 2.0）
**凭据**：`ANYSEARCH_API_KEY` 可选（无 key 走匿名访问、限速更低）
**CLI 完整路径**：`python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py`
**完整 SKILL**：`~/.hermes/skills/anysearch/SKILL.md`（需要时再读，避免每次调都读）

### last30days（过去 30 天社媒舆情）— 强在"看口碑/找趋势/找案例"

| 数据源 | 例子 |
|---|---|
| Reddit | "r/LocalLLaMA 最近怎么看 Hermes" |
| X / Twitter | "AI agent 圈本月热度" |
| YouTube | "本地 LLM 跑 M4 实测视频" |
| TikTok | 消费/营销话题（创作者 + 标签筛选） |
| Hacker News | 月度 Top AI 工具讨论 |
| Polymarket | 预测市场对某事件的赔率 |
| GitHub | 某 repo/用户最近动态 |
| Web | 普通网页（brave/exa/serper/parallel 4 个后端可选） |

**需要 Python ≥ 3.12**（用 `~/.local/bin/python3.12`，独立 venv 不影响 hermes 主环境）
**支持模式**：`--quick`（低延迟）/ `--deep`（高召回）/ `--debug`
**支持 plan 注入**：`--plan '{"intent":"...","freshness_mode":"month","subqueries":[...]}'`
**可选凭据**（`SCRAPECREATORS_API_KEY` / `OPENAI_API_KEY` / `XAI_API_KEY` 等 12 个 env，缺哪个对应源退化）
**CLI 完整路径**：`python3.12 ~/.hermes/skills/research/last30days-skill-main/skills/last30days/scripts/last30days.py`（**写真路径，不写软链路径**——软链是给用户命令用的，程序内走真路径避免符号链接失效）
**完整 SKILL**：`~/.hermes/skills/research/last30days/SKILL.md`（13.5 万字巨细无遗，需要细节再读）

## 兜底链

```
search.py "..."
  ├─ 路由 anysearch ─┐
  │                  ├─ 正常 → 输出主路 + 补充路
  │                  └─ 异常 → agg_search.py (DDGS) 兜底
  └─ 路由 last30days → 走 last30days 必跑（不兜底，因为社媒舆情无替代）
```

**任何 search 任务的兜底都从 search.py 开始**——你只看到"主路 + 补充路 + 兜底"三层结果，引擎选择是 search.py 的事，不是调用者的事。

## v3 升级（2026-06-07 04:30）：Trafilatura + DiskCache 替换

### 进化方法论（**用户 04:20 拍板的 FIRST-CLASS 规则**）

> **"先用当下的再去全网搜罗比当下更强的更好的也是免费的来替换当下的方案才是进化，而不是在当下的情况不停地找错，这个不是进化，这是修补"**

**修补 vs 进化的区别**：

| 行为 | 修补 | 进化 |
|------|------|------|
| 看到 searxng 后端空 | 写 fetch_url 替代它 | **先问"当下最强免费方案是什么"**，全网搜（`web_search "best free X 2026"`），找到 Trafilatura 替换整个提取器层 |
| 发现缓存慢 | 加 in-memory dict 优化 | 搜全网缓存库（`diskcache`/`cachetools`/`fakeredis`），用 DiskCache 替换 |
| 触发条件 | 用户说"修个 bug" | 用户说"升级"/"找更强的"/"全网对比" |

**铁律**：任何组件要改之前，**先 `web_search "best free <类> 2026"` 跑全网对比**，再决定替换什么，不是直接打补丁。

### v2 → v3 全网对比结果

| 位置 | v2 方案 | 全网最强免费方案 | 验证 |
|------|---------|------------------|------|
| URL 提取 | html2text + stdlib regex | **Trafilatura 2.0.0**（社区基准 #1，击败 readability-lxml/newspaper4k/boilerpipe） | 实测 github.com 提取从"一堆 nav 垃圾"→"项目描述+安装命令" |
| 缓存 | JSON 文件手写 | **DiskCache 5.6.3**（自动 TTL+LRU+原子写+并发安全） | 1000 写 0.063s |
| 搜索主路 | anysearch | 仍是 anysearch（Brave 2026/2 砍免费、SearXNG 公网连不通） | — |
| 搜索兜底 | DDGS + curl HTML | 同上 | — |
| 社媒舆情 | last30days | 没找到更强免费路线 | 保持 |

**排除的候选（实测本机不能跑）**：
- ❌ Jina Reader (`r.jina.ai`) — DNS 解析到 Facebook IP，10s 超时
- ❌ Brave Search API — 2026 年 2 月砍掉免费层
- ❌ SearXNG 公共实例 — 5 个公网实例从本机全部连不通

### v3 升级实际效果

```
fetch_url.py "https://github.com/NousResearch/hermes-agent"  # Trafilatura
  → 输出干净的项目描述、模型支持列表、安装命令（v1 输出一堆 nav 菜单）

search.py "DeepSeek V4 发布"  # DiskCache 缓存
  第 1 次: 4.6s
  第 2 次: 0.035s  ✅ 缓存命中
```

### v3 改动清单

| 文件 | 改动 |
|------|------|
| `~/.hermes/scripts/fetch_url.py` | v1 → v2：Trafilatura 2.0.0 主提取器 + DiskCache 缓存层 |
| `~/.hermes/scripts/search.py` | v3 → v3.1：JSON 缓存 → DiskCache |
| `~/.hermes/cache/fetch_url_v2/` | 新增（v1 的 `fetch_url/` 旧 JSON 已清理） |
| `~/.hermes/cache/search/` | 从 JSON 改为 DiskCache 格式 |

### 路径选择铁律（v1 留下，v3 保留）

**用户管入口用软链，程序内用真路径**：

- 用户命令/CLI 接口 → 走软链（用户体验好，改路径只动软链）
  - `~/.hermes/skills/research/last30days` → 软链 → 真路径
- 程序内部调用 → 写真路径（避开软链失效/被改）
  - `search.py` 里 `LAST30 = ".../last30days-skill-main/skills/last30days/scripts/last30days.py"`

**为什么**：软链是单点故障——指向 `/tmp` 重启就断、指向不存在的目录就死链。程序内部写真路径直接定位，避开符号链接失效。详细踩坑实录见 `references/free-search-stack-2026-06-07.md` §4。

## 反模式（不要做）

- ❌ 在 cron / subagent 里直接调 `anysearch_cli.py` 或 `last30days.py` ——绕过路由规则，容易漏一路
- ❌ 用 hermes 内置 `web_search` 工具做严肃搜索 ——质量/新鲜度/去重都差
- ❌ 装新搜索引擎（SearXNG 自建等） ——踩过坑，重复造轮
- ❌ 让用户选通道 ——用户不参与选通道，Telegram bot / QQ bot / cron 全部默认走 `search.py`
- ❌ 用 `pip3` 给 last30days 装包 ——装到系统 Python 没权限。让 uv 自己选解释器 ——会偷吸 hermes-agent 的 3.11 venv。**永远** `uv pip install --python <具体路径>`。
- ❌ 软链指向 `/tmp` 或 `~/.local/share/` ——macOS 重启就清，或目标根本不存在。**永远**指向 `~/.hermes/skills/research/last30days-skill-main/skills/last30days`。
- ❌ 程序内写真实路径还是软链路径混用 ——统一原则：CLI 入口走软链（用户体验），程序内部写真路径（避开软链失效）。
- ❌ 看到当下方案有问题就直接打补丁 ——**先全网搜"best free X 2026"对比，再决定替换**（用户 04:20 拍板的进化方法论）。修补 ≠ 进化。

## 触发词速查

| 你听到/看到 | 动作 |
|---|---|
| "搜一下 X" / "查 X" / "找 X" | `search.py "X"` |
| "最近大家怎么看 X" / "X 舆情" | `search.py "X"`（自动走 last30days 主路） |
| "X 怎么用" / "X 价格" / "X 评测" | `search.py "X"`（自动走 anysearch 主路） |
| "研究 X" / "深度查 X" | `search.py "X"` 或 `search.py "X" --deep`（手动 deep 模式） |
| cron / 定时任务里要查资料 | `search.py "..."`（直接调，不写 web_search） |
| subagent 收到的 research 子任务 | `search.py "..."` |

## 文件清单

| 路径 | 角色 |
|---|---|
| `~/.hermes/scripts/search.py` | **统一入口**（所有 agent 唯一调这个，v3.1 加 DiskCache + 三层降级） |
| `~/.hermes/scripts/fetch_url.py` | **本地 URL 提取器 v2**（Trafilatura 主提取 + DiskCache 缓存） |
| `~/.hermes/hermes-agent/venv/bin/python` | venv 解释器（fetch_url 跑这，html2text/trafilatura/diskcache 都在） |
| `~/.hermes/skills/anysearch/SKILL.md` | anysearch 完整文档（兜底用） |
| `~/.hermes/skills/research/last30days/SKILL.md` | last30days 完整文档（13.5 万字） |
| `~/.hermes/skills/ddgs-searxng-agg-search/SKILL.md` | agg_search.py 兜底链（DDGS 聚合） |
| `~/.hermes/scripts/agg_search.py` | DDGS 多引擎聚合（anysearch 挂了才用） |
| `~/.hermes/cache/search/` | search 缓存目录（DiskCache，24h TTL） |
| `~/.hermes/cache/fetch_url_v2/` | fetch_url 缓存目录（DiskCache，24h TTL） |
| `references/search-pipeline-architecture.md` | 管道架构图+文件清单+依赖表 |
| `references/last30days-install-and-broken-symlink.md` | **last30days 安装/软链翻车实录+venv 3 坑+升级流程**（用户报告"找不到了"时第一手查这个） |
| `references/free-search-stack-2026-06-07.md` | **免费联网搜索栈实战笔记**（6 个隐蔽坑：软链 /tmp、venv 用错解释器、fetch_url 跑哪个 venv、软链 vs 真路径、**DiskCache 替换 JSON、Trafilatura 替换 html2text**） |
| `references/free-search-replacement-decision-2026-06-07.md` | **全网对比决策指南**（5 个位置的候选实测 + 排除清单 + 进化方法论 + **v1→v3.0.0 升级对照表**） |

## last30days 升级/翻车速查

⚠️ **软链别指 /tmp**：`~/.hermes/skills/research/last30days` 是软链，必须指向 `last30days-skill-main/skills/last30days`（持久），不能指 `/private/tmp/...`（macOS 重启就清）。详见 `references/last30days-install-and-broken-symlink.md`。

⚠️ **venv 必须 3.12**：用 `uv venv --python ~/.local/bin/python3.12` + `uv pip install --python .venv/bin/python requests click rich`。**不要**用 `pip3`（装到系统 Python 没权限），**不要**让 uv 自己选解释器（会吸到 hermes-agent venv 3.11）。

## 维护记录

- **v3.0.0 (2026-06-07)** — Trafilatura + DiskCache 进化版（**取代 v2 的 html2text + JSON**）
  - 嵌入"修补 vs 进化"方法论（用户 04:20 拍板）
  - fetch_url.py v1 → v2：html2text+stdlib → **Trafilatura 2.0.0**（scrapinghub 基准 #1）
  - 缓存层：JSON 文件 → **DiskCache 5.6.3**（自动 TTL+LRU+原子写+并发安全）
  - 全网对比了 4 个提取器候选、3 个缓存候选
  - 排除：Jina Reader（本机连不上）、Crawl4AI（太重）、Brave Search（2026/2 砍免费）、SearXNG 公网（连不上）
  - 实测：同一 URL 提取从"100% nav 垃圾"→"真正正文"；查询缓存 0.035s 命中
- **v2.0.1 (2026-06-07 深夜)** — 补实战笔记 + 修路径 bug
  - 新增 `references/free-search-stack-2026-06-07.md`（4 个隐蔽坑的详细复盘：软链 /tmp、venv 用错解释器、fetch_url 跑哪个 venv、软链 vs 真路径）
  - 修复 SKILL.md 里的 last30days 路径——从软链路径改成真路径（程序内部不应走软链）
  - 加"路径选择铁律"子章节：用户管入口走软链，程序内写真路径
- **v2.0.0 (2026-06-07)** — fetch_url.py 新增 + search.py v3 加缓存+三层降级
  - 新增 `~/.hermes/scripts/fetch_url.py`（单文件，零外部依赖，html2text 优先）
  - search.py 加 curl DDG 应急兜底 + 24h 缓存 + 50s last30days 超时
  - 实际效果：第 2 次查询从 18s 降到 0.02s（缓存命中）
- **v1.0.0 (2026-06-06)** — 首版固化。基于 QQ 拍板的 search.py v2 路由 + 两个底座引擎能力边界 + 兜底链。
- 路由规则变更：直接改 `search.py` 的 `route()` 函数 + 同步更新本 SKILL.md 的"路由规则"段。
- 底座引擎升级：升级 `anysearch` 或 `last30days` skill 后，无需改本文件——本文件是"如何使用"，不重复底座实现。
