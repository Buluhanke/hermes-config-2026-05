---
name: hermes-memory-hpc
description: "Phase 3 核心：供应商长期记忆，像老员工一样有记忆。"
---

# hermes-memory-hpc

**Phase 3 核心**：供应商长期记忆，像老员工一样有记忆。

---

## 三层记忆架构（Three-Layer Memory Architecture）

```
┌─────────────────────────────────────────────────────┐
│  L1 短期记忆（Session Working Memory）               │
│  容量：当前 session 的对话上下文，约 20 条            │
│  淘汰：session 结束即丢弃                            │
│  用途：当前任务、进行中的询价/谈判状态               │
├─────────────────────────────────────────────────────┤
│  L2 中期记忆（ChromaDB Supplier Memory）            │
│  容量：~1000 条供应商记录                           │
│  淘汰：权重衰减至阈值（见"记忆权重衰减"）           │
│  用途：供应商历史、价格、交期、态度摘要             │
├─────────────────────────────────────────────────────┤
│  L3 长期记忆（Obsidian Knowledge Graph）           │
│  容量：无限制，持久化在文件系统                     │
│  淘汰：永不丢失，重要性降级时归档                   │
│  用途：老板心理模型、行业知识、供应商关系网络       │
└─────────────────────────────────────────────────────┘
```

### 层间数据流转

```
用户输入 → L1 过滤
  ├─ 如果是供应商查询 → L2 向量搜索 → 回复 + 可选写回 L1
  ├─ 如果涉及老板偏好 → L3 Obsidian 查询 → 更新老板心理模型
  └─ 重要交互 → 异步写入 L2（ChromaDB）+ L3（Obsidian）
```

---

## 记忆权重衰减（Memory Weight Decay）

### 衰减公式

```
W(t) = W₀ × e^(-λt) × I^p
```

- `W₀`：初始权重（首次交互时 = 1.0）
- `λ`：衰减率参数（默认 0.05/月）
- `t`：距上次交互的月数
- `I`：重要性因子（interaction importance）
  - 成交订单：I = 2.0
  - 老板负面情绪事件：I = 1.8
  - 普通询价：I = 1.0
  - 无回复的报价请求：I = 0.6
- `p`：加权指数（默认 1.0）

### 衰减调度策略

```python
# 每小时轻量检查（基于文件时间戳，不加载数据库）
# 每天深度检查（加载全量数据，重新计算权重）
# 每月归档：权重 < 0.15 的记录移至 Obsidian 归档库

ARCHIVE_THRESHOLD = 0.15   # 低于此值归档到 Obsidian
DELETE_THRESHOLD  = 0.05   # 低于此值从 ChromaDB 删除（已归档前提下）
DECAY_RATE_LAMBDA = 0.05   # 月衰减率
```

### 交互权重加成（Boost）

每次新交互时，根据结果更新权重：

| 交互类型 | 权重变化 |
|---------|---------|
| 成交 | W = max(W, 1.0)，重置衰减计时 |
| 投诉/负面 | W × 1.5，重置衰减计时 |
| 无回复报价 | W × 0.8 |
| 主动询价（未成交） | W × 1.1 |

---

## 老板心理模型（Boss Psychology Model）

老板的记忆不是客观事实库，而是**带有情绪标签的主观经验图谱**。

### 心理模型数据结构

```yaml
老板画像:
  name: "用户"  # 加密存储
  决策风格: "成本优先型 | 质量优先型 | 关系型 | 速度优先型"
  价格敏感度: 1-10  # 10=极致低价，1=不在乎价格
  情绪触发器:
    - "反复压价超过3次"
    - "交货延迟超过2天"
    - "态度敷衍"
  偏好供应商特征:
    - "爽快不啰嗦"
    - "能赊账"
    - "有现货"
  禁忌:
    - "介绍竞品"
    - "报价含含糊糊"
```

### 老板心理模型更新时机

```python
# 每次老板对话后调用
update_boss_model(
    conversation_summary="讨论了纸箱采购，老板嫌价格太高",
    emotional_tags=["不满", "议价中"],
    decision_made="暂缓，要求再压价10%"
)

# 每次成交后调用
record_deal_outcome(
    supplier="义乌星火",
    boss_reaction="满意，说以后就这家",
    repeat_order_likelihood="高"
)
```

