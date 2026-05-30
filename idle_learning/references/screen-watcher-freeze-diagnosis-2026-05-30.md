# 昨夜系统冻结诊断报告（2026-05-30）

## 事件时间线

| 时间 | 事件 |
|------|------|
| 23:58 | screen_watcher 正常运行，每15秒检测 |
| 02:50 | 屏幕被锁定，screencapture 开始超时 |
| 02:50-03:10 | **297次 screencapture 失败**，handler 进程堆积 |
| 02:50 | "Handler仍在运行"跳过逻辑开始堆积触发 |
| 03:00+ | Lark 平台 ping_timeout (conn_id 轮换断开) |

## 根因

1. **smolvlm2 分析慢**（10-15秒/次），handler 处理期间新的 screen 变化持续进来
2. **屏幕锁定** → `screencapture -x` 超时5秒，失败后 watcher 继续重试
3. **"Handler仍在运行"跳过** 逻辑导致触发堆积，新的触发继续进入
4. **Ollama runner 内存**（~2.8GB/次）持续占用，未及时释放

## 关键日志证据

```
[2026-05-30 02:50:14] Screenshot failed: Command '['screencapture', '-x', ...']' timed out after 5 seconds
[2026-05-30 02:50:28] Screenshot failed: Command '['screencapture', '-x', ...']' timed out after 5 seconds
...
（共297次失败）
[2026-05-30 02:50:02] Handler仍在运行，跳过本次触发
[2026-05-30 02:50:39] Handler仍在运行，跳过本次触发
（连续堆积）
```

## 平台层日志（Lark ping_timeout）

```
[Lark] [2026-05-30 02:12:11,188] [ERROR] receive message loop exit, err: received 3003 (registered) ping_timeout
[Lark] [2026-05-30 03:08:12,523] [ERROR] receive message loop exit, err: received 3003 (registered) ping_timeout
[Lark] [2026-05-30 03:36:40,626] [ERROR] receive message loop exit, err: received 3003 (registered) ping_timeout
```
→ Lark 连接因超时主动断开，Gateway 无崩溃

## 恢复方式

手动 Ctrl+C 终止 screen_watcher 进程 + 重启 Hermes Gateway（今天早上7:34手动启动）

## 防护措施（已在 screen_watcher.py 实施）

1. **冷却时间**：handler 触发后 60s 内不再触发新 handler（`COOLDOWN_FILE` 机制）
2. **screencapture 超时**：5秒超时直接跳过，不重试
3. **Handler 仍在运行**：检测到 lock 文件存在则跳过本次触发

## 诊断命令

```bash
# 检查昨晚02-03点的screenshot失败次数
grep -c "Screenshot failed\|returned non-zero" ~/.hermes/logs/screen_watcher.log

# 检查handler进程是否堆积
ps aux | grep screen_trigger_handler | grep -v grep | wc -l

# 检查screen_watcher是否在跑
ps aux | grep screen_watcher | grep -v grep

# 检查Ollama runner内存
ps aux | grep "ollama runner" | awk '{print $2, $6/1024/1024 "MB"}'
```