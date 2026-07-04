# macOS GUI app launch from launchd — 根因诊断档案

## 案例 1: chrome-keepalive 循环开关 (2026-06-28 14:08)

**现象**: 重启开机后, `ai.hermes.chrome-keepalive` 每 30 秒拉一次 Chrome, 启动 8 秒后被杀, 30 秒后再起。PID 一直换: 4101 → 4220 → 4388 → 4533 → 4671 → 4822 → 4973 → 5103...

**stderr 证据** (`/tmp/chrome_9222.log`):
```
DevTools listening on ws://127.0.0.1:9222/devtools/browser/...
Created TensorFlow Lite XNNPACK delegate for CPU.
Trying to load the allocator multiple times. This is *not* supported.
[ERROR:registration_request.cc:291] Registration response error message: DEPRECATED_ENDPOINT
[ERROR:connection_factory_impl.cc:484] ConnectionHandler failed with net error: -2
[ERROR:gpu_process_host.cc:1005] GPU process exited unexpectedly: exit_code=15
[ERROR:network_service_instance_impl.cc:722] Network service crashed or was terminated, restarting service.
```

**OS log 证据** (`log show --predicate 'process == "Google Chrome"' --last 5m`):
```
Df Google Chrome[4822:...] [AppKit:AutomaticTermination] _NSDisableAutomaticTerminationAndLog "No windows open yet"
Df Google Chrome[4822:...] [AppKit:AutomaticTermination] _NSEnableAutomaticTerminationAndLog "No windows open yet"
Df Google Chrome[4822:...] [AppKit:AutomaticTermination] _NSDisableAutomaticTerminationAndLog "Restoring windows"
Df Google Chrome[4822:...] [AppKit:AutomaticTermination] _NSEnableAutomaticTerminationAndLog "Restoring windows"
Df Google Chrome[4822:...] [CoreAnalytics:client] Entering exit handler.
Df Google Chrome[4822:...] [CoreAnalytics:client] Queueing exit procedure onto XPC queue.
```

时间线 (PID 4822):
- 12:06:05 启用 AutomaticTermination ("No windows open yet")
- 12:11:05 `_updateToReflectAutomaticTerminationState ... _kLSApplicationWouldBeTerminatedByTALKey=0`
- 12:13:46 (约 7 秒后) CoreAnalytics Entering exit handler → 进程退出

**keepalive log bug 顺手发现** (`chrome_keepalive.sh` log 函数):
```bash
log() {
    msg="$(date '+%Y-%m-%d %H:%M:%S') [chrome-keepalive] $1"
    echo "$msg" >> "$LOG"
    [[ "$DRY_RUN" == "true" ]] && echo "$msg" || echo "$msg"  # ← 永远走 echo, 每行写两遍
}
```
诊断被噪音糊了一层 (每行 log 重复), 干扰阅读。已修: 删掉第二个 echo。

## 修复方案

**Before** (`chrome_keepalive.sh`):
```bash
"$CHROME_BIN" \
    --remote-debugging-port=$DEBUG_PORT \
    --remote-allow-origins=* \
    --user-data-dir="$USER_DATA_DIR" \
    --no-first-run --no-default-browser-check \
    "about:blank" \
    > /tmp/chrome_${DEBUG_PORT}.log 2>&1 &
sleep 8
```

**After**:
```bash
/usr/bin/open -na "$CHROME_BIN" --args \
    --remote-debugging-port=$DEBUG_PORT \
    --remote-allow-origins=* \
    --user-data-dir="$USER_DATA_DIR" \
    --no-first-run --no-default-browser-check \
    "about:blank" \
    > /tmp/chrome_${DEBUG_PORT}.log 2>&1
sleep 8
```

## 验证

```bash
# 1. 手动触发一次
bash ~/.hermes/scripts/chrome_keepalive.sh --force

# 2. 35 秒后再看
sleep 35 && lsof -nP -iTCP:9222 -sTCP:LISTEN -t  # PID 应保持不变

# 3. 看 keepalive log
tail -6 ~/.hermes/logs/chrome_keepalive.log  # 应显示 "状态正常, 单一进程占 9222"
```

实测 PID 5466 启动 35s 后仍在, keepalive 走"状态正常"路径, 不再起新进程。

## 关键 takeaway

- launchd 没 WindowServer 连接, 直接 exec GUI app → AppKit 觉得 "No windows open" → 30s 后 SIGTERM
- `open -na <app> --args ...` 走 LaunchServices, 标准 AppKit 生命周期, 拿 NSApp 完整生命周期
- `about:blank` 传不传不重要, 关键是 LaunchServices 路径
- 诊断 4 步: stderr exit_code=15 → log show AutomaticTermination → log show Entering exit handler → 改 open -na