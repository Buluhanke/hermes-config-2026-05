---
name: n8n-mcp-deployment
description: n8n工作流自动化平台的MCP接入，Hermes通过自然语言查询和控制n8n实例
triggers:
  - n8n状态查询
  - workflow管理
  - n8n执行记录
---

# n8n MCP Deployment

n8n工作流自动化平台的MCP（Model Context Protocol）接入，使Hermes能够通过自然语言查询和控制n8n实例。

## 触发条件

- 用户询问n8n状态、workflow数量、激活/暂停workflow
- 需要检查n8n执行记录、失败任务
- 将n8n与Hermes工具链集成

## 前置要求

- n8n实例运行在Docker（`hermes-ai-n8n-1`）或本地（`http://127.0.0.1:5678`）
- n8n数据库位于 `/Users/aimac/n8n_data`（Docker卷挂载）
- 宿主机Python需有pyobjc（用于某些MCP工具）

## 核心流程

### 1. API Key生成（无需UI登录）

n8n使用encryptionKey初始化，API Key存储在SQLite中。生成方式：

```python
import secrets, sqlite3, uuid

api_key = 'n8n_' + secrets.token_urlsafe(24)  # e.g. n8n_pbv54VyhlZMpTUWhM0nnPFHH-p2kiW6f

# 写入n8n数据库
conn = sqlite3.connect('/path/to/n8n_data/database.sqlite')
user_id = conn.execute('SELECT id FROM user LIMIT 1').fetchone()[0]
conn.execute('''INSERT INTO user_api_keys (id, userId, label, apiKey, createdAt, updatedAt, scopes, audience)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
    (str(uuid.uuid4()), user_id, 'Hermes Agent', api_key,
     '2026-05-18 12:11:12.521', '2026-05-18 12:11:12.521', '["*"]', 'public-api'))
conn.commit()
```

### 2. 数据库回写Docker

```bash
# 从容器拷贝数据库
docker cp hermes-ai-n8n-1:/home/node/.n8n/database.sqlite /tmp/n8n_db.sqlite

# 修改后复制回去
docker cp /tmp/n8n_db.sqlite hermes-ai-n8n-1:/home/node/.n8n/database.sqlite

# 重启容器使改动生效
docker restart hermes-ai-n8n-1
```

### 3. MCP工具配置

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  n8n:
    command: /opt/homebrew/bin/python3  # Mac需用Homebrew Python（有pyobjc）
    args:
    - /tmp/hermes-n8n-mcp/server.py
    env:
      N8N_MCP_ENV: /Users/aimac/.config/n8n-mcp/env
    connect_timeout: 30
    timeout: 60
```

### 4. 环境配置文件

```bash
mkdir -p ~/.config/n8n-mcp/
# ~/.config/n8n-mcp/env
N8N_API_KEY=n8n_pb...
```

## 可用工具（11个）

| 工具 | 功能 |
|------|------|
| `health` | 检查n8n API连通性 |
| `list_workflows` | 列出所有workflow |
| `get_workflow` | 按ID获取单个workflow |
| `find_workflows` | 按名称/标签搜索 |
| `list_executions` | 列出执行记录 |
| `get_execution` | 获取执行详情 |
| `recent_failures` | 最近失败的执行 |
| `export_workflow` | 导出workflow JSON |
| `activate_workflow` | 激活workflow |
| `deactivate_workflow` | 暂停workflow |
| `container_logs` | Docker容器日志 |

## 验证

```bash
curl -s http://127.0.0.1:5678/rest/workflows \
  -H "X-N8N-API-Key: n8n_pbv54VyhlZMpTUWhM0nnPFHH-p2kiW6f" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('workflows:', d.get('total',0))"
```

## 已知限制

- n8n API Key以JWT格式存储在数据库，需encryptionKey解密。直接生成新Key写入数据库最简单。
- active=false的workflow不会被`list_workflows?active=true`返回

## 文件

- MCP server: `/tmp/hermes-n8n-mcp/server.py`
- 配置env: `~/.config/n8n-mcp/env`
- 数据库备份: `/tmp/n8n_db.sqlite`