# MacBook Air K 深度审计 — 2026-07-23

## 审计命令模板（下次直接复制）

```bash
# 基础状态
ssh kk@192.168.8.236 "uptime; top -l 1 | grep PhysMem; df -h /"

# Hermes 进程
ssh kk@192.168.8.236 "ps aux | grep hermes | grep -v grep"

# Gateway state
ssh kk@192.168.8.236 "cat ~/.hermes/gateway_state.json"

# Cron jobs
ssh kk@192.168.8.236 "cat ~/.hermes/cron/jobs.json | python3 -c \"import json,sys; [print(j['name'],j['schedule'],j['last_status']) for j in json.load(sys.stdin)['jobs']]\""

# fact_store 真实状态（必须用 venv python）
ssh kk@192.168.8.236 "~/.hermes/hermes-agent/venv/bin/python3 - << 'PYEOF'
import sqlite3, os
c = sqlite3.connect('/Users/kk/.hermes/memory_store.db')
print('facts:', c.execute('SELECT COUNT(*) FROM facts').fetchone()[0])
print('WAL size:', os.path.getsize('/Users/kk/.hermes/memory_store.db-wal'))
PYEOF"

# 错误日志
ssh kk@192.168.8.236 "tail -30 ~/.hermes/logs/errors.log"

# Skills 数量
ssh kk@192.168.8.236 "ls ~/.hermes/skills/ | wc -l && du -sh ~/.hermes/skills/"
```

## 本次发现的问题清单

| # | 严重度 | 问题 | 验证命令 |
|---|--------|------|----------|
| 1 | 🔴 | fact_store 只有1条（测试写入），真实知识 0 条 | `SELECT COUNT(*) FROM facts` |
| 2 | 🔴 | WAL 文件 32KB 活跃但 facts 表为空 = 写入目标错位 | `ls -la memory_store.db*` |
| 3 | 🔴 | memory tool 拦截 `ssh_access` threat pattern | `grep ssh_access logs/errors.log` |
| 4 | 🟡 | morning-health cron "Failed to compute next run" | `cron jobs.json` |
| 5 | 🟡 | Telegram 断连日志 | `grep telegram logs/errors.log | tail` |
| 6 | 🟡 | kanban.db 0 张表（未初始化） | `sqlite3 kanban.db "SELECT name FROM sqlite_master WHERE type='table'"` |
| 7 | 🟡 | self_heal_watchdog 无 cron | cron list |
| 8 | 🟡 | idle_learning 脚本不存在 | `ls scripts/idle_learning*` |
| 9 | 🟢 | 221 skills 占用 57MB（需清理） | `du -sh skills/` |

## 新发现 failure mode: fact_store WAL 活跃但 facts 空

**症状**：`memory_store.db-wal` 持续 32KB+，但 `SELECT COUNT(*) FROM facts` = 0 或极少。

**根因**：holographic memory provider 写入时遇到错误（如 embedding API key 缺失），SQLite 将内容放入 WAL 但未 commit 到主文件。

**诊断**：
```bash
ssh kk@192.168.8.236 "~/.hermes/hermes-agent/venv/bin/python3 - << 'PYEOF'
import sqlite3
c = sqlite3.connect('/Users/kk/.hermes/memory_store.db')
c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
print('facts after checkpoint:', c.execute('SELECT COUNT(*) FROM facts').fetchone()[0])
PYEOF"
```

---

## 2026-07-23 全面修复记录

### 修复1：fact_store 批量同步（本机217条 → 远程）

```bash
# 1. 本机导出（清洗控制字符）
~/.hermes/hermes-agent/venv/bin/python3 -c "
import sqlite3, json
c = sqlite3.connect('/Users/aimac/.hermes/memory_store.db')
facts = c.execute('SELECT content,category,tags,trust_score,retrieval_count,helpful_count FROM facts').fetchall()
cleaned = []
for f in facts:
    content = ''.join(ch for ch in f[0] if ch == '\n' or ch == '\t' or (ord(ch) >= 32 and ord(ch) != 127))
    cleaned.append([content, f[1], f[2], f[3], f[4], f[5]])
with open('/tmp/facts_clean.json', 'w') as out:
    json.dump(cleaned, out, ensure_ascii=False)
"

# 2. rsync 到远程 /tmp
rsync -avz /tmp/facts_clean.json kk@192.168.8.236:/tmp/

# 3. 远程批量导入
ssh kk@192.168.8.236 "~/.hermes/hermes-agent/venv/bin/python3 - << 'PYEOF'
import sqlite3, json
with open('/tmp/facts_clean.json') as f:
    facts = json.load(f)
conn = sqlite3.connect('/Users/kk/.hermes/memory_store.db')
existing = {r[0] for r in conn.execute('SELECT content FROM facts')}
added = skipped = 0
for fact in facts:
    content, category, tags, trust_score, retrieval_count, helpful_count = fact
    if content in existing:
        skipped += 1; continue
    try:
        conn.execute('INSERT INTO facts VALUES (?,?,?,?,?,?)', (content,category,tags,trust_score,retrieval_count,helpful_count))
        added += 1
    except: pass
conn.commit()
print(f'新增:{added} 跳过:{skipped} 总计:{conn.execute(\"SELECT COUNT(*) FROM facts\").fetchone()[0]}')
PYEOF"
```

