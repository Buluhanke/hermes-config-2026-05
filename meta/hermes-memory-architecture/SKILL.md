---
name: hermes-memory-architecture
description: Hermes 记忆系统真实架构 — 2026-07-08实测版，2026-07-08清理后定稿。MEMORY.md+USER.md+concept_store.md为文件系统层，LanceDB为语义层，fact_store.db已删除（0行legacy）。记忆审计必须先验证真实状态再操作。
version: 1.1.0
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
| `idle_learning_log.md` | `~/.hermes/memories/` | Jun 6-19历史学习归档（55KB） | 无 | 55KB ✅ |
| `LanceDB` | `~/.hermes/lancedb/memories.lance/` | 语义记忆（session结束后自动提取写入） | 无 | 活跃，skills_used字段已支持 |

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

**教训**: memory-cn skill 描述 Mnemosyne 为 active provider，但实际已切换到 LanceDB。skill文档 ≠ 真实状态。每次必须先验证。

**教训**: Hermes 的 memory 路径固定为 `~/.hermes/memories/`（由 `get_memory_dir()` 源码决定），不是 `memory/`、`memories/`、`data/MEMORY.md` 等其他路径。历史上曾散落过 5 份重复文件，每次审计必须 `find ~/.hermes -name "MEMORY.md" -o -name "USER.md"` 确认只有活跃路径存在。

## 记忆文件审计清单

| 检查项 | 命令 | 期望结果 |
|---|---|---|
| 所有文件大小 | `ls -la ~/.hermes/memories/` | 无0字节垃圾文件 |
| fact_store行数 | `sqlite3 fact_store.db "SELECT COUNT(*) FROM facts" 2>/dev/null` | **0行=废弃，应删除**（不是"待启用"，已是legacy） |
| **MOA provider别名** | `grep "nv-qwen3.5-397b" ~/.hermes/config.yaml` | 应无输出；有输出=引用了不存在的provider，应改为实际provider名 |
| **SOUL.md硬编码PID** | `grep "pid [0-9]" ~/.hermes/SOUL.md` | 应无输出；有输出=gateway重启后立即失效，改为"任意pid的venv python" |
| fact_store结构 | `sqlite3 fact_store.db ".schema" 2>/dev/null` | 字段: id/key/value/source/confidence/created_at/updated_at |
| LanceDB行数 | `~/.hermes/hermes-agent/venv/bin/python3 -c "import lancedb; ..."` | 当前为0，新库 |
| MEMORY/USER重复 | `grep -c "Ponytail\|数字主人\|先装再清" ~/.hermes/memories/MEMORY.md` | 应为0 |
| 过时引用 | `grep "ChromaDB\|GBrain\|Mnemosyne" ~/.hermes/memories/*.md` | 应无或已修正 |
| **废弃文件检查** | `find ~/.hermes -name "MEMORY.md" -o -name "USER.md" 2>/dev/null` | **所有结果必须在 `~/.hermes/memories/` 内**；根目录/`data/`/`memory/`里的同名文件已废弃，应删除 |
| **memory/ 目录** | `ls -la ~/.hermes/memory/` | 此目录（`~/.hermes/memory/`）完全废弃，**不等于**活跃的 `memories/`；包含98KB fact_store.db（已无用）+ 27个旧references文档 + idle learning重复文件，应整体删除 |
| **chroma_memory/ 目录** | `ls -la ~/.hermes/chroma_memory/` | ChromaDB残留（471KB），config无chroma provider引用，应删除 |
| **根目录废弃skill文件** | `ls ~/.hermes/skill_*.md ~/.hermes/briefing_*.md ~/.hermes/*patrol*.md 2>/dev/null` | 应无输出；历史版本遗留的空壳skill应删除 |

## 精简合并规则

**定位分离**：
- `MEMORY.md` = 纯技术操作（配置/调试/Chrome/搜索/技能/挂起任务）
- `USER.md` = 用户偏好/铁律/Ponytail/决策风格
- 两文件内容不重叠，grep交叉验证应为0

**可删除**：
- 与活跃文件重复的备份（`MEMORY.md.bak`、`.lock`、`archive/`）
- `fact_store.db`（已确认0行，删除而非归档）
- 根目录废弃skill文件（`skill_*.md`、`briefing_*.md`、`*patrol*.md`等历史遗留空壳）

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
