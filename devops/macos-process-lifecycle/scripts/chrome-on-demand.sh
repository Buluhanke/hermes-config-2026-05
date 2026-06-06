#!/bin/bash
# chrome-on-demand.sh — Chrome debug 按需启停
# 用法: bash chrome-on-demand.sh {start|stop|status}
# 
# 原理：
#   - start: 检测端口 9333，无监听则启动 Chrome（独立 user-data-dir，cookies 不丢）
#   - stop:  kill Chrome 进程（优雅 SIGTERM → 3s → SIGKILL）
#   - status: running:PID 或 stopped

PORT=${PORT:-9333}
CHROME_APP="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_ARGS=(
    "--user-data-dir=/Users/aimac/.hermes/chrome-debug"
    "--remote-debugging-port=$PORT"
    "--load-extension=/Users/aimac/.hermes/mcp-chrome-extension"
    "--no-first-run"
    "--no-default-browser-check"
    "--no-startup-window"
)

find_pid() {
    lsof -i :$PORT -t 2>/dev/null | head -1 || true
}

do_start() {
    existing=$(find_pid)
    if [ -n "$existing" ]; then
        echo "Chrome debug 已运行 PID=$existing"
        echo "$existing" > /tmp/hermes-chrome-cdp.pid
        return 0
    fi
    echo "启动 Chrome debug..."
    "$CHROME_APP" "${CHROME_ARGS[@]}" &> /dev/null &
    sleep 3
    pid=$(find_pid)
    if [ -n "$pid" ]; then
        echo "Chrome debug 启动成功 PID=$pid"
        echo "$pid" > /tmp/hermes-chrome-cdp.pid
        return 0
    else
        echo "Chrome debug 启动失败（端口仍无监听）"
        return 1
    fi
}

do_stop() {
    pid=$(find_pid)
    if [ -n "$pid" ]; then
        echo "关闭 Chrome PID=$pid"
        kill -TERM $pid 2>/dev/null || true
        sleep 3
        kill -0 $pid 2>/dev/null && kill -9 $pid 2>/dev/null || true
        rm -f /tmp/hermes-chrome-cdp.pid
        echo "Chrome debug 已关闭"
    else
        echo "Chrome debug 未运行"
    fi
}

do_status() {
    pid=$(find_pid)
    if [ -n "$pid" ]; then
        echo "running:$pid"
    else
        echo "stopped"
    fi
}

case "${1:-status}" in
    start) do_start ;;
    stop)  do_stop ;;
    status) do_status ;;
    *)     echo "用法: $0 {start|stop|status}" ;;
esac