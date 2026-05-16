# TUI Gateway slash_worker 进程泄漏

## 症状

Dashboard (`http://localhost:5173/chat`) 启动/响应极慢，`ps aux` 显示大量残留的 `tui_gateway.slash_worker` 进程：

```
ps aux | grep slash_worker | grep -v grep | wc -l
# → 20+ （正常应该 ≤ 1）
```

## 根因分析

### 1. `_sessions` 字典无上限

`hermes_agent/tui_gateway/server.py` 第 118 行：

```python
_sessions: dict[str, dict] = {}
```

这是一个内存字典，每次开新对话/会话都会往里加一条记录，**只增不减**。没有任何 LRU、eviction 或 max size 限制。

### 2. `atexit` 只处理正常退出

```python
# server.py 第 332 行
atexit.register(_shutdown_sessions)
```

`_shutdown_sessions()` 会关闭每个 session 的 slash_worker，但 `atexit` **只在 Python 进程正常退出时触发**。当：
- Dashboard 页面刷新
- 浏览器崩溃
- `kill -9` 强制杀进程
- 断电/系统休眠

……TUI gateway 进程直接死掉，`atexit` 根本不会执行，残留的 slash_worker 子进程变成孤儿（orphan）挂在系统里。

### 3. slash_worker 生命周期

每次 Dashboard 新会话，`tui_gateway/server.py` 的 `_SlashWorker.__init__` 启动一个子进程：

```python
self.proc = subprocess.Popen([
    sys.executable, "-m", "tui_gateway.slash_worker",
    "--session-key", session_key,
])
```

父进程（TUI gateway）退出后，子进程 `slash_worker` 失去父进程，但由于它本身是独立 Python 进程（不是线程），不会随父进程一起终止，变成 **僵尸进程（zombie）/孤儿进程（orphan）**。

### 4. 每个 worker 初始化成本高

每次新的 slash_worker 启动都要：
1. 加载 `.env` 环境变量
2. 初始化所有插件（plugin discovery，扫描 `~/.hermes/plugins/`）
3. 连接 MCP servers（gbrain、browser_use）
4. 探测模型 metadata

这些重复初始化开销很大，多个残留进程同时耗 CPU/内存会显著拖慢 Dashboard。

## 诊断命令

```bash
# 看有多少残留进程
ps aux | grep slash_worker | grep -v grep | wc -l

# 看进程详情（session key + 启动时间）
ps aux | grep slash_worker | grep -v grep

# 看内存/CPU占用
ps aux | grep slash_worker | grep -v grep | awk '{print $2, $6/1024 "MB", $9, $11, $12, $13}'
```

## 临时清理

```bash
pkill -f "tui_gateway.slash_worker"
# 或精确清理（保留当前会话的 worker）
ps aux | grep slash_worker | grep -v grep | grep -v "session-key $(tmux display-message -p '#S' 2>/dev/null)" | awk '{print $2}' | xargs kill -9
```

正常情况下 `/new` 后旧 worker 应该被 `worker.close()` 回收，如果反复出现泄漏说明 drain 机制有另一个问题（见下）。

## 相关问题：drain 失效（另一个slash_worker泄漏原因）

除了 `_sessions` 字典泄漏外，还有另一个已知 drain 机制失效的问题：

- **症状**：`/new` 后旧会话的 agent 任务（找品、浏览器等）仍在后台运行
- **根因**：`restart_drain_timeout: 60` 对某些任务类型（涉及独立子进程、浏览器自动化的）没有正确接入 drain 链路
- **诊断**：`ps aux | grep slash_worker`，如果 `/new` 后 60s 仍未减少
- **清理**：`pkill -f "tui_gateway.slash_worker"`

这是 upstream bug，临时方案是手动 kill。

## 长期解决方案（upstream fix）

需要在 `tui_gateway/server.py` 中实现：

1. `_sessions` 字典加 max size 限制（如最多 10 个 session），超出时 eviction 最老的
2. 或者在 session 结束时（而非进程退出时）主动清理对应的 slash_worker
3. 考虑用 `weakref` 或显式 `worker.close()` 替代 `atexit` 依赖

**注意**：这个 upstream fix 需要修改 Hermes Agent 源码，临时方案是监控 + 手动清理。
