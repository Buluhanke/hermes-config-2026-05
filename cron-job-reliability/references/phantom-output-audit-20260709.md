# 2026-07-09 自我审计：phantom output 问题

## 问题
ABCD 夜间自学轮次 7/8 01:00 运行，wrapper log 显示 4/4 阶段成功，
但事实：
- `新写入 0 条 fact`（跳过 28 条已存在）
- `fact_store` 总数 76 条（本轮无增长）
- `self_model.json` 报告 "auto skill: 12 generated" 但 `skills/auto-generated/` 不存在
- auto_skill_scan_wrapper 报 "改动 2 个 domain" 但无 skill 文件落地

## 诊断命令
```bash
# 1. 确认 auto-generated 目录是否存在
ls ~/.hermes/skills/auto-generated/ 2>/dev/null && echo "存在" || echo "不存在"

# 2. self_model.json 是否和实际匹配
cat ~/.hermes/state/self_model.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
auto = d.get('auto_skill_count', d.get('skills',{}).get('auto_generated',0))
print(f'reported auto skill: {auto}')
import pathlib
ag = pathlib.Path('$HOME/.hermes/skills/auto-generated/')
if ag.exists():
    print(f'actual files: {len(list(ag.iterdir()))}')
else:
    print('auto-generated dir: 不存在')
"

# 3. fact_store 总数（对比历史输出）
python3 -c "
import sqlite3
conn = sqlite3.connect('$HOME/.hermes/memory_store.db')
c=conn.execute('SELECT COUNT(*) FROM facts').fetchone()[0]
print(f'fact_store total: {c}')
"

# 4. batch_facts_from_log 是否真的在写
grep "新写入" ~/.hermes/cron/output/idle_learning/*.log

# 5. 检查脏数据（age 异常大 = 日期计算 bug）
python3 -c "
import sqlite3
conn = sqlite3.connect('$HOME/.hermes/memory_store.db')
for r in conn.execute('SELECT fact_id, created_at, substr(content,1,50), trust_score FROM facts ORDER BY fact_id DESC LIMIT 20').fetchall():
    print(r)
"
```

## 根因

### 根因1：argparse 传参静默失败
auto_skill_scan_wrapper.sh 传 `python3 auto_skill_from_failure.py scan --min-count 3`
但 script 只接受 `--dry-run` 和 `--days`，不接受 `scan` 子命令。
argparse 遇到未知参数立即 exit(2)，wrapper 继续跑后续 self-reinforce 步骤，
cron 认为整轮 ok，但主脚本从未执行。

**Lessons**：
- wrapper 写了参数但 script 不接受 → 静默失败（最危险的 bug 类型）
- `script --help` 验证是防这类 bug 的最低成本手段
- self-reinforce 等后续步骤成功不证明主脚本成功了（它们是独立的）

### 根因2：fact_decay.py 只报不删
fact_decay.py 能正确识别 trust≤0.05 的过期 facts 并打印清单，
但默认只打印不删除（除非加 --delete flag）。
症状：fact_store 出现 age=20642d 这种不可能的数字（日期计算 bug 的脏数据），
trust=0.000 但 fact_decay 只报告"可删除"而不实际删除。
本次案例：id 97/98/99/109 四条 age=20642d，created_at 却是 2026-06-05。

### 根因3：self_model auto_skill_count 从内存计非文件计
self_model.json 里的 `auto_skill_count` 是脚本内存里的变量，
不等于 `~/.hermes/skills/auto-generated/` 目录下的实际文件数。
wrapper 报 "auto skill: 12 generated" 但目录可能不存在或为空。

## 修复状态
1. ✅ 修复1：wrapper 去掉 `scan --min-count`，主脚本直接运行（已修复）
2. ✅ 修复2：手动 DELETE 脏数据（fact_decay --delete 待确认）
3. ✅ 修复3：auto_skill 文件现在正常落地（2026-07-08 11:13 生成了 error-patterns-20260708.md）
4. ⏳ 待办：self_model.json 的 auto_skill_count 应从实际落地文件计数

## 验证清单
```bash
# 每次 idle_learning_wrapper 跑完后执行
python3 -c "
import sqlite3, pathlib
db = pathlib.Path('$HOME/.hermes/memory_store.db')
ag = pathlib.Path('$HOME/.hermes/skills/auto-generated/')
conn = sqlite3.connect(str(db))
total = conn.execute('SELECT COUNT(*) FROM facts').fetchone()[0]
bad = conn.execute('SELECT COUNT(*) FROM facts WHERE trust_score <= 0.05').fetchone()[0]
print(f'fact_store: {total} total, {bad} bad (trust<=0.05)')
ag_files = len(list(ag.iterdir())) if ag.exists() else 0
print(f'auto-generated skills: {ag_files} files')
"
```
