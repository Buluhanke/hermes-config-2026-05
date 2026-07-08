---
name: hermes-observability
description: >
  Hermes LLM 可观测性 skill — 记录 token 消耗、延迟、错误率、Provider 分布。
  数据全本地 SQLite，不外发任何数据。
  
  用法：
  - `hermes_observability_log(provider, model, input_tokens, output_tokens, latency_ms, status, error)` — 记录一次 LLM 调用
  - `hermes_observability_stats(days=7)` — 统计近 N 天数据
  - `hermes_observability_errors(days=7)` — 最近错误
  - `hermes_observability_provider_breakdown()` — Provider/Model 分布
  - `hermes_observability_cost_estimate()` — 估算成本
  - `hermes_observability_daily(since_days=30)` — 近 N 天每日趋势

  底层：SQLite + OpenTelemetry SpanExporter 接口，数据存在 ~/.hermes/llm_traces.db
triggers:
  - observability: 可观测性/调用统计/token消耗/延迟/错误率/成本/用量
  - tracing: 追踪/tracing/trace/llm日志/调用日志
  - metrics: 指标/metrics/用量/provider分布
---

# Hermes Observability — 本地 LLM 可观测性

全本地存储，不依赖任何外部服务。数据路径：`~/.hermes/llm_traces.db`

## 数据库 Schema

```sql
CREATE TABLE llm_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT,
    span_id TEXT,
    parent_span_id TEXT,
    provider TEXT,        -- openai / anthropic / glm / deepseek 等
    model TEXT,           -- claude-sonnet-4 / gpt-4o 等
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    latency_ms REAL,      -- 端到端延迟，毫秒
    status TEXT,          -- success / error / timeout
    error TEXT,           -- 错误信息
    cost_usd REAL,        -- 估算成本（USD）
    timestamp TEXT,       -- ISO 格式
    duration_ms REAL      -- 模型实际推理时间（若可测）
);
```

## Token 单价表（USD / 1M tokens）

```python
PRICING = {
    "anthropic/claude-sonnet-4":   {"input": 3.0, "output": 15.0},
    "anthropic/claude-opus-4":     {"input": 15.0, "output": 75.0},
    "anthropic/claude-haiku-4":    {"input": 0.8, "output": 4.0},
    "openai/gpt-4o":              {"input": 2.5, "output": 10.0},
    "openai/gpt-4o-mini":         {"input": 0.15, "output": 0.60},
    "openai/o3":                  {"input": 10.0, "output": 40.0},
    "openai/o4-mini":             {"input": 1.1, "output": 4.4},
    "google/gemini-2.5-pro":      {"input": 1.25, "output": 5.0},
    "google/gemini-2.5-flash":    {"input": 0.075, "output": 0.30},
    "deepseek/deepseek-chat":     {"input": 0.027, "output": 0.27},
    "zhipu/glm-4-flash":          {"input": 0.07, "output": 0.07},  # batch价
    "minimax/M2.7-32k":           {"input": 0.07, "output": 0.14},
    "custom:zai":                 {"input": 2.0, "output": 8.0},    # 估算
}
# 未知 model 默认 input=1.5, output=7.0 (USD/M)
DEFAULT = {"input": 1.5, "output": 7.0}
```

## 快速使用命令

```bash
# 初始化数据库（首次使用）
python3 -c "
import sqlite3, os
db = os.path.expanduser('~/.hermes/llm_traces.db')
c = sqlite3.connect(db)
c.execute('''CREATE TABLE IF NOT EXISTS llm_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT, span_id TEXT, parent_span_id TEXT,
    provider TEXT, model TEXT,
    prompt_tokens INTEGER, completion_tokens INTEGER, total_tokens INTEGER,
    latency_ms REAL, status TEXT, error TEXT, cost_usd REAL,
    timestamp TEXT, duration_ms REAL)''')
c.commit()
print('DB ready:', db)
"

# 查看统计
python3 - <<'EOF'
import sqlite3, os
db = os.path.expanduser('~/.hermes/llm_traces.db')
c = sqlite3.connect(db)

# 通用查询函数
def q(sql, params=()):
    return c.execute(sql, params).fetchall()

print("=== Hermes LLM 可观测性 ===\n")
total = q("SELECT COUNT(*) FROM llm_traces")[0][0]
print(f"总调用: {total}")

ok = q("SELECT COUNT(*) FROM llm_traces WHERE status='success'")[0][0]
err = q("SELECT COUNT(*) FROM llm_traces WHERE status='error'")[0][0]
print(f"成功率: {ok}/{total} ({ok/total*100:.1f}%)")

avg_lat = q("SELECT AVG(latency_ms) FROM llm_traces WHERE latency_ms > 0")[0][0]
print(f"平均延迟: {avg_lat:.0f}ms")

toks = q("SELECT SUM(prompt_tokens), SUM(completion_tokens) FROM llm_traces")
pt, ct = toks[0] or (0, 0)
print(f"总 token: 输入 {pt:,} / 输出 {ct:,}")

cost = q("SELECT SUM(cost_usd) FROM llm_traces")[0][0] or 0
print(f"估算成本: ${cost:.4f}")

print("\n--- Provider 分布 ---")
for row in q("SELECT provider, model, COUNT(*), AVG(latency_ms) FROM llm_traces GROUP BY provider, model ORDER BY COUNT(*) DESC"):
    print(f"  {row[0]} / {row[1]}: {row[2]}次, avg {row[3]:.0f}ms")

print("\n--- 近 7 天每日趋势 ---")
rows = q("""
    SELECT DATE(timestamp) as day, COUNT(*), 
           ROUND(SUM(cost_usd),4), ROUND(AVG(latency_ms),0)
    FROM llm_traces
    WHERE timestamp >= datetime('now','-7 days')
    GROUP BY day ORDER BY day
""")
for day, cnt, cost_d, lat in rows:
    print(f"  {day}: {cnt}次, ${cost_d}, {lat:.0f}ms avg")
EOF
```

## 集成到 Hermes 的方式

在 `~/.hermes/` 创建 `llm_traces.db` 后，以上命令可随时查询。
建议通过 cron 定期输出简报：
```bash
0 9 * * * python3 ~/.hermes/skills/hermes-observability/query.py --stats --days 1
```

## ⚠️ 当前状态：数据写入链路未接通

DB 已就绪（`~/.hermes/llm_traces.db`），但 Hermes 的 LLM 调用尚未接入。
skill 查出来的都是空数据是正常的——等待第一次 tracing 集成完成才有数据。

集成方式（待落地）：
1. 在 Hermes gateway 的 LLM provider 调用处加 hook，每次请求后写一条记录到 DB
2. 或通过 cron 定期从 Hermes 日志/DB 抽取 token 使用量写入
3. 集成完成前，数据来源：手动调用 `query.py --insert` 或从 provider API 对账单估算

## 告警阈值（超过以下值推送 Telegram）

- 单次请求延迟 > 30s → warn
- 错误率 > 20% → error
- 日成本 > $5 → info
