---
name: web-search-enhanced
version: "1.0.0"
description: "搜索增强 新鲜度过滤来源评级自适应重试。Use when 搜索要求高质量要滤掉旧闻"
triggers:
  - 联网搜索
  - 搜索一下
  - 查一下
  - web search
  - 搜索
  - 全网搜索
---

# Web Search Enhanced — 搜索增强三层架构

## 整体架构

```
web_search 原始结果
    ↓
【Layer 1】 freshness + 来源评级
    ↓
【Layer 2】质量判定 + 自适应重试
    ↓
【Layer 3】搜索历史 → fact_store
    ↓
最终结果返回用户
```

**设计原则：每层独立，不相互调用，只共享数据 schema。**

---

## Layer 1 — Freshness + 来源评级

### 1a. Freshness 过滤（默认一个月内）

用户没指定时间范围时，默认过滤一个月内的结果。

### 1b. 来源质量评级

| 等级 | 标识 | 来源类型 |
|---|---|---|
| A | 一手 | 官方文档/arXiv/GitHub README/知名媒体 |
| B | 专业 | 行业报告/StackOverflow/知乎 |
| C | 聚合 | 百度百科/简书/个人博客 |
| D | AI摘要 | 疑似AI批量生成内容 |

展示格式：`[时间|等级] 标题 | URL`

---

## Layer 2 — 质量判定 + 自适应重试

低质量时（<3条结果 + 全部C/D级）自动换词重试，最多2次。

重试策略：同义词替换 → 换角度搜索

结果合并去重，末尾附质量报告。

---

## Layer 3 — 搜索历史存档

搜索完成后写入 fact_store：

```
web_search | 日期 | query | results数量 | 来源分布 | AI摘要数量
```

tags 提取 query 中的实体词。

下次搜索同实体时，先 probe 历史记录并提示用户。

---

## 实施状态

| 层级 | 状态 | 实现位置 |
|---|---|---|
| Layer 1 freshness | ✅ 固化 | `~/.hermes/scripts/search_enhance.py` |
| Layer 1 来源评级 | ✅ 固化 | `~/.hermes/scripts/search_enhance.py` |
| Layer 2 自适应重试 | ✅ 固化 | `~/.hermes/scripts/search_enhance.py` |
| Layer 3 fact写入 | ✅ 固化 | `~/.hermes/scripts/search_enhance.py`（需从 agent 内调用） |

## 使用方式（agent 内调用）

```python
# 在 execute_code 或 agent 工具链中：
import sys
sys.path.insert(0, '/Users/aimac/.hermes/scripts')
from search_enhance import enhance_search, format_output
from hermes_tools import web_search, fact_store

results, report = enhance_search(
    query="用户查询词",
    web_search_func=web_search,
    max_retries=2,
    do_fact_store=True,
    fact_store_func=fact_store,
)

# 输出带来源评级 + 质量报告
print(format_output(results, report))
```

## 验证结果（2026-08-06 实测）

- "Qwen3.8发布 2026年8月" → 1次搜索，8条结果，一手1专业1未知6，✅ 无需重试
- "这是什么"（模糊词）→ 触发2次重试，共3次搜索，自动换角度，质量报告显示"自动重试2次" ✅

## fact_store 写入格式

每次有效搜索完成自动写入，content 格式：
`web_search | 2026-08-06 | query: xxx | results:N | 来源:grade_count | 时间:range`

tags 提取自 query 实体词，下次搜索同实体时先 probe 已有历史。
