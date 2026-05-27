# 搜索降级方案

当 `web_search`（Firecrawl）不可用时，用 `duckduckgo-search` 替代。

## 触发条件

1. `web_search` 返回 `Payment Required` 或网络超时
2. cron 环境外部站点（github.com/hacker news）全部超时
3. 需要轻量联网搜索但无预算

## 优先级

```
web_search (Firecrawl)  ← 首选（有预算时）
    ↓ 失败
duckduckgo-search (ddgs)  ← 降级备选（免费，无API key）
    ↓ 也失败
本地 Brain_Lab 缓存  ← 兜底方案
    ↓ 也无
静默退出（SILENT）
```

## 使用方法

```bash
# 检查 ddgs 是否可用
command -v ddgs >/dev/null && echo "ddgs:ok" || echo "ddgs:missing"

# CLI方式搜索（推荐）
ddgs text -q "AI agent mac desktop automation 2025" -m 5 -t m -o json

# 典型降级搜索流
ddgs text -q "GitHub trending AI Agent" -m 5 -t d -o json | python3 -c "
import sys, json
for r in json.load(sys.stdin):
    print(r.get('title',''), '|', r.get('href',''))
"
```

## 已知限制

- ddgs 与 `execute_code` 是不同运行时，pip装在terminal环境不等于`execute_code`能import
- 降级搜索仅用于发现阶段，内容提取仍依赖 curl/web_extract
- cron 环境网络不通时（本次发现），ddgs 也无法连通，此时只能读本地缓存

## 相关skill

- `idle_learning` — 空闲自学流程（已集成本降级方案）
- `proactive-self-evolution` — 主动进化框架（已集成本降级方案）