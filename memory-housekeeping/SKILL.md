---
name: memory-housekeeping
description: "记忆维护 fact_store减肥HRR重建MEMORY压缩月度。Use when 记忆系统膨胀要定期瘦身"
triggers:
  - "记忆满了"
  - "fact_store清理"
  - "MEMORY.md超限"
  - "HRR向量"
  - "记忆增强激活"
---

# Memory Housekeeping — 记忆系统定期维护

## 三层存储与限制

| 层 | 路径 | 限制 |
|----|------|------|
| MEMORY.md | `~/.hermes/memories/MEMORY.md` | ≤2200字符 |
| USER.md | `~/.hermes/memories/USER.md` | ≤1375字符 |
| fact_store | `~/.hermes/memory_store.db` | 无硬限制 |

**正确路径（2026-07-26 确认）**：`~/.hermes/memory_store.db`，不是 `fact_store.db`（那是 0 字节历史遗留空文件，可直接 `rm ~/.hermes/fact_store.db`）。查询命令：
```bash
sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) FROM facts;"
```

**警惕假性 healthy**：self_heal 日志每 10 分钟打印"fact_store 可写"，只验证写入权不验证完整性。不要被它迷惑。必须手动跑 `PRAGMA integrity_check;` 确认真健康。

**malformed 修复 SOP（2026-08-18 实测，350/355 facts 恢复）**：
1. `cp memory_store.db memory_store.db.corrupted_backup`
2. `sqlite3 memory_store.db ".recover" > /tmp/recovered.sql`
3. `sqlite3 /tmp/memory_store_new.db < /tmp/recovered.sql`
4. `rm -f memory_store.db-wal memory_store.db-shm`（WAL/SHM 与新 db 冲突，必须删）
5. `mv /tmp/memory_store_new.db memory_store.db`
6. `sqlite3 memory_store.db "PRAGMA integrity_check;"` 验证
7. **Gateway 重启**：`hermes gateway restart`（malformed 来自 gateway 持有旧 WAL 连接句柄，gateway 内无法自重启）

## 维护检查单（按顺序执行）

### Step 1: 容量检查
```bash
echo "MEMORY.md: $(wc -c < ~/.hermes/memories/MEMORY.md) bytes (limit 2200)"
echo "USER.md: $(wc -c < ~/.hermes/memories/USER.md) bytes (limit 1375)"
sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) total, COUNT(CASE WHEN hrr_vector IS NOT NULL THEN 1 END) with_hrr, COUNT(CASE WHEN retrieval_count >= 0 THEN 1 END) active FROM facts;"
```

### Step 2: 诊断垃圾模式
```bash
sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) FROM facts WHERE retrieval_count < 0;"          # 流水线残骸（idle-learning失败残留）
sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) FROM facts WHERE category = 'user-pattern';"   # 情感统计快照
sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) FROM facts WHERE category LIKE 'arXiv AI |%';"  # 论文单篇碎片
sqlite3 ~/.hermes/memory_store.db "SELECT category, COUNT(*) FROM facts WHERE category LIKE 'arXiv摘要%' GROUP BY category;"  # 摘要碎片
```

### Step 3: 清理 + 重建 HRR（必须成对执行）
```python
import sys
sys.path.insert(0, '~/.hermes/hermes-agent/plugins/memory/holographic')
from store import MemoryStore

store = MemoryStore('~/.hermes/memory_store.db')

# 删除三类垃圾
for q in [
    "DELETE FROM facts WHERE retrieval_count < 0",
    "DELETE FROM facts WHERE category = 'user-pattern'",
    "DELETE FROM facts WHERE category LIKE 'arXiv AI |%'",
]:
    n = store._conn.execute(q)
    print(f"Deleted {n.rowcount} rows")

# 合并arXiv摘要（每日期最多1条，综合多篇为一条）
dates = store._conn.execute(
    "SELECT DISTINCT category FROM facts WHERE category LIKE 'arXiv摘要%'"
).fetchall()
for row in dates:
    cat = row[0]
    facts = store._conn.execute(
        "SELECT fact_id FROM facts WHERE category = ?", (cat,)
    ).fetchall()
    if len(facts) > 1:
        del_ids = [f[0] for f in facts[1:]]
        placeholders = ','.join('?' * len(del_ids))
        store._conn.execute(f"DELETE FROM facts WHERE fact_id IN ({placeholders})", del_ids)
        print(f"Consolidated {cat}")

store._conn.commit()
store.close()

# 清理后必须重建HRR向量
store2 = MemoryStore('~/.hermes/memory_store.db')
n = store2.rebuild_all_vectors()
store2.close()
print(f'HRR vectors rebuilt: {n} facts')
```

