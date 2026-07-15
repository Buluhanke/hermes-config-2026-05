---
name: self-improvement-pipeline
version: 0.1
description: |
  Hermes 自我学习 pipeline 生命周期管理：Detect→Collect→Reflect→Crystallize→Integrate。
  当 facts 在 fact_store 里 retrieval_count=0 且不触发升华时，按本 skill 诊断。
triggers:
  - "自我学习 pipeline 不工作"
  - "fact_store retrieval_count 全是 0"
  - "skill 升华没触发"
  - "自学的知识吃灰"
  - "ABCD 学习产出为 0"
trigger_type: debugging
tags: [abcd, idle-learning, fact-store, skill-crystallization, debugging]
created: 2026-07-15
来源: 2026-07-15 自我学习闭环修复
---

# Self-Improvement Pipeline — 生命周期管理与故障排查

##  Pipeline 架构

```
知识采集 → fact_store → E2反思消化(ret=0→1) → E升华(ret≥1→skill) → skills/目录
     ↑                                          ↑
  A/B/C/D orchestrator                  abcd_learner.py
```

**三条铁律（违反=facts吃灰）：**
1. E2 必须覆盖所有 category，不能只限 `arxiv-insight` + `general`
2. E2 必须处理 `retrieval_count = -999` 的新 fact（sentinel 值）
3. E升华 SQL 的列数必须与 `write_skill(fact)` 的解包顺序完全匹配（6列：fact_id, content, category, tags, trust_score, retrieval_count）

##  故障排查流程

### Step 1：检查 retrieval_count 分布
```bash
python3 - << 'EOF'
import sqlite3
from pathlib import Path
db = Path.home() / '.hermes' / 'memory_store.db'
conn = sqlite3.connect(str(db))
cur = conn.execute('''
    SELECT
        CASE
            WHEN retrieval_count = -999 THEN "sentinel(未升华)"
            WHEN retrieval_count = 0 THEN "未引用"
            WHEN retrieval_count > 0 THEN "已引用"
        END as bucket,
        COUNT(*) as cnt
    FROM facts GROUP BY bucket
''')
for r in cur.fetchall(): print(f"  {r[0]}: {r[1]}条")
conn.close()
EOF
```

### Step 2：检查 E2 会选中哪些 facts
```bash
python3 - << 'EOF'
import sqlite3
from pathlib import Path
db = Path.home() / '.hermes' / 'memory_store.db'
conn = sqlite3.connect(str(db))
rows = conn.execute('''
    SELECT fact_id, category, content, retrieval_count
    FROM facts
    WHERE (retrieval_count = 0 OR retrieval_count = -999)
      AND trust_score >= 0.60
    ORDER BY created_at DESC LIMIT 10
''').fetchall()
for r in rows:
    print(f"[{r[0]}] cat={r[1][:30]} ret={r[3]} | {r[2][:60]}")
conn.close()
EOF
```

### Step 3：检查升华阈值和 SQL 列数
```bash
# abcd_learner.py 当前阈值
grep "RETRIEVAL_THRESHOLD\|TRUST_THRESHOLD" ~/.hermes/skills/abcd-learner/abcd_learner.py

# idle_learning_wrapper.sh E升华 SQL（必须是6列）
grep -A5 "ready = conn.execute" ~/.hermes/scripts/idle_learning_wrapper.sh
```

### Step 4：手动触发 E2 + E升华
```bash
# 升级所有 ret=0 高质量 facts
python3 - << 'EOF'
import sqlite3, time
from pathlib import Path
db = Path.home() / '.hermes' / 'memory_store.db'
conn = sqlite3.connect(str(db))
facts = conn.execute('''
    SELECT fact_id, content FROM facts
    WHERE retrieval_count = 0 AND trust_score >= 0.80
''').fetchall()
for fid, content in facts:
    conn.execute('''
        UPDATE facts SET retrieval_count = retrieval_count + 1,
        helpful_count = helpful_count + 1, updated_at = ?
        WHERE fact_id = ?
    ''', (time.time(), fid))
    print(f"  ✅ {content[:70]}")
conn.commit(); conn.close()
EOF

# 触发升华
python3 ~/.hermes/skills/abcd-learner/abcd_learner.py
```

##  已知坑点

| 坑 | 症状 | 修复 |
|----|------|------|
| E2 只查 `ret=0` 不查 `ret=-999` | 新 fact 永远不升级 | `WHERE (ret=0 OR ret=-999)` |
| E升华 SQL 只有4列 | `write_skill` 解包错位，静默失败 | 必须返回6列 |
| E2 category 白名单太窄 | topic 类 facts 被跳过 | 去掉 `category IN (...)` 限制 |
| `active_learner` 搜索失败也写入 | fact_store 充满垃圾 | `write_fact()` 加 `if "failed" in content: return` |
| 升华阈值=3 太高 | 新 fact 永远到不了3 | 阈值降到1，trust降到0.65 |
| 占位符简报写入 fact_store | 简报内容是"简报N字符" | 学习脚本不应写占位符，应写完整内容 |

##  文件位置

- `~/.hermes/scripts/idle_learning_wrapper.sh` — pipeline 入口
- `~/.hermes/scripts/active_learner.py` — 主动学习采集
- `~/.hermes/skills/abcd-learner/abcd_learner.py` — 升华引擎
- `~/.hermes/memory_store.db` — fact 存储
