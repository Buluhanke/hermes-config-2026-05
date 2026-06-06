# 搜索降级方案（2026-06-05 更新）

## 当前搜索栈（2026-06-05 17:30 修正 — 含 anysearch）

```
首选: anysearch CLI  ← 真"聚合", 70+ 引擎, 中文质量好, 无需 key
    ↓ 挂了 / 限额
agg_search.py (ddgs + searxng 并行)
    ↓ searxng 全部挂
ddgs 单独  ← 实际主力 (但中文弱)
    ↓ ddgs 挂
HN Firebase API  ← 最终降级
    ↓ 也挂
静默退出 (SILENT)
```

**Firecrawl 已卸载。** `web_search` / `web_extract` 工具不再可用。

### ⚠️ 重要修正（前版"只有 agg_search.py"是错的）

`anysearch` skill 一直装着、**今天 (2026-06-05 17:30) 实测可用**、中文质量比 ddgs 好一个量级。

```bash
# anysearch CLI（推荐，匿名访问免 key）
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py search "关键词" --max_results 5
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py batch_search --queries '[{"query":"q1","max_results":5}]'
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py extract "https://..."
```

**触发选择**：
- 中文/中文用户搜索 → **anysearch**（"小米SU7 价格"秒回国内站：小米官网/网通社/太平洋，ddgs 中文几乎没结果）
- 英文/技术搜索 → anysearch 或 ddgs 均可
- 限时抢数据 / 批量并发 → anysearch `batch_search`

**重要区分**：anysearch 是**真搜索引擎聚合**；`~/.hermes/scripts/multi_ask_v3.py` 是**6 个 AI 站点对话聚合**（完全不同问题）。

## agg_search.py — 主搜索（ddgs + searxng 并行）

```bash
python3 ~/.hermes/scripts/agg_search.py "查询词" 10
JSON_OUTPUT=1 python3 ~/.hermes/scripts/agg_search.py "查询词" 10  # JSON 输出
```

**当前实测状态（2026-06-05）：**
| 引擎 | 状态 | 备注 |
|------|------|------|
| ddgs | ✅ 可用 | 主力，Python 包已装 |
| searxng/searx.party | ❌ 429 限流 | 持续，无法排队通过 |
| searxng/searxng.org | ❌ 404 | 已下线 |
| searxng/127.0.0.1:8888 | ❌ Connection refused | 未部署（用户禁用 Docker） |

**注意**：ddgs 对中文查询返回结果质量差（电商/社媒/低相关度）。换英文词重搜。

## ddgs 单独（searxng 全挂时的降级）

```bash
ddgs text -q "query" -m 10
```

⚠️ **正确格式**：`ddgs text -q "query" -m N`，不是 `ddgs search`。

## HN Firebase API — 最终降级

免费稳定，无需认证。

⚠️ **必须用文件中介，禁止内联 `python3 -c`**：
```bash
# ✅ 正确：先 curl 到文件，再 python3 解析
curl -s "https://hacker-news.firebaseio.com/v0/topstories.json" -o /tmp/hn_ids.json
python3 /tmp/hn_parse.py   # 解析文件

# ❌ 禁止：cron 环境会拦截 python3 -c 和 heredoc
```

⚠️ **重要区分**：`news.ycombinator.com` 和 `hacker-news.firebaseio.com` 是不同域名，预检失败 ≠ API 失败。

## 关键陷阱

⚠️ **cron/scheduled 环境下，`python3 -c` 内联写法被拦截！** 必须先写 `.py` 文件再执行。

⚠️ **批量 curl 容易超时**：推荐每批 5 个，分批执行。

⚠️ **不要用 `web_search` / `web_extract` 工具**：Firecrawl 已卸载，返回 Payment Required。
