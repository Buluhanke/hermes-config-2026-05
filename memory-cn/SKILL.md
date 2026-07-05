---
name: memory-cn
version: 2.0.0
description: Hermes 中文记忆系统 — 两层架构：fact_store(FTS5 SQLite) + Mnemosyne(SQLite向量)，skill 沉淀能力，memory 工具存偏好
created: 2026-06-25
updated: 2026-07-05
platforms: [macos]
metadata:
  hermes:
    tags: [memory, fact-store, fts5, sqlite, search, chinese]
    related_skills: [context-optimization, proactive-execution]
---

# Memory-CN — Hermes 中文记忆系统优化 (v2.0)

## 架构现状（2026-07-06 v2.0）

Hermes 记忆系统是 **三层架构**：

| 层 | 组件 | 用途 | 搜索方式 |
|----|------|------|----------|
| P0 | `MEMORY.md` (~2KB) | 核心偏好/高频规则 | 全文扫描 |
| P1 | `fact_store.db` (FTS5 SQLite) | 经验/教训/规则沉淀 | FTS5 全文搜索 |
| P2 | **Mnemosyne** (向量+SQLite) | 语义记忆/偏好/跨会话 | sub-ms 向量查询 |

**2026-07-06 新增**：Mnemosyne 已安装为 `memory.provider`，char_limit 6600（原来 2200 的 3 倍）。

---

## 一、fact_store 诊断与调优

### 诊断命令

```bash
# fact_store 基本统计
sqlite3 ~/.hermes/memory/fact_store.db "SELECT COUNT(*) FROM facts;"
sqlite3 ~/.hermes/memory/fact_store.db "SELECT COUNT(*), AVG(trust) FROM facts WHERE trust > 0.05;"

# 低信任/过期条目
sqlite3 ~/.hermes/memory/fact_store.db "SELECT id, topic, trust FROM facts WHERE trust <= 0.05;"

# 无tags条目（搜索命中率杀手）
sqlite3 ~/.hermes/memory/fact_store.db "SELECT id, LENGTH(tags) FROM facts WHERE tags IS NULL OR tags = '';"

# fact_decay 脚本
python3 ~/.hermes/scripts/fact_decay.py
```

### 健康标准

| 指标 | 健康值 | 修复阈值 |
|------|--------|----------|
| 活跃条数 | > 50 | < 20 时需激活 |
| 平均 trust | ≥ 0.4 | < 0.3 时需衰减 |
| 无tags条数 | 0 | > 5 时需补打 |
| 过期条数 | 0 | > 0 时需删除 |

---

## 二、FTS5 中文分词优化

### unicode61 Bug（已知问题）

`unicode61` 分词器把连续CJK字符当作一个token：
- 搜索 "怀孕" 无法匹配 "老婆刚怀孕"（因为后者是单token）
- 搜索 "内存" 可能漏掉 "内存泄漏"

### 诊断

```bash
# 查看当前分词配置
sqlite3 ~/.hermes/memory/fact_store.db "PRAGMA table_info(facts);"
sqlite3 ~/.hermes/memory/fact_store.db "SELECT sql FROM sqlite_master WHERE type='table' AND name LIKE '%_fts%';"
```

### 缓解策略

**策略1：中文关键词之间加空格**（现有数据）

对历史条目补充空格分隔：
```bash
# 示例：用python批量给中文文本加空格（粗略分词）
python3 -c "
import re, sqlite3
conn = sqlite3.connect('$HOME/.hermes/memory/fact_store.db')
cur = conn.cursor()
cur.execute('SELECT id, text FROM facts WHERE text NOT NULL')
for row in cur.fetchall():
    # 简单处理：在2-4个连续汉字间加空格
    fixed = re.sub(r'([\u4e00-\u9fff]{2,4})', r' \1 ', row[1])
    if fixed != row[1]:
        cur.execute('UPDATE facts SET text=? WHERE id=?', (fixed.strip(), row[0]))
conn.commit()
"
```

**策略2：MMR搜索权重调整**

在搜索查询中使用 `BM25` 排序 + 向量重排：
- FTS5 BM25 对中文单token效果好
- 混合搜索时 vectorWeight 0.75（Mem0推荐值）

---

## 三、Mnemosyne 用法（2026-07-06 新增）

### 已安装
```bash
pip install mnemosyne-memory  # ✅ 已装 v3.11.1
hermes memory status          # 显示 mnemosyne (local)
```

### Python API
```python
from mnemosyne import remember, recall

# 记住语义偏好
remember("用户讨厌反问，偏好直接执行", importance=0.9)

# 语义召回
results = recall("用户行为偏好")
```

### Mnemosyne 优势
- sub-millisecond 查询（比 FTS5 快）
- 向量语义搜索（不只是关键词）
- SQLite 本地存储，无需外部服务
- Hermes 官方集成（`memory.provider: mnemosyne`）

