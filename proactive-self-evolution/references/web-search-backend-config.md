# Web搜索后端配置（2026-06-02 更新）

## 现状

- `web.backend: ddgs` ✅ 可用（日常主力）
- `web.search_backend: ddgs` ✅ 可用
- `web.extract_backend: ddgs` ✅ 已从 firecrawl 切换
- `SEARXNG_URL` → 已从 `http://127.0.0.1:8888` 改为 `https://searx.party`（但 searx.party 持续 429 限流）

## 搜索后端稳定性排序（2026-06-02 实测 50+ 实例）

| 方案 | 状态 | 备注 |
|------|------|------|
| ddgs | ✅ 稳定首选 | 免费，无需 API key，即装即用 |
| GitHub API | ✅ 稳定备用 | 免认证，rate limit 宽松 |
| SearXNG 公开实例 | ❌ 全军覆没 | 50+ 实例测试：95%+ 已死或限流 |
| Docker SearXNG | ❌ 不可用 | Docker Desktop 未安装 |
| Firecrawl | ⚠️ 需付费 | 免费 tier 额度极低 |

## SearXNG 公开实例阵亡记录（2026-06-02）

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

## 教训

- **Firecrawl 需要付费 API**：注册送额度但长期免费不可用
- **SearXNG 公开实例不可依赖**：不要假设任何公开实例长期可用
- **原则**：web backend 优先用 ddgs（本地免费），不要默认用需要 API key 的服务

## 验证命令

```bash
# ddgs（推荐）
python3 -c "from ddgs import DDGS; d=DDGS(); print(list(d.text('test', max_results=1)))"

# SearXNG 本地实例（需 Docker，已不可用）
curl -s --max-time 5 "http://127.0.0.1:8888/search?q=test&format=json" | head -c 200
```

## 相关配置

```yaml
web:
  backend: ddgs
  search_backend: ddgs
  extract_backend: ddgs  # 不是 firecrawl（需付费）
```

## 环境变量

```bash
SEARXNG_URL=https://searx.party       # 仅参考（SearXNG 已不可用）
SEARXNG_INSTANCE_URL=http://127.0.0.1:8888  # 本地实例（需 Docker，未安装）
```