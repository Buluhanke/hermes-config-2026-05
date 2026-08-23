---
name: database-client
description: 数据库客户端工具 — PostgreSQL / MySQL / SQLite 连接、查询、导出、坑点排查。触发：database、postgresql、mysql、sqlite、数据库查询。
triggers:
  - database
  - postgresql
  - mysql
  - sqlite
  - 数据库查询
author: Hermes Agent
version: 1.0.0
tags:
  - database
  - postgresql
  - mysql
  - sqlite
  - client
  - sql
created: 2026-08-10
updated: 2026-08-10
---

# database-client — 数据库客户端技能

覆盖 PostgreSQL、MySQL、SQLite 三种数据库的 client 工具使用，包括安装、连接、常用命令、导出操作和常见坑点。

---

## 场景 A — PostgreSQL Client（psql）

### A1. 安装

```bash
brew install postgresql@16
# 安装后需将 bin 目录加入 PATH
echo 'export PATH="/usr/local/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### A2. 连接

```bash
# 基本连接
psql -h <host> -p 5432 -U <user> -d <db>

# 示例（本地默认 socket）
psql -U postgres -d mydb

# 远程连接
psql -h 192.168.1.100 -p 5432 -U admin -d mydb

# 带密码（环境变量方式，避免交互式输入）
export PGPASSWORD='your_password'
psql -h <host> -p 5432 -U <user> -d <db>

# SSL 连接（远程生产环境推荐）
psql "sslmode=require host=<host> port=5432 dbname=<db> user=<user>"
```

### A3. 常用命令

```sql
-- 列出所有数据库
\l
\l+

-- 切换数据库
\c mydb

-- 列出所有表
\dt
\dt+

-- 列出表结构
\d table_name
\d+ table_name

-- 列出所有用户/角色
\du
\du+

-- 执行 SQL
SELECT * FROM table_name LIMIT 10;
INSERT INTO table_name (col1, col2) VALUES ('val1', 'val2');
UPDATE table_name SET col1 = 'val1' WHERE id = 1;
DELETE FROM table_name WHERE id = 1;

-- 查看当前连接信息
\conninfo

-- 列出所有 schema
\dn
\dn+

-- 列出索引
\di

-- 列出视图
\dv

-- 执行外部文件
\i /path/to/script.sql

-- 列出已加载扩展
\dx
```

### A4. 导出

```sql
-- 导出表数据到 CSV（psql 客户端内）
\copy table_name TO '/tmp/table_name.csv' WITH (FORMAT csv, HEADER true);

-- 导出查询结果
\copy (SELECT * FROM table_name WHERE condition) TO '/tmp/result.csv' WITH (FORMAT csv, HEADER true);

-- 导出到 psql 命令行输出（不用 \copy）
\o /tmp/output.txt
SELECT * FROM table_name;
\o

-- 整个数据库导出（需 pg_dump，非 psql 命令）
pg_dump -h <host> -U <user> -d <db> -Fc > backup.dump

-- 纯 SQL 格式导出
pg_dump -h <host> -U <user> -d <db> --inserts > backup.sql
```

### A5. 坑点

| 坑点 | 说明 | 解决 |
|------|------|------|
| `psql: connection refused` | 服务未启动或端口错误 | 确认 host/port，检查 pg_hba.conf 是否允许该 IP |
| `psql: FATAL: password authentication failed` | 密码错误或认证方式不匹配 | 确认 PGPASSWORD 环境变量，检查 pg_hba.conf 认证方式（md5/scram-sha-256） |
| `psql: FATAL: Peer authentication failed` | Unix socket 连接时 OS 用户不匹配 | 改用 `-h 127.0.0.1` TCP 连接，或修改 pg_hba.conf 的 `local` 认证方式 |
| 远程连接无响应 | 防火墙或 SSL 配置问题 | 确认 5432 端口开放，添加 `sslmode=require` |
| 中文字段/数据乱码 | 客户端编码不一致 | 执行 `SET client_encoding TO 'UTF8';` |
| `pg_dump: too many command-line arguments` | 参数顺序错误 | 顺序：pg_dump [options] -d dbname |
| 导出 CSV 字段含逗号/换行 | 未用 WITH (FORMAT csv) | 必须加 `WITH (FORMAT csv, HEADER true)`，否则字段内逗号会导致错位 |

---

## 场景 B — MySQL Client（mysql）

### B1. 安装

```bash
brew install mysql-client
# mysql-client 默认安装在 /usr/local/opt/mysql-client/bin
export PATH="/usr/local/opt/mysql-client/bin:$PATH"
echo 'export PATH="/usr/local/opt/mysql-client/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### B2. 连接

