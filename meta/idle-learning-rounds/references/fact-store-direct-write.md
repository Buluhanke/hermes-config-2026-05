# fact_store 直写 Fallback

**何时需要**: 当 `batch_facts_from_log.py` 报「✅ 新写入 0 条 / 跳过 N 条」但本轮明明有新发现时。脚本是硬编码 FACTS 列表，本轮新发现不在内 = 数据丢失，必须直接写 fact_store。

## Schema

```sql
-- DB: ~/.hermes/memory/fact_store.db
CREATE TABLE facts (
  id INTEGER PRIMARY KEY,
  topic TEXT NOT NULL,
  text TEXT NOT NULL,
  source TEXT,
  trust REAL DEFAULT 0.5,
  created_at REAL DEFAULT 0,
  updated_at REAL DEFAULT 0,
  tags TEXT DEFAULT '[]'  -- JSON array
);
```

## Python 直写 snippet

```python
import sqlite3, json, time
from pathlib import Path

DB = Path.home() / ".hermes" / "memory" / "fact_store.db"
conn = sqlite3.connect(DB)
c = conn.cursor()
now = time.time()

new_facts = [
    {
        "topic": "本轮 idle_learning A 方向: <具体发现>",
        "text": "<200 字内的可执行结论>",
        "source": "idle_learning_log.md 2026-MM-DD 方向X",
        "trust": 0.65,  # 0.60-0.80 区间，新发现不应高于 0.85
        "tags": ["idle-learning", "round-YYYY-MM-DD", "direction-X"]
    },
    # ... 每方向一条
]

added = 0
for f in new_facts:
    # 去重: topic 唯一
    c.execute("SELECT id FROM facts WHERE topic = ?", (f["topic"],))
    if c.fetchone():
        print(f"  跳过已存在: {f['topic'][:50]}")
        continue
    c.execute("""INSERT INTO facts (topic, text, source, trust, created_at, updated_at, tags)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (f["topic"], f["text"], f["source"], f["trust"], now, now,
               json.dumps(f["tags"], ensure_ascii=False)))
    print(f"  ✅ 新增 [{c.lastrowid}]: {f['topic'][:60]}")
    added += 1

conn.commit()
print(f"\n新增 {added} 条")
c.execute("SELECT COUNT(*) FROM facts")
print(f"fact_store 总计: {c.fetchone()[0]} 条")
conn.close()
```

## Trust 设定参考

| 类别 | trust 区间 | 示例 |
|---|---|---|
| 实测验证通过 | 0.85-0.95 | 跑通工具、看 exit 0 + 真实输出 |
| 来源可靠 + 实测一致 | 0.75-0.85 | web 兜底抓的论文、cve_scan 结果 |
| 单源 / 待验证 | 0.60-0.75 | 本轮发现、临时观察 |
| 推断 / 软信号 | 0.50-0.60 | 「下次关注」类（**避免写入**，应留在报告里） |

**禁止 trust > 0.85 给新发现**：必须是「多轮验证 + 多源交叉」才给高分。

## Tags 命名约定

- `idle-learning` — 必加，标记 idle_learning 来源
- `round-YYYY-MM-DD` — 轮次日期，方便后续按时间过滤
- `direction-{A|B|C|D}` — 4 个方向标签
- 主题标签：`screen-watcher` / `cve` / `paper` / `action-diversity` / `script-internals` 等

## 验证

直写后必须再跑一次 fact_decay 确认：
```bash
python3 ~/.hermes/scripts/fact_decay.py
# 期望看到 总数 +1~+N，活跃计数同步增加
```

## 历史案例（2026-06-30）

- 5 条本轮发现直写，IDs 109-113
- 直写后 fact_decay 显示 78→83 条，全活跃，平均 trust 0.539→0.550
- 5 条 trust 0.65-0.80 落在「单源 + 实测一致」区间

## 反模式（禁止）

- ❌ 写 trust > 0.85 给本轮新发现（未多源交叉验证）
- ❌ 写太长的 text（> 500 字）— fact_decay --score 会截断显示
- ❌ 跳过 created_at/updated_at 时间戳（衰减机制依赖时间）
- ❌ 用单条 INSERT 代替逐条 + 去重 — 会重复写入 topic