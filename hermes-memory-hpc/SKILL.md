---
name: hermes-memory-hpc
description: "Memory hygiene + system-level persistent memory. NOTE: Supplier/procurement business memory is user-owned, not Hermes-owned. Hermes maintains only system config, tool state, and technical learnings."
---

# hermes-memory-hpc

**核心原则：Hermes 不拥有商业数据记忆，只拥有系统级技术记忆。**

当用户说"跟采购和1688相关全部删除" → 立即清除所有 fact_store + memory.md + user.md 中的商业相关内容，保留系统配置。

## 记忆分类

| 类型 | 归属 | 示例 |
|------|------|------|
| 商业数据 | 用户 owns | 供应商、 价格、采购案例、公司名 |
| 系统配置 | Hermes owns | CDP端口、Chrome PID、工具路径、学习到的技术 |
| 核心准则 | Hermes owns | 真人化行为准则、硬件约束、自我修复机制 |

## 存储方案

| 工具 | 用途 | 大小 |
|------|------|------|
| fact_store | 实体知识、系统级事实、验证过的技术 | ~80KB |
| memory.md | 系统配置、工具状态、运行约束 | <5KB |
| user.md | 用户偏好、沟通风格、硬约束 | <3KB |
| state.db | session历史（自动，不碰） | 1.2GB |

## 触发条件

- 采购完成后 → **不存** Hermes，Hermes不拥有采购数据
- 询价前 → **不查询** 供应商数据库，直接去1688实时搜
- 系统配置变更 → 立即更新 fact_store + memory.md
- 学会新技术/工具用法 → 写入 fact_store

## 存储方案（已升级 V2）

**实际存储**：ChromaDB 持久化向量数据库（`~/.hermes/supplier_memory/`），而非 SKILL.md 旧版声称的 JSON 文件。

ChromaDB 提供了按标签过滤（`where={"supplier": "xxx"}`）和语义搜索（`query_texts=[...]`）的能力，比 JSON 文件更适合"查询供应商历史"场景。

> ⚠️ 历史遗留：旧版 SKILL.md 写的是 JSON 文件存储（`/tmp/hermes_supplier_memory.json`），实际代码早已迁移到 ChromaDB。如果看到 SKILL.md 和代码矛盾，以 `memory_hpc.py` 为准。

---

## V2 主动召回架构（memory_v2.py）

memory_v2.py 在 memory_hpc.py 基础上新增三层：

| 层 | 组件 | 作用 |
|----|------|------|
| L1 | ChromaDB `memories_v2` | 原始记忆，向量存储 |
| L2 | `detect_scenario()` | 场景标签（采购询价/1688运营/系统配置/日常闲聊） |
| L3 | `user_profile.json` | 用户画像（价格敏感度、常用平台、供应商偏好） |
| Hook | `proactive_recall()` | **每轮对话前自动召回**，把相关记忆注入 context |

### 场景检测关键词

```python
SCENARIOS = {
    "采购询价": ["供应商", "报价", "价格", "交期", "便宜", "进货", "拿货", "货源"],
    "1688运营": ["1688", "商品", "标题", "主图", "价格修改", "发布", "上架", "SKU"],
    "系统配置": ["安装", "配置", "npm", "Docker", "端口", "启动", "重启", "报错"],
    "记忆管理": ["记忆", "忘记", "记得", "存了没", "召回", "搜索"],
    "日常闲聊": [],  # 无关键词时默认
}
```

### 核心函数

```python
import sys
sys.path.insert(0, '/Users/aimac/.hermes/hermes-memory-hpc')

from memory_v2 import (
    proactive_recall,      # ← 每轮对话前自动调用
    detect_scenario,       # 手动触发场景检测
    remember,              # L1+L2 存入（自动打场景标签）
    recall,                # L1+L2 双重召回
    get_user_profile,      # L3 画像查询
    get_profile_summary,   # L3 画像摘要
    remember_supplier,     # 兼容旧接口
)

# 每轮对话前调用一次，返回格式化记忆字符串，注入 LLM context
context = proactive_recall("用户刚才说的话")
```

### 用户数据清理原则

用户说"全部删掉"→立即删除：
```bash
rm -rf ~/.hermes/supplier_memory    # ChromaDB 数据
rm -f ~/.hermes/user_profile.json    # 画像数据
```
- `memory_v2.py` 代码保留，下次写入时自动重建空库
- 清理完后重新自检：`python3 memory_v2.py`

---

## 旧版接口（memory_hpc.py）

旧版 `memory_hpc.py` 的 `suppliers` / `conversations` collection 已废弃，数据已清。新代码统一用 `memory_v2.py` 的 `memories_v2` / `conversations_v2` collection。

