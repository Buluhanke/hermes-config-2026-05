---
name: neon
description: Neon Serverless Postgres，分支数据库与Autoscaling
version: 1.0.0
---

# Neon — Serverless Postgres

## When to Use
Serverless环境下的Postgres、需要分支数据库用于测试、Postgres兼容性优先的场景。比PlanetScale更贴近标准Postgres，扩展性强，适合有Postgres经验的团队。

## Core Features
- **分支数据库**: 瞬间创建完整数据副本用于测试
- **Autoscaling**: 负载自适应扩缩容
- **冷启动优化**: 计算节点按需启动，0时无费用
- **标准Postgres**: 100%兼容Postgres 15/16
- **Prisma/ORM集成**: 官方支持Prisma、Drizzle
- **点时间恢复**: 任意时间点恢复数据

## Quick Start
```bash
pip install psycopg[binary]
```

连接字符串从Neon Dashboard获取：
```python
import psycopg2

conn = psycopg2.connect(
    "postgresql://user:password@ep-xxx-123456.us-east-2.aws.neon.tech/neondb"
)

with conn.cursor() as cur:
    cur.execute("SELECT version()")
    print(cur.fetchone())
```

Prisma集成（`schema.prisma`）：
```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}
```

分支操作：
```bash
# CLI创建分支
neon branch create --name test-branch

# 连接分支
psql "postgresql://user:pass@ep-xxx/test-branch"
```

Autoscaling配置：Dashboard→Project→Settings→Compute，自动根据连接数调整

## Pitfalls
- 冷启动有秒级延迟，首条查询可能较慢
- 强依赖AWS us-east-2区域，延迟敏感业务注意地域
- 免费套餐计算时间有限，超出自动暂停
- 分支删除前需断开所有连接
- 某些Postgres扩展不支持（如某些FDW）
