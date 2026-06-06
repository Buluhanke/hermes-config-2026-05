#!/bin/bash
# Top 10 内存大户 + 可清理性评估
# 输出每个进程的：PID / RSS(MB) / 名称 / etime / 父 PID / 可清理评估

echo "=== Top 10 内存大户 + 可清理性评估 ==="
echo "时间: $(date)"
echo ""

ps -A -o pid,ppid,etime,rss,command | sort -k4 -rn | head -11 | tail -10 | while read pid ppid etime rss cmd; do
  mb=$((rss/1024))
  name=$(echo "$cmd" | awk '{print $1}' | sed 's|/Contents/.*||; s|/MacOS/.*||; s|.*/||')
  cmd_short=$(echo "$cmd" | awk '{for(i=8;i<=NF&&i<15;i++)printf "%s ",$i; print ""}' | cut -c1-80)

  # 可清理性评估
  flag=""
  if [ "$ppid" = "1" ]; then
    flag="⚠️ 系统服务"
  elif ps -p $pid -o stat= 2>/dev/null | grep -q Z; then
    flag="🧟 僵尸"
  elif echo "$cmd" | grep -q "hermes\|Hermes\|gateway"; then
    flag="🔴 Hermes 自家"
  elif echo "$cmd" | grep -q "Claude"; then
    flag="🟡 用户 Claude"
  elif [ "$mb" -gt 200 ]; then
    flag="🟢 可评估"
  fi

  printf "  %-7s %4dMB  %-12s  etime=%-12s  %s\n  └─ %s\n" \
    "PID $pid" "$mb" "$name" "$etime" "$flag" "$cmd_short"
done

echo ""
echo "=== 系统总览 ==="
free_pages=$(vm_stat | awk '/Pages free:/ {print $3}')
free_gb=$(python3 -c "print(round($free_pages * 16384 / 1024 / 1024 / 1024, 2))")
echo "  空闲内存: ${free_gb} GB / 24 GB"
echo "  Swap: $(sysctl vm.swapusage | awk -F'used = ' '{print $2}')"
echo "  负载: $(sysctl -n vm.loadavg)"
