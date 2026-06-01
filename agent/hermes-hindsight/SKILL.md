---
name: hermes-hindsight
description: "Hindsight 本地记忆引擎 — AI Agent 终身记忆系统，已废弃 Docker/Ollama 方案。当前系统使用 holographic 原生插件（memory_store.db）提供 fact_store 能力。"
---

# hermes-hindsight ⚠️ 已废弃

**状态：Docker/Ollama 方案已废弃（2026-06-02）**

Colima 已停止，Hindsight Docker 容器已删除。当前记忆由 holographic 插件（fact_store 工具）提供，存储在 `~/.hermes/memory_store.db`（SQLite FTS5）。

## 当前记忆架构

```
MEMORY.md (22023字节)  ← 注入 system prompt 的快照
fact_store (holographic)  ← 5条facts，信任分0.5，未经训练
session_search (state.db)  ← 98379条消息，FTS5索引
```

| 组件 | 状态 | 说明 |
|------|------|------|
| MEMORY.md | ✅ 正常 | 手动更新，有过时内容需定期清理 |
| fact_store | ⚠️ 稀疏 | 仅5条facts，需持续补充重要结论 |
| session_search | ✅ 正常 | FTS5 AND查询，搜短词更有效 |
| Hindsight Docker | ❌ 已删除 | Colima停止时一起清掉了 |
| ChromaDB | ❌ 未运行 | Colima停止，不在 |

## FTS5 查询注意

```
搜"壁纸" → 能找到"动态壁纸"
搜"动态壁纸" → 0结果（AND模式）
重要结论必须写 MEMORY.md + fact_store，不能依赖 session_search
```

## 重新部署（仅当需要 ChromaDB 向量检索时）

如需恢复 Hindsight Docker：
```bash
colima start --cpu 2 --memory 2G
docker run -d --name hermes-hindsight -p 8899:8888 -p 9999:9999 ...
```

**当前不需要**：holographic 的 fact_store 已覆盖基本记忆需求。
