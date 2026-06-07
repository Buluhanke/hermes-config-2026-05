# Free Search Stack 实战笔记（2026-06-07）

本会话从 0 搭出"完全免费、零付费后端"的联网搜索体系，踩了 4 个隐蔽的坑。这份文档记录坑点 + 验证步骤 + 修复命令。

## 1. last30days 软链指向 /tmp — 重启就断

**症状**：用户报告"last30days 找不到了"或"它怎么丢了"。检查发现：

```bash
ls -la ~/.hermes/skills/research/last30days
# lrwxr-xr-x  ... last30days -> /private/tmp/last30days-skill-repo/skills/last30days
ls /private/tmp/last30days-skill-repo/skills/last30days/
# ls: No such file or directory  ← 目标已不存在
```

**根因**：`/tmp` 是 macOS 临时目录，**重启就清**。所有"我把仓库放 /tmp 然后软链出去"的安装方式都中招。

**修复**：

```bash
# 软链重指持久路径
cd ~/.hermes/skills/research
ln -sfn /Users/aimac/.hermes/skills/research/last30days-skill-main/skills/last30days last30days
readlink last30days
# 验证: /Users/aimac/.hermes/skills/research/last30days-skill-main/skills/last30days
ls last30days/SKILL.md && echo "✅ linked OK"
```

**铁律**（已入 SKILL.md）：

- ❌ 不要用软链到 `/tmp`、`~/.local/share/`（目标不存在 = 死链）
- ✅ 软链到 `~/.hermes/skills/research/last30days-skill-main/skills/last30days`（持久）

## 2. venv 解释器选错 — uv 偷偷用 3.11

**症状**：last30days 报错 `ModuleNotFoundError: No module named 'requests'`，但 `pip install` 看似成功了。

**根因**：`uv` 默认会找到 `~/.hermes/hermes-agent/venv`（Python 3.11，是 hermes 的主 venv），`uv pip install` 装到那里去了。last30days 要求 Python 3.12+，装到 3.11 venv 完全用不上。

**坑 1**：`uv sync` 直接读 `pyproject.toml`，会自动选 hermes-agent 的 venv（3.11）。

**坑 2**：`pip3 install` 装到系统 Python（要 sudo），或者装到不存在的环境。

**修复**：

```bash
# 1. 在 last30days-skill-main 目录下用 uv venv 强制指 3.12
cd ~/.hermes/skills/research/last30days-skill-main
uv venv --python /Users/aimac/.local/bin/python3.12
# → Creating virtual environment at: .venv

# 2. 装依赖必须指 .venv/bin/python
uv pip install --python .venv/bin/python requests click rich
# → 装到 3.12 venv，不再偷偷吸 hermes-agent

# 3. 验证
.venv/bin/python -c "import requests, click, rich; print('OK 3.12')"
```

**铁律**：

- last30days **必须** Python ≥ 3.12（项目 pyproject.toml 写死）
- 永远用 `uv venv --python <具体路径>` 而**不**让 uv 选
- 永远用 `uv pip install --python .venv/bin/python` 而**不**用裸 `uv pip install`

## 3. fetch_url.py 跑哪个 venv？

**症状**：fetch_url.py 用 html2text 做 HTML → markdown，但 `import html2text` 报 ModuleNotFoundError。

**根因**：last30days 那个 3.12 venv 里没装 html2text。要么：
- 装到 3.12 venv（污染 last30days 依赖）
- 装到 hermes-agent 主 venv（3.14 已经有 requests/click/rich，多 html2text 不冲突）

**选 hermes-agent 主 venv**，原因：
- 跑 fetch_url 是 agent 行为，不是 last30days 的事
- 主 venv 已经有依赖管理基础
- last30days 的 venv 保持干净（只装 3 个核心包）

**安装命令**：

```bash
uv pip install --python ~/.hermes/hermes-agent/venv/bin/python html2text
# + markdownify 装上（备选）
uv pip install --python ~/.hermes/hermes-agent/venv/bin/python markdownify
```

**调用**：

```bash
~/.hermes/hermes-agent/venv/bin/python ~/.hermes/scripts/fetch_url.py "https://..."
```

**铁律**：

- fetch_url.py 跑 `~/.hermes/hermes-agent/venv/bin/python`（不是 last30days 的 3.12 venv）
- last30days.py 跑 `~/.local/bin/python3.12`（独立 venv）

