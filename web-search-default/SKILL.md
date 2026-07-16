---
name: web-search-default
version: 1.1.0
description: 联网搜索固化路径 — 任何搜索任务立即执行，优先 web_search + firecrawl/serper
triggers:
  - 联网搜索
  - 搜索一下
  - 查一下
  - web search
  - 搜索
  - 全网搜索
  - 你全网搜索
---

# 联网搜索固化路径

## 触发条件
任何需要联网搜索的任务 → **0思考立即执行 web_search**，不先回复"正在搜索"。

**绝对禁止**：先说"正在搜索..."再用工具。说了两次"全网搜索"才执行 = Failure 71。

## 搜索路径（按优先级）

### 路径A（默认快速搜索）
```
web_search（自动路由，最快返回）
```

### 路径B（指定 provider）
```
web_search_plus(provider=firecrawl)   # 主选，内容质量高
web_search_plus(provider=serper)      # 备选
```

### 路径C（复杂研究/多来源）
```
web_search_plus(depth=deep-reasoning, provider=firecrawl)
→ web_extract_plus(provider=firecrawl)
→ browser_navigate（兜底）
```

### 路径D（提取页面内容）
```
web_extract / web_extract_plus(provider=firecrawl)
```

## API Keys 配置
- `~/.hermes/.env` 写入：
  - `SERPER_API_KEY=cd64fc17664b5dd5c77f18251d1e682f39336f92`
  - `FIRECRAWL_API_KEY=ac20d764428940c2a3e08c211845116f6aeba88af2c`
- env 变更后必须重启 gateway 才生效

## Gateway 重启（env 变更后必走）
1. `write_file /tmp/do_restart.sh` → 内容：`launchctl kickstart -k gui/501/ai.hermes.gateway`
2. `bash /tmp/do_restart.sh`

## 铁律
- 联网搜索任务用 web_search，不用截图 OCR
- 先搜索再提取，不用 AI summarize 代替原始搜索
- 遇到问题换 provider，不停下来等授权

## 长期记忆方案研究（2026-07）

| 方案 | 评价 | 状态 |
|------|------|------|
| **Mnemosyne** (mnemosyne-oss, 1.3k stars) | ⭐ Hermes专用，零依赖SQLite，v3.10，40 contributors | 候选 |
| **Mem0** | benchmark 92.5 LoCoMo，21框架集成 | 备选 |
| **Hermes FTS5 Semantic Skill Retrieval** | Issue #17649，官方开发中 | 待上线 |
| **现有 MEMORY.md + fact_store** | 2200字符限制，架构性缺陷 | 待替换 |

**推荐**：pip install mnemosyne-memory 替换现有方案。详见 `references/memory-systems-research.md`。
