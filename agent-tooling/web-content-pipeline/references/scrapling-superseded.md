# scrapling — ⚠️ LEGACY (2026-07-05 audit)

## 状态

**scrapling 已停止维护（~2025），不再推荐使用。**

## 替代方案

| 场景 | scrapling | 推荐替代 |
|------|-----------|---------|
| 普通HTTP抓取 | ✅ | `fetch_url.py` (Trafilatura) — 更轻量 |
| JS渲染页 | ✅ | `defuddle` — 内置headless，更干净 |
| Cloudflare绕过 | ✅ | `crawl4ai` — 异步+更好JS支持 |
| 多页爬虫 | ✅ | `crawl4ai spider` — 异步并发 |

## 为什么废弃

- 2025年后未更新（GitHub停止维护）
- Python 3.14兼容问题
- `crawl4ai`在异步/SPA/BM25过滤全面超越
- `defuddle`在token节省上更好

## 如果遇到scrapling代码

不要去修或重装，直接迁移到web-content-pipeline的5层fallback链。

## 参考

- 父skill: `web-content-pipeline` (五层fallback链)
- 替代: `crawl4ai` (references/crawl4ai-when-to-use.md)
