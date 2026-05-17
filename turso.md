---
name: turso
description: Turso LibSQL边缘数据库，多区域复制与SQLite兼容
version: 1.0.0
---

# Turso — LibSQL边缘数据库

## When to Use
边缘部署、低延迟本地数据库、多区域复制场景。LibSQL（SQLite兼容）适合嵌入式/客户端存储，通过复制实现全球低延迟访问。

## Core Features
- **LibSQL引擎**: SQLite兼容 plus 复制和嵌入式支持
- **边缘复制**: 数据复制到全球多个区域
- **嵌入式**: 可内嵌到应用进程，无需独立服务器
- **多租户**: 单实例支持多个数据库
- **HTTP查询**: 轻量协议，适合Serverless
- **实时同步**: 嵌入式与云端数据同步

## Quick Start
```bash
# 安装CLI
brew install tursodatabase/tap/turso

# 创建数据库
turso db create myapp

# 获取连接URL
turso db show myapp --url
```

Python SDK：
```python
import libsql_client

client = libsql_client.create_client(
    url="libsql://myapp-user.turso.io",
    auth_token="xxx"
)

result = await client.execute("SELECT * FROM users LIMIT 10")
for row in result.rows:
    print(row)
```

嵌入式（本地开发）：
```python
# 本地文件作为数据库
client = libsql_client.create_client(url="file:local.db")

# 或内存数据库
client = libsql_client.create_client(url="memory:")
```

多区域复制：
```bash
# 添加复制区域
turso db regions add myapp eu-west

# 查看当前 replica 位置
turso db show myapp
```

## Pitfalls
- LibSQL语法与标准SQLite略有差异（UTC时间函数等）
- 复制延迟：强一致性写入有跨区域延迟
- 免费套餐单数据库5GB限制
- HTTP接口查询有超时，不适合大事务
- 嵌入式同步需处理冲突策略
