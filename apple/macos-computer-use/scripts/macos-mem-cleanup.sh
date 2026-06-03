#!/usr/bin/env bash
# 清理 macOS 内存占用的快捷脚本
# 用法：./macos-mem-cleanup.sh [--chrome | --all | --verify]
#
# --chrome  只关 Chrome 窗口（保留 debug 模式进程）
# --all     杀 Chrome 进程（节省 ~2GB，下次需要时再启）
# --verify  只验证当前窗口数，不清理
#
# 关键：所有清理操作之后必须跑一次 verify，确认窗口数=0
# 这是 2026-06-03 教训：跑完清理命令≠真的清理了

set -e

verify_chrome() {
  osascript -e 'tell application "System Events" to count of windows of process "Google Chrome"' 2>/dev/null | tr -d ' '
}

verify_chrome_procs() {
  pgrep -fl "Google Chrome" 2>/dev/null | wc -l | tr -d ' '
}

case "${1:-}" in
  --verify)
    echo "=== 当前 Chrome 状态 ==="
    echo "窗口: $(verify_chrome)"
    echo "进程: $(verify_chrome_procs)"
    ;;
  --all)
    echo "=== 杀 Chrome 进程（节省 ~2GB） ==="
    osascript -e 'tell application "Google Chrome" to quit' 2>/dev/null || true
    sleep 2
    pkill -9 -f "Google Chrome Helper" 2>/dev/null || true
    pkill -9 -f "Google Chrome" 2>/dev/null || true
    sleep 1
    n=$(verify_chrome)
    p=$(verify_chrome_procs)
    echo "窗口: $n | 进程: $p"
    [[ "$p" -eq 0 ]] && echo "✅  清理完成" || echo "⚠️  进程残留"
    ;;
  --chrome|"")
    echo "=== 关 Chrome 所有窗口（保留 debug 模式进程） ==="
    osascript -e 'tell application "Google Chrome" to close every window' 2>/dev/null
    sleep 1
    n=$(verify_chrome)
    echo "窗口: $n"
    if [[ "$n" -gt 0 ]]; then
      echo "⚠️  还有窗口残留，重试"
      osascript -e 'tell application "Google Chrome" to close every window' 2>/dev/null
      sleep 1
      n=$(verify_chrome)
      echo "重试后: $n"
    fi
    [[ "$n" -eq 0 ]] && echo "✅  清理完成" || echo "❌  仍有残留"
    ;;
  *)
    echo "用法: $0 [--chrome | --all | --verify]"
    exit 1
    ;;
esac
