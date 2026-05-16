# Web Backend 配置指南

Hermes 的 web 工具（搜索/抓取/爬取）支持多个后端。本文档说明如何配置和排查 Web Search 后端。

## 支持的 Backend

| 后端 | 类型 | 国内直连 | 是否需要 Key | 费用 |
|------|------|---------|-------------|------|
| Firecrawl | 国外 | ❌ 需代理 | `FIRECRAWL_API_KEY` | 500积分免费 → $20/月 |
| Bocha (博查) | 国内 | ✅ | `BOCHA_API_KEY` | 1000次免费/3月 |
| SearXNG | 自建Docker | ✅ | 无（自建） | **零费用** |
| Parallel | 国外 | ❌ 需代理 | `PARALLEL_API_KEY` | 付费 |
| Tavily | 国外 | ❌ 需代理 | `TAVILY_API_KEY` | 付费 |
| Exa | 国外 | ❌ 需代理 | `EXA_API_KEY` | 付费 |

## 自动检测优先级

当 `config.yaml` 中没有显式设置 `web.backend` 时，`_get_backend()` 按以下顺序自动检测：

```
Firecrawl → Bocha → 默认 Firecrawl

**SearXNG 不参与自动检测** — 没有对应的环境变量，必须显式在 `web.backend` 设置为 `searxng` 才能使用。
```

检测条件是对应 API Key 环境变量是否存在：

```python
backend_candidates = (
    ("firecrawl", _has_env("FIRECRAWL_API_KEY") or _has_env("FIRECRAWL_API_URL") or _is_tool_gateway_ready()),
    ("bocha", _has_env("BOCHA_API_KEY")),
    ("parallel", _has_env("PARALLEL_API_KEY")),
    ("tavily", _has_env("TAVILY_API_KEY")),
    ("exa", _has_env("EXA_API_KEY")),
)
```

## 推荐配置（双后端）

同时配置 Firecrawl（主力）+ Bocha（国内备用）：

```yaml
# ~/.hermes/config.yaml
web:
  backend: firecrawl   # 显式指定，避免依赖自动检测
```

```bash
# ~/.hermes/.env
FIRECRAWL_API_KEY=fc-your-key
BOCHA_API_KEY=YOUR_API_KEY-key
```

效果：
- Firecrawl 优先使用（搜索质量更高、支持 extract/crawl）
- 如果 Firecrawl 不可用但 Bocha 有 key，自动降级到 Bocha
- **不需要手动改 `web.backend` 来切换**，auto-detection 自动处理

## SearXNG（自建 Docker，零费用）

SearXNG 是一个自托管的元搜索引擎，通过 Docker 部署，**完全免费、无 API Key**，且国内网络直接可用。

### 部署方式

```bash
docker run -d --name searxng -p 127.0.0.1:8888:8080 searxng/searxng:latest
```

### 配置 Hermes

```yaml
# ~/.hermes/config.yaml
web:
  backend: searxng          # 必须显式设置（SearXNG 不参与自动检测）
```

SearXNG 不需要在 `.env` 中配置任何 API Key。

### 验证 SearXNG 是否可用

```bash
# 检查容器是否运行
docker ps | grep searxng

# 检查 HTTP 是否正常
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8888
# 预期返回 200
```

### 免费额度对比与优先级策略

| 后端 | 免费额度 | 有效期 | 备注 |
|------|---------|--------|------|
| Firecrawl | 500 积分（一次性） | **永不过期** | 1积分≈1次搜索，2并发，用完需付费$20/月起 |
| Bocha | 1000 次调用 | **3个月**（领取后） | 需手动领取免费试用资源包 |

**推荐策略：先用 Firecrawl（不设有效期），博查留着保底（3个月过期）。**
代码自动检测顺序已按此逻辑排列：Firecrawl → Bocha。

### 验证各个后端

```bash
# 临时切换到 Bocha 验证
hermes config set web.backend bocha
# 测试搜索
# 验证完成后切回
hermes config set web.backend firecrawl
```

## 配置方式

### 方式一：只配 key，靠自动检测（不推荐）

只要 `.env` 中有对应 API Key，Hermes 会自动选择优先级最高的可用后端。但这种方式依赖环境变量，不够明确。

### 方式二：显式设置 backend（推荐）

```bash
hermes config set web.backend firecrawl
```

或在 config.yaml 中直接写入：

```yaml
web:
  backend: firecrawl
```

## Web Backend 切换工作流程

切换后端时，需要同时更新 config.yaml 和 .env，然后重启 gateway 才能生效。

### 完整切换步骤

```bash
# 1. 如果新后端需要 API Key → 写入 .env
echo 'BOCHA_API_KEY=YOUR_API_KEY-key' >> ~/.hermes/.env
# 或手动编辑 ~/.hermes/.env

# 2. 修改 config.yaml 中的 web.backend
hermes config set web.backend searxng
# 或手动编辑 ~/.hermes/config.yaml

# 3. 重启 gateway 使配置生效（必须）
hermes gateway restart

# 4. 验证生效
# 检查 gateway 日志确认新 backend 被加载
tail -3 ~/.hermes/logs/gateway.log | grep -i "backend\|searxng\|bocha\|firecrawl"
```

### 常见场景：bocha ↔ searxng 互换

| 当前→目标 | 需要改 config.yaml | 需要改 .env | 需要重启 |
|----------|-------------------|------------|---------|
| searxng → bocha | `web.backend: bocha` | 添加 `BOCHA_API_KEY=...` | ✅ |
| bocha → searxng | `web.backend: searxng` | 不需要（SearXNG 无 Key） | ✅ |
| bocha → firecrawl | `web.backend: firecrawl` | 添加 `FIRECRAWL_API_KEY=...` | ✅ |

### 注意事项

- **切换后端不走配置即服务**（如 Dashboard 的 MODEL CHANGE），必须手工改 config.yaml + .env
- **不重启 gateway 不生效** — 任何 `web.backend` 变更都需要 `hermes gateway restart`
- 如果 `.env` 中同时有多个 API Key 但 `web.backend` 只设了一个，其他 Key 会被忽略（不浪费调用）
- 对于本机（aimac@192.168.0.4）场景，SearXNG 容器已部署并监听 `127.0.0.1:8888`，切换只需改 `web.backend` 为 `searxng` 后重启

## 常见问题

### Firecrawl key 在 .env 但 web_search 不工作

检查 config.yaml 中是否有 `web.backend` 写成了别的值（如 bocha、parallel）。如果没有写，auto-detection 会自动选 Firecrawl。可以显式设置来排除疑点。

### 两个 key 都在 .env，用的是哪一个？

Firecrawl 优先。想临时用 Bocha 时显式设 `web.backend: bocha`。

### Firecrawl 403 / 余额不足

Firecrawl 的免费额度通常有每月调用限制。如果返回 403，检查：
1. API Key 是否有效
2. 是否超出免费额度
3. 国内网络是否需要代理

### Bocha 403 "not enough money"

Bocha 有 1000 次免费试用额度，但需要**手动领取**（不是自动的）：
1. 登录 https://open.bochaai.com
2. 控制台 → 资源包管理 → 领取"Web Search API 免费试用"（1000次/0元/3个月）
3. 领取后立即生效

详见 `references/bocha-search-backend-patch.md` 的「免费额度领取」章节。

## web_extract 和 web_crawl

- `web_search` 所有后端都支持
- `web_extract` 和 `web_crawl` 只有 Firecrawl 原生支持（Bocha/Parallel/Tavily/Exa 仅搜索）
- 如果 backend 不是 Firecrawl，extract/crawl 调用会报错或回退
