# cua-driver 空转模式 — 2026-06-04 实战案例

## 现象

`/Applications/CuaDriver.app/Contents/MacOS/cua-driver serve` 常驻后台，**平时空转 45% CPU / 53MB RAM**。
直觉上想 kill 省资源，但**它不能杀**：
- 杀完 `mcp_cua_driver_*` 工具族（`mcp_cua_driver_click` / `get_window_state` / `zoom` 等）全失效
- 重新拉起要等 launchd bootstrap + 5-10 秒初始化
- **正在跑的 computer_use 任务会卡住**

## 真相：99% 时间在 `_pthread_wqthread` 等任务

`sample <pid> 2 1` 出来的调用栈：

```
1457 Thread_8878556   DispatchQueue_1: com.apple.main-thread  (serial)
    1457 NSApplication run → _DPSBlockUntilNextEventMatchingListInMode
    → 100% 在 nextEventMatchingMask:untilDate:inMode:dequeue 阻塞等待事件

   13 _pthread_start → cua-serve (实际业务逻辑)
   12 tokio-rt-worker × N (多 worker 池, 平时都 idle)
```

**主线程**：100% 在 `-nextEventMatchingMask:untilDate:inMode:dequeue` —— AppKit 标准事件循环，**这是 macOS GUI 应用的正常 idle 行为**。
**tokio worker**：12+ 个线程池，平时全在 `parking_lot::condvar` 等唤醒。
**实际业务代码**：13 个采样点（< 1%），即服务在"空转"。

## 关键判断

| 模式 | CPU 占用 | 能不能杀 | 原因 |
|---|---|---|---|
| 99% `_pthread_wqthread` / 阻塞等 | 30-50% 单核 | ❌ 不能杀 | tokio/AppKit 标准 idle，不是 bug |
| 99% 实际业务代码（NSWindow update / VLM 推理 / sample loop） | 30-50% 单核 | ⚠️ 考虑杀 | 真有任务在跑，先停任务再杀 |
| 99% 系统调用（`__workq_kernreturn`） | 0-5% | ✅ 可杀 | 真的在等系统，无外部依赖 |

**判断姿势**：`sample <pid> 2 1 | grep -E "main-thread|thread_start" | head`，看主线程/子线程分别在干啥。

## 实用解法

### 1. 不杀，但降低 CPU 占用

cua-driver 是 Rust 写的，没有调优参数能让它"真闲着"。**接受 45% CPU 作为基础设施税**。如果内存压力真的到了 80% 红线，**用 mcp tool 跑完后立即停手**（不杀进程，只是别用）。

### 2. 30 分钟空闲回收（用户拍板，2026-06-04 落地）

**不能简单按 CPU 时间判断**——cua-driver 99% 时间 CPU 时间在涨（workqueue 内核记账），即使真的没在跑 Hermes 任务，etime + cputime 也会继续增加。

**正确姿势**：**按"是否被 Hermes 工具调用过"判断**——需要在每个 `mcp_cua_driver_*` 调用前后写时间戳到 `~/.hermes/state/cua-driver-last-use.json`，cron watchdog 读这个判断。

当前实现（job `2f527c06f06d`）的简化版：用 `ps cputime` delta 30 分钟 = 0 才杀，但**这个判断对 cua-driver 是错的**（它 cputime 永远在涨）。**需要修正**。

### 3. 杀前必停任务

```bash
# 1. 看 mcp_cua_driver_* 是否正在被用
hermes ps | grep cua  # 假设有这种工具, 或查 gateway.log

# 2. 查 last use timestamp
cat ~/.hermes/state/cua-driver-last-use.json 2>/dev/null

# 3. 杀
launchctl bootout gui/$(id -u)/com.trycua.driver
```

### 4. 重启（on-demand）

```bash
launchctl bootstrap gui/$(id -u) /Library/LaunchDaemons/com.trycua.driver.plist
# 或
open -a CuaDriver
```

启动后**等 5-10 秒**再调用 `mcp_cua_driver_*`，否则会拿到 "driver not ready"。

## 总结教训

> **进程 CPU 高 ≠ 进程在干活**。要 `sample` 看 call graph 才知道。

同样的判断适用于：
- `WindowServer`（桌面合成，20% CPU 正常）
- `loginwindow`（GUI 事件循环）
- 任何 Electron 应用的 main 进程
- 任何 tokio / actix / async-std 的 Rust 进程

**只要进程在 idle 模式（阻塞在 event loop / condvar）就不算浪费资源，强行杀它反而要付出 on-demand 冷启动的代价。**
