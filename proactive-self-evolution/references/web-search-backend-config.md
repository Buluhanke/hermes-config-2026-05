# Web搜索后端配置（2026-06-05 更新）

## 现状

| 配置项 | 值 | 状态 |
|--------|-----|------|
| `web.backend` | ddgs | ✅ 主力搜索 |
| `web.search_backend` | ddgs | ✅ 主力搜索 |
| `web.extract_backend` | searxng | ⚠️ 公用实例全挂，本地未部署 |

**说明**：`extract_backend: searxng` 是目标配置，实际降级到 ddgs（SearXNG 公用实例全部 429/404）。

## 搜索后端稳定性排序

| 方案 | 状态 | 备注 |
|------|------|------|
| **ddgs** | ✅ 稳定首选 | 免费，无需 API key，即装即用 |
| GitHub API | ✅ 稳定备用 | 免认证，rate limit 宽松 |
| SearXNG 公开实例 | ❌ 全军覆没 | 50+ 实例测试：95%+ 已死或限流 |
| Docker SearXNG | ❌ 用户禁用 Docker | — |
| Firecrawl | ⚠️ 已卸载 | 需付费，免费额度极低，已从插件移除 |

## SearXNG 公开实例阵亡记录

```
searx.be         → 403 Forbidden（JSON 不通）
searx.party      → 429 Too Many Requests（持续，等待 90s+ 仍限流）
searxng.vern.cc  → 429
searx.li         → 404
searx.tuxcloud.net → 429
searxng.org      → 404
searx.ddot.cc    → 530
searx.lynL.org   → 429
searx.trom.tf     → 429
其余 40+        → 000 超时
```

**根因**：公开 SearXNG 被大量滥用，所有稳定实例都加了严格限流或已下线。

## 聚合搜索脚本

`~/.hermes/scripts/agg_search.py` — 并行查 ddgs + SearXNG，URL 去重输出。

```bash
python3 ~/.hermes/scripts/agg_search.py "查询词" 10
```

## 教训

- **ddgs 是免费唯一解**：本地 Python 包，无需网络，无 API 限制
- **SearXNG 公开实例不可依赖**：不要假设任何公开实例长期可用
- **Firecrawl 已卸载**：需付费，免费 tier 不可用
- **原则**：web backend 永远用 ddgs，extract 可尝试 searxng（自动降级）

## 相关配置

```yaml
web:
  backend: ddgs
  search_backend: ddgs
  extract_backend: searxng
```

## 验证命令

```bash
# ddgs（推荐）
python3 -c "from ddgs import DDGS; d=DDGS(); print(list(d.text('test', max_results=1)))"

# 聚合搜索（ddgs + SearXNG fallback）
python3 ~/.hermes/scripts/agg_search.py "AI agent" 5

# SearXNG 本地实例（需 Docker，已不可用）
curl -s --max-time 5 "http://127.0.0.1:8888/search?q=test&format=json" | head -c 200
```

## 环境变量

```bash
SEARXNG_URL=https://searx.party       # 仅参考（SearXNG 已不可用）
SEARXNG_INSTANCE_URL=http://127.0.0.1:8888  # 本地实例（需 Docker，未安装）
```
