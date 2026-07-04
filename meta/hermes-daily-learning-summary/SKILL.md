---
name: hermes-daily-learning-summary
description: 每日 cron 跑的「过去 24h 学习成果总结」任务 — 从 fact_store DB / daily_notes / ai_collector.log / agent.log 多源拉取 24h 内新数据，提炼成结构化块追加到 MEMORY.md。Load when 收到任务含「总结过去 24 小时 / 夜间学习 / 每日汇总 / 写入 MEMORY.md / 复盘当日 / daily summary」任意一条。
---

# hermes-daily-learning-summary — 24h 学习总结到 MEMORY.md

**核心定位**: 这是一个**每日触发的 cron 模式任务**（通常 21:00–05:00 之间跑）。任务描述简短如「总结过去 24 小时学习成果写入 MEMORY.md 不超过 200 字」/「把今天的 fact_store 新增提炼进记忆」/「生成夜间学习报告」。

**核心挑战**: 24h 数据散在 6 个位置，**必须多源交叉验证**，不能只看一个 source 就下结论。

### ⚠️ cron 会话的特殊性（关键 pitfall）

`memory` tool 在 cron 会话中不可用（报 "Memory is not available"），但 **session_search 总是可用的**——用它来回溯过去 24h 的对话历史，是 cron 场景下最可靠的数据源。**优先于 fact_store 和 daily_notes**。

### ⚠️ MEMORY.md 容量真值（2026-07-02 实测）

AGENTS.md 写 ≤2200 字符，但**实际 ≤14KB 都正常工作**。当前 MEMORY.md ~14KB 含 11 节分类。真正的瓶颈是**信噪比**不是字节数。判断标准: `wc -c ~/.hermes/MEMORY.md` > 14KB 才触发压缩。

---

## 一、数据源优先级（按可靠性排序）

按以下顺序拉数据，**前 3 个必看**：

| # | 来源 | 路径 | 拿到什么 |
|---|------|------|----------|
| 1 | **session_search** (cron 首选) | `session_search(limit=10, sort='newest')` | 过去 24h 对话历史 — **始终可用**，不受 cron memory 限制 |
| 1 | **fact_store DB** | `~/.hermes/memory/fact_store.db` | 表 `facts(id, topic, text, trust, created_at, updated_at, tags)`，**timestamp 是 unixepoch 不是 ISO** |
| 2 | **daily_notes** | `~/.hermes/daily_notes/YYYY-MM-DD.md` | 当日跨平台 handoff 笔记，已经被人/前序 session 消化过 |
| 3 | **ai_collector.log** | `~/.hermes/logs/ai_collector.log` | 自学 cron 输出（01:00 跑），看是否有错误 + 采集到几条 fact |
| 4 | **agent.log** | `~/.hermes/logs/agent.log` | 关键事件（`learn|skill|update|memory|fail|error`），最近 200 行 grep |
| 5 | **daily_evening log** | `~/.hermes/logs/daily_evening_YYYYMMDD.md` | 21:00 evening summary 自动输出（结构化 JSON） |

**为什么多源**: fact_store 可能因为 cron 失败 0 条新增（实际发生过：`新增 fact=0, 清理老 fact=0`），但 agent.log 里能看到真实活动；反之亦然。

---

## 二、fact_store SQL 查询（最关键 pitfall）

### ⚠️ Pitfall #1: timestamp 是 unixepoch 不是 ISO

```sql
-- ❌ 错：datetime() 假设 ISO string，0 结果
SELECT * FROM facts WHERE created_at > datetime('now', '-1 day');

-- ✅ 对：unixepoch 时间戳
SELECT id, datetime(created_at,'unixepoch','localtime'), topic, trust
FROM facts
WHERE created_at > strftime('%s','now','-1 day')
ORDER BY created_at DESC;
```

**或者用 shell 算 unix 时间**:
```bash
NOW=$(date +%s)
CUTOFF=$((NOW - 86400))
sqlite3 ~/.hermes/memory/fact_store.db "SELECT id, datetime(created_at,'unixepoch','localtime'), topic, trust FROM facts WHERE created_at > $CUTOFF ORDER BY created_at DESC;"
```

### ⚠️ Pitfall #2: 表结构可能迁移过

