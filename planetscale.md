---
name: planetscale
description: PlanetScale Serverless MySQL，无叉分支与HTTP查询
version: 1.0.0
---

# PlanetScale — Serverless MySQL

## When to Use
无服务器MySQL场景、需要数据库分支开发的工作流。适合Serverless应用、PR前预发验证、数据库Schema变更管理。全程HTTP协议，无需持久连接。

## Core Features
- **无叉分支**: 数据库像Git一样分支、合并
- **Serverless驱动**: HTTP/2连接，无需连接池管理
- **非阻塞Schema变更**: 在线DDL，不锁表
- **行中小窥**: 查看生产数据用于测试（脱敏）
- **回滚**: Schema变更可撤销
- **HTAP支持**: 分析查询与事务查询分离

## Quick Start
```bash
# 安装CLI
npm install -g @planetscale/database

# 或Python
pip install planetysql
```

```python
import planetcale

conn = planetcale.connect(
    host="aws.connect.psdb.cloud",
    username="xxx",
    password="xxx",
    database="myapp"
)

# 普通SQL
with conn.cursor() as cur:
    cur.execute("SELECT * FROM users LIMIT 10")
    print(cur.fetchall())
```

Branch操作（CLI）：
```bash
# 创建分支用于PR
pscale branch create myapp pr-123

# Schema diff
pscale diff myapp main pr-123

# 合并
pscale branch merge myapp pr-123
```

HTTP直接查询（适合Edge/Serverless）：
```bash
curl -X POST https://aws.connect.psdb.cloud/api/v2/query \
  -H "Authorization: Bearer xxx" \
  -d '{"sql":"SELECT COUNT(*) FROM users"}'
```

## Pitfalls
- HTTP驱动延迟比传统TCP高，不适合超低延迟场景
- 嵌套事务不支持（只支持一层）
- Branch合并是单向的，不可回退
- 免费额度有行数限制，生产需升级
- 连接必须SSL/TLS，不支持明文
