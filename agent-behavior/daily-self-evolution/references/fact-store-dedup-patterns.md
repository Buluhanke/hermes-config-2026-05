# fact_store 去重模式参考 (2026-06-04 实战沉淀)

`memory_store.db.facts` 表的 UNIQUE 约束只在 content 完全相同时生效。
**绝大多数 fact content 包含时间/数字**（"14 次/h"、"磁盘 92%"、"CDP 9333 异常"），所以每次写都是新字符串 → 重复堆积。

**实测堆积样本** (2026-06-04 抓取):
```
trust=0.7 错误模式 #14/15/16 三条 content 类似，但 created_at 递增
retrieval_count 全 0  ← 说明重复了, 没人/没工具用
```

## 模式 A: 时段去重 (1 条/N 小时)

适用: 工具错误统计、Telegram 错误数等"周期性观察"

```python
import sqlite3, sys
from datetime import datetime
HOUR_KEY = datetime.now().strftime("tool_err_%Y%m%d%H")  # 含小时指纹
c = sqlite3.connect('/Users/aimac/.hermes/memory_store.db')
r = c.execute('SELECT 1 FROM facts WHERE tags LIKE ?', (f'%{HOUR_KEY}%',)).fetchone()
if r:
    c.close(); sys.exit(1)
c.execute('INSERT INTO facts (content, category, tags, trust_score) VALUES (?, ?, ?, ?)',
          ('小时工具错误聚集: 14 次 — 需要 daily 分析',
           'error_pattern', f'tools,alert,{HOUR_KEY}', 0.7))
c.commit(); c.close()
sys.exit(0)
```

## 模式 B: 日期去重 (1 条/天)

适用: 磁盘预警、代理挂掉、CDP 异常等"日级重要告警"

```python
import sqlite3, sys
from datetime import datetime
TODAY_KEY = datetime.now().strftime("disk_warn_%Y%m%d")
c = sqlite3.connect('/Users/aimac/.hermes/memory_store.db')
r = c.execute('SELECT 1 FROM facts WHERE tags LIKE ?', (f'%{TODAY_KEY}%',)).fetchone()
if r:
    c.close(); sys.exit(1)
c.execute('INSERT INTO facts (content, category, tags, trust_score) VALUES (?, ?, ?, ?)',
          ('磁盘 92% > 阈值 85% — 建议清理 logs/screenshots',
           'alert', f'disk,critical,{TODAY_KEY}', 0.8))
c.commit(); c.close()
sys.exit(0)
```

## 模式 C: 一次性 (无去重, 靠 UNIQUE 约束)

适用: 知识采集、静态事实等"写一次就够"

```python
import sqlite3
c = sqlite3.connect('/Users/aimac/.hermes/memory_store.db')
c.execute('INSERT OR IGNORE INTO facts (content, category, tags, trust_score) VALUES (?, ?, ?, ?)',
          ('GPT-5.5 是 OpenAI 2026-06-01 发布的推理模型', 'general', 'llm,openai', 0.6))
c.commit(); c.close()
```

## Shell 端接 exit code (关键)

```bash
PY="$HOME/.hermes/hermes-agent/venv/bin/python"
FACT_ADDED=0

# 模式 A: 每小时一次
HOUR_KEY="tool_err_$(date +%Y%m%d%H)"
if "$PY" -c "
import sqlite3, sys
c = sqlite3.connect('/Users/aimac/.hermes/memory_store.db')
r = c.execute('SELECT 1 FROM facts WHERE tags LIKE ?', ('%${HOUR_KEY}%',)).fetchone()
c.close()
sys.exit(0 if not r else 1)
" 2>/dev/null; then
    : # 已存在, 跳过
else
    # exit code 1 = 新增, 写库
    "$PY" -c "
import sqlite3, sys
c = sqlite3.connect('/Users/aimac/.hermes/memory_store.db')
c.execute('INSERT INTO facts (content, category, tags, trust_score) VALUES (?, ?, ?, ?)',
          ('小时工具错误聚集: 14 次', 'error_pattern', 'tools,alert,${HOUR_KEY}', 0.7))
c.commit(); c.close()
sys.exit(0)
" && FACT_ADDED=$((FACT_ADDED+1))
fi
```

## 验证命令 (写完必跑)

```bash
# 1. 验证 fact 入库
sqlite3 ~/.hermes/memory_store.db \
  "SELECT content, trust_score, datetime(created_at) FROM facts WHERE tags LIKE '%${HOUR_KEY}%'"

# 2. 验证 FTS5 同步 (FTS5 偶发不同步, 触发器已修但要测)
sqlite3 ~/.hermes/memory_store.db \
  "SELECT content FROM facts_fts WHERE facts_fts MATCH '工具错误'"

# 3. 失败时手动同步
sqlite3 ~/.hermes/memory_store.db \
  "INSERT INTO facts_fts(facts_fts) VALUES('rebuild')"
```

