#!/bin/bash
# chrome-watchdog.sh — Chrome CDP 空闲自动关闭 watchdog
# 用法：bash chrome-watchdog.sh（后台运行）
# 退出条件：无CDP客户端连接时等待IDLE_MIN分钟后关闭Chrome并退出

PORT=${PORT:-9333}
IDLE_MIN=${IDLE_MIN:-30}
LOG=${LOG:-/tmp/hermes-chrome-watchdog.log}

log() { echo "[$(date '+%H:%M:%S')] $1" >> "$LOG"; }

find_pid() {
    lsof -i :$PORT -t 2>/dev/null | head -1 || true
}

has_clients() {
    # Chrome自己占1个listening，established>1说明有外部客户端
    local n
    n=$(lsof -i :$PORT -s TCP:ESTABLISHED 2>/dev/null | wc -l | tr -d ' ')
    [ "$n" -gt 1 ]
}

stop_chrome() {
    local pid
    pid=$(find_pid)
    [ -z "$pid" ] && return 0
    log "关闭 Chrome PID=$pid"
    kill -TERM $pid 2>/dev/null || true
    sleep 3
    kill -0 $pid 2>/dev/null && kill -9 $pid 2>/dev/null || true
    log "Chrome 已关闭"
}

while true; do
    sleep 60
    pid=$(find_pid)
    if [ -z "$pid" ]; then
        log "Chrome 未运行，退出 watchdog"
        exit 0
    fi
    if has_clients; then
        log "CDP 客户端活跃，PID=$pid"
    else
        log "无 CDP 客户端，空闲 ${IDLE_MIN} 分钟，关闭 Chrome PID=$pid"
        stop_chrome
        exit 0
    fi
done