# Memory Hygiene — fact_store 不写噪声 (2026-06-27 实战)

## 核心原则

**写入前必绑定 retrieval 触发场景**, 否则 0 价值。

## 2026-06-27 大扫除实战数据

- fact_store 总条数: **145**
- 被 retrieval 过的: **0 条 (0%)**
- 删除: **129 条 (-89%)**
- 留下: **16 条 trust≥0.8 的高价值 fact**

## 噪声三大类 (被批量删)

1. **重复事件型** (76 条): "小时工具错误聚集: N 次 — 需要 daily 分析分布" 一模一样的模板, 6/5~6/24 共 76 条, 0 价值
2. **过期快照型** (30 条): GitHub commit hash / 一次性 CVE / 单条论文摘要 / Hermes 模型快照
3. **低质 general** (23 条): trust<0.7 + ret=0 + help=0 的"我知道但没用过"条目

## 写入前 3 问 (硬规则)

写任何 fact 之前必答:

1. **谁会 retrieve 这条?** — 必须能说出具体触发场景
2. **trust 是怎么涨上去的?** — 不是写入时设 0.5, 是后续被 retrieve + helpful 后才到 0.7+
3. **半年后还有用吗?** — 一次性 commit/CVE/benchmark → 半年后 0 价值

任何一项答不上 → 别写。

## 检索健康度自检

```python
import sqlite3
conn = sqlite3.connect('/Users/aimac/.hermes/memory_store.db')
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM facts WHERE retrieval_count > 0 OR helpful_count > 0")
print(f"Ever used: {cur.fetchone()[0]} / <total>")
# 期望: 至少 30% 以上的 fact 被 retrieve 过
# 低于 10% = 整个 fact_store 在写噪声, 触发清理
```

## 清理 SOP (按 trust + retrieval 双重过滤)

```sql
-- 留: trust≥0.8 OR (retrieval_count>0 AND helpful_count>0)
-- 删: trust<0.8 AND retrieval_count=0 AND helpful_count=0
DELETE FROM facts
WHERE trust_score < 0.8
  AND retrieval_count = 0
  AND helpful_count = 0;
-- 灰区 (trust 0.5~0.8 + ret=0): 看 updated_at, >30 天 = 删
```

## 触发词

- "memory 满了 / fact_store 满了 / 写不进记忆" → 先跑健康度, 删噪声再写
- "fact_store 0 retrieval / 写了从不读" → 触发 hygiene 流程
- "保留哪些 fact" → trust≥0.8 + ret>0 双重过滤

## 跟 v1.11.0 cron 静默化的关系

| 维度 | cron 静默化 | fact_store hygiene |
|---|---|---|
| 噪声类型 | 自动推送消息 | 自动入库 fact |
| 浪费的是 | 用户注意力 | context 窗口 + 检索时间 |
| 修法 | deliver=local + no_agent=True | 写入前必绑定 retrieval 场景 |
| 健康指标 | 一天推送条数 | fact ret/total 比例 |

## 反面案例

- 145 条 fact 0 retrieval → 浪费 ~10MB DB + 检索全是噪声干扰
- "小时工具错误聚集" 写 76 次 → 真异常被淹没
- 一次性论文/CVE 30+ 条 → 半年后全 stale

## 正面案例 (留的 16 条)

- 实战事故教训 (PR #14397, self_evolution.sh SIGTERM 根因, launchd cwd=/) — 踩坑直接 grep
- 框架铁律 (STAR-4D / Ponytail / Pitfalls) — 触发词命中就检索
- 真实工具 SOP (Telegram Pool timeout / Chrome CDP) — 出错直接 ret