**结果：新增 217 条，总计 219 条（2条测试数据）**

### 修复2：threat_patterns.py 注释语法（`//` → `#`）

Python 不认识 `//` 注释，必须用 `#`：

```python
ssh kk@192.168.8.236 "~/.hermes/hermes-agent/venv/bin/python3 - << 'PYEOF'
with open('/Users/kk/.hermes/hermes-agent/tools/threat_patterns.py') as f:
    lines = f.readlines()
out = []
for line in lines:
    if line.lstrip().startswith('//'):
        indent = len(line) - len(line.lstrip())
        out.append(' ' * indent + '#' + line.lstrip()[1:])
    else:
        out.append(line)
with open('/Users/kk/.hermes/hermes-agent/tools/threat_patterns.py', 'w') as f:
    f.writelines(out)
import py_compile; py_compile.compile('/Users/kk/.hermes/hermes-agent/tools/threat_patterns.py', doraise=True)
print('Syntax OK')
PYEOF"
```

**教训：SSH heredoc 里写 Python 时，注释必须用 `#`，不能用 `//`**

### 修复3：morning-health cron 格式（`cron` → `expr`）

`jobs.json` 中 schedule 字段 `"cron": "0 8 * * *"` 应为 `"expr"`：

```python
for job in data['jobs']:
    if job['name'] == 'morning-health':
        if 'cron' in job['schedule']:
            job['schedule']['expr'] = job['schedule'].pop('cron')
        if job['state'] == 'error':
            job['state'] = 'scheduled'
```

### 修复4：hermes cron create 语法

```bash
# 错误
hermes cron create --schedule 'every 10m' ...

# 正确（schedule 是位置参数）
hermes cron create 'every 10m' --name 'xxx' --script 'xxx.sh' --no-agent --deliver local
```

### 修复5：kanban.db 初始化

```python
conn.execute('''CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
    description TEXT, status TEXT DEFAULT "todo",
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
conn.execute('''CREATE TABLE IF NOT EXISTS task_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER REFERENCES tasks(id),
    event TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
```

### 修复6：脚本路径修复（aimac → kk）

rsync 后远程脚本里硬编码了 `/Users/aimac`，替换：

```bash
sed -i '' 's|/Users/aimac/.hermes|/Users/kk/.hermes|g' ~/.hermes/scripts/self_evolution.sh
sed -i '' 's|/Users/aimac/.hermes|/Users/kk/.hermes|g' ~/.hermes/scripts/self_heal_watchdog.sh
sed -i '' 's|/Users/aimac/.hermes|/Users/kk/.hermes|g' ~/.hermes/scripts/idle_learning_wrapper.sh
sed -i '' 's|/Users/aimac/.hermes|/Users/kk/.hermes|g' ~/.hermes/scripts/abcd_learner.py
sed -i '' 's|/Users/aimac/.hermes|/Users/kk/.hermes|g' ~/.hermes/scripts/active_learner.py
```

### 新增 cron jobs

| Job | Schedule | Script |
|-----|----------|--------|
| self-heal-watchdog | every 10m | self_heal_watchdog.sh |
| idle-learning | every 2h (120m) | idle_learning_wrapper.sh |

### 同步 scripts 清单

```
abcd_learner.py
active_learner.py
auto_skill_from_failure.py
idle_learning_wrapper.sh
idle_learning_orchestrator.py
deep_research.sh
daily_patrol.sh
self_evolution_daily_learn.sh
self_evolution.sh
self_heal_watchdog.sh
mem_patrol.sh
anysearch_heal.sh
abcd_auto_fix.py
abcd_gap_parser.py
knowledge_miner.py
knowledge_miner_wrapper.sh
```

---

## SSH remote audit 要点

- SSH 超时很常见（防火墙/机器休眠），等待 30s 无响应后再重试
- 远程命令用 `&&` 串联，一次 SSH 获取多维度状态
- macOS 无 `free -h`，用 `top -l 1 | grep PhysMem` 代替
- 嵌套 SSH 命令引号转义复杂，用 Python heredoc 代替
- **远程 Hermes venv 必须显式路径**：`~/.hermes/hermes-agent/venv/bin/python3`，不能用系统 `python3`
- rsync 文件到远程时用 `/tmp` 中转，避免 `~/.hermes/` 权限问题