## 四、Mem0/Mimir 架构借鉴

### Mem0 架构（2026年最佳实践）

```
Tier 1: RAM / Context Window（瞬时记忆）
  → Hermes当前会话的 memory tool 注入

Tier 2: SQLite + FTS5 + Vector（持久记忆）
  → Hermes fact_store.db（当前）
  → 可升级：加向量列 + bge-reranker（Mimir路线）

Tier 3: 日志/归档（冷存储）
  → ~/.hermes/memory/ 日志文件
```

**Mem0核心原则（可借鉴）**：
1. **单一事实来源**：每条fact只写一次，不重复
2. **agent-generated facts等权**：Hermes的推断和用户的陈述同等存储
3. **衰减模型**：trust随时间线性衰减，>90天进入低信任区

### Mimir 架构（SQLite FTS5 + Vector混合）

Mimir = SQLite FTS5 + dense vector search，MCP-native，**完全本地**。

**对Hermes的借鉴**：在fact_store.db中加向量列：
```sql
-- 可选升级路径（当前Hermes未实现）
CREATE VIRTUAL TABLE facts_fts USING fts5(text, content=facts, content_rowid=id);
ALTER TABLE facts ADD COLUMN embedding BLOB;  -- 向量嵌入
```

**短期优先级**：先优化FTS5查询，不加向量层（向量需要额外依赖）

---

## 四、搜索质量提升（当前可落地）

### 4.1 查询扩展（Query Expansion）

搜索 "内存" 时同时搜 "RAM" "memory" "存储"：
```sql
SELECT * FROM facts WHERE facts_fts MATCH 'memory OR RAM OR 内存 OR 存储';
```

### 4.2 标签过滤优先

带明确tags的条目优先级更高：
```sql
SELECT f.*, LENGTH(f.tags) as tag_len
FROM facts f
WHERE f.trust > 0.15
ORDER BY tag_len DESC, f.trust DESC
LIMIT 10;
```

### 4.3 时间衰减

优先显示近期条目（Mem0 halfLifeDays=90天的简化版）：
```sql
-- 近30天条目boost
SELECT *,
  CASE WHEN created_at > strftime('%s','now','-30 days') THEN 1.2 ELSE 1.0 END as time_boost,
  trust * (CASE WHEN created_at > strftime('%s','now','-30 days') THEN 1.2 ELSE 1.0 END) as weighted_trust
FROM facts
WHERE trust > 0.15
ORDER BY weighted_trust DESC
LIMIT 10;
```

---

## 五、MEMORY.md 优化（< 2200字符）

当前限制：2200字符，超限自动压缩。

### 结构模板

```markdown
# MEMORY.md — 系统级记忆

## 用户偏好（不变）
- 决策风格：直接动手不反问
- 执行偏好：本地优先，配置透明
- 数字人定位：Mac mini数字主人

## 核心规则（高频引用）
- proactive-execution：收到立即做，失败换方法，3次才报
- verification-before-reporting：汇报前必须有验证输出

## 环境（需更新时改）
- 模型：MiniMax-M2.7-highspeed（主）/ deepseek-chat（付费）
- 浏览器：Chrome CDP 9222
- gateway：PID 11325（2026-07-02）

## 最新教训（最近30天）
<!-- 每个条目不超过50字 -->
- [日期] [类别] [一句话教训]
```

---

## 六、自动维护 Cron

```yaml
# ~/.hermes/cron/memory-maintenance.yaml
# 每周日凌晨2点执行
schedule: "0 2 * * 0"
script: ~/.hermes/scripts/memory_maintenance.sh
deliver: local
no_agent: true
```

```bash
#!/bin/bash
# memory_maintenance.sh
echo "=== fact_store 健康检查 ==="
python3 ~/.hermes/scripts/fact_decay.py

echo "=== 低信任清理 ==="
sqlite3 ~/.hermes/memory/fact_store.db "DELETE FROM facts WHERE trust <= 0.05;"

echo "=== 无tags条目报告 ==="
count=$(sqlite3 ~/.hermes/memory/fact_store.db "SELECT COUNT(*) FROM facts WHERE tags IS NULL OR tags = '';")
echo "无tags条目: $count"
if [ "$count" -gt 10 ]; then
  echo "需要补打tags"
fi

echo "=== MEMORY.md 大小检查 ==="
size=$(wc -c < ~/.hermes/memories/MEMORY.md)
echo "MEMORY.md: $size bytes"
if [ "$size" -gt 2200 ]; then
  echo "需要压缩"
fi
```

---

## 七、相关skill

- `context-optimization`：token优化，MEMORY.md大小管理
- `proactive-execution`：Failure案例写入fact_store的时机
- `verification-before-reporting`：汇报前验证，影响fact可信度判断
