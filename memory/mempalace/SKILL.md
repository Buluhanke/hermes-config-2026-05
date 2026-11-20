---
name: mempalace
description: MemPalace v3.6.0 — 57K⭐开源AI记忆系统，完整原文存储+语义搜索，R@5=96.6%（零LLM依赖）。Mac M4用CoreML加速。适合：对话历史存档、项目上下文找回、代码片段记忆。触发：需要记忆检索/历史上下文/长期记忆。
version: "1.0.0"
author: Nous Research
license: MIT
group: 记忆
metadata:
  hermes:
    tags: [memory, mempalace, fact-store]
    related_skills:
      - agent-reach
      - deep-research
      - context-compression
triggers:
  - AI记忆系统
  - 对话历史检索
  - 语义搜索记忆
  - 长程上下文
  - mempalace
  - 找回之前的对话
l1: 记忆
l2: mempalace
---

## When to Use

**Use when the task requires long-term memory, conversation history retrieval, project context recall, or any scenario where information must persist across sessions** — MemPalace is the zero-LLM-write-memory layer; pair it with agent-reach for external search when you need both internal memories and external knowledge.

---

# MemPalace v3.6.0 — 57K⭐开源AI记忆系统

```bash
uv tool install mempalace
mkdir -p ~/.mempalace
mempalace init ~/.mempalace --yes
```

## 核心工作流

### 挖掘内容进记忆宫殿
```bash
# 挖掘项目文件
mempalace mine ~/projects/myapp

# 挖掘Claude Code对话历史
mempalace mine ~/.claude/projects/ --mode convos

# 挖掘任意目录
mempalace mine /path/to/anywhere
```

### 语义搜索
```bash
mempalace search "项目决策细节"
mempalace search "某个bug的解决方案"
```

### 唤醒上下文（CLI输出，供agent读取）
```bash
mempalace wake-up
```

### MCP服务器（接入Claude Code等agent）
```bash
mempalace mcp
# 或REST API服务
mempalace serve
```

## 架构概念

- **Wing（翼）**：实体/人/项目
- **Room（房间）**：主题/话题
- **Drawer（抽屉）**：原始内容
- **Hall**：语义主题标签（emotions/consciousness/memory/technical等）

## 后端选择

| 后端 | 模式 | 安装 |
|------|------|------|
| `chroma` | 本地嵌入（默认） | 内置 |
| `sqlite_exact` | 本地精确 | 内置 |
| `qdrant` | 服务器REST | 内置 |
| `pgvector` | Postgres | `mempalace[pgvector]` |
| `milvus` | 本地Lite | `mempalace[milvus]` |

## 验证安装

```bash
mempalace --version   # 3.6.0
mempalace status      # palace状态
```

## 已知坑

- `init` 需要交互式输入，用 `--yes` 自动接受
- Ollama不可用时会报warning，不影响本地embedding（CoreML自动fallback）
- palace默认在 `<dir>/palace` 子目录
- Docker用户：`docker run -i --rm -v mempalace-data:/data mempalace`

## ⚠️ 关键坑：sessions/ ≠ 全部对话

**`~/.hermes/sessions/` 里的JSON文件只是请求转储，不是完整对话。**

Hermes的真实对话存在 `~/.hermes/state.db`（全量消息+全渠道），结构：
```
sessions表：cli/desktop/qqbot/telegram/tui/weixin/subagent
messages表：2854条消息（user+assistant）
```

挖掘 state.db 全渠道对话（一次性步骤）：
```python
# Python提取脚本 → references/state-db-mine.py
import sqlite3, json

conn = sqlite3.connect('/Users/aimac/.hermes/state.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("""
    SELECT m.session_id, s.source, m.role, m.content, m.timestamp
    FROM messages m JOIN sessions s ON m.session_id = s.id
    WHERE m.content IS NOT NULL AND m.content != ''
    AND m.role IN ('user', 'assistant')
    ORDER BY s.source, m.timestamp
""")
records = [{'session_id': r['session_id'], 'source': r['source'],
            'role': r['role'], 'content': r['content'][:2000], 'ts': r['timestamp']}
           for r in cur.fetchall()]
with open('/tmp/hermes_all_channels.jsonl', 'w') as f:
    for r in records: f.write(json.dumps(r, ensure_ascii=False)+'\n')
# 然后：
# mkdir -p ~/.mempalace/hermes_channels
# cp /tmp/hermes_all_channels.jsonl ~/.mempalace/hermes_channels/
# mempalace mine ~/.mempalace/hermes_channels
```

全渠道分布（2026-07实测）：
| 渠道 | 消息数 |
|------|--------|
| qqbot | 668 |
| cli | 210 |
| desktop | 99 |
| tui | 44 |
| weixin | 29 |
| telegram | 6 |
| subagent | 2 |

## 参考文档
- `references/state-db-mine-recipe.md` — state.db 全渠道对话提取脚本、渠道分布数据（2026-07-22实测）、sessions.json 与 request_dump_*.json 的真实含义

## 流式检索与重排（2026 迭代）

### 问题
MemPalace 当前是纯语义向量检索（chroma 后端），检索到的是「最相关的 N 个原文」，但未经过多源重排。对 100+ 条检索结果，语义相似度最高的 10 条不一定是最终最有价值的 10 条——同一答案可能出现在多个房间，语义相似度高的旧情绪条目会挤压事实类条目。

### 解决：三层检索流水线

```python
# 1. 检索：BM25（关键词）+ 向量（语义）+ 图谱（实体链接）三管齐下
bm25_results = palace.bm25_search(query)
vector_results = palace.vector_search(query)
graph_results = palace.graph_search(query)   # 实体 → 关联房间

# 2. 归一化：BM25 按 idf 得分，向量按 cosine 得分，图谱按相邻层级
scores = normalize(bm25_scores) + normalize(vector_scores) + normalize(graph_scores)

# 3. 重排：RRF（Reciprocal Rank Fusion）合并，权重可调
# rrf = 1 / (k + rank_i)  对每个来源独立排名求和
rrf_scores = rrf(bm25_results, vector_results, graph_results, k=60)

# 4. 输出：按 rrf 得分排序，取 top-5 做最终展示
final_results = sort_by_rrf(rrf_scores)[:5]
```

### 坑
- BM25 对中文细微差别（如「北向资金」vs「北向资金异常」）不敏感，需用分词器（jieba）预处理
- 图谱检索容易死循环，如同一个实体出现在多个房间，需要去重
- RRF 的 k 值（默认 60）需根据检索池规模标定，池太小 k 太大会压扁差异，池太大 k 太小会只返回第一来源

### 替代方案
- Mem0 / Hindsight 的多策略检索（TEMPR）是成熟参考
- 若要零 LLM 写路径，BM25+向量+重排仍可行；若要更高召回，考虑在 Chroma 之外叠一个轻量图索引
