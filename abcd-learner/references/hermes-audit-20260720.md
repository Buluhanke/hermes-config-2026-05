# Hermes 大排查清单 — 2026-07-20

## 排查入口

```bash
# 核心检查
hermes doctor
hermes config
hermes status
hermes tools list
hermes mcp list

# crontab（独立于 hermes cron list）
crontab -l

# 日志
tail -50 ~/.hermes/logs/gateway.log
tail -30 ~/.hermes/logs/self_evolution.log
tail -30 ~/.hermes/logs/idle_learning.log
tail -30 ~/.hermes/logs/active_learner.log
```

## 发现的13类问题

### 🔴 严重（当日修复）

| # | 问题 | 根因 | 修复 |
|---|------|------|------|
| 1 | **patrol 日志目录不存在** | cron 写 `logs/patrol/` 但目录从未创建 | `mkdir -p ~/.hermes/logs/patrol` |
| 2 | **能力画像写入失败** | heredoc 内嵌 Python JSON 解析失败，静默捕获不住 | 新建 `write_capability_fact.py` + 修改 `self_evolution_daily_learn.sh` |
| 3 | **AI 资讯写入失败** | stdout 去 markdown 后 `## 1.` → `1.`，正则不匹配 | 修正则 `(?:^###\s+\|^ {0,3})\d+\.` |
| 4 | **active_learner 搜索全挂** | `["python3", ...]` 走系统 python，anysearch 依赖 venv 包 | 改用 HERMES_PY 绝对路径 |
| 5 | **response_store.db 空表** | 无代码引用，20KB 浪费 | `rm ~/.hermes/response_store.db` |

### 🟡 中等（已定位，待修）

| # | 问题 | 根因 | 状态 |
|---|------|------|------|
| 6 | **llm_traces 零记录** | observability skill 是空壳，llm_trace.py 从未建立 | skill 无 query.py，写入链路无代码 |
| 7 | **Telegram 间歇断连** | HTTP 连接池耗尽 (`Pool timeout: All connections occupied`) | 当前能自恢复，30min 持续断连再调大 pool |
| 8 | **NVIDIA NIM SSL 错误** | `SSL: UNEXPECTED_EOF_WHILE_READING` 协议违规 | fallback 有 cerebras 备选，不影响主流程 |
| 9 | **Gemini HTTP 400** | doctor 检测未影响实际使用 | 主模型是 MiniMax |
| 10 | **skills snapshot 孤儿引用** | `.archive` 恢复后未刷新 snapshot | snapshot 存在但孤儿引用已清零 |
| 11 | **hermes cron list 显示 0** | cron 工具不扫系统 crontab | crontab 有 7 条，但工具显示 0 |

### 🟢 轻微（已处理）

| # | 问题 | 处理 |
|---|------|------|
| 12 | fact_store schema 列名不匹配 | 修复后 `fact_id INTEGER PRIMARY KEY` 对齐 |
| 13 | 176 facts 持续在库 | 正常增长，能力画像+AI资讯已成功写入 |

## 验证命令

```bash
# fact_store 健康
sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) FROM facts;"

# 最新 learning/capability facts
sqlite3 ~/.hermes/memory_store.db \
  "SELECT fact_id, category, substr(content,1,60) FROM facts \
   WHERE category IN ('learning','capability') ORDER BY fact_id DESC LIMIT 5;"

# 日志最后一行
tail -3 ~/.hermes/logs/self_evolution.log
tail -3 ~/.hermes/logs/active_learner.log

# 目录存在
ls ~/.hermes/logs/patrol/
ls ~/.hermes/response_store.db  # 应返回 No such file
```