## 反模式 (绝对不要)

```sql
-- ❌ 危险! 会把用户真知识 (trust 0.5) 全删
DELETE FROM facts WHERE trust_score < 0.6

-- ❌ 没用! content 含时间数字时 UNIQUE 失效
INSERT OR IGNORE INTO facts (content, ...) VALUES ('错误 14 次', ...)

-- ❌ 没用! tags 也允许重复
INSERT OR IGNORE INTO facts (content, tags, ...) VALUES (..., 'tools,alert', ...)
```

正确删除条件 (90 天 + trust<0.3):
```sql
DELETE FROM facts
WHERE created_at < datetime('now', '-90 days')
  AND trust_score < 0.3
```

## 历史教训 (2026-06-04)

- 实测跑了 3 次 hourly 注入同错误 → 第一次 +1 fact, 后两次 exit code 1 → FACT_ADDED 不增 → ✅ 闭环
- 第一次跑 trust<0.6 删除 → 34 条真知识全没了, 救回 3 条 (GPT-5.5/Stagehand/browser-use), 剩余 31 条内容未知
- 教训写入 `daily-self-evolution` SKILL.md "fact_store 维护铁律" 章节

## 🚨 隐蔽 bug: `set -u` + launchd 提前 unbound (2026-06-05 真事故)

**症状**:
- `evolution.log` 显示 "新 fact=0" 但 `errors.log` 当天确实有 22+ 次工具错误
- 手动 `bash self_evolution.sh hourly` 跑 → 正常写 fact (fact_id 79 写入)
- launchd 自动跑 → 完全不写
- 表现: "去重逻辑好像坏了" / "hourly 失效" → 实际是 launchd 那次**整个 bash 早就 exit 了**

**根因**:
- 脚本顶部 `set -uo pipefail` (line 14)
- 第 71 行 `FIXED=$((FIXED+1))` — 在 FIXED 初始化 (line 105) **之前**就用了
- 手动跑时 bash 容忍未初始化变量 (interactive shell 通常 set -u 不开)
- **launchd 严格模式** → 碰到 unbound 变量 → 整脚本 exit 1 → 后续所有 fact 写逻辑跳过
- evolution_err.log 只记录 1 行 `line 86: FIXED: unbound variable` (初次出错时), 后续被吞
- 用户看到的"hourly 不写 fact"= 100% silent failure

**诊断三步法** (写 fact 突然不工作时必走):
```bash
# 1. 看 stderr log (很多 plist 没配 StandardErrorPath, 先补)
ls -la ~/.hermes/logs/evolution_err.log 2>/dev/null
cat ~/.hermes/logs/evolution_err.log 2>/dev/null | tail -5

# 2. 如果没 stderr log → 在 plist 里加
cat ~/Library/LaunchAgents/ai.hermes.self-evolution.plist | grep -A1 StandardErrorPath
# 没配就补:
#   <key>StandardErrorPath</key>
#   <string>/Users/aimac/.hermes/logs/evolution_err.log</string>

# 3. 手动跑 vs launchd 跑对比
bash /Users/aimac/.hermes/scripts/self_evolution.sh hourly  # 手动 (通常 OK)
# launchd 那次: 看 launchctl 日志
log show --predicate 'process == "launchd"' --last 5m | grep hermes
```

**修法 (铁律: 变量在最早使用前初始化)**:
```bash
# ❌ 反例: 初始化在 if 分支里, 提前用就 unbound
if [ "$MODE" = "hourly" ]; then
    log "..."
    # 这里 FIXED 已经可能用了
    if ...; then
        FIXED=$((FIXED+1))  # unbound!
    fi
    # 后面才初始化
    FIXED=0  # 晚了
    FACT_ADDED=0
fi

# ✅ 正例: 入口顶部立刻初始化
if [ "$MODE" = "hourly" ]; then
    log "===== hourly 巡检 + 修复开始 ====="

    # --- 0. 计数器提前初始化 (避免 set -u 时 unbound) ---
    FIXED=0
    FACT_ADDED=0

    # --- 1. ...
```

**预防检查清单** (改任何 set -u 脚本前必走):
```bash
# 1. 列出所有 $((VAR+1)) 出现位置
grep -n '\$((.*+1))' ~/.hermes/scripts/*.sh

# 2. 确认每处 VAR 都在它之前初始化
grep -n '^[A-Z_]*=0' ~/.hermes/scripts/self_evolution.sh

# 3. 跑一次 bash -n (语法) + 手动跑 (功能) + launchd 跑 (环境)
bash -n ~/.hermes/scripts/self_evolution.sh  # 语法
bash ~/.hermes/scripts/self_evolution.sh hourly  # 手动
# 等下次 launchd 触发 (或 launchctl kickstart) → 看 stderr
```

**配套: launchd plist 必须配 StandardErrorPath**, 否则所有 bash strict-mode 错误全丢, silent failure 找半天找不到。
