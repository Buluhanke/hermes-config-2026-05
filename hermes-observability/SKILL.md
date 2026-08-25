---
name: hermes-observability
description: "LLM可观测 SQLite traces token延迟错误率成本。Use when 分析token消耗调用延迟错误率"
triggers:
  - token/消耗/用量/token消耗/成本统计
  - LLM可观测性/observability/tracing
  - latency/延迟/响应时间
  - 错误率/error rate
  - provider分布/model分布
  - cost/账单/估算费用
pitfalls:
  - 查询结果为空不代表写入失败——Gateway 重启后新代码才生效，且是异步写入
  - DB文件存在但表为空是正常状态（Gateway 重启前旧代码未写入）
  - npm/全局 node 包安装反复超时（网络原因）—— OmniRoute 等 npm 包安装时遇到 180s 超时是常态，换镜像或预编译 binary 解决
  - npm 安装不完整（缺 node_modules）导致 omniroute 无法启动——症状是 `Error: Cannot find package 'commander'` 等 ESM import 错误，需重新完整安装
  - npm 安装可通过 `npm config set registry https://registry.npmmirror.com` 换国内镜像加速
---

# Hermes LLM 可观测性

## 核心文件

- **写入模块**：`~/.hermes/hermes-agent/agent/llm_trace.py`（threading fire-and-forget，不阻塞主循环）
- **查询脚本**：`~/.hermes/skills/hermes-observability/query.py`
- **DB**：`~/.hermes/llm_traces.db`

## 数据库表结构

```sql
llm_traces (
  id, trace_id, span_id, parent_span_id,
  provider, model,
  prompt_tokens, completion_tokens, total_tokens,
  latency_ms, status, error, cost_usd,
  timestamp, duration_ms,
  cache_read_tokens, cache_write_tokens, reasoning_tokens
)
```

## 查询命令

```bash
# 近30天统计（总调用/tokens/成本/延迟/错误率）
python3 ~/.hermes/skills/hermes-observability/query.py --stats --days 30

# 每日趋势
python3 ~/.hermes/skills/hermes-observability/query.py --daily --days 7

# 按 Provider 分布
python3 ~/.hermes/skills/hermes-observability/query.py --providers

# 错误记录
python3 ~/.hermes/skills/hermes-observability/query.py --errors --days 7

# 指定日期
python3 ~/.hermes/skills/hermes-observability/query.py --date 2026-07-08
```

## 写入链路

`conversation_loop.py` 在以下位置调用 `llm_trace.write_trace()`：
- **成功路径**（line ~2135）：API call 完成后写入 status=success
- **错误路径**（line ~2977）：API 异常时写入 status=error

写入是 threading fire-and-forget，失败不阻断主循环。

## 定价表（USD per million tokens）

内置于 `llm_trace.py` 的 `_PRICING` 字典，覆盖：
`anthropic/*`, `openai/*`, `google/*`, `deepseek/*`, `zhipu/*`, `minimax/*`, `custom:zai`

未知模型使用默认费率 `(1.5 input, 7.0 output)`。

## 状态检查

```bash
sqlite3 ~/.hermes/llm_traces.db "SELECT COUNT(*) FROM llm_traces;"
```

## 使用方式
使用方式：