如需回退旧接口，import 方式：
```python
from memory_hpc import remember_supplier, recall_supplier  # 兼容包装函数仍有效
```

---

## 触发条件

- 采购完成后 → `remember_supplier()` 或 `remember()` 存入记忆
- 询价前 → `proactive_recall()` 自动召回（无需手动调用）
- 对话中 → `detect_scenario()` 判断场景类型
- 用户要求清空 → `rm -rf ~/.hermes/supplier_memory && rm -f ~/.hermes/user_profile.json`

## 数据存储

- **数据库位置**：`~/.hermes/supplier_memory/`（ChromaDB 持久化目录）
- **V2 集合名**：`memories_v2`、`conversations_v2`
- **画像文件**：`~/.hermes/user_profile.json`
- **每条记录**：L1 content + L2 scenario 标签 + L3 metadata

## 数据存储

- **数据库位置**：`~/.hermes/supplier_memory/`（ChromaDB 持久化目录）
- **集合名**：`memories_v2`（V2主记忆）、`conversations_v2`（对话历史）
- **画像**：`~/.hermes/user_profile.json`
- **ID 格式**：`mem_{timestamp_ms}`

## 快速使用

```python
import sys
sys.path.insert(0, '/Users/aimac/.hermes/hermes-memory-hpc')

from memory_v2 import (
    proactive_recall,       # ← 每轮对话前自动调用（核心新增）
    detect_scenario,        # 手动场景检测
    remember,               # L1+L2 存入
    recall,                 # L1+L2 双重召回
    get_user_profile,       # L3 画像
    get_profile_summary,    # L3 摘要
    remember_supplier,      # 兼容旧接口
    recall_supplier,        # 兼容旧接口
)

# 每轮对话前：自动场景检测 + 召回 + 画像注入
context = proactive_recall("用户消息内容")
# 返回格式：
# [采购询价相关记忆]
# 1. [2026-06-02] 义乌星火包装 5.2元 - 纸箱50*40*30
# [用户特征] 平台:1688 | 价格敏感:中 | 偏好:积极配合

# 存入供应商记忆
remember_supplier(
    supplier_name="义乌星火包装",
    product="纸箱 50*40*30",
    price=5.2,
    delivery_days=3,
    attitude="积极",
    notes="老板姓王，说话直接"
)

# 主动场景召回
scenario = detect_scenario("帮我改一下1688商品标题")
# → "1688运营"

# 画像查询
print(get_profile_summary())
```

## 数据存储

- **数据库位置**：`~/.hermes/supplier_memory/`（ChromaDB 持久化目录）
- **集合名**：`suppliers`
- **每条记录**：存储为 JSON 字符串（documents）+ 标签字段（metadatas: supplier, product, price, attitude, source）
- **ID 格式**：`{supplier_name}_{timestamp}`

## ⚠️ 已知坑点

### ChromaDB query() 与 get() 返回格式不同

这是最常踩的坑。ChromaDB 的 query() 和 get() 方法返回的 documents/metadatas 结构不同：

| 方法 | documents 格式 | metadatas 格式 |
|------|---------------|---------------|
| `query()` | `[["doc1", "doc2"]]`（嵌套列表） | `[{"supplier":"..."}]` 或 `[[{...},{...}]]` |
| `get()` | `["doc1", "doc2"]`（扁平列表） | `{"supplier":"..."}` 或 `[{...},{...}]` |

**修复方案**（已写入 `memory_hpc.py`）：

```python
docs = results["documents"]
metas = results.get("metadatas")
if docs and isinstance(docs[0], list):
    docs = docs[0]
if metas and isinstance(metas[0], list):
    metas = metas[0]
```

**症状**：`json.loads(doc)` 报了 `TypeError: the JSON object must be str, bytes or bytearray, not list`——说明 doc 实际是个列表，需要展平一层。

### Qwen3 模型返回单引号 JSON

当用 Qwen 系列模型做 `recall_supplier` 或任何涉及 JSON 解析的流程时，Qwen 习惯返回单引号 JSON（`{'key': 'value'}`），而 Python 的 `json.loads()` 只认双引号。

**修复方案**（已写入 `memory_hpc.py`）：

```python
if isinstance(doc, str) and doc.startswith("{"):
    clean_doc = doc.replace("'", '"')
else:
    clean_doc = doc
data = json.loads(clean_doc)
```

**症状**：`json.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)`——说明 JSON 开头用了单引号。

### 与 emotion 分析联动

```python
from humanization_core import analyze_emotion
from memory_hpc import remember_conversation

# 收到老板消息时
emotion = analyze_emotion("老板消息内容")
remember_conversation(
    role="老板",
    content="老板消息内容",
    tags=[emotion["emotion"], emotion["urgency"]]
)
```

