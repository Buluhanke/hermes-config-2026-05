# 搜索降级方案

当 `web_search`（Firecrawl）不可用时，用以下方案替代。

## 触发条件

1. `web_search` 返回 `Payment Required` 或网络超时
2. cron 环境外部站点（github.com/hacker news）全部超时
3. 需要轻量联网搜索但无预算

## 降级优先级

```
web_search (Firecrawl)  ← 首选（有预算时）
    ↓ 失败
HN Firebase API（免费，无需认证）  ← 首选降级
    ↓ 也失败
GitHub API（直接调 REST，无需认证）  ← 次选降级
    ↓ 也失败
Bing 搜索（浏览器模式，绕过 Google 验证码）  ← 备选
    ↓ 也失败
本地 Brain_Lab 缓存  ← 兜底方案
    ↓ 也无
静默退出（SILENT）
```

## HN Firebase API — 首选降级

免费稳定，无需 API key，直接调 REST：

```bash
# 获取 HN 当日热门故事 IDs（terminal 环境）
curl -s "https://hacker-news.firebaseio.com/v0/topstories.json" | python3 -c "
import sys, json
ids = json.load(sys.stdin)[:8]
for i in ids:
    print(i)
"

# 并行抓详情（避免串行慢）
python3 -c "
import urllib.request, json

ids = [48299753, 48296794, 48301603]
for i in ids:
    try:
        d = json.loads(urllib.request.urlopen(f'https://hacker-news.firebaseio.com/v0/item/{i}.json', timeout=5).read())
        print(d.get('title',''), '|', (d.get('url') or 'no url')[:80])
    except:
        pass
"
```

注意：HN 的故事不一定与 AI 领域相关，适合作为"技术视野巡检"，不适合精准搜索。

## GitHub API — 次选降级

```
GET https://api.github.com/search/repositories?q=AI+agent+desktop+automation+2026&sort=stars&per_page=8
```

```bash
curl -s "https://api.github.com/search/repositories?q=AI+agent+desktop+automation+2026&sort=stars&per_page=8" \
  -H "Accept: application/vnd.github.v3+json" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for r in d.get('items', [])[:8]:
    print(r['full_name'], '★', r['stargazers_count'], '|', r.get('description','')[:60])
"
```

⚠️ GitHub API 在 cron script-execution 策略下可能返回 `pending_approval`，遇此直接跳过。

## Bing 搜索 — 备选降级

Google 触发验证码，改用 Bing：

```
https://www.bing.com/search?q=<query>&setlang=zh-CN
```

用 `browser_navigate` 打开，Bing 不需要 JS 渲染，`browser_snapshot` 直接拿结果。

## ddgs（已安装但测试发现不可用）

`ddgs` 在本环境未安装，跳过此方案。

## 相关 skill

- `idle_learning` — 空闲自学流程（已集成本降级方案）
- `proactive-self-evolution` — 主动进化框架（已集成本降级方案）