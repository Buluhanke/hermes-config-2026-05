#!/usr/bin/env bash
# mac-resource-report.sh — 一键 macOS 资源诊断报告
# 输出: 内存 / Swap / Load / Top 10 进程 / 慢响应排查线索
# 依赖: awk, python3, vm_stat, sysctl, ps (BSD)
set -e

echo "═══════════════════════════════════════════════════════════"
echo "  macOS 资源诊断报告 — $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ── Step 1: 系统快照 ──
echo "【1/4】系统级快照"
echo "─────────────────────────────────────────────────────────"
free_pages=$(vm_stat | awk '/Pages free:/ {print $3}')
echo "  💾 空闲内存: $(python3 -c "print(round($free_pages * 16384 / 1024 / 1024 / 1024, 2))") GB"
echo "  💽 Swap: $(sysctl -n vm.swapusage | awk -F'used = ' '{print $2}')"
echo "  ⚙️  负载 (1/5/15 min): $(sysctl -n vm.loadavg | tr -d '{}')"
echo "  🖥  CPU 核数: $(sysctl -n hw.ncpu)"
echo ""

# ── Step 2: Top 10 内存 ──
echo "【2/4】内存 Top 10 (按 RSS 排序, KB)"
echo "─────────────────────────────────────────────────────────"
ps -A -o pid,rss,command | sort -k2 -rn | head -11 | tail -10 | \
  awk '{printf "  PID %-6s %5.0f MB  %s\n", $1, $2/1024, substr($3,1,60)}'
echo ""

# ── Step 3: Top 5 CPU ──
echo "【3/4】CPU Top 5"
echo "─────────────────────────────────────────────────────────"
ps -A -o pid,pcpu,command | sort -k2 -rn | head -6 | tail -5 | \
  awk '{printf "  PID %-6s %4.1f%%  %s\n", $1, $2, substr($3,1,60)}'
echo ""

# ── Step 4: 慢响应排查线索 ──
echo "【4/4】Hermes Gateway 健康 + 最近慢响应排查"
echo "─────────────────────────────────────────────────────────"
GW_PID=$(pgrep -f "hermes_cli.main gateway" | head -1)
SW_PID=$(pgrep -f "screen_watcher.py" | head -1)
CHROME_PID=$(pgrep -f "chrome-debug.*remote-debugging-port" | head -1)

if [ -n "$GW_PID" ]; then
  RSS=$(ps -p $GW_PID -o rss= | tr -d ' ')
  echo "  ✅ Gateway (PID $GW_PID) RSS: ${RSS}KB"
else
  echo "  ❌ Gateway 未运行"
fi

if [ -n "$SW_PID" ]; then
  echo "  ✅ screen_watcher (PID $SW_PID) 正常"
else
  echo "  ❌ screen_watcher 未运行"
fi

if [ -n "$CHROME_PID" ]; then
  echo "  ✅ Chrome debug (PID $CHROME_PID) 正常"
else
  echo "  ❌ Chrome debug 未运行"
fi

# 最近 5 条 inbound + response ready
echo ""
echo "  📜 最近 5 条 gateway 响应记录:"
grep "response ready" ~/.hermes/logs/gateway.log 2>/dev/null | tail -5 | \
  awk '{printf "    %s  %ss  %s calls\n", $1, $NF-3, $(NF-3)}' 2>/dev/null || \
  echo "    (无日志)"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  建议:"
echo "  - 空闲 < 2GB → 杀 bash-language-server / 重启 Chrome"
echo "  - loadavg > CPU核数 → 有进程在排队，ps aux 查谁"
echo "  - Gateway 不在 → nohup ~/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main gateway run --replace &"
echo "═══════════════════════════════════════════════════════════"