### 心理模型在推理中的应用

> **重要**：老板心理模型是 **L3 长期记忆（Obsidian）** 的一部分，每次决策前先查询模型，避免触发老板禁忌。

```
询价前检查：
1. 查询老板价格敏感度 → 决定是否主动报低价
2. 查询老板情绪触发器 → 避免提及竞品/压价次数
3. 查询老板偏好 → 优先推荐符合偏好的供应商
```

---

## Obsidian 集成方案（Obsidian Integration）

### 目标

将 L3 长期记忆存储在 Obsidian vault 中，利用 Obsidian 的双向链接、查询和图谱视图构建供应商关系网络和老板心理模型知识图谱。

### 目录结构

```
~/Obsidian/hermes-memory/
├── 00 老板档案/
│   ├── 老板心理模型.md
│   ├── 决策风格.md
│   └── 情绪日志/
│       └── 2025-05-17.md
├── 01 供应商库/
│   ├── 活跃供应商/
│   │   ├── 义乌星火包装.md
│   │   └── 温州华鑫纸业.md
│   └── 归档供应商/
│       └── [归档记录]
├── 02 供应商关系图谱/
│   └── supplier-relationships.graph.md  # 使用 Obsidian graph view
├── 03 行业知识/
│   ├── 纸箱行业.md
│   └── 物流时效.md
└── 04 决策记录/
    └── 2025-05 采购决策日志.md
```

### Obsidian 元数据格式（YAML frontmatter）

```yaml
---
supplier: 义乌星火包装
type: 活跃供应商
last_contact: 2025-05-10
weight: 0.85
products:
  - 纸箱 50*40*30
  - 泡沫箱
contact: 王老板 138xxxx
tags:
  - 包装
  - 纸箱
  - 积极
aliases:
  - 星火包装
  - 义乌星火
last_interaction:
  date: 2025-05-10
  summary: 询价纸箱，老板回复快
  outcome: pending
emotion_log:
  - date: 2025-05-10
    emotion: 积极
    note: 响应迅速
---

# 供应商详情

## 价格历史
| 日期 | 产品 | 单价 | 备注 |
|------|------|------|------|
| 2025-05-10 | 纸箱 50*40*30 | ¥5.2 | 报价含税 |

## 交互摘要
（双向链接到 [[老板心理模型]] 和相关 [[决策记录]]）
```

### 核心操作

#### 1. 存入 Obsidian（写入）

```python
from memory_hpc import save_to_obsidian

# 供应商记录写入
save_to_obsidian(
    vault_path="~/Obsidian/hermes-memory",
    record_type="supplier",  # supplier | boss_model | decision_log
    data={
        "supplier": "义乌星火包装",
        "type": "活跃供应商",
        "weight": 0.85,
        "last_contact": "2025-05-10",
        "content": "## 价格历史\n\n| 日期 | 产品 | 单价 |\n|------|------|------|\n| 2025-05-10 | 纸箱 | ¥5.2 |"
    }
)

# 老板心理模型更新
save_to_obsidian(
    vault_path="~/Obsidian/hermes-memory",
    record_type="boss_model",
    data={
        "type": "心理模型更新",
        "emotion": "不满",
        "trigger": "价格谈不拢",
        "summary": "老板对当前报价不满意，要求再压10%"
    }
)
```

#### 2. 查询 Obsidian（读取）

```python
from memory_hpc import query_obsidian

# 查询老板心理模型
print(query_obsidian(
    vault_path="~/Obsidian/hermes-memory",
    query="价格敏感度"
))

# 查询供应商历史
print(query_obsidian(
    vault_path="~/Obsidian/hermes-memory",
    query="义乌星火"
))

# 生成供应商关系图谱数据（Obsidian Graph View 兼容格式）
print(query_obsidian(
    vault_path="~/Obsidian/hermes-memory",
    query="supplier graph data",
    format="graph"  # 返回 JSON 格式的节点和边
))
```

#### 3. 归档策略

