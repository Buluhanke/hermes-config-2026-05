# 联网搜索 v2 路由 (search.py) — 2026-06-05 QQ bot 拍板版

> 替代旧的"4 引擎聚合"思路, 改用路由式分发: 不同 query 自动走不同通道。
> 给明天的 agent 必读 — 别再装新搜索引擎, 别再接 web_search, 走这一个就够。

## 为什么是 search.py (不是 ddgs, 不是 SearXNG, 不是 web_search)

**6/5 实测结论**:
- ❌ 公开 SearXNG 95% 死 (searx.party/searxng.org 都 404 或 429)
- ❌ web_search 工具 Firecrawl 额度耗尽, 返回空
- ✅ ddgs 2 引擎活着 (中文 zh-cn / 英文 en)
- ✅ anysearch 通道全跑通, last30days 通道有 fallback 兜底
- **结论**: 走 search.py 路由, 用户不参与选通道

## search.py 路由规则 (第 32-52 行)

```python
last30_signal  = ["舆情", "口碑", "最近大家怎么看", "过去30天", "过去一个月",
                   "本月趋势", "本月热点", "这个月", "社媒", "reddit", "hn",
                   "polymarket", "twitter", "tiktok", "过去几周", "近几周"]
anysearch_signal = ["什么", "怎么", "推荐", "评测", "价格", "技术", "参数",
                     "事实", "配置", "规格", "哪个好", "好不好", "怎么样",
                     "对比", "比较", "区别", "教程", "攻略", "选购"]

if has_last30 and has_any:
    return "anysearch", "last30days"  # 两个都中: anysearch 主 + last30 补充
if has_last30:
    return "last30days", "both"        # 只命中 last30
if has_any:
    return "anysearch", "last30days"   # 只命中 anysearch: anysearch 主 + last30 补充
return "anysearch", "last30days"       # 模糊地带: anysearch 主 + last30 补充
```

## 触发词速查表

| 用户说 | 主通道 | 补充通道 |
|---|---|---|
| "X 舆情 / 口碑 / 大家怎么看" | last30days | — |
| "X 过去 30 天 / 本月 / 社媒" | last30days | — |
| "X 什么 / 怎么 / 推荐" | anysearch | last30days |
| "X 价格 / 评测 / 对比" | anysearch | last30days |
| "X 教程 / 攻略 / 选购" | anysearch | last30days |
| 模糊 query | anysearch | last30days |
| anysearch 挂了 | **agg_search.py (ddgs)** | — |

## 入口 3 个

```bash
# Python 路由版 (默认, 推荐)
python3 ~/.hermes/scripts/search.py "<query>" [N]

# Bash 薄包装 (cron 脚本里用, 优先 anysearch, 挂了走 ddgs)
bash ~/.hermes/scripts/search.sh "<query>" [N]

# 兜底 (只跑 ddgs, 不路由)
python3 ~/.hermes/scripts/agg_search.py "<query>" [N]
```

## 底层组件 (现成的, 别重装)

- ✅ `~/.hermes/scripts/search.py` — 路由入口 (115 行, 拍板版)
- ✅ `~/.hermes/scripts/search.sh` — Bash 薄包装
- ✅ `~/.hermes/skills/anysearch/scripts/anysearch_cli.py` — anysearch 通道
- ✅ `~/.hermes/skills/research/last30days/scripts/last30days.py` — last30days 通道
- ✅ `~/.hermes/scripts/agg_search.py` — 兜底 (ddgs, 2 引擎活着, SearXNG 远端 95% 死)

## 禁止 (用户 6/5 立的新规)

- ❌ 调 `web_search` 工具 (Firecrawl 额度耗尽)
- ❌ 装新搜索引擎
- ❌ SearXNG 自建 / Docker / 装本地 (用户 6/5 点过死胡同)
- ❌ 看到 "试试 X 搜索引擎" → 引本规则, **不动**

## 路由观察 (6/5 实测 18 query)

- **触发词命中率 100%**: 评测/趋势/本月/6月 → last30days; 最新/什么/怎么 → anysearch
- **last30days 弱点**: 中文小众主题 (Hermes 6月发布) 证据薄, fallback-local-score demotion 普遍
- **anysearch 强项**: 技术 query (SWE-bench / Opus 4.8) 命中率高, last30days 补充段质量高
- **结论**: search.py 路由设计稳, **不需要改**

## 验证命令 (改完跑一遍, 路由应该正常分)

```bash
# last30days 触发
python3 ~/.hermes/scripts/search.py "AI 舆情 本月趋势" 5
# 期望: 路由: 主=last30days | 补充=...

# anysearch 触发
python3 ~/.hermes/scripts/search.py "小米SU7 价格 评测" 5
# 期望: 路由: 主=anysearch | 补充=last30days

# 模糊地带
python3 ~/.hermes/scripts/search.py "Hermes 进化" 5
# 期望: 路由: 主=anysearch | 补充=last30days
```

## daily_active_learning.sh 接入建议

```bash
# 旧版 (不推荐)
ddgs text -q "$query" -m 3 -o json

# 新版 (走 search.py 路由)
python3 ~/.hermes/scripts/search.py "$query" 3
```

## 教训 (新会话起来必读)

1. **起手先看** `~/.hermes/scripts/search.py` 在不在 → 在, 直接用
2. **别接 web_search tool** (Firecrawl 额度耗尽, 公开 SearXNG 95% 死, 走 search.py 路由才是正解)
3. **Telegram bot 默认就调 search.py**, **用户不感知通道**
4. **写 idle_learning 脚本时, 默认调 search.py, 不直接调 ddgs/searxng**

## 反面教材 (6/5 真实事件)

### 反例 1: 16:30 telegram agent 重复接 searxng MCP
- 我看 memory 提 "ddgs + SearXNG" 就当全部真相, **没读 agg_search.py 实锤**
- 真相: agg_search.py 是 4 引擎聚合, search.py 是 5 引擎路由
- 修法: 看到 "SearXNG" 先 `ls ~/.hermes/scripts/`, 别直接接 MCP

### 反例 2: 21:00 evening_summary 用 4 引擎写入
- 老的 21:00 总结只走 ddgs + SearXNG, 没考虑 last30days/anysearch
- 修法: 21:00 evening 改用 search.py 路由, 输出 4 通道结果