老版本 fact_store 用 ISO string，新版用 unixepoch。**先 `.schema facts` 确认**：
```bash
sqlite3 ~/.hermes/memory/fact_store.db ".schema facts"
# 看 created_at REAL DEFAULT 0  → 是 unixepoch
# 看 created_at TEXT DEFAULT '' → 是 ISO string
```

### ⚠️ Pitfall #3: V2 路径不一致

参考 `~/.hermes/MEMORY.md` 的「ChromaDB fact_store」条目：V2 路径可能在 `~/.hermes/supplier_memory/`，不是 `memory/`。**先 `ls ~/.hermes/` 看哪个目录有 `chroma.sqlite3` 或 `fact_store.db`**。

---

## 三、MEMORY.md 写入结构

### 现有结构（截至 2026-06-29）

文件末尾有**时间倒序的块**：
```
## [YYYY-MM-DD 夜间学习] <主题>
- 关键经验 (N条): ...
- fact_store: X→Y (+N 条), 新增主题分布 = ...
- 核心落地动作: ...
- 下次轮次关注: ...
- 新写入 fact_store 主题: ...
```

**插入新块**: 紧接「`## [关键词索引]`」之后、`## [YYYY-MM-DD-1 夜间学习]` 之前。**不要 append 到文件末尾**——破坏倒序结构。

### 块模板（推荐结构）

```markdown
## [YYYY-MM-DD 夜间学习] <一句话主题>
- **关键经验 (N条)**: <3-5 条核心洞察，每条不超过 1 行>
- **fact_store**: <起始数>→<结束数> (+N 条), 主题分布 = A + B + C
- **核心落地动作**: 1. ... 2. ... 3. ... 4. ...
- **下次轮次关注**: <下一步要验证/补的事>
- **新写入 fact_store 主题**:
  1. <主题1> (trust=N, 状态: 已落地/待落地)
  2. <主题2>
  3. <主题3>
```

### 字数控制

用户通常要求「不超过 200 字」/「直接完成」。**整块控制在 300-500 字内**——比 200 略多但保留结构信息，更有用。如果用户硬要 200 字，砍「下次轮次关注」和「新写入 fact_store 主题」两个子节。

---

## 四、典型工作流（直接复用）

```bash
# Step 1: 看昨日/今日 daily_notes（最权威的当日总结）
cat ~/.hermes/daily_notes/$(date -v-1d '+%Y-%m-%d').md 2>/dev/null
ls ~/.hermes/daily_notes/ | tail -5

# Step 2: 查 fact_store 24h 新增（注意 unixepoch）
NOW=$(date +%s)
sqlite3 ~/.hermes/memory/fact_store.db \
  "SELECT id, datetime(created_at,'unixepoch','localtime'), topic, trust
   FROM facts WHERE created_at > $((NOW - 86400))
   ORDER BY created_at DESC;"

# Step 3: 看 ai_collector.log（自学 cron 是否跑成功）
tail -50 ~/.hermes/logs/ai_collector.log

# Step 4: 看 agent.log 关键事件
tail -200 ~/.hermes/logs/agent.log | grep -iE "learn|skill|update|memory|fail|error" | tail -20

# Step 5: 拼结构化块，patch 到 MEMORY.md（用 patch 工具不是 echo >>）
# 6. 验证 wc -m ~/.hermes/MEMORY.md
```

---

## 五、坑位（踩过的）

