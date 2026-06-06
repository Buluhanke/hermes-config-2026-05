# 搜索管道架构

**最后更新**: 2026-06-06

## 架构概览

```
用户/Agent/Cron/Subagent
        │
        ▼
  search.py (统一入口)
        │
   ┌────┴────┐
   ▼         ▼
anysearch  last30days
(主路)    (补充路/舆情)
   │         │
   ▼         ▼
 合并输出（主路 + 补充路）
   │
   ▼ agg_search.py (DDGS 多引擎聚合，兜底)
```

## 文件清单

| 路径 | 角色 | Skill 归属 |
|---|---|---|
| `~/.hermes/scripts/search.py` | 统一入口脚本（路由逻辑） | 本 skill |
| `~/.hermes/skills/anysearch/SKILL.md` | anysearch 完整文档 | `anysearch` skill |
| `~/.hermes/skills/anysearch/scripts/anysearch_cli.py` | anysearch CLI | `anysearch` skill |
| `~/.hermes/skills/research/last30days/SKILL.md` | last30days 完整文档 | `last30days` skill |
| `~/.hermes/skills/research/last30days/scripts/last30days.py` | last30days CLI | `last30days` skill |
| `~/.hermes/scripts/agg_search.py` | DDGS 多引擎聚合兜底 | `ddgs-searxng-agg-search` skill |
| `~/.hermes/skills/ddgs-searxng-agg-search/SKILL.md` | 兜底链+健康诊断 | `ddgs-searxng-agg-search` skill |
| `~/.hermes/skills/unified-search-routing/SKILL.md` | 上层路由定义（怎么调） | 本 skill |

## 依赖

| 组件 | 依赖 | 备注 |
|---|---|---|
| anysearch | Python 3.6+ + requests 或 Node.js 或 Bash | 匿名可用 |
| last30days | Python 3.12+（`~/.local/bin/python3.12`） | 主 venv 3.11 不行 |
| agg_search.py | Python 3.6+ + duckduckgo-search | 纯 Python 无外部依赖 |
| search.py | Python 3.6+ | 调上面三个 |

## 路由规则（search.py route() 函数逻辑）

| 查询信号 | 主通道 | 补充通道 |
|---|---|---|
| 舆情/口碑/最近/过去30天/社媒/reddit/hn/twitter/tiktok/polymarket | last30days | anysearch |
| 什么/怎么/推荐/评测/价格/技术/参数/事实/配置/哪个好/对比/教程 | anysearch | last30days |
| 两者都有信号 | anysearch | last30days |
| 无强信号（默认）| anysearch | last30days |
| anysearch 异常 | agg_search.py (DDGS) | — |
| last30days 异常（缺 3.12）| 不降级, 跳过补充 | — |

## 验证方式

```bash
# 完整路由验证
python3 ~/.hermes/scripts/search.py "Mac mini M4 跑 LLM" 2

# 期望输出:
# 🔍 [查询] 路由: 主=anysearch | 补充=last30days
# ## Search Results (N results)
# ...
# ── last30days 补充 ──
# 🌐 last30days vX.X.X: 查询
# ...
```
