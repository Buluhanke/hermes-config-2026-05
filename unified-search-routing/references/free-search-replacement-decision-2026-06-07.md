# 免费联网搜索栈 — 全网对比决策指南

**2026-06-07 实测**，适用于 Mac mini + hermes-agent + 24GB 内存环境。

## 决策树

```
要换掉一个组件 →
  ① web_search "best free <组件类> 2026" 跑 3-5 个候选
  ② 对每个候选：实测本机能不能跑（DNS / 端口 / 鉴权）
  ③ 跑出来质量对比（同一 URL/同一 query）
  ④ 选最强的免费方案替换，不是叠加补丁
```

## 5 个位置的实际决策（2026-06-07）

### 1. URL 内容提取

| 候选 | 实测结果 | 决策 |
|------|----------|------|
| **Trafilatura 2.0.0** | GitHub 提取从 nav 垃圾→真文 | ✅ 选 |
| readability-lxml | 没测（社区基准 < Trafilatura） | ❌ |
| newspaper4k | 没测（社区基准 < Trafilatura） | ❌ |
| Jina Reader (`r.jina.ai`) | DNS→Facebook IP, 10s 超时 | ❌ 本机不通 |
| Crawl4AI | 太重（要装 Docker / 浏览器） | ❌ |
| my-self-fetch_url.py (html2text) | 实测输出一堆 nav 链接 | ❌ 替换 |

**结论**：用 Trafilatura 2.0.0。`pip install trafilatura`（GPL-3.0）。

### 2. 缓存层

| 候选 | 实测结果 | 决策 |
|------|----------|------|
| **DiskCache 5.6.3** | 1000 写 0.063s，自动 TTL+LRU+原子写 | ✅ 选 |
| cachetools | 仅内存（不跨进程） | ❌ |
| fakeredis | 测试用 | ❌ |
| JSON 文件手写 | 1s+ 写 1000 条 | ❌ 替换 |

**结论**：用 DiskCache。`uv pip install diskcache`（BSD）。

### 3. 搜索引擎主路

| 候选 | 实测结果 | 决策 |
|------|----------|------|
| anysearch (anysearch.dev) | 5s 给 5 精准结果 | ✅ 保持 |
| Brave Search API | 2026/2 砍掉免费层 | ❌ |
| SearXNG 公共实例 | 5 个公网实例本机全超时 | ❌ |
| DDGS (DuckDuckGo) | 第一条结果经常不相关 | ⚠️ 兜底用 |

**结论**：保持 anysearch 主路，DDGS 兜底。

### 4. 社媒舆情

| 候选 | 决策 |
|------|------|
| last30days | ✅ 保持（最强免费路线） |
| 商业工具（Brand24/Sprout/Mention） | ❌ 付费 |

### 5. web_extract 后端

| 候选 | 决策 |
|------|------|
| searxng (公网实例) | ❌ 本机连不通（5 个公网实例全超时） |
| Firecrawl / Tavily / Parallel | ❌ 付费 |
| fetch_url.py (本地) | ✅ 替代 web_extract 用 |

## 排除候选的"实测不通过"清单（避免重复劳动）

| 工具 | 失败原因 |
|------|----------|
| Jina Reader (`r.jina.ai`) | DNS 解析到 Facebook IP（157.240.2.36），连接 10s 超时 |
| Brave Search API | 2026/2 官方砍掉 2000 月免费层 |
| SearXNG 5 个公网实例（searx.be/sapti.me/tiekoetter/priv.au/bus-hit.me） | 本机 curl `format=json` 全部 NOT JSON，公网实例已失效或被限 |

## 升级触发词

| 你听到/看到 | 动作 |
|------------|------|
| "升级联网搜索" | 跑 `web_search "best free X 2026"` 全网对比 |
| "找更强的方案" | 同上（用户 04:20 拍板的进化方法论） |
| "打补丁 / 修补" | 停下来——先问"全网有没有更强的免费方案" |
| "X 是不是坏了" | 1 句"我先复测" + 4 步实测（不狡辩不推回） |

## 完整文件路径

- `~/.hermes/scripts/fetch_url.py`（Trafilatura + DiskCache 主提取器）
- `~/.hermes/scripts/search.py`（统一入口 + DiskCache 缓存）
- `~/.hermes/cache/search/`（DiskCache 格式）
- `~/.hermes/cache/fetch_url_v2/`（DiskCache 格式）

## 历史踩坑（避免重蹈）

| 翻车 | 教训 |
|------|------|
| last30days 软链指 `/tmp/...` | 软链别指临时目录；用 `find ~/.hermes -type d -name X` 全局验证 |
| uv pip install 装到 3.11 venv | 显式 `--python .venv/bin/python` 指定解释器 |
| fetch_url 输出 nav 垃圾 | 别自己写提取器，Trafilatura 已经是社区 #1 |
