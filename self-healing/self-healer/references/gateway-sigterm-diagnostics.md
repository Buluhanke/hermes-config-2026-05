# Gateway SIGTERM 诊断手册

## 两种SIGTERM的本质区别

**`--replace` 接管型（正常）**
```
Received SIGTERM as a planned --replace takeover — exiting cleanly
Shutdown context: signal=SIGTERM under_systemd=no parent_pid=28198
```
这是 gateway 自己的行为——用 `--replace` 启动新进程时，新进程发 SIGTERM 给旧进程，让它优雅退出。**无害。**

**外部强杀型（问题）**
```
Received SIGTERM — initiating shutdown
Shutdown context: signal=SIGTERM under_systemd=yes parent_pid=1
```
parent_pid=1 表示进程被 init/systemd 接管后杀死。**这是真正的异常**，意味着 macOS 系统在回收 gateway 进程。

## 诊断工具：gateway-exit-diag.log（结构化出口日志）

路径：`~/.hermes/logs/gateway-exit-diag.log`

每条记录是JSON，包含：`tag`（gateway.start/exit_clean/exit_nonzero）、`pid`、`success`、`replace`字段。

**诊断restart storm的标准步骤**：
```bash
# 1. 找所有非replace启动（自发启动，非--replace接管）
grep '"tag": "gateway.start"' ~/.hermes/logs/gateway-exit-diag.log | grep '"replace": false'

# 2. 找紧跟的退出条目（自发退出）
grep '"tag": "gateway.start"' gateway-exit-diag.log | python3 -c "
import sys, json
for line in sys.stdin:
    d = json.loads(line)
    print(d['pid'], d.get('replace'), d.get('success'))
"

# 3. 时间间隔分析（正常实例运行>10分钟，restart storm每1-2分钟就退）
grep '"tag": "gateway.start"' gateway-exit-diag.log | \
  python3 -c "
import sys, json
from datetime import datetime
entries = [json.loads(l) for l in sys.stdin]
for i in range(1, len(entries)):
    prev_ts = datetime.fromisoformat(entries[i-1]['ts'])
    curr_ts = datetime.fromisoformat(entries[i]['ts'])
    gap = (curr_ts - prev_ts).total_seconds()
    if gap < 300 and entries[i]['replace'] == False:
        print(f'PID {entries[i][\"pid\"]}: {gap:.0f}s间隔（异常短）')
"

# 4. 确认MCP失败是原因
grep "MCP server.*failed" ~/.hermes/logs/gateway.error.log | tail -10
```

**restart storm的诊断特征**：
- `gateway-exit-diag.log` 中 `success: false` + `replace: false` 条目密集
- 时间间隔 60-180秒（说明一启动就崩）
- `gateway.error.log` 中有 MCP 连接失败记录

## launchd KeepAlive + MCP失败 = 重启风暴（2026-06-01新发现）

**机制**：
1. Gateway启动 → MCP服务器（n8n/searxng）连接失败
2. MCP重试3次，每次失败产生异步TaskGroup错误
3. 错误累积 → Gateway内部崩溃或退出码非0
4. **launchd的 `KeepAlive=true`** 检测到进程退出 → 立即重启
5. 新进程又MCP失败 → 又崩溃 → 又重启 → **循环**

**诊断特征**：
- `gateway-exit-diag.log` 中大量 `success: false` 的 `gateway.exit_nonzero` 条目
- 时间间隔规律（每1-2分钟一次）
- `replace: false` 说明不是 `--replace` 替换，是自发退出

## 快速诊断命令

```bash
# 统计今日外部SIGTERM次数（判断是否异常）
grep "initiating shutdown" ~/.hermes/logs/gateway.log | grep "$(date '+%b %d')" | wc -l

# 历史对比（正常情况每天<1次）
grep "initiating shutdown" ~/.hermes/logs/gateway.log | grep -vE "May|Jun" | wc -l   # 早期累计
grep "initiating shutdown" ~/.hermes/logs/gateway.log | grep "May 30|May 31" | wc -l  # 前两天

# 找最近一次外部强杀
grep -B1 "initiating shutdown" ~/.hermes/logs/gateway.log | grep -v "planned" | tail -5

# 查看gateway当前运行时长（判断是否刚重启）
ps -o etime= -p $(pgrep -f "hermes_cli.main gateway" | head -1)
```

## macOS 随机SIGTERM的已知应对方案

1. **15分钟自检脚本兜底**（`~/.hermes/scripts/hermes_self_check.sh`）—挂了自动拉起
2. **nohup包装层**—给gateway套shell父进程，降低被系统回收概率
3. **launchd托管**—做成macOS服务，比nohup更稳（需要写plist，复杂但最正规）

## 相关修复记录（2026-06-01）

- searxng MCP：`uvx mcp-server-searxng` → `npx -y searxng-mcp`
- n8n MCP路径：`/tmp/hermes-n8n-mcp/server.py` → `~/.hermes/n8n-mcp/server.py`
- 这两个错误配置导致MCP连接重试3次/次，异步任务堆积，是gateway前期不稳定的帮凶

## 异常阈值参考

| 频率 | 状态 | 建议 |
|------|------|------|
| <1次/天 | 正常 | 无需处理 |
| 1-3次/天 | 轻微异常 | 观察+自检脚本兜底 |
| >3次/天（集中在短窗口） | 严重异常 | 加固方案：launchd保活 |
