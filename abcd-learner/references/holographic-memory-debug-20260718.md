# Holographic Memory Debug: retrieval_count 全零排查

**日期**: 2026-07-18  
**症状**: 174条 facts，retrieval_count 全部 = 0  
**影响**: idle_learning 写入的记忆从未被实际检索使用

---

## 排查路径

### 第一层：数据验证

```sql
-- 确认 facts 确实存在
SELECT COUNT(*) FROM facts;  -- 174条

-- 确认 retrieval_count 全 0
SELECT COUNT(*) FROM facts WHERE retrieval_count = 0;  -- 174条
SELECT COUNT(*) FROM facts WHERE retrieval_count >= 1;  -- 0条
```

### 第二层：代码链路追踪

**调用链**:
```
turn_context.py → agent._memory_manager.prefetch_all(query)
  → holographic/__init__.py:HolographicMemoryProvider.prefetch(query)
    → FactRetriever.search(query)  ← 问题在这里
    (绕过了 store.search_facts() 的 UPDATE retrieval_count)
```

**两条检索路径**:
1. `store.search_facts()` — 直接 FTS5 检索，**有** UPDATE retrieval_count ✅
2. `retriever.search()` — 混合检索（FTS5 + Jaccard + HRR），**无** UPDATE ❌

prefetch 使用的是路径2，所以计数从不更新。

### 第三层：provider 激活验证

**根因1**: `config.yaml` 的 `memory:` 部分没有 `provider: holographic`

```python
# agent_init.py 里的初始化逻辑
_mem_provider_name = mem_config.get("provider", "")  # 空字符串
if _mem_provider_name and _mem_provider_name.strip():  # False → 跳过
    agent._memory_manager = _MemoryManager()
```

**修复**:
```yaml
# config.yaml
memory:
  provider: holographic  # ← 加这行
  nudge_interval: 10
  flush_min_turns: 6
```

**验证**:
```bash
# 重启 gateway 后检查日志
grep -i "holographic\|memory.*provider.*activat" ~/.hermes/logs/gateway.log
```

### 第四层：retrieval_count 更新修复

**文件**: `plugins/memory/holographic/retrieval.py`

在 `FactRetriever.search()` 返回前添加计数更新（与 store.search_facts() 逻辑一致）:

```python
# Sort by score descending, return top limit
scored.sort(key=lambda x: x["score"], reverse=True)
results = scored[:limit]

# Update retrieval_count for returned facts
if results:
    ids = [r["fact_id"] for r in results if "fact_id" in r]
    if ids and self.store:  # 注意是 self.store 不是 self._store
        placeholders = ",".join("?" * len(ids))
        self.store._conn.execute(
            f"UPDATE facts SET retrieval_count = retrieval_count + 1 WHERE fact_id IN ({placeholders})",
            ids,
        )
        self.store._conn.commit()
```

**注意**: 属性名是 `store`，不是 `_store`（后者是 MemoryStore 自己的内部属性）

### 第五层：独立验证脚本

```python
import sys, sqlite3, os
for mod in list(sys.modules.keys()):
    if 'holographic' in mod or 'memory' in mod:
        del sys.modules[mod]
sys.path.insert(0, '/Users/aimac/.hermes/hermes-agent')
from plugins.memory.holographic.retrieval import FactRetriever
from plugins.memory.holographic.store import MemoryStore

db = os.path.expanduser('~/.hermes/memory_store.db')
store = MemoryStore(db_path=db)
retriever = FactRetriever(store=store)
conn = sqlite3.connect(db)

# 找一个 ret=0 的 fact 测试
row = conn.execute("SELECT fact_id, content, retrieval_count FROM facts WHERE retrieval_count=0 LIMIT 1").fetchone()
if row:
    keyword = row[1].split()[0]
    before = row[2]
    results = retriever.search(keyword)
    after = conn.execute("SELECT retrieval_count FROM facts WHERE fact_id=?", (row[0],)).fetchone()[0]
    print(f"before={before}, after={after} {'✅' if after > before else '❌'}")
conn.close()
```

---

## 关键文件位置

| 文件 | 作用 |
|---|---|
| `~/.hermes/config.yaml` | memory provider 配置 |
| `plugins/memory/holographic/retrieval.py` | `FactRetriever.search()` — 修复位置 |
| `plugins/memory/holographic/store.py` | `store.search_facts()` — 原始计数逻辑 |
| `plugins/memory/holographic/__init__.py` | `HolographicMemoryProvider.prefetch()` — 调用 search() |
| `agent/memory_manager.py` | `prefetch_all()` — 入口 |
| `agent/turn_context.py` | 调用 `prefetch_all()` 的位置 |
| `agent/agent_init.py` | memory manager 初始化，读取 `config.memory.provider` |

---

## Gateway 无法内部重启的处理

```python
# ❌ 错误：从 gateway 内部调用 restart
terminal("bash ~/.hermes/scripts/restart_gateway.sh")
# Error: cannot restart from inside the gateway process

# ✅ 正确：用 subagent 从外部执行
delegate_task(goal="kill PID && hermes gateway start")
```