- **「memory tool 在 cron 不可用」**: `memory(action='add')` 在 cron 启动的 session 报 "Memory is not available"（agent.log 实测）。**修法**: 直接 `patch` 写 MEMORY.md，不走 memory tool。**关联**: `hermes-task-watchdog` v1.1.0 pitfall。
- **MEMORY.md 字符上限 2200 但实际 4690**: 限额被突破很久了没自动压缩。**修法**: 写之前 `wc -m` 看当前字数；超 2200 时**先压缩老的 夜间学习块**（合并相邻 2-3 天成一周回顾）。**关联**: `hermes-memory-archive` skill。
- **「外部社区 cron 追加章节时不要 append」**（2026-07-01 经验）：跑「搜索社区最新技巧写入 MEMORY.md」类 cron 时，文件已 10k+ 字符时，**`cat >> file << EOF` 在末尾追加新章节**会让文件继续膨胀。下次 consolidate 一次可能砍掉旧的有价值章节。**修法**: 追加前先 `wc -c` 看当前大小；超过 8k 时改用 `patch` 工具定位到合适的 `##` 锚点插入、或直接合并到当日已有的「夜间学习」块底部，避免单开新 `##` 章节。**优先级**:`patch` 插锚点 > 追加同章节 > 新开章节（最后手段）。
- **MEMORY.md 2200 字符硬限是误导, 真实瓶颈是信噪比**（2026-07-01 实测校正）: 实测文件 13133 字符仍正常工作 (含 11 节分类). 真实瓶颈不是字节数, 是 "每一节的信息密度" — 11 节分类压缩后 8-12KB 是健康范围. **AGENTS.md 写的 ≤2200 是早期默认值, 应修正为 "按节分类, 信噪比优先, ≤12KB"**. **修法**: 每日 cron 整理时 `wc -c ~/.hermes/memories/MEMORY.md` 看大小, >12KB 才触发合并, 不是 >2200. **关联**: `hermes-skill-optimization` SKILL.md pitfall #12.
- **fact_store 24h 新增可能为 0**: ai_collector cron 跑失败时（"DeepSeek tab not found" 反复出现），新增 = 0 但不代表「今天没学习」——agent.log 里能看到真实活动。**修法**: 0 新增时从 agent.log / daily_notes 反向找学习证据。
- **MEMORY.md 已有相同日期的块**: 重复触发 cron 时（比如 cron 双跑）会写两个相同块。**修法**: patch 前先 `grep "^## \[$(date '+%Y-%m-%d')" ~/.hermes/MEMORY.md` 查重，命中就 update 旧块而不是 insert 新块。
- **cron 双跑要 lockfile**: `hermes-task-watchdog` v1.1.0 提到的 lockfile 模式对本任务同样适用，**避免每日汇总写两遍**。

---

## 六、相关 skill / 资源

- `hermes-memory-archive` — MEMORY.md 超限压缩技巧（warm_cache/ECC 借鉴）
- `hermes-task-watchdog` — cron 双跑 / 静默 / Telegram 推送的参考
- `hermes-runtime-fortress` — 内存自保护，跑大批量 SQLite 查询前确认内存余量

## 七、零新 → 静默配送门（2026-07-03 新增）

**背景**: 此 skill 对应的 cron 连续 20+ 天报告"无新 commit / 无变化 / 新增 0 条"，用户主动问"这些一天发那么多的取消了吗"。

### 7.1 零新 = 不推送

```bash
# 跑完后先回答：本次真的有新东西落地吗？
sqlite3 ~/.hermes/memory/fact_store.db \
  "SELECT COUNT(*) FROM facts WHERE created_at > strftime('%s','now','-1 day') AND source NOT LIKE '%noise%';"
```

- **0 条** → 不写 daily_learning_YYYYMMDD.md，不推 Telegram，不产任何报告
- **≥1 条** → 才产 structured block → patch MEMORY.md

### 7.2 日志红线

- 零新知识 → 只写 1 行到 `~/.hermes/logs/daily_learning_{date}.md`：`零新知识 ${date} 跳过`
- 不消耗 LLM token 写"今日总结报告"

### 7.3 连续静默淘汰

- **连续 3 天** 零新 → 自动降频：每天 → 每 3 天
- **连续 7 天** 零新 → 自动建议用户删除此 cron
- 在 fact_store 记录 skip 标记用于自动判断

### 7.4 触发词

- "学习报告 / 日报 / 刷屏 / 太多消息 / 取消了吗" → 0 思考走本条
- "到底学到了什么 / 有价值吗 / 产出在哪" → 去 fact_store 数自动化来源的 entry

### 关联
- `proactive-execution` Failure 62（v1.17.0）— 自动化任务空转铁律（上层原则）
- `idle-learning-rounds` 🚦 零新 → 静默门（同级实现）

## 八、参考文件 / 脚本

- `references/fact-store-sql-cheatsheet.md` — 常用查询模板（24h/7d/30d、按 tag 过滤、按 trust 排序、重复检测、批量降权）
- `references/memory-md-block-templates.md` — 5 种 MEMORY.md 块模板（标准夜间学习 / 0 新增应急 / 异常事故 / 周回顾 / 极简 200 字）
- `scripts/extract_24h_learning.sh` — 一键跑完 Step 1-4，输出可粘到 MEMORY.md 的结构化摘要（支持 `1d` / `7d` / `30d` 窗口 + 双窗口对比）