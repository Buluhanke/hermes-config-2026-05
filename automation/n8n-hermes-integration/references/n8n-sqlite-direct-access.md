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
