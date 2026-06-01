# 记忆系统深度审计工作流（2026-06-02）

## 三层架构

| 层 | 工具 | 存储 | 状态 |
|----|------|------|------|
| 上下文记忆 | MEMORY.md / USER.md | `~/.hermes/memories/` 文本文件 | ⚠️ 容易过时 |
| 结构化记忆 | fact_store (holographic) | `memory_store.db` SQLite FTS5 | ⚠️ 需主动补录 |
| 对话历史 | session_search | `state.db` 1.2GB / 9.8万条消息 | ✅ 正常 |

## 审计步骤

### 1. 查 fact_store
```python
import sqlite3
conn = sqlite3.connect('~/.hermes/memory_store.db')
cur = conn.execute("SELECT COUNT(*) FROM facts")
print(cur.fetchone()[0], "facts stored")
```

### 2. 查 MEMORY.md 大小
```bash
wc -c ~/.hermes/memories/MEMORY.md  # 应 < 40000
wc -c ~/.hermes/memories/USER.md    # 应 < 20000
```

### 3. 查 state.db 健康度
```bash
sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM messages"   # 应 > 10000
sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM sessions"  # 应 > 10
```

### 4. 查会话数据库位置
```bash
# state.db 是会话 DB（不是 sessions.db）
sqlite3 ~/.hermes/state.db "SELECT id, title FROM sessions ORDER BY started_at DESC LIMIT 5"
```

### 5. 查进程残留
```bash
ps aux | grep -iE "ollama|wallpaper|hammerspoon" | grep -v grep
```

## 常见过时项

- Docker/Colima/Ollama 状态（容易记录停用了但进程残留）
- Hindsight 集成状态（Docker 停了就不在）
- SearXNG 状态（pip 包是客户端不是服务器）

## 重要结论写入 fact_store 的触发条件

- 跨会话必须记住的技术结论（根因/解法）
- 非显而易见的工作流发现
- 用户明确表达的偏好/纠正
- API key 位置/状态变化
- GitHub/阿里云等服务的配置问题

## session_search FTS5 注意

- AND 查询要求所有词命中
- 搜"动态壁纸 屏幕" → 0结果
- 搜"壁纸" → 能找到
- 搜不到 ≠ 没记录，可能是关键词不匹配