## 4. search.py 里的 LAST30 路径要写软链还是写真路径？

**问题**：`LAST30` 变量在 search.py 里。如果写软链 `~/.hermes/skills/research/last30days/scripts/last30days.py`，软链换了就要改。写真路径 `~/.hermes/skills/research/last30days-skill-main/skills/last30days/scripts/last30days.py`，直接但脆弱。

**选择**：写**真路径**，不写软链路径。

原因：
- 软链是"用户接口"——用户用 `last30days` 命令时走软链 OK
- 但 search.py 是程序接口，程序不应该"经过符号链接"——软链指向变了，程序路径就断
- 真路径让 search.py 直接定位到具体文件，避开符号链接失效的坑

**写代码**：

```python
# ~/.hermes/scripts/search.py
LAST30 = os.path.expanduser(
    "~/.hermes/skills/research/last30days-skill-main/skills/last30days/scripts/last30days.py"
)
# NOT: LAST30 = "~/.hermes/skills/research/last30days/scripts/last30days.py"
```

**铁律**：

- 用户命令/CLI → 用软链（用户体验好）
- 程序内部路径 → 用真路径（避免软链失效/被改）

## 5. v3.0.0 升级：缓存层从 JSON 文件 → DiskCache（进化版）

**v1 缓存的短板**（参考 SKILL.md v2.0.0 时代）：自己写 JSON 文件 + 手算 `time.time() - ts > 86400` 判过期。

**v3.0.0 替换为 DiskCache 5.6.3**（BSD 许可，`uv pip install diskcache`）。为什么：

- 自动 TTL（`expire=86400` 参数，不用手算）
- 自动 LRU 淘汰（磁盘满自动清旧的）
- 原子写（不用 lock，并发安全）
- 1000 写 0.063s（JSON 方案 1s+）

**代码模式**（search.py 和 fetch_url.py 都用同一套）：

```python
import diskcache
_cache = diskcache.Cache("~/.hermes/cache/search", expiry=86400)

# 写
_cache.set("query key", output, expire=86400)

# 读（过期自动返 None）
hit = _cache.get("query key")
if hit:
    return hit
```

**缓存目录**（v3.0.0 后）：

- `~/.hermes/cache/search/`（search.py，DiskCache 格式）
- `~/.hermes/cache/fetch_url_v2/`（fetch_url.py，DiskCache 格式）
- ~~`~/.hermes/cache/fetch_url/`~~（v1 的 JSON 方案已删，目录清空）

**降级**：DiskCache 没装时（ImportError）自动 fallback 到"无缓存直跑"模式，不报错。

## 6. v3.0.0 升级：URL 提取从 html2text → Trafilatura（进化版）

**v1 fetch_url 的短板**（自己写 html2text + stdlib regex）：

- html2text 不剥 nav/sidebar，输出"Skip to content / Navigation Menu / Sign in / ..."
- 实测 GitHub 页面提取：100% 都是 UI 垃圾，没一句正文

**v3.0.0 替换为 Trafilatura 2.0.0**（GPL-3.0，`uv pip install trafilatura`）。为什么：

- scrapinghub 基准测试**击败** readability-lxml/newspaper4k/boilerpipe/goose3
- 自动识别 nav/aside/script 剥掉
- 实测同一 URL：输出"Persistent memory and auto-generated skills — it learns your projects and never forgets how it solved a problem."

**代码模式**：

```python
import trafilatura
md = trafilatura.extract(html, output_format="markdown",
                         include_comments=False, include_tables=True)
```

**降级链**（v3.0.0 fetch_url.py）：
1. Trafilatura 2.0.0（主）
2. html2text（兜底，Trafilatura 没装时用）
3. stdlib regex（终极兜底，零依赖）

**方法论铁律**（用户 04:20 拍板 FIRST-CLASS 规则）：

> 任何组件要改之前，**先 `web_search "best free <类> 2026"` 跑全网对比**，再决定替换什么，不是直接打补丁。

**修补 vs 进化**：
- 修补：searxng 失败 → 写 fetch_url 替代它
- 进化：searxng 失败 → 全网对比 → 找到 Trafilatura → 替换整个提取器层

## 验证清单（每次升级后跑这 4 步）

