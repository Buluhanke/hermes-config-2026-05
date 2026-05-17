# Daemon 系统（2026-05-18 实现）

## 架构

```
gateway/run.py  每60s tick
    └── cron/daemon_scheduler.py  (tick_daemons)
            ├── DaemonState: STOPPED/RUNNING/STARTING/FAILED/HEARTBEAT_MISSING
            ├── DaemonTask (dataclass) → 持久化到 ~/.hermes/daemons/daemons.json
            └── _daemon_threads[daemon_id] = threading.Thread
                        │
                        └── tools/daemon_tool.py  (daemon() 工具，self-register)
```

## 文件清单

| 文件 | 作用 |
|------|------|
| `cron/daemon_scheduler.py` | 核心调度引擎，630行 |
| `tools/daemon_tool.py` | 暴露给 Agent 的 `daemon()` 工具，539行 |
| `gateway/run.py` | 已修改：line 16615 import + line 16632 tick 调用 |

## API

```python
daemon(action="create", name="1688价格监控", prompt="...", interval_seconds=300)
daemon(action="list")
daemon(action="start", daemon_id="abc123")
daemon(action="stop", daemon_id="abc123")
daemon(action="status", daemon_id="abc123")
daemon(action="heartbeat", daemon_id="abc123")  # daemon 内部调用，报告存活
daemon(action="remove", daemon_id="abc123")
```

## 状态机

```
STOPPED → STARTING → RUNNING
                    ↓
              (失败) FAILED / HEARTBEAT_MISSING
                    ↓
              (自动重启) → STARTING
```

## 与 cronjob 的区别

| | Cronjob | Daemon |
|---|---|---|
| 触发 | 定时 | 持续运行+间隔执行 |
| 状态 | 无状态 | 有状态（running/stopped） |
| 持久化 | ~/.hermes/crons/jobs.json | ~/.hermes/daemons/daemons.json |
| 心跳 | 无 | 有（heartbeat_timeout_seconds） |
| 自动重启 | 无 | 有（enabled=True 时） |

## 使用场景（1688采购）

```python
# 价格监控 daemon
daemon(action="create",
       name="纸箱价格监控",
       prompt="""每5分钟访问1688纸箱商品页，检查当前价格。
       如果价格低于上次记录超过5%，发送告警到QQ。
       记录每次检查结果到 ~/.hermes/daemons/price_log.json""",
       interval_seconds=300,
       heartbeat_timeout_seconds=600)

# 供应商消息轮询
daemon(action="create",
       name="供应商消息轮询",
       prompt="""每10分钟检查1688供应商是否有新消息。
       如果有新消息，提取内容并记录到日志。""",
       interval_seconds=600)
```

## 注意事项

- daemon 内部需定期调用 `daemon(action="heartbeat", daemon_id="...")` 报告存活
- 如果 daemon 进程卡死，gateway tick 会检测到 HEARTBEAT_MISSING 并尝试重启
- 不要在 daemon 内部做阻塞 IO，会导致心跳超时
- daemon 是线程级并发，不是进程级隔离