## 已知局限

- 记忆越多查询越慢，ChromaDB 的分页查询可缓解
- 当前用 `where={"supplier": name}` 精确过滤 + 向量语义搜索。不支持跨供应商语义搜索
- ChromaDB 数据持久在 `~/.hermes/supplier_memory/`，不会随聊天 session 消失，但不会自动清理旧数据

## 相关文件

| 文件 | 用途 |
|------|------|
| `~/.hermes/scripts/recall.py` | **Hybrid recall 顶层 API**（FTS5+vec 混合） |
| `~/.hermes/scripts/_fts_trigram_upgrade.py` | 一次性 FTS5→trigram 中文友好迁移 |
| `references/rag-hybrid-recall-2026-06-05.md` | 完整实战笔记：4 测试 query 评分分布 + 4 个必踩坑 stack trace |

## 附: fact_store (memory_store.db) 维护补充

`memory_store.db.facts` 表与 ChromaDB 是**两个独立系统**——ChromaDB 管商业记忆, fact_store 管系统级技术记忆。两套维护规则不能混。

### fact_store 写入模板 (去重 + 退出码)

```python
import sqlite3, sys
FINGERPRINT = "tool_err_2026060400"  # 必带: 日期/小时/类别组合
c = sqlite3.connect('/Users/aimac/.hermes/memory_store.db')
r = c.execute('SELECT 1 FROM facts WHERE tags LIKE ?', (f'%{FINGERPRINT}%',)).fetchone()
if r:
    c.close(); sys.exit(1)  # 已存在
c.execute('INSERT INTO facts (content, category, tags, trust_score) VALUES (?, ?, ?, ?)',
          ('...', 'error_pattern', f'tools,alert,{FINGERPRINT}', 0.7))
c.commit(); c.close()
sys.exit(0)  # 新增
```

### ❌ 常见误操作

1. **`DELETE FROM facts WHERE trust_score < 0.6`** — 危险, 用户的真知识 trust 多 0.5, 一刀切会全删
2. **`INSERT OR IGNORE`** — content 含时间/数字时失效, 必须用 tags 指纹 + SELECT 预检
3. **不验证就信 "写成功"** — FTS5 trigger 偶发不同步, 必须 `SELECT * FROM facts WHERE tags LIKE '%fp%'` 验证

### ✅ 正确清理

- 只删 `created_at < 90d AND trust_score < 0.3` 的老 fact (由 `ai_knowledge_collector.sh` 自动跑)
- 手动删前先 `cp memory_store.db memory_store.db.bak.YYYYMMDD`
- 想"清空重练"? 改 `DELETE WHERE tags LIKE '%dev_%'` (按 tag 前缀精准删), 不要清全表

### FTS5 验证命令

```bash
# 验证 fact 入库
sqlite3 ~/.hermes/memory_store.db "SELECT content, trust_score FROM facts WHERE tags LIKE '%<FINGERPRINT>%'"

# 验证 FTS5 索引同步 (FTS5 偶发不同步, 触发器已修但要测)
sqlite3 ~/.hermes/memory_store.db "SELECT content FROM facts_fts WHERE facts_fts MATCH '<关键词>'"

# 手动同步 FTS5 (如怀疑不同步)
sqlite3 ~/.hermes/memory_store.db "INSERT INTO facts_fts(facts_fts) VALUES('rebuild')"
```

详见 `daily-self-evolution` skill 的"fact_store 维护铁律"小节。

---

## Vector 层 + Hybrid Recall (2026-06-05 落地)

FTS5 解决关键词检索，但**语义检索**（"内存" ≈ "RAM"，"ollama 拉模型" ≈ "下载 GGUF"）需要向量层。本节给出轻量、单 db、零外部依赖的实现。

### 架构

```
                  ~/.hermes/memory_store.db
                  ┌────────────────────────────────┐
                  │ facts (30+ 行)                  │
                  │ facts_fts (BM25 关键词)        │
                  │ facts_vec (sqlite-vec, 768d)   │ ← 语义检索
                  │ entities + fact_entities        │
                  │ memory_banks                    │
                  └────────────────────────────────┘
                          │
              recall.py 顶层 API
              ┌──────────────┴──────────────┐
              │ FTS5 trigram (BM25)         │ → score_f  (0-1)
              │ sqlite-vec (cosine/L2)     │ → score_v  (0-1)
              └──────────────┬──────────────┘
                            │
                  score = (1-α)·score_f + α·score_v   (默认 α=0.5)
                            │
                         top-K
```

**关键决策**（每一步都有治本理由）：