```bash
# 1. last30days 软链活着
readlink ~/.hermes/skills/research/last30days
ls ~/.hermes/skills/research/last30days/SKILL.md

# 2. last30days venv 3.12 装好
cd ~/.hermes/skills/research/last30days-skill-main
.venv/bin/python -c "import requests, click, rich; print('OK 3.12')"

# 3. last30days 真能跑（实测 4 源）
.venv/bin/python skills/last30days/scripts/last30days.py "Hermes Agent" --emit=compact 2>&1 | head -3
# 应该看到: Reddit 12 threads, YouTube 9 videos, HN 8 stories, GitHub 8 results

# 4. fetch_url 能跑
~/.hermes/hermes-agent/venv/bin/python ~/.hermes/scripts/fetch_url.py "https://hermes-agent.nousresearch.com/" --title-only
# 应该看到: 📄 Hermes Agent — The Agent That Grows With You | Nous Research

# 5. search.py 三层降级跑通
~/.hermes/hermes-agent/venv/bin/python ~/.hermes/scripts/search.py "RTX 5090 价格"
# 应该看到: 🔍 路由 + 5 条结果
# 第二次跑应该看到: 💾 [缓存命中] RTX 5090 价格
```

## 性能数据

### v1（JSON 缓存 + html2text）— 2026-06-07 早

| 场景 | 第 1 次 | 第 2 次（缓存） | 节省 |
|------|---------|-----------------|------|
| 模糊查询（双引擎） | 18.5s | 0.023s | 99.9% |
| 抓取 URL 全文 | 0.5-1s | <0.05s | 90%+ |
| 舆情查询（last30days 主） | 10.9s | 0.02s | 99.8% |

### v3.0.0（DiskCache + Trafilatura）— 2026-06-07 04:30

| 场景 | 第 1 次 | 第 2 次（缓存） | 节省 |
|------|---------|-----------------|------|
| 模糊查询（双引擎） | 4.6s | **0.035s** | 99.2% |
| 抓取 URL 全文 | 0.4s | 0.16s | 60% |
| 舆情查询（last30days 主） | 10.9s | 0.035s | 99.7% |
| **DiskCache 1000 写** | **0.063s** | — | （vs JSON 1s+）|
| **Trafilatura 提取质量** | 真文 | — | （vs html2text 100% nav 垃圾）|

## 总结：免费联网搜索栈

```
                ┌─────────────────────────────────────────┐
                │  统一入口: search.py "查询"            │
                └────────────────┬────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
        ┌──────────┐        ┌──────────┐       ┌──────────┐
        │anysearch │        │last30days│       │fetch_url │
        │通用/事实 │        │过去30天  │       │本地抓URL │
        │(免费)    │        │(免费)    │       │(免费)    │
        └──────────┘        └──────────┘       └──────────┘
              │                  │
              ▼                  ▼
        ┌──────────┐        ┌──────────┐
        │DDGS 兜底 │        │(无降级，  │
        │(免费)    │        │ 社媒无替)│
        └──────────┘        └──────────┘
              │
              ▼
        ┌──────────┐
        │curl DDG  │
        │应急(免费)│
        └──────────┘
              +
        ┌─────────────────────┐
        │ 24h 缓存层(DiskCache)│
        │ ~/.hermes/cache/     │
        │ 自动 TTL+LRU+原子写 │
        └─────────────────────┘
        ```

        **关键文件**（v3.0.0）：

        - `~/.hermes/scripts/search.py`（v3.1，~250 行 Python，统一入口 + DiskCache 缓存）
        - `~/.hermes/scripts/fetch_url.py`（v2，~250 行 Python，Trafilatura 主提取 + DiskCache 缓存）
        - `~/.hermes/hermes-agent/venv/`（3.14，fetch_url 跑这，html2text/trafilatura/diskcache 装这）
        - `~/.hermes/skills/research/last30days-skill-main/.venv/`（3.12，last30days 跑这，3 个核心包）
        - `~/.hermes/cache/search/`（DiskCache 格式）
        - `~/.hermes/cache/fetch_url_v2/`（DiskCache 格式）

**关键原则**：

- 用户管入口（搜什么、查什么）→ 我管实现（哪个引擎、怎么降级）
- 全部免费（0 元 API 成本）
- 缓存优先（重复查询秒返）
- 三层降级（anysearch → DDGS → curl DDG）
- 软链用户接口 + 真路径程序接口
