# Hermes 全渠道对话挖掘 — state.db 提取方案

## 核心发现

`~/.hermes/sessions/` 里的 JSON 文件（request_dump_*.json）是 API 请求转储（请求体+错误日志），**不是对话内容**。

真实对话历史存在 `~/.hermes/state.db`，结构：

```sql
-- sessions 表：各渠道会话索引
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL,   -- cli|desktop|qqbot|telegram|tui|weixin|subagent
  user_id TEXT,
  started_at REAL,
  message_count INTEGER DEFAULT 0,
  ...
);

-- messages 表：真实消息（2854条，含 user+assistant+tool）
CREATE TABLE messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL REFERENCES sessions(id),
  role TEXT NOT NULL,        -- user|assistant|system|tool
  content TEXT,
  tool_calls TEXT,
  tool_name TEXT,
  timestamp REAL NOT NULL,
  ...
);
```

## 提取脚本

```python
import sqlite3, json

conn = sqlite3.connect('/Users/aimac/.hermes/state.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
SELECT m.session_id, s.source, m.role, m.content, m.timestamp
FROM messages m
JOIN sessions s ON m.session_id = s.id
WHERE m.content IS NOT NULL AND m.content != ''
AND m.role IN ('user', 'assistant')
ORDER BY s.source, m.timestamp
""")

records = []
for row in cur.fetchall():
    records.append({
        'session_id': row['session_id'],
        'source': row['source'],
        'role': row['role'],
        'content': row['content'][:2000],
        'timestamp': row['timestamp']
    })

with open('/tmp/hermes_all_channels.jsonl', 'w') as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
```

## 导入 MemPalace

```bash
mkdir -p ~/.mempalace/hermes_channels
cp /tmp/hermes_all_channels.jsonl ~/.mempalace/hermes_channels/
mempalace mine ~/.mempalace/hermes_channels
```

## 全渠道分布（2026-07-22 实测）

| 渠道 | 会话数 | 消息数 |
|------|--------|--------|
| qqbot | 5 | 668 |
| cli | 7 | 210 |
| desktop | 7 | 99 |
| tui | 2 | 44 |
| weixin | 1 | 29 |
| telegram | 1 | 6 |
| subagent | 1 | 2 |
| **合计** | **24** | **1058** |

## sessions.json 是什么

`~/.hermes/sessions/sessions.json`（4KB）只是会话元数据索引，记录 session_id → platform 的映射，message_count 全部为 0。不是对话内容。

## request_dump_*.json 是什么

OmniRoute API 调用失败时的请求转储（请求体含 system prompt + messages + API key 前缀），用于调试 API 错误，**不含对话回复内容**。