```python
# ChromaDB 权重低于阈值时，自动归档到 Obsidian
# 不删除 ChromaDB 记录，只标记为"已归档"，Obsidian 作为永久备份

if current_weight < ARCHIVE_THRESHOLD:
    # 导出到 Obsidian 归档目录
    archive_to_obsidian(supplier_name, full_record)
    # 标记 ChromaDB 记录
    mark_as_archived(supplier_name)
```

### ChromaDB ↔ Obsidian 协同原则

| 数据类型 | 主要存储 | 备份 | 查询频率 |
|---------|---------|------|---------|
| 供应商向量（语义搜索） | ChromaDB | Obsidian | 高频 |
| 老板心理模型 | Obsidian | ChromaDB（JSON） | 中频 |
| 决策日志 | Obsidian | — | 低频 |
| 行业知识 | Obsidian | — | 低频 |

---

## 存储方案

**实际存储**：ChromaDB 持久化向量数据库（`~/.hermes/supplier_memory/`），而非 SKILL.md 旧版声称的 JSON 文件。

ChromaDB 提供了按标签过滤（`where={"supplier": "xxx"}`）和语义搜索（`query_texts=[...]`）的能力，比 JSON 文件更适合"查询供应商历史"场景。

> ⚠️ 历史遗留：旧版 SKILL.md 写的是 JSON 文件存储（`/tmp/hermes_supplier_memory.json`），实际代码早已迁移到 ChromaDB。如果看到 SKILL.md 和代码矛盾，以 `memory_hpc.py` 为准。

## 触发条件

- 采购完成后，调用 `remember_supplier()` 存入记忆
- 询价前，调用 `recall_supplier()` 或 `get_supplier_summary()` 唤醒记忆
- 对比供应商时，调用 `compare_suppliers()`
- **新增**：老板对话后调用 `update_boss_model()`，ChromaDB 权重低于阈值时自动归档至 Obsidian

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
    update_boss_model,      # 更新老板心理模型（新增）
    query_obsidian,          # 查询 Obsidian 知识库（新增）
    save_to_obsidian,       # 写入 Obsidian（新增）
    get_decayed_weight,     # 获取当前衰减权重（新增）
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

# 老板对话后更新心理模型
update_boss_model(
    conversation_summary="讨论了纸箱采购，老板嫌价格太高",
    emotional_tags=["不满", "议价中"],
    decision_made="暂缓，要求再压价10%"
)

# 查询老板心理（Obsidian）
boss_model = query_obsidian(
    vault_path="~/Obsidian/hermes-memory",
    query="价格敏感度"
)
print(boss_model)
```

## 数据存储

### ChromaDB（L2 中期记忆）

- **数据库位置**：`~/.hermes/supplier_memory/`（ChromaDB 持久化目录）
- **集合名**：`suppliers`
- **每条记录**：存储为 JSON 字符串（documents）+ 标签字段（metadatas: supplier, product, price, attitude, source）
- **ID 格式**：`{supplier_name}_{timestamp}`
- **权重字段**：`metadatas` 中含 `weight`（衰减后权重）和 `last_interaction`（上次交互时间戳）

### Obsidian（L3 长期记忆）

- **Vault 位置**：`~/Obsidian/hermes-memory/`
- **主要笔记**：老板心理模型、供应商归档、行业知识
- **格式**：Markdown + YAML frontmatter，支持双向链接和图谱视图

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
from memory_hpc import remember_conversation, update_boss_model

# 收到老板消息时
emotion = analyze_emotion("老板消息内容")
remember_conversation(
    role="老板",
    content="老板消息内容",
    tags=[emotion["emotion"], emotion["urgency"]]
)

# 同步更新老板心理模型（情绪触发器）
update_boss_model(
    conversation_summary="老板消息内容",
    emotional_tags=[emotion["emotion"]],
    decision_made=None
)
```

## 已知局限

- 记忆越多查询越慢，ChromaDB 的分页查询可缓解
- 当前用 `where={"supplier": name}` 精确过滤 + 向量语义搜索。不支持跨供应商语义搜索
- ChromaDB 数据持久在 `~/.hermes/supplier_memory/`，不会随聊天 session 消失，但不会自动清理旧数据
- **新增**：Obsidian 集成依赖本地 vault 路径，需确保 `~/Obsidian/hermes-memory/` 存在
