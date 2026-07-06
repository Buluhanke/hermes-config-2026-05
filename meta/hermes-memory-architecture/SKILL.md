---
name: hermes-memory-architecture
description: Hermes 记忆系统真实架构 — 2026-07-08实测版本。MEMORY.md+USER.md+concept_store.md为文件系统层，LanceDB为语义层，fact_store.db为legacy空库。记忆审计必须先验证真实状态再操作。
version: 1.0.0
created: 2026-07-08
updated: 2026-07-08
type: reference
category: meta
triggers:
  - "记忆审计"
  - "memory audit"
  - "查记忆"
  - "清理记忆"
  - "记忆满了"
  - "fact_store"
  - "lancedb"
  - "semantic memory"
  - "清理memories"
---

# Hermes Memory Architecture — 实测版 (v1.0)

**注意：hub skill memory-cn 描述的是旧架构（Mnemosyne），以下为 2026-07-08 实测真实状态。**

## 记忆系统真实架构

| 组件 | 路径 | 用途 | 上限 | 状态 |
|---|---|---|---|---|
| `MEMORY.md` | `~/.hermes/memories/` | 系统技术记忆（配置/调试/Chrome/技能/挂起任务），与USER.md内容不重叠 | 66,000字符 | 3.7KB ✅ |
| `USER.md` | `~/.hermes/memories/` | 用户偏好/铁律/Ponytail/决策风格，与MEMORY.md内容不重叠 | 66,000字符 | 2.6KB ✅ |
| `concept_store.md` | `~/.hermes/memories/` | 19条抽象经验规则 | 无 | 9KB ✅ |
| `chrome-cdp-ax-tree.md` | `~/.hermes/memories/` | CDP技术文档 | 无 | 2KB ✅ |
| `fact_store.md` | `~/.hermes/memories/` | 空库说明 | 无 | 309B |
| `fact_store.db` | `~/.hermes/memories/` | FTS5 SQLite，**当前0行，legacy待启用** | — | 28KB, 0行 |
| `LanceDB` | `~/.hermes/lancedb/memories.lance/` | 语义记忆（session结束后自动提取写入） | 无 | 0行，待首次session结束 |

## 配置状态

```bash
# memory.provider 当前配置
hermes config show | grep -A5 "memory:"

# memory_char_limit 当前值
grep memory_char_limit ~/.hermes/config.yaml
# 当前值: 66000 (2026-07-08 已从6600扩容)

# LanceDB 验证
hermes memory status
```

## 审计标准流程

**先验证再操作，禁止未读完文件就决策：**

```
步骤1 ls -la ~/.hermes/memories/         → 列出所有文件+大小
步骤2 sqlite3 fact_store.db ".schema"     → 查真实表结构（skill文档可能过时）
步骤3 sqlite3 fact_store.db "SELECT COUNT(*) FROM facts" → 查实际行数
步骤4 diff USER.md MEMORY.md              → 查两文件重复内容
步骤5 grep -c "过时关键词" *.md            → 查过时引用(ChromaDB/GBrain/Mnemosyne)
步骤6 确认后再操作：删除/合并/修改
```

**教训**：memory-cn skill 描述 Mnemosyne 为 active provider，但实际已切换到 LanceDB。skill文档 ≠ 真实状态。每次必须先验证。

## 记忆文件审计清单

| 检查项 | 命令 | 期望结果 |
|---|---|---|
| 所有文件大小 | `ls -la ~/.hermes/memories/` | 无0字节垃圾文件 |
| fact_store结构 | `sqlite3 fact_store.db ".schema"` | 字段: id/key/value/source/confidence/created_at/updated_at |
| fact_store行数 | `sqlite3 fact_store.db "SELECT COUNT(*) FROM facts"` | 当前为0 |
| LanceDB行数 | `~/.hermes/hermes-agent/venv/bin/python3 -c "import lancedb; ..."` | 当前为0，新库 |
| MEMORY/USER重复 | `grep -c "Ponytail\|数字主人\|先装再清" MEMORY.md` | 应为0 |
| 过时引用 | `grep "ChromaDB\|GBrain\|Mnemosyne" *.md` | 应无或已修正 |

## 精简合并规则

**定位分离**：
- `MEMORY.md` = 纯技术操作（配置/调试/Chrome/搜索/技能/挂起任务）
- `USER.md` = 用户偏好/铁律/Ponytail/决策风格
- 两文件内容不重叠，grep交叉验证应为0

**可删除**：
- `archive/` 空目录
- `*.lock` 锁文件
- 与另一文件内容重复的章节

**human-core-memory.md**：已删除（与USER.md重复），其"学习路径"章节已合并入MEMORY.md。

## LanceDB 插件

- 安装：`hermes plugins install lancedb/hermes-agent-memory`
- 启用：`hermes plugins enable lancedb`
- 依赖：`uv pip install --python ~/.hermes/hermes-agent/venv/bin/python3 lancedb openai pyyaml`
- 工具：`lancedb_recall` / `lancedb_remember` / `lancedb_read` / `lancedb_forget`
- 触发：session结束后 on_session_end 自动提取事实写入

## 相关 Skills

- `memory-cn`（hub skill，受保护不可修改，**内容可能过时**）
- `concept_store.md`（本地，记忆层次结构第5层）
- `context-optimization`（token优化）
