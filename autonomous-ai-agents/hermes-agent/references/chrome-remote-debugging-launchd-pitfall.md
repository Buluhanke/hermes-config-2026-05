# Chrome Remote Debugging + launchd Pitfall

**日期：** 2026-05-09  
**环境：** macOS，Chrome for Hermes.app（复制副本），hermes-agent 通过 launchd 托管 gateway

## 问题现象

用 launchd plist 启动 Chrome for Hermes（`--remote-debugging-port=9222`）后：
- `lsof -i :9222` 显示端口正常监听
- `ps aux | grep Chrome` 显示进程存在
- 但所有 CDP 发现方法均失败（`ws://127.0.0.1:9222/...` 返回 Connection refused）
- browser 工具无法连接

## 根因

launchd 启动的进程运行在 **系统级的 session 0**（launchd 自身的会话），没有 GUI 图形会话（WindowServer）。

Chrome 检测到没有可用图形会话后：
- 进程启动，但不创建 CDP 监听 socket（或创建后立即关闭）
- 导致外部 CDP 客户端无法 WebSocket 连接到调试端口

用户自己手动双击启动的 Chrome 运行在 **用户登录会话**（GUI session），CDP 正常工作。

## 错误排查记录

```
# 端口在监听
lsof -i :9222
→ Chrome for Hermes  PID 7691  LISTEN

# 但 CDP WebSocket 连接失败
curl http://127.0.0.1:9222/json
→ curl: (7) Failed to connect to 127.0.0.1 port 9222 after 0ms: Connection refused

# Chrome 日志
# [0511/134657.123456:ERROR:browser_main.cc(1369)] No window available. Cannot create CDP listener.
```

## 正确做法

**方案A：.command 脚本（推荐）**

1. 复制 Chrome 为独立副本：
   ```bash
   cp -R "/Applications/Google Chrome.app" "/Applications/Chrome for Hermes.app"
   ```

2. 创建启动脚本 `~/.hermes/scripts/chrome-hermes.command`：
   ```bash
   #!/bin/bash
   "/Applications/Chrome for Hermes.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 "$@"
   ```

3. 赋予执行权限：
   ```bash
   chmod +x ~/.hermes/scripts/chrome-hermes.command
   ```

4. 用户需要 CDP 时手动双击该 .command 文件

**方案B：open 命令启动**

```bash
open -a "Chrome for Hermes" --args --remote-debugging-port=9222
```

## 结论

launchd 适合启动无 GUI 依赖的服务（gateway、dashboard），不适合启动需要图形会话的 GUI 应用。

如果需要 Chrome CDP 调试，必须通过用户桌面会话启动，不能用 launchd 托管。