```bash
# 基本连接
mysql -h <host> -P 3306 -u <user> -p <db>

# 示例（本地 socket）
mysql -u root -p mydb

# 远程连接
mysql -h 192.168.1.100 -P 3306 -u admin -p mydb

# 连接时指定字符集（避免中文乱码）
mysql -h <host> -P 3306 -u <user> -p <db> --default-character-set=utf8mb4

# 带密码（避免交互式）
mysql -h <host> -P 3306 -u <user> -p -e "SELECT 1"

# SSH 隧道 + MySQL（安全远程访问）
ssh -L 3307:127.0.0.1:3306 user@remote-host
mysql -h 127.0.0.1 -P 3307 -u <user> -p <db>
```

### B3. 常用命令

```sql
-- 列出所有数据库
SHOW DATABASES;

-- 切换数据库
USE mydb;

-- 列出当前数据库所有表
SHOW TABLES;

-- 查看表结构
DESC table_name;
SHOW CREATE TABLE table_name;

-- 查看表详细信息
SHOW TABLE STATUS FROM mydb;

-- 常用 DML
SELECT * FROM table_name LIMIT 10;
INSERT INTO table_name (col1, col2) VALUES ('val1', 'val2');
UPDATE table_name SET col1 = 'val1' WHERE id = 1;
DELETE FROM table_name WHERE id = 1;

-- 查找列
SHOW COLUMNS FROM table_name;
SHOW FULL COLUMNS FROM table_name;

-- 查看当前连接信息
SELECT CURRENT_USER();
SHOW STATUS LIKE 'Threads_connected';

-- 执行存储过程
CALL stored_procedure_name();

-- 查看字符集配置
SHOW VARIABLES LIKE 'character_set%';
SHOW VARIABLES LIKE 'collation%';

-- 切换数据库后执行
SELECT DATABASE();
```

### B4. 导出

```sql
-- 导出表数据到文件（需 FILE 权限，secure_file_priv 限制路径）
SELECT * FROM table_name INTO OUTFILE '/tmp/table_name.csv'
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n';

-- 导出查询结果（mysql 命令行模式）
mysql -h <host> -u <user> -p <db> -e "SELECT * FROM table_name" > /tmp/result.tsv

-- 导出整个数据库（需 mysqldump）
mysqldump -h <host> -u <user> -p <db> > /tmp/mydb_backup.sql

-- 导出特定表
mysqldump -h <host> -u <user> -p <db> table_name > /tmp/table_name.sql

-- 导出所有数据库
mysqldump -h <host> -u <root> -p --all-databases > /tmp/all_databases.sql

-- 只导出表结构（不导出数据）
mysqldump -h <host> -u <user> -p <db> --no-data > /tmp/structure_only.sql

-- 导出时压缩
mysqldump -h <host> -u <user> -p <db> | gzip > /tmp/backup.sql.gz
```

### B5. 坑点

| 坑点 | 说明 | 解决 |
|------|------|------|
| `ERROR 2002 (HY000): Can't connect to local MySQL server` | socket 路径错误或服务未启动 | 加 `-h 127.0.0.1` 强制 TCP，或确认 socket 路径 `/tmp/mysql.sock` |
| `ERROR 1045 (28000): Access denied` | 用户名/密码错误或 host 限制 | 确认 `-u` 用户名对应 host 权限，MySQL 用户有 host 字段 |
| `ERROR 1290: secure_file_priv` | 导出路径被限制 | `SHOW VARIABLES LIKE 'secure_file_priv';` 查看允许路径，或 mysqldump 代替 INTO OUTFILE |
| 中文乱码 | 字符集不匹配 | 连接加 `--default-character-set=utf8mb4`，表/库确保 utf8mb4 |
| `mysqldump: Got error 1049: Unknown database` | 数据库名拼写错误 | `SHOW DATABASES;` 确认存在性 |
| 大表导出慢/内存爆 | mysqldump 默认一次性加载 | 加 `--quick` 或 `--single-transaction` 参数 |
| Mac M 系列芯片找不到 mysql client | brew 安装路径问题 | `brew link --force mysql-client`，或确认 PATH 指向正确 |

---

## 场景 C — SQLite（本地数据库）

SQLite 无需安装，macOS 内置。

### C1. 连接

```bash
# 打开已有数据库（文件不存在则创建）
sqlite3 mydb.db

# 内存数据库（临时，断开即消失）
sqlite3 :memory:

# 打开远程数据库（需 URL）
sqlite3 https://example.com/mydb.db   # 需 curl 支持
```

### C2. 常用命令（sqlite3 内）

```sql
-- 列出所有表
.tables

-- 查看表结构
.schema table_name

-- 查看完整表结构（含索引等）
.schema --pretty table_name

-- 列出所有索引
.indexes

-- 查看数据库信息
.database

-- 查看表数据（需在 sqlite3 交互式内）
SELECT * FROM table_name LIMIT 10;

-- 常用 DML
INSERT INTO table_name (col1, col2) VALUES ('val1', 'val2');
UPDATE table_name SET col1 = 'val1' WHERE id = 1;
DELETE FROM table_name WHERE id = 1;

-- 查看所有表和视图
.table

-- 查看列信息（SQLite 3.23+）
PRAGMA table_info(table_name);
PRAGAG table_xinfo(table_name);

-- 开启列显示
.headers on
.mode column
.mode list
.mode csv

-- 执行外部 SQL 文件
.read /path/to/script.sql

-- 查看版本
SELECT sqlite_version();
```

