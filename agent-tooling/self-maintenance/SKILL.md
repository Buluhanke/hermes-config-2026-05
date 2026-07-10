---
name: self-maintenance
description: Hermes 自我监控 + 自我修复 + 主动巡逻。Gateway 保活、内存守护、每日健康检查、失败自愈。
triggers:
  - gateway 重启后恢复任务
  - 服务挂了需要自动修复
  - 每日定时巡逻
  - 内存不足需要清理
  - 主动发现并解决问题
pitfalls:
  - gateway 停了不知道 — 必须有 cron 定时检查
  - 只检查不修复 — 检查出来问题必须自动处理
  - 任务中断后不恢复 — gateway 重启后第一件事是恢复 pending_tasks
---

# Self-Maintenance — Hermes 自我维护

## 核心原则

Gateway 是 Hermes 的命根子。Gateway 停了 = 所有能力归零。必须 24/7 有人盯着。

## 每日巡逻 SOP（bash ~/.hermes/scripts/daily_patrol.sh）

每次巡逻必须检查：
1. Gateway 进程（`pgrep -f hermes-gateway`）— 停了则 restart
2. Chrome CDP 端口（`curl localhost:9222/json/version`）— 必须返回 Browser 版本
3. OmniRoute API（`curl localhost:20128/api/monitoring/health`）— 500 是正常的（缺 key），connection refused 才要管
4. 内存使用（`vm_stat`）— Pages free 低于 2 万要清理
5. 磁盘使用（`df -h /`）— 低于 5GB 要告警

巡逻结果写入 `~/.hermes/logs/patrol/YYYYMMDD.txt`，有异常推送 Telegram Home channel。

## Gateway 保活

关键进程名：`hermes-gateway`、`hermes_cli.main gateway run`

检查：
```bash
pgrep -f "hermes-gateway" || pgrep -f "hermes_cli.main gateway run"
```

重启：
```bash
bash ~/.hermes/scripts/restart_gateway.sh
```

重启后第一件事：读取 `pending_tasks.json`，恢复未完成的任务。

## 内存守护

Mac Mini 24GB 红线：内存使用 > 75% 必须卸载 LLaVA 等重量级进程。

已落地 cron：*/5 * * * * `memory_watchdog.py`

## 失败自愈优先级

1. Gateway 挂了 → restart_gateway.sh
2. Chrome CDP 挂了 → pkill Chrome 重启
3. OmniRoute 挂了 → omniroute serve 重启
4. 内存红了 → 卸载 LLaVA / 清理缓存
5. 磁盘红了 → 清理 hermes logs / npm cache

## 相关脚本

- `~/.hermes/scripts/restart_gateway.sh` — Gateway 重启
- `~/.hermes/scripts/daily_patrol.sh` — 每日巡逻（含所有健康检查）
- `~/.hermes/scripts/memory_watchdog.py` — 内存守护
- `~/.hermes/scripts/pending_tasks.py` — 任务持久化

## Cron 任务

建议每日 09:00 跑一次 daily_patrol.sh，输出到 `~/.hermes/logs/patrol/`。