### Step 4: FTS5 重建（如检索返回0结果）
FTS5 触发器在 add_fact 时写入，但历史数据可能未同步。重建方法：
```python
store = MemoryStore('~/.hermes/memory_store.db')
store._conn.execute("DELETE FROM facts_fts")
store._conn.commit()
for fact_id, content, tags in store._conn.execute("SELECT fact_id, content, tags FROM facts").fetchall():
    store._conn.execute(
        "INSERT INTO facts_fts(rowid, content, tags) VALUES (?, ?, ?)",
        (fact_id, content, tags or '')
    )
store._conn.commit()
store.close()
```
**注意**：`user` 是 FTS5 停用词（匹配永远是0），用 `hermes`/`memory`/`learning` 等词测试。

### Step 5: MEMORY.md / USER.md 压缩
- MEMORY.md 目标：≤2200字符，结构 `【日期】教训：具体一条§`（≤30行，每条≤50字）
- USER.md 目标：≤1375字符，结构 `### 决策梯子## 用户定位## 行为铁律## 业务背景`

## llm_traces 零条说明
skill 文档说 `conversation_loop.py` 有埋点，但 `llm_trace.py` 不存在，llm_traces.db 从未有过写入器。`post_api_request` 钩子在 conversation_loop.py ~line 5145 是真实通路，langfuse 插件在消费它，但没有本地写入器。激活需新建独立 tracing 插件。

## 实测清理 SOP（2026-07-31 验证通过）

### Fact store 列名是 `fact_id`，不是 `id`
```python
import sqlite3
c = sqlite3.connect('/Users/aimac/.hermes/memory_store.db')
# ✅ 正确
c.execute("SELECT fact_id, content, trust_score FROM facts")
c.execute("DELETE FROM facts WHERE fact_id = ?", (fid,))
c.execute("UPDATE facts SET trust_score = 0.75 WHERE fact_id = ?", (fid,))
# ❌ 错误（no such column: id）
c.execute("SELECT id, content FROM facts")
```

### 信任分清理决策树（111→58 实测）

**先看分布**：
```python
c.execute("SELECT trust_score, COUNT(*) FROM facts GROUP BY trust_score").fetchall()
# → [(0.9,1), (0.85,6), (0.8,2), (0.75,10), (0.72,1), (0.7,15),
#    (0.68,3), (0.65,33), (0.6,32), (0.5,8)]
```

**删除类型**（立即删除，不过夜）：
1. Hermes 状态快照（`category` 含 "Hermes能力状态"）— 过期状态记录
2. arXiv 摘要：`retrieval_count=0 AND helpful_count=0 AND category LIKE 'arXiv%'` — 从未被调用，垃圾
3. idle-learning 流水线残骸：`retrieval_count=0 AND helpful=0 AND content` 含流水线方向标记

**提升类型**（retrieval≥2 说明被用过，只是没标记 helpful，直接拉分）：
```sql
UPDATE facts SET trust_score = 0.75
WHERE fact_id IN (638, 637, 636, 635, 218, 654, 650, 648, 642)
-- 对应 retrieval_count ≥ 2 但 trust_score < 0.7 的 fact
```

**保留观察**（retrieval=1 但 trust<0.7）：这些是被调用过一次但系统没训练上来的，保留不处理。

### 批量删除 arXiv 摘要（0 retrievals + 0 helpful）
```python
deleted = c.execute("""
    DELETE FROM facts
    WHERE trust_score < 0.7
    AND retrieval_count = 0
    AND helpful_count = 0
    AND category LIKE 'arXiv%'
""").rowcount
print(f"Deleted {deleted} unused arXiv summaries")
c.commit()
```

### MEMORY.md 备份堆积
备份文件名格式 `MEMORY.md.bak.<timestamp>`，超过 3 个即为堆积，直接删。
```python
import glob, os
backups = glob.glob('/Users/aimac/.hermes/memories/MEMORY.md.bak.*')
if len(backups) > 3:
    for b in backups:
        os.remove(b)
    print(f"Deleted {len(backups)} stale backups")
```

### 验证命令（清理后必跑）
```python
total = c.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
trusted = c.execute("SELECT COUNT(*) FROM facts WHERE trust_score >= 0.7").fetchone()[0]
low = c.execute("SELECT COUNT(*) FROM facts WHERE trust_score < 0.7").fetchone()[0]
print(f"Final: {total} facts, {trusted} trusted (≥0.7), {low} low-trust")
# 目标：trusted 占比 ≥ 60%，low-trust ≤ 20 条
```
