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

## 存储方案

**实际存储**：ChromaDB 持久化向量数据库（`~/.hermes/supplier_memory/`），而非 SKILL.md 旧版声称的 JSON 文件。

ChromaDB 提供了按标签过滤（`where={"supplier": "xxx"}`）和语义搜索（`query_texts=[...]`）的能力，比 JSON 文件更适合"查询供应商历史"场景。

> ⚠️ 历史遗留：旧版 SKILL.md 写的是 JSON 文件存储（`/tmp/hermes_supplier_memory.json`），实际代码早已迁移到 ChromaDB。如果看到 SKILL.md 和代码矛盾，以 `memory_hpc.py` 为准。

## 触发条件

- 采购完成后，调用 `remember_supplier()` 存入记忆
- 询价前，调用 `recall_supplier()` 或 `get_supplier_summary()` 唤醒记忆
- 对比供应商时，调用 `compare_suppliers()`

## 快速使用

```python
import sys
sys.path.insert(0, '/Users/aimac/.hermes/skills/hermes-memory-hpc')

from memory_hpc import (
    remember_supplier,      # 存入供应商记忆
    recall_supplier,        # 语义搜索记忆
    get_supplier_summary,   # 生成摘要
    compare_suppliers,      # 对比两家供应商
    remember_conversation,  # 记录老板消息/对话
)

# 采购结束后存入记忆
remember_supplier(
    supplier_name="义乌星火包装",
    product="纸箱 50*40*30",
    price=5.2,
    delivery_days=3,
    attitude="积极",
    notes="老板姓王，说话直接"
)

# 询价前语义查询（ChromaDB 向量搜索）
print(recall_supplier("义乌星火包装", query="价格"))

# 生成人类可读摘要
print(get_supplier_summary("义乌星火包装"))

# 对比两个供应商
print(compare_suppliers("义乌星火包装", "温州华鑫纸业", "纸箱"))
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