| 决策 | 不选 | 选 | 理由 |
|------|------|----|------|
| 向量库 | qdrant / chroma / milvus | **sqlite-vec 单 extension** | 跟 FTS5 同 db、零额外内存、跟着 fact_store 一起备份 |
| 维度 | 1536 (OpenAI) | **768 (nomic-embed-text)** | 本地离线，Ollama 已有 Ollama，274MB 模型 |
| Embed 模型 | text-embedding-3 | **nomic-embed-text** | 离线、不花 token、Mac M4 Metal 跑 19.7 tok/s |
| 混合权重 | RRF / Cross-encoder | **线性加权 (0.5/0.5)** | 简单可调，5 站内已够用 |

### 一键搭建（实测顺序）

```bash
# 1. 装 Python binding
$HOME/.hermes/hermes-agent/venv/bin/python -m pip install sqlite-vec

# 2. 拉 nomic-embed-text (274MB)
ollama pull nomic-embed-text

# 3. FTS5 升 trigram (中文友好 — 不升命中 0 条中文)
python3 $HOME/.hermes/scripts/_fts_trigram_upgrade.py
#    备份会自动建: memory_store.db.pre_vec.bak + .pre_trigram.bak

# 4. 装 vec 虚拟表 + 30 条 reindex
python3 $HOME/.hermes/scripts/recall.py --reindex
#    30 条实测 0.876s, 0 失败
```

### 查 (recall.py 顶层 API)

```bash
# 5 站内 top-5
python3 $HOME/.hermes/scripts/recall.py "Mac mini M4 内存配置" -k 5

# 调整 vec/FTS 权重 (0=纯 FTS, 1=纯 vec)
python3 $HOME/.hermes/scripts/recall.py "AI Agent 框架" --vec-weight 0.7

# 索引状态
python3 $HOME/.hermes/scripts/recall.py --stats
#   期望: facts=30, FTS5=30, vec=30, 覆盖率 100.0%
```

### Hybrid 评分公式

```python
# FTS5 BM25 归一化 (越小越好, 0=完美, -10=差)
fts_score = max(0, 1 + bm25 / 10)

# sqlite-vec L2 distance 归一化 (越小越好, 0=相同, 1.5=无关)
vec_score = max(0, 1 - distance / 1.5)

# 合并
final = (1 - vec_weight) * fts_score + vec_weight * vec_score
```

### ⚠️ 4 个必踩坑（已踩过）

1. **host_key 没前导点**：`host_key='.claude.ai'` 查不到。Chrome 实际存的是 `host_key='claude.ai'`。**诊断命令**：
   ```python
   conn.execute("SELECT DISTINCT host_key FROM cookies WHERE name='sessionKey'")
   # 期望: 'claude.ai' (无前导点) — 不是 '.claude.ai'
   ```

2. **FTS5 hyphen 触发 column 错误**：query `"GPT-5"` 直接报 `no such column: 5`。
   **修法**：包双引号当 phrase，或 replace `-` 为空格。recall.py 已两层 fallback。

3. **FTS5 默认 unicode61 不支持中文**：`facts_fts MATCH '浏览器'` 命中 0 条。
   **修法**：trigram tokenizer — 见 `_fts_trigram_upgrade.py`。**单字/双字查询（如 "内存"）仍 0 命中**（trigram 最小 3 字符），多字符查询覆盖率正常。

4. **vec 索引可能 0 行**：`recall.py` 第一次跑报错 → 跑 `recall.py --reindex`。**永远跑完查 `--stats` 确认覆盖率 100% 再上线**。

### 文件清单

| 路径 | 用途 |
|------|------|
| `~/.hermes/scripts/recall.py` | **核心 API** — FTS5+vec hybrid，4 站跨 AI 都可读 |
| `~/.hermes/scripts/_fts_trigram_upgrade.py` | 一次性迁移 FTS5→trigram，**有备份** |
| `~/.hermes/memory_store.db` (facts_vec) | 768d 向量虚拟表 |
| `~/.hermes/memory_store.db.pre_*.bak` | vec + trigram 升级前的双备份 |
| `references/rag-hybrid-recall-2026-06-05.md` | **完整实战笔记**：脚本源码、reindex 耗时、4 测试 query 的 score 分布、4 个坑的完整 stack trace |

### 何时**不**用 RAG

- 查询是 1-2 个英文关键词（如 "GPT-5"）→ **纯 FTS5 够**，关 vec 省 50ms
- facts 表 < 5 条 → FTS5 比 vec 准（数据少 vec 噪声大）
- 要跨 9 站 cross-validate 一句话（"AI Agent 框架"）→ **直接 browser_cdp 拉 multi-site 答案**，RAG 是事后归档用
