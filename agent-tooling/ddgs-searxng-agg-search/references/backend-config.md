# 搜索后端配置记录（2026-06-05 22:00 更新）

## config.yaml 当前值
```yaml
web:
  backend: ddgs
  search_backend: ddgs
  # extract_backend: searxng 已移除（2026-06-05 22:00）
  # 完整 searxng MCP 段已删
```

**MCP servers 段**不再有 `searxng:` 条目（删了 `command: /opt/homebrew/bin/searxng`）。

## .env 当前值
```
# 2026-06-05 22:00 删:
# SEARXNG_ALLOW_PRIVATE=1
# SEARXNG_INSTANCE_URL=http://127.0.0.1:8888
# SEARXNG_URL=https://searx.party
```

`anysearch` 凭据（可选）：`ANYSEARCH_API_KEY=<key>` from https://anysearch.com/console/api-keys。

## 设置命令（hermes config CLI）
```bash
hermes config set web.backend ddgs
hermes config set web.search_backend ddgs
# extract_backend 不再设（已移除）
```

## backend 选择逻辑（web_tools.py）
- `web.backend` — 全局默认
- `web.search_backend` — 搜索专用，覆盖 backend
- `web.extract_backend` — 内容提取专用，覆盖 backend（**已删除**，框架回退默认）
- 实际生效：`ddgs`（搜索）+ 框架默认（提取）

## Hermes web 插件列表（2026-06-05 状态）
```
plugins/web/
├── ddgs/        ✅ 可用（ddgs Python 包，主力降级）
├── searxng/     ❌ 已删除（用户禁用 Docker + 公开实例全挂）
├── exa/         ❌ 需 EXA_API_KEY
├── parallel/    ❌ 需 PARALLEL_API_KEY
├── tavily/      ❌ 需 TAVILY_API_KEY
├── xai/         ❌ 需 xai 凭证
└── brave_free/  ❌ 需 BRAVE_SEARCH_API_KEY
```

**重要补充**：用户实际使用的**首选** `anysearch` 不在 `plugins/web/` 列表里——它是独立 skill（`~/.hermes/skills/anysearch/`），通过 `anysearch_cli.py` subprocess 调，与 hermes 框架 web 插件体系**平行存在**。这种"框架插件 + 独立 skill"的双轨设计让 anysearch 可以零框架改动直接用。

## 搜索后端稳定性排序
| 方案 | 状态 | 备注 |
|------|------|------|
| **anysearch** | ✅ 首选 | 70+ 引擎，匿名免 key，中英文都好 |
| **ddgs** | ✅ 稳定降级 | 免费，无需 API key |
| GitHub API | ✅ 稳定备用 | 免认证，rate limit 宽松 |
| SearXNG 公开实例 | ❌ 移除 | 2026-06-05 全删 |
| Docker SearXNG | ❌ 禁用 | 用户禁用 Docker |
| Firecrawl | ❌ 已卸载 | 需付费，免费额度极低 |

## 验证命令
```bash
# 首选路径（所有平台统一）
bash ~/.hermes/scripts/search.sh "AI agent" 5

# 直调 anysearch
python3 ~/.hermes/skills/anysearch/scripts/anysearch_cli.py search "test" 3

# 降级路径
python3 ~/.hermes/scripts/agg_search.py "AI agent" 5
# 期望: "anysearch:N (首选)" 段，或 "anysearch:0 → ddgs 降级:N"
```
