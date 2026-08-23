# Holographic Memory 诊断报告 — 2026-07-26

## 确认的架构

- **DB路径**：`~/.hermes/memory_store.db`（不是 `memory/fact_store.db`）
- **memory.provider**：`holographic`（config.yaml确认）
- **FTS5**：内置，内容列+tags列，触发器在 add_fact 时写入
- **HRR向量**：1024维纯Python实现，encode_atom 用 SHA-256，相位编码
- **检索策略**：FTS5(40%) + Jaccard(30%) + HRR(30%)，numpy不可用时自动重分配

## 已验证的写入链路

- `MemoryStore.add_fact()` → 写入 facts 表 → 触发器写入 facts_fts → `_compute_hrr_vector()` 写入 hrr_vector
- `MemoryStore.rebuild_all_vectors()` → 遍历所有 fact 重建 HRR + 重建 memory_banks

## 已验证的检索链路

- `FactRetriever.search()` → FTS5候选 → Jaccard重排 → trust加权 → 返回

## FTS5 停用词问题

**`user` 是 FTS5 停用词**，永远匹配0条。测试查询用 `hermes`/`memory`/`learning` 等非停用词。

```python
# 正确测试
retriever.search("hermes memory")  # 返回结果
retriever.search("user preferences")  # 永远0条（停用词）
```

## HRR 重建后 facts 数量不对

`rebuild_all_vectors()` 只处理 `fact_id, content, category` 列。如果之前的清理导致 fact_id 出现断层（如删除 400→420号后只剩16条），它只处理当前存在的 fact，**不会自动重新编号**。这是正常的。

## FTS5 手动重建脚本

当 FTS 返回0但 facts 有数据时（触发器失效），手动重建：

```python
import sys
sys.path.insert(0, '~/.hermes/hermes-agent/plugins/memory/holographic')
from store import MemoryStore
store = MemoryStore('~/.hermes/memory_store.db')
store._conn.execute("DELETE FROM facts_fts")
store._conn.commit()
for fact_id, content, tags in store._conn.execute(
    "SELECT fact_id, content, tags FROM facts"
).fetchall():
    store._conn.execute(
        "INSERT INTO facts_fts(rowid, content, tags) VALUES (?, ?, ?)",
        (fact_id, content, tags or '')
    )
store._conn.commit()
store.close()
```

## llm_traces.db 为0的原因

- skill 文档说 `agent/llm_trace.py` 存在且被 conversation_loop.py 调用
- **实际情况**：`llm_trace.py` 不存在，`conversation_loop.py` 也没有直接调用它
- 真实钩子：`post_api_request`（line ~5145），langfuse 插件在消费
- 没有本地写入器写入 llm_traces.db

## 本次清理结果

| 操作 | 删除数 |
|------|--------|
| retrieval_count < 0（残骸） | 72条 |
| category = 'user-pattern'（统计快照） | 28条 |
| arXiv单篇碎片（每篇1条） | 57条 |
| arXiv摘要合并（8日期→4条） | 从32条合并为4条 |

最终：16条精炼 fact，全部有 HRR 向量。

## HRR 激活命令

```bash
cd ~/.hermes/hermes-agent && python3 -c "
import sys
sys.path.insert(0, 'plugins/memory/holographic')
from store import MemoryStore
store = MemoryStore('~/.hermes/memory_store.db')
n = store.rebuild_all_vectors()
store.close()
print(f'HRR vectors: {n}')
"
```
