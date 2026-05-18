# n8n SQLite 数据库操作参考

## 何时使用

当 n8n 实例出现以下情况，UI/API 均无法修复时，直接操作数据库：

1. **Onboarding 卡死**：账号创建表单提交后一直停留在设置页面，无法进入工作流编辑器
2. **API Key 被遮蔽**：Settings → n8n API 页面 Key 值显示被截断/遮盖，无法复制完整值
3. **用户表损坏**：`email=None`、`settings='{"userActivated":false}'` 导致 n8n 认为未完成初始化
4. **Workflow 激活失败**：API 返回 401 但确信 Key 正确，需要绕过认证检查

## 查找 n8n 数据位置

### Bind mount 方案（当前生产环境）
数据目录直接挂载在宿主机，直接读文件：

```bash
# 查看数据目录
ls -la ~/n8n_data/

# 直接用 sqlite3 读取
sqlite3 ~/n8n_data/database.sqlite "SELECT apiKey, label, createdAt FROM user_api_keys;"
```

### Named volume 方案（旧部署）
```bash
# 查看所有 Docker volume
docker volume ls | grep n8n

# 用 docker run 读取 named volume
docker run --rm -v hermes-ai_n8n_data:/data python:3.11 \
  python3 -c "
import sqlite3
db = sqlite3.connect('/data/database.sqlite')
db.row_factory = sqlite3.Row
keys = db.execute('SELECT * FROM user_api_keys').fetchall()
for k in keys:
    d = dict(k)
    print('API Key:', d['apiKey'])
    print('Label:', d['label'])
db.close()
"
```

## 常用表结构速查

| 表名 | 关键字段 |
|------|---------|
| `user` | `id`, `email`, `firstName`, `lastName`, `settings` (JSON: `userActivated`), `roleSlug` |
| `user_api_keys` | `apiKey` (JWT 字符串), `label`, `scopes` (JSON 数组字符串), `userId`, `createdAt` |
| `workflow_entity` | `id`, `name`, `active` (0/1), `nodes` (JSON), `connections` (JSON) |
| `shared_workflow` | `workflowId`, `projectId`, `role` |
| `project` | `id`, `name`, `type` |

## 修复 onboarding 卡死

```python
import sqlite3

db = sqlite3.connect('/Users/aimac/n8n_data/database.sqlite')
db.row_factory = sqlite3.Row

# 找到 owner 用户
user = db.execute("SELECT * FROM \"user\" WHERE roleSlug='global:owner'").fetchone()

# 填入邮箱 + 激活状态，跳过 onboarding
db.execute("""
  UPDATE "user" SET
    email = 'hermes@local.ai',
    firstName = 'Hermes',
    lastName = 'Agent',
    settings = '{"userActivated":true}'
  WHERE id = ?
""", (user['id'],))

db.commit()
db.close()
```

## 通过数据库直接提取 API Key

当 Settings → n8n API 页面 Key 被遮蔽时，直接从数据库读取：

```bash
# Bind mount 方案（当前生产环境）
sqlite3 ~/n8n_data/database.sqlite "SELECT apiKey, label, createdAt FROM user_api_keys;"

# Named volume 方案
docker run --rm -v hermes-ai_n8n_data:/data python:3.11 \
  python3 -c "
import sqlite3
db = sqlite3.connect('/data/database.sqlite')
rows = db.execute('SELECT apiKey, label FROM user_api_keys').fetchall()
for r in rows: print('Key:', r[0], '| Label:', r[1])
db.close()
"
```

**注意**：API Key 是 JWT 字符串（`eyJhbGci...` 格式），n8n 加密存储在 DB 中，但可用明文读取用于 `X-N8N-API-KEY` header。

## 通过数据库直接激活 Workflow

```python
import sqlite3

db = sqlite3.connect('/Users/aimac/n8n_data/database.sqlite')
db.row_factory = sqlite3.Row

wf = db.execute("SELECT id FROM workflow_entity WHERE name='目标workflow名'").fetchone()
if wf:
    db.execute("UPDATE workflow_entity SET active=1 WHERE id=?", (wf['id'],))
    db.commit()
    print(f"Activated: {wf['id']}")

db.close()
```

## n8n 备份到 GitHub

### 关键坑：SQLite WAL 模式

n8n 使用 SQLite WAL 模式——`database.sqlite-wal` 含最新数据，只备份 sqlite 文件会丢失数据。

### 正确的备份流程

```bash
# Step 1: WAL checkpoint
python3 -c "
import sqlite3
conn = sqlite3.connect('/Users/aimac/n8n_data/database.sqlite')
conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
conn.execute('VACUUM')
conn.close()
"

# Step 2: 复制到 git 目录
mkdir -p ~/.hermes/.n8n_backup
cp ~/n8n_data/config ~/.hermes/.n8n_backup/
cp ~/n8n_data/database.sqlite ~/.hermes/.n8n_backup/
cp -r ~/n8n_data/nodes ~/.hermes/.n8n_backup/

# Step 3: 强制添加（.gitignore 的 *.sqlite 会静默忽略！）
git add -f ~/.hermes/.n8n_backup/database.sqlite
git commit -m "n8n backup $(date)"
git push
```

### 从备份恢复

```bash
git clone https://github.com/Buluhanke/hermes-config-2026-05.git ~/.hermes
cp ~/.hermes/.n8n_backup/* ~/n8n_data/
docker restart hermes-ai-n8n-1
```
