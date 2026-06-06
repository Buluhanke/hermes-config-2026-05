#!/bin/bash
# Chrome 9333 保活脚本 v1.0
#
# 用途: 确保只有一个 Chrome 进程跑在 9333 端口, 用 system Default profile (保留登录态)
#
# 根因 (2026-06-05 15:40 用户报"9 站登录态全丢" 根因诊断):
#   多次启动 Chrome 抢同一个 user-data-dir, 第二个 Chrome 的 SingletonLock
#   失败读不到现有 cookies, 同时 pkill -9 误杀了带登录态的 Chrome.
#
# 规则:
#   1. 永远只允许 1 个 Chrome 进程带 --remote-debugging-port=9333
#   2. 强制使用 system Default profile (跟用户日常 Chrome 一致, 登录态共享)
#   3. 启动参数白名单 (--no-first-run 等安全参数, 不加 -headless)
#   4. 检测到多个 Chrome 时, 杀端口不在 9333 的那个, 保留 9333 上的
#
# 调度: launchd plist ai.hermes.chrome-keepalive (每 5 分钟)
#
# 用法:
#   bash chrome_keepalive.sh           # 正常模式 (检测到问题就修)
#   bash chrome_keepalive.sh --dry-run # 只检查不修, 输出问题
#   bash chrome_keepalive.sh --force   # 强制重启 (先杀光再起)

set -uo pipefail
HERMES_HOME="${HOME:-/Users/aimac}/.hermes"
LOG="$HERMES_HOME/logs/chrome_keepalive.log"
DEBUG_PORT=9333
USER_DATA_DIR="$HOME/Library/Application Support/Google/Chrome/Default"
CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
mkdir -p "$HERMES_HOME/logs"

DRY_RUN=false
FORCE=false
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --force) FORCE=true ;;
    esac
done

log() {
    # ⚠️ launchd stdout 也会被 daemon 抓存档, 这里只写 LOG 不写 stdout 避免双打
    msg="$(date '+%Y-%m-%d %H:%M:%S') [chrome-keepalive] $1"
    echo "$msg" >> "$LOG"
}

# === 1. 找所有跑着 9333 端口的 Chrome PID ===
PORT_PIDS=($(lsof -nP -iTCP:$DEBUG_PORT -sTCP:LISTEN -t 2>/dev/null))

# === 2. 找所有启了 remote-debugging-port 的 Chrome 进程 ===
ALL_DEBUG_PIDS=($(pgrep -fl "Google Chrome.*--remote-debugging-port" 2>/dev/null | awk '{print $1}'))

log "📊 当前 Chrome 状态: 9333 LISTEN=${PORT_PIDS[*]:-无}, 全部 debug Chrome=${ALL_DEBUG_PIDS[*]:-无}"

# === 3. 判定哪些需要处理 ===
NEED_KILL=()
KEEP_PID=""

# 情况 A: 没有 9333 监听 → 必须启动
if [ ${#PORT_PIDS[@]} -eq 0 ]; then
    log "⚠️  9333 端口无监听"
    if [ "$DRY_RUN" == "true" ]; then
        log "  [DRY-RUN] 会启动 Chrome --user-data-dir=$USER_DATA_DIR"
    else
        log "  → 启动 Chrome (用 system Default profile 保留登录态)"
        "$CHROME_BIN" \
            --remote-debugging-port=$DEBUG_PORT \
            --remote-allow-origins=* \
            --user-data-dir="$USER_DATA_DIR" \
            --no-first-run --no-default-browser-check \
            > /tmp/chrome_9333.log 2>&1 &
        sleep 3
        NEW_PORT_PIDS=($(lsof -nP -iTCP:$DEBUG_PORT -sTCP:LISTEN -t 2>/dev/null))
        if [ ${#NEW_PORT_PIDS[@]} -gt 0 ]; then
            log "  ✅ Chrome 已起来 PID=${NEW_PORT_PIDS[0]}"
        else
            log "  ❌ Chrome 启动失败, 看 /tmp/chrome_9333.log"
        fi
    fi
    exit 0
fi

# 情况 B: 9333 上有监听
KEEP_PID="${PORT_PIDS[0]}"
log "✅ 9333 端口在 PID=$KEEP_PID 上"

# 情况 C: 还有别的 debug Chrome 在跑 (抢同一个 profile)
for pid in "${ALL_DEBUG_PIDS[@]}"; do
    if [ "$pid" != "$KEEP_PID" ]; then
        # 排除子进程 (renderer/gpu/network/utility)
        CMD=$(ps -p "$pid" -o command= 2>/dev/null)
        if echo "$CMD" | grep -qE "Helper|crashpad"; then
            continue
        fi
        NEED_KILL+=("$pid")
    fi
done

if [ ${#NEED_KILL[@]} -gt 0 ]; then
    log "⚠️  发现 ${#NEED_KILL[@]} 个多余的 debug Chrome: ${NEED_KILL[*]}"
    for pid in "${NEED_KILL[@]}"; do
        CMD=$(ps -p "$pid" -o args= 2>/dev/null | head -c 100)
        log "  PID=$pid ARGS=$CMD"
        if [ "$DRY_RUN" == "true" ]; then
            log "  [DRY-RUN] 会 kill $pid"
        else
            kill -TERM "$pid" 2>/dev/null
            sleep 1
            if ps -p "$pid" >/dev/null 2>&1; then
                kill -9 "$pid" 2>/dev/null
                log "  🔪 SIGKILL: $pid"
            else
                log "  ✅ SIGTERM: $pid"
            fi
        fi
    done
else
    log "✅ Chrome 状态正常, 单一进程占 9333"
fi

# === 4. --force 模式: 重启 Chrome (保留登录态) ===
if [ "$FORCE" == "true" ]; then
    log "🔄 --force 模式: 重启 Chrome"
    if [ -n "$KEEP_PID" ]; then
        if [ "$DRY_RUN" == "true" ]; then
            log "  [DRY-RUN] 会 kill $KEEP_PID 然后重启"
        else
            kill -TERM "$KEEP_PID" 2>/dev/null
            sleep 2
            kill -9 "$KEEP_PID" 2>/dev/null
            "$CHROME_BIN" \
                --remote-debugging-port=$DEBUG_PORT \
                --remote-allow-origins=* \
                --user-data-dir="$USER_DATA_DIR" \
                --no-first-run --no-default-browser-check \
                > /tmp/chrome_9333.log 2>&1 &
            sleep 3
            log "  ✅ Chrome 已重启"
        fi
    fi
fi

log "===== chrome-keepalive 完成 ====="
exit 0
