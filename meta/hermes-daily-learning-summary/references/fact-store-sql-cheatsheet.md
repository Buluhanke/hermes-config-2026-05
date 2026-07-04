# fact_store SQL 查询速查（Hermes）

**DB 位置**: `~/.hermes/memory/fact_store.db`（V2 可能在 `~/.hermes/supplier_memory/`）
**表**: `facts(id INTEGER PK, topic TEXT, text TEXT, source TEXT, trust REAL DEFAULT 0.5, created_at REAL DEFAULT 0, updated_at REAL DEFAULT 0, tags TEXT DEFAULT '[]')`
**关键**: `created_at` 和 `updated_at` 是 **unixepoch 浮点秒**（如 `1782680523.62`），不是 ISO string。

---

## 1. 24h / 7d / 30d 时间窗（最常用）

```sql
-- ⚠️ unixepoch 一定要显式转换
SELECT id,
       datetime(created_at, 'unixepoch', 'localtime') AS created_local,
       topic,
       trust,
       substr(text, 1, 100) AS preview
FROM facts
WHERE created_at > strftime('%s', 'now', '-1 day')
ORDER BY created_at DESC;

-- 7 天
WHERE created_at > strftime('%s', 'now', '-7 days')

-- 30 天
WHERE created_at > strftime('%s', 'now', '-30 days')
```

**或者 shell 算 unix now**（避免每次 SQL 都重算）：
```bash
NOW=$(date +%s)
sqlite3 ~/.hermes/memory/fact_store.db \
  "SELECT id, datetime(created_at,'unixepoch','localtime'), topic, trust
   FROM facts WHERE created_at > $((NOW - 86400))
   ORDER BY created_at DESC;"
```

---

## 2. ❌ 错误示范（坑 #1）

```sql
-- 错 1：datetime() 默认按 ISO string parse
WHERE created_at > datetime('now', '-1 day')
-- 返回 0 行，因为 sqlite 把 '1782680523.62' 当 ISO 解析失败

-- 错 2：直接和 ISO 字面量比
WHERE created_at > '2026-06-28 00:00:00'
-- 同上，0 结果

-- 错 3：用 julianday 把 unix 转 day（精度丢）
WHERE julianday(created_at) > julianday('now', '-1 day')
-- 偶尔能 work 但浮点边界易踩坑
```

---

## 3. 按 tag 过滤（JSON 数组列）

`tags` 是 JSON 数组字符串如 `'["skill-vetter","ethics"]'`。用 `like` 或 `json_each`：

```sql
-- 方法 A: like（快但不精确，'skill' 会匹到 'skill-vetter' 和 'skillful'）
WHERE tags LIKE '%skill-vetter%'

-- 方法 B: json_each（精确但稍慢）
WHERE EXISTS (
  SELECT 1 FROM json_each(tags)
  WHERE json_each.value = 'skill-vetter'
)
```

---

## 4. 按 trust 排序 / 过滤

```sql
-- 高 trust（≥0.8）按时间倒序
SELECT id, topic, trust, datetime(created_at,'unixepoch','localtime')
FROM facts
WHERE trust >= 0.8
ORDER BY created_at DESC
LIMIT 20;

-- 低 trust 候选清理（trust<0.3 且 30d+ 未引用）
SELECT id, topic, trust,
  datetime(created_at,'unixepoch','localtime') AS created,
  datetime(updated_at,'unixepoch','localtime') AS updated
FROM facts
WHERE trust < 0.3
  AND updated_at < strftime('%s', 'now', '-30 days');
```

---

## 5. 重复检测（同名同 trust）

```sql
-- 找 topic 出现 ≥2 次的事实（可能被反复写入）
SELECT topic, COUNT(*) AS cnt, MAX(trust) AS max_trust,
  datetime(MAX(created_at),'unixepoch','localtime') AS last_seen
FROM facts
GROUP BY topic
HAVING cnt > 1
ORDER BY cnt DESC;
```

---

## 6. 统计概览

```sql
-- 总数 + trust 分布
SELECT
  COUNT(*) AS total,
  SUM(CASE WHEN trust >= 0.8 THEN 1 ELSE 0 END) AS high_trust,
  SUM(CASE WHEN trust >= 0.5 AND trust < 0.8 THEN 1 ELSE 0 END) AS mid_trust,
  SUM(CASE WHEN trust < 0.5 THEN 1 ELSE 0 END) AS low_trust
FROM facts;

-- 最近 7 天每天新增量
SELECT
  date(created_at, 'unixepoch', 'localtime') AS day,
  COUNT(*) AS new_facts
FROM facts
WHERE created_at > strftime('%s', 'now', '-7 days')
GROUP BY day
ORDER BY day DESC;

-- 按 source 分布
SELECT source, COUNT(*) AS cnt
FROM facts
GROUP BY source
ORDER BY cnt DESC;
```

---

## 7. 实用维护操作

```sql
-- 删除单条（谨慎）
DELETE FROM facts WHERE id = 123;

-- 批量软降权（信任度 -0.1）
UPDATE facts
SET trust = MAX(0.0, trust - 0.1),
    updated_at = strftime('%s','now')
WHERE updated_at < strftime('%s','now','-90 days')
  AND trust < 0.5;

-- 加 tag
UPDATE facts
SET tags = json_insert(tags, '$[#]', 'new-tag'),
    updated_at = strftime('%s','now')
WHERE id = 123;

-- 删 tag
UPDATE facts
SET tags = (
  SELECT json_group_array(value)
  FROM json_each(tags)
  WHERE value != 'old-tag'
),
updated_at = strftime('%s','now')
WHERE id = 123;
```

---

## 8. 一次性 schema 自检脚本

每次升级/迁移后跑一遍确认结构没变：

```bash
sqlite3 ~/.hermes/memory/fact_store.db <<'EOF'
.schema facts
SELECT 'row_count', COUNT(*) FROM facts;
SELECT 'time_range',
  datetime(MIN(created_at),'unixepoch','localtime'),
  datetime(MAX(created_at),'unixepoch','localtime')
FROM facts;
EOF
```

如果 `created_at` 是 `TEXT` 类型，老 DB 用 ISO string —— 见 SKILL.md 第二节 Pitfall #2 的兼容 SQL。