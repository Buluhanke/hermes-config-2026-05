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