### C3. 导出

```sql
-- 导出整个数据库为 SQL（重建脚本）
.output /tmp/backup.sql
.dump
.output stdout

-- 导出表数据为 CSV（sqlite3 命令行）
sqlite3 mydb.db ".mode csv" ".output /tmp/table.csv" "SELECT * FROM table_name;"
sqlite3 mydb.db ".mode csv" ".headers on" ".output /tmp/table.csv" "SELECT * FROM table_name;"

-- 导出为 JSON（sqlite 3.38+）
sqlite3 mydb.db "SELECT json_group_array(row_to_json(t)) FROM (SELECT * FROM table_name LIMIT 10) t;"

-- 从备份恢复
sqlite3 restored.db < /tmp/backup.sql
```

### C4. 坑点

| 坑点 | 说明 | 解决 |
|------|------|------|
| 多线程写入锁住 | SQLite 写锁是数据库级 | 用 `BEGIN TRANSACTION` 批量写入，避免高并发 |
| 文件权限问题 | db 文件属主不对 | `chmod 644 mydb.db`，目录需有写权限 |
| 导入大 SQL 文件失败 | 事务未提交/磁盘满 | `sqlite3 mydb.db < script.sql`，或分批执行 |
| `.tables` 看不到表 | 大小写敏感，Windows 下需注意 | `SELECT name FROM sqlite_master WHERE type='table';` |
| 数值类型自动转换 | SQLite 是弱类型 | 用 `CAST(col AS INTEGER/TEXT/REAL)` 显式转换 |
| WAL 模式下无法压缩 | 需要先关闭 WAL | `PRAGMA journal_mode=DELETE;` 后 `VACUUM;` |
| 路径含空格 | 命令行解析问题 | 用双引号包裹路径：`sqlite3 "/path/with spaces/mydb.db"` |

---

## 通用坑点总结（PostgreSQL vs MySQL vs SQLite）

| 对比项 | PostgreSQL | MySQL | SQLite |
|--------|-----------|-------|--------|
| 默认端口 | 5432 | 3306 | 无（本地文件） |
| 默认认证 | md5/scram-sha-256（可配 peer） | mysql_native_password | 无（文件权限） |
| SSL 支持 | native（`sslmode=require`） | `--ssl-mode=REQUIRED` | 不适用 |
| 大小写敏感 | 默认敏感（取决于 OS） | Windows 不敏感，Linux 敏感 | 敏感 |
| 注释语法 | `--` 和 `/* */` | `--` 和 `/* */` | `--` 和 `/* */` |
| 分页语法 | `LIMIT n OFFSET n` 或 `OFFSET n LIMIT n` | `LIMIT n OFFSET n` | `LIMIT n OFFSET n` |
| 自增 ID | `SERIAL` 或 `GENERATED ALWAYS AS IDENTITY` | `AUTO_INCREMENT` | `INTEGER PRIMARY KEY`（自动设为 rowid） |
| 空字符串 vs NULL | 严格区分 | 区分，但可以 `=''` 隐式转换 | 区分 |
| 批量插入性能 | `INSERT INTO ... VALUES (...), (...), (...)` | 同，MySQL 最快 | 事务包裹最快 |

---

## 验证步骤（连接测试）

### PostgreSQL 验证

```bash
export PGPASSWORD='your_password'
psql -h <host> -p 5432 -U <user> -d <db> -c "SELECT 1 AS test;"
# 期望输出：test\r\n------\r\n1
```

### MySQL 验证

```bash
mysql -h <host> -P 3306 -u <user> -p -e "SELECT 1 AS test;"
# 期望输出：test\r\n1
```

### SQLite 验证

```bash
sqlite3 /tmp/test_verify.db "SELECT 1 AS test;"
# 期望输出：1
# 也可用内存数据库：
sqlite3 :memory: "SELECT 1 AS test;"
```

---

## 快速参考命令卡

```bash
# PostgreSQL
brew install postgresql@16
psql -h <host> -p 5432 -U <user> -d <db>
\dt \du \l
\copy table TO '/tmp/out.csv' WITH (FORMAT csv, HEADER true)

# MySQL
brew install mysql-client
mysql -h <host> -P 3306 -u <user> -p <db>
SHOW DATABASES; USE db; SHOW TABLES;
mysqldump -h <host> -u <user> -p <db> > backup.sql

# SQLite
sqlite3 file.db          # 无需安装
sqlite3 :memory:          # 临时内存数据库
.tables .schema .dump
sqlite3 file.db "SELECT * FROM t LIMIT 5;"
```
