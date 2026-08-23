#!/usr/bin/env bash
# CDP lifecycle helper — start / stop / status for the local Chrome CDP service
# on macOS, wired through the launchd plist at
#   ~/Library/LaunchAgents/com.hermes.chrome-cdp.plist
#
# Defaults assume the skill's recommended plist (label com.hermes.chrome-cdp,
# KeepAlive=false — see chrome-cdp-control SKILL.md "Pitfall: KeepAlive=true
# makes Chrome unstoppable" for why).
#
# Usage:
#   cdp_lifecycle.sh status   — show current state (plist / launchd / port / pages)
#   cdp_lifecycle.sh start    — bootstrap the launchd service (Chrome comes up)
#   cdp_lifecycle.sh stop     — bootout the launchd service (Chrome dies, plist stays)
#   cdp_lifecycle.sh restart  — stop then start
#   cdp_lifecycle.sh on-boot  — set KeepAlive=true (always running, harder to quit)
#   cdp_lifecycle.sh on-demand — set KeepAlive=false (default; start manually)
#
# All commands are idempotent. "start" when already running is a no-op success.
# "stop" when already stopped is a no-op success.

set -euo pipefail

LABEL="com.hermes.chrome-cdp"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
PORT=9222
UID_NUM=$(id -u)

ensure_plist() {
    if [[ ! -f "$PLIST" ]]; then
        echo "  ❌ plist not found: $PLIST"
        echo "     Install the template: cp $(dirname "$0")/../templates/com.hermes.chrome-cdp.plist $PLIST"
        exit 1
    fi
}

plist_loaded() {
    launchctl list 2>/dev/null | grep -q "$LABEL"
}

chrome_running() {
    pgrep -fl "Google Chrome.*remote-debugging-port=${PORT}" >/dev/null 2>&1
}

port_responsive() {
    curl -s -o /dev/null -m 2 "http://127.0.0.1:${PORT}/json/version" 2>/dev/null
}

cmd_status() {
    echo "=== CDP state ==="
    echo "  plist:    $PLIST $([[ -f $PLIST ]] && echo '(present)' || echo '(MISSING)')"
    if [[ -f $PLIST ]]; then
        ka=$(/usr/libexec/PlistBuddy -c 'Print :KeepAlive' "$PLIST" 2>/dev/null || echo "?")
        ral=$(/usr/libexec/PlistBuddy -c 'Print :RunAtLoad' "$PLIST" 2>/dev/null || echo "?")
        echo "  config:   KeepAlive=$ka  RunAtLoad=$ral"
    fi
    echo "  launchd:  $(plist_loaded && echo 'loaded' || echo 'not loaded')"
    echo "  chrome:   $(chrome_running && echo 'running' || echo 'not running')"
    echo "  port :$PORT $(port_responsive && echo 'responsive' || echo 'no response')"
    if port_responsive; then
        n=$(curl -s "http://127.0.0.1:${PORT}/json" | python3 -c 'import sys,json; print(sum(1 for t in json.loads(sys.stdin.read()) if t.get("type")=="page"))' 2>/dev/null || echo '?')
        echo "  pages:    $n open"
    fi
}

cmd_start() {
    ensure_plist
    if chrome_running && port_responsive; then
        echo "  ✅ already running"; return 0
    fi
    if plist_loaded; then
        echo "  ✅ launchd already loaded, waiting for Chrome..."
    else
        launchctl bootstrap "gui/${UID_NUM}" "$PLIST" 2>&1 || true
        echo "  ✅ bootstrapped launchd service"
    fi
    for i in 1 2 3 4 5 6 7 8 9 10; do
        if port_responsive; then
            echo "  ✅ CDP up after ${i}s"
            return 0
        fi
        sleep 1
    done
    echo "  ⚠️  CDP did not respond on port $PORT after 10s"
    echo "  ⚠️  tail of ~/.hermes/chrome_cdp.log:"
    tail -10 "$HOME/.hermes/chrome_cdp.log" 2>/dev/null || true
    return 1
}

cmd_stop() {
    ensure_plist
    if ! plist_loaded; then
        echo "  ✅ launchd already not loaded"; return 0
    fi
    launchctl bootout "gui/${UID_NUM}/$LABEL" 2>&1 || true
    echo "  ✅ booted out launchd service"
    for i in 1 2 3 4 5; do
        if ! chrome_running; then echo "  ✅ Chrome exited after ${i}s"; return 0; fi
        sleep 1
    done
    if chrome_running; then
        echo "  ⚠️  Chrome still running after bootout (KeepAlive=true?). Killing process..."
        pkill -f "Google Chrome.*remote-debugging-port=${PORT}" 2>/dev/null || true
        sleep 1
        if chrome_running; then echo "  ❌ Chrome still alive"; return 1; fi
        echo "  ✅ Chrome killed"
    fi
}

cmd_restart() { cmd_stop; sleep 1; cmd_start; }

toggle_keepalive() {
    local target="$1"
    ensure_plist
    local current
    current=$(/usr/libexec/PlistBuddy -c 'Print :KeepAlive' "$PLIST" 2>/dev/null || echo "")
    if [[ "$current" == "$target" ]]; then
        echo "  ✅ KeepAlive already $target"; return 0
    fi
    /usr/libexec/PlistBuddy -c "Set :KeepAlive $target" "$PLIST"
    echo "  ✅ KeepAlive set to $target"
    if plist_loaded; then
        echo "  ⚠️  plist modified while loaded — bootout+bootstrap to apply"
        cmd_stop
        cmd_start
    fi
}

cmd_onboot()    { toggle_keepalive true; }
cmd_ondemand()  { toggle_keepalive false; }

case "${1:-status}" in
    status)    cmd_status ;;
    start)     cmd_start ;;
    stop)      cmd_stop ;;
    restart)   cmd_restart ;;
    on-boot)   cmd_onboot ;;
    on-demand) cmd_ondemand ;;
    *) echo "Usage: $0 {status|start|stop|restart|on-boot|on-demand}"; exit 2 ;;
esac