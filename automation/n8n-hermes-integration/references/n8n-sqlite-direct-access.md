# n8n SQLite 数据库操作参考

## 何时使用

当 n8n 实例出现以下情况，UI/API 均无法修复时，直接操作数据库：

1. **Onboarding 卡死**：账号创建表单提交后一直停留在设置页面，无法进入工作流编辑器
2. **API Key 被遮蔽**：Settings → n8n API 页面 Key 值显示被截断/遮盖，无法复制完整值
3. **用户表损坏**：`email=None`、`settings='{"userActivated":false}'` 导致 n8n 认为未完成初始化
4. **Workflow 激活失败**：API 返回 401 但确信 Key 正确，需要绕过认证检查

## 查找 n8n 数据卷

```bash
# 查看所有 Docker volume
docker volume ls | grep n8n

# 典型输出（named volume 格式）
hermes-ai_n8n_data
```

## Python one-liner 读取任意表

```bash
docker run --rm \
  -v hermes-ai_n8n_data:/data \
  -v /tmp:/hosttmp \
  python:3.11 \
  python3 -c "
import sqlite3, json
db = sqlite3.connect('/data/database.sqlite')
db.row_factory = sqlite3.Row

# === 读取 API Keys ===
keys = db.execute('SELECT * FROM user_api_keys').fetchall()
for k in keys:
    d = dict(k)
    print('API Key:', d['apiKey'])
    print('Label:', d['label'])
    print('Scopes:', d['scopes'][:80], '...')
    print()

# === 读取 Workflows ===
wfs = db.execute('SELECT id, name, active FROM workflow_entity').fetchall()
for w in wfs:
    print('Workflow:', dict(w))

# === 读取 User ===
user = db.execute('SELECT * FROM \"user\"').fetchone()
print('User:', dict(user))

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

db = sqlite3.connect('/data/database.sqlite')
db.row_factory = sqlite3.Row

# 找到 owner 用户
user = db.execute("SELECT * FROM \"user\" WHERE roleSlug='global:owner'").fetchone()
print("Before:", dict(user))

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
print("After:", dict(db.execute("SELECT * FROM \"user\"").fetchone()))
db.close()
print("Done! 刷新浏览器 n8n 页面即可进入编辑器。")
```

## 通过数据库直接激活 Workflow

如果 API Key 已知，但 `/rest/` 端点需要 session cookie，可直接在 DB 改 `active` 字段：

```python
import sqlite3

db = sqlite3.connect('/data/database.sqlite')
db.row_factory = sqlite3.Row

# 激活 workflow（active=1）
wf = db.execute("SELECT id FROM workflow_entity WHERE name='Hermes OCR Pipeline'").fetchone()
if wf:
    db.execute("UPDATE workflow_entity SET active=1 WHERE id=?", (wf['id'],))
    db.commit()
    print(f"Activated workflow {wf['id']}")
else:
    print("Workflow not found")

db.close()
```

## 完整修复 n8n 实例脚本

```python
#!/usr/bin/env python3
"""修复 n8n onboarding + 激活 workflow"""
import sqlite3, sys

def fix_n8n(volume_name='hermes-ai_n8n_data'):
    db = sqlite3.connect(f'/data/database.sqlite')
    db.row_factory = sqlite3.Row

    # 1. 修复 user
    user = db.execute("SELECT * FROM \"user\" WHERE roleSlug='global:owner'").fetchone()
    if user and user['email'] is None:
        db.execute("""
          UPDATE "user" SET
            email=?, firstName=?, lastName=?,
            settings='{"userActivated":true}'
          WHERE id=?
        """, ('hermes@local.ai', 'Hermes', 'Agent', user['id']))
        print(f"[OK] User fixed: {user['id']}")

    # 2. 激活指定 workflow
    target = sys.argv[1] if len(sys.argv) > 1 else 'Hermes OCR Pipeline'
    wf = db.execute(
        "SELECT id FROM workflow_entity WHERE name=?", (target,)
    ).fetchone()
    if wf:
        db.execute("UPDATE workflow_entity SET active=1 WHERE id=?", (wf['id'],))
        print(f"[OK] Workflow '{target}' activated: {wf['id']}")

    db.commit()
    db.close()
    print("[OK] All done")

if __name__ == '__main__':
    fix_n8n()
```

## 注意事项

- **Volume 路径**：容器内数据库路径是 `/home/node/.n8n/database.sqlite`，映射到 Docker named volume
- **n8n reset 命令**：`docker exec <container> n8n user-management:reset` 会重置 DB，但会清空所有用户和工作流（破坏性）
- **JWT Token 格式**：n8n API Key 是 JWT（`eyJ...` 开头），包含 `iss: n8n` 和 `aud: public-api`，可用于 Public API 认证
- **scopes 格式**：数据库里存的是 JSON 数组字符串，不是逗号分隔字符串

---

## n8n 备份到 GitHub（重要！）

### 架构

```
宿主机 ~/n8n_data/         ← Docker volume mount
    ├── database.sqlite   ← 主数据库（WAL 模式，checkpoint后~1MB）
    ├── database.sqlite-wal   ← 未合并写入（4MB+，checkpoint后自动删除）
    ├── nodes/
    └── config

GitHub: Buluhanke/hermes-config-2026-05/.n8n_backup/
```

**当前 Hermes n8n 路径**：`/Users/aimac/n8n_data`
**Docker 容器名**：`hermes-ai-n8n-1`

### 关键坑：SQLite WAL 模式

n8n 使用 SQLite WAL 模式：
- `database.sqlite` 主文件（checkpoint后~1MB）不含最新写入
- `database.sqlite-wal`（可达 4MB+）才是最新数据所在
- 只备份 sqlite 文件而不 checkpoint，**会丢失最新数据**

### 正确的备份流程

```bash
# Step 1: WAL checkpoint（合并 WAL 到主数据库）
python3 -c "
import sqlite3
conn = sqlite3.connect('/Users/aimac/n8n_data/database.sqlite')
conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')  # 删除WAL文件
conn.execute('VACUUM')
conn.close()
"

# Step 2: 复制到 git 目录
rm -rf ~/.hermes/.n8n_backup
mkdir -p ~/.hermes/.n8n_backup
cp ~/n8n_data/config ~/.hermes/.n8n_backup/
cp ~/n8n_data/database.sqlite ~/.hermes/.n8n_backup/
cp -r ~/n8n_data/nodes ~/.hermes/.n8n_backup/

# Step 3: 强制添加（绕过 .gitignore 的 *.sqlite 规则）
git add -f ~/.hermes/.n8n_backup/database.sqlite \
          ~/.hermes/.n8n_backup/config \
          ~/.hermes/.n8n_backup/nodes
git commit -m "n8n backup $(date)"
git push
```

### 关键坑2：.gitignore 的 *.sqlite 规则

`~/.hermes/.gitignore` 包含 `*.sqlite`，会导致 `.n8n_backup/database.sqlite` 被静默忽略（不报错，文件就是不上传！）。**必须用 `git add -f` 强制添加**。

### 自动备份 Cronjob

每天凌晨 4 点执行 `backup_n8n.sh`，已内置 checkpoint + force-add 逻辑。

### 从备份恢复

```bash
# 克隆配置
git clone https://github.com/Buluhanke/hermes-config-2026-05.git ~/.hermes

# 复制 n8n 数据
cp ~/.hermes/.n8n_backup/* ~/n8n_data/

# 重启容器
docker restart hermes-ai-n8n-1
```
