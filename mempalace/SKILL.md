---
name: mempalace
description: MemPalace v3.6.0 — 57K⭐开源AI记忆系统，完整原文存储+语义搜索，R@5=96.6%（零LLM依赖）。Mac M4用CoreML加速。适合：对话历史存档、项目上下文找回、代码片段记忆。触发：需要记忆检索/历史上下文/长期记忆。
triggers:
  - AI记忆系统
  - 对话历史检索
  - 语义搜索记忆
  - 长程上下文
  - mempalace
  - 找回之前的对话
version: 1.0.0
---

## 安装与初始化

```bash
uv tool install mempalace
mkdir -p ~/.mempalace
mempalace init ~/.mempalace --yes
```

## 核心工作流

### 挖掘内容进记忆宫殿
```bash
# 挖掘项目文件
mempalace mine ~/projects/myapp

# 挖掘Claude Code对话历史
mempalace mine ~/.claude/projects/ --mode convos

# 挖掘任意目录
mempalace mine /path/to/anywhere
```

### 语义搜索
```bash
mempalace search "项目决策细节"
mempalace search "某个bug的解决方案"
```

### 唤醒上下文（CLI输出，供agent读取）
```bash
mempalace wake-up
```

### MCP服务器（接入Claude Code等agent）
```bash
mempalace mcp
# 或REST API服务
mempalace serve
```

## 架构概念

- **Wing（翼）**：实体/人/项目
- **Room（房间）**：主题/话题
- **Drawer（抽屉）**：原始内容
- **Hall**：语义主题标签（emotions/consciousness/memory/technical等）

## 后端选择

| 后端 | 模式 | 安装 |
|------|------|------|
| `chroma` | 本地嵌入（默认） | 内置 |
| `sqlite_exact` | 本地精确 | 内置 |
| `qdrant` | 服务器REST | 内置 |
| `pgvector` | Postgres | `mempalace[pgvector]` |
| `milvus` | 本地Lite | `mempalace[milvus]` |

## 验证安装

```bash
mempalace --version   # 3.6.0
mempalace status      # palace状态
```

## 已知坑

- `init` 需要交互式输入，用 `--yes` 自动接受
- Ollama不可用时会报warning，不影响本地embedding（CoreML自动fallback）
- palace默认在 `<dir>/palace` 子目录
- Docker用户：`docker run -i --rm -v mempalace-data:/data mempalace`

## ⚠️ 关键坑：sessions/ ≠ 全部对话

**`~/.hermes/sessions/` 里的JSON文件只是请求转储，不是完整对话。**

Hermes的真实对话存在 `~/.hermes/state.db`（全量消息+全渠道），结构：
```
sessions表：cli/desktop/qqbot/telegram/tui/weixin/subagent
messages表：2854条消息（user+assistant）
```

挖掘 state.db 全渠道对话（一次性步骤）：
```python
# Python提取脚本 → references/state-db-mine.py
import sqlite3, json

conn = sqlite3.connect('/Users/aimac/.hermes/state.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("""
    SELECT m.session_id, s.source, m.role, m.content, m.timestamp
    FROM messages m JOIN sessions s ON m.session_id = s.id
    WHERE m.content IS NOT NULL AND m.content != ''
    AND m.role IN ('user', 'assistant')
    ORDER BY s.source, m.timestamp
""")
records = [{'session_id': r['session_id'], 'source': r['source'],
            'role': r['role'], 'content': r['content'][:2000], 'ts': r['timestamp']}
           for r in cur.fetchall()]
with open('/tmp/hermes_all_channels.jsonl', 'w') as f:
    for r in records: f.write(json.dumps(r, ensure_ascii=False)+'\n')
# 然后：
# mkdir -p ~/.mempalace/hermes_channels
# cp /tmp/hermes_all_channels.jsonl ~/.mempalace/hermes_channels/
# mempalace mine ~/.mempalace/hermes_channels
```

全渠道分布（2026-07实测）：
| 渠道 | 消息数 |
|------|--------|
| qqbot | 668 |
| cli | 210 |
| desktop | 99 |
| tui | 44 |
| weixin | 29 |
| telegram | 6 |
| subagent | 2 |

## 参考文档
- `references/state-db-mine-recipe.md` — state.db 全渠道对话提取脚本、渠道分布数据（2026-07-22实测）、sessions.json 与 request_dump_*.json 的真实含义
