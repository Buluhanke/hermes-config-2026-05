---
name: hermes-hindsight
description: "Hindsight 本地记忆引擎 — AI Agent 终身记忆系统，已废弃 Docker/Ollama 方案。当前系统使用 holographic 原生插件（memory_store.db）提供 fact_store 能力。"
---

# hermes-hindsight ⚠️ 已废弃

**状态：Docker/Ollama 方案已废弃（2026-06-02）**

Colima 已停止，Hindsight Docker 容器已删除。当前记忆由 holographic 插件（fact_store 工具）提供，存储在 `~/.hermes/memory_store.db`（SQLite FTS5）。

## 当前记忆架构（三层）

```
MEMORY.md (22KB) ← 系统快照，常驻 system prompt
fact_store (9条facts) ← 结构化知识，trust 0.5，需主动积累
session_search (9.8万消息) ← 对话历史，FTS5 索引
```

| 组件 | 状态 | 说明 |
|------|------|------|
| MEMORY.md | ✅ 正常 | 手动更新，324行，系统状态快照 |
| fact_store | ⚠️ 稀疏 | 9条facts，需持续补充重要结论 |
| session_search | ✅ 正常 | 98,379条消息，FTS5 AND查询 |
| Hindsight Docker | ❌ 已删除 | 数据不可恢复，ghcr.io拉取失败 |
| ChromaDB | ❌ 未运行 | Colima停止，不在 |

## FTS5 查询注意

- AND模式：所有词都必须命中。搜 `"壁纸"` → 能找到 `"动态壁纸"`；搜 `"动态壁纸 屏幕"` → 0结果
- 搜精确短语：加引号 `"exact phrase"`
- 搜宽泛：搜短单词（如 `"壁纸"` 而不是 `"动态壁纸"`，搜 `"Colima"` 而不是 `"Colima Docker内存问题"`）
- **重要结论必须写 MEMORY.md + fact_store，不能依赖 session_search 作为唯一记忆**

## 重新部署（仅当需要 ChromaDB 向量检索时）

如需恢复 Hindsight Docker：
```bash
colima start --cpu 2 --memory 2G
docker run -d --name hermes-hindsight -p 8899:8888 -p 9999:9999 ...
```

**当前不需要**：holographic 的 fact_store 已覆盖基本记忆需求。
