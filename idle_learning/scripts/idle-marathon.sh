#!/bin/bash
# idle-marathon.sh — 马拉松式空闲自学脚本
# 用法: ./idle-marathon.sh <截止时间戳(Unix)> [间隔秒数]
# 例: ./idle-marathon.sh $(date -d "08:00 tomorrow" +%s) 1800
#
# 截止时间到达后自动退出，生成学习报告发给用户

set -e

DEADLINE=${1:-$(( $(date +%s) + 28800 ))}  # 默认8小时后
INTERVAL=${2:-1800}                          # 默认30分钟
LOG_FILE=~/Brain_Lab/idle_learning_log.md
REPORT_FILE=~/Brain_Lab/marathon_report_$(date +%Y%m%d_%H%M).md

echo "🚀 马拉松自学启动"
echo "📌 截止时间: $(date -r $DEADLINE '+%Y-%m-%d %H:%M')"
echo "📌 循环间隔: ${INTERVAL}秒"
echo ""

# 学习方向池（4个层次轮流）
declare -a DIRECTIONS=(
    "Vision/屏幕感知能力"
    "理解/内容理解能力" 
    "规划/任务规划能力"
    "执行/手眼配合能力"
)

dir_index=0
cycle=0

while true; do
    now=$(date +%s)
    remaining=$((DEADLINE - now))
    
    if [ $remaining -le 0 ]; then
        echo "⏰ 截止时间到达，停止自学"
        break
    fi
    
    cycle=$((cycle + 1))
    direction=${DIRECTIONS[$((dir_index % 4))]}
    dir_index=$((dir_index + 1))
    
    echo "[$(date '+%Y-%m-%d %H:%M')] 循环#$cycle | 剩余${remaining}秒 | 方向: $direction"
    
    {
        echo "---"
        echo "## 马拉松循环 #$cycle"
        echo "**时间**: $(date '+%Y-%m-%d %H:%M')"
        echo "**学习方向**: $direction"
        echo ""
    } >> "$LOG_FILE"
    
    # 这里放 idle_learning 的核心逻辑（联网搜索 + 写 memory）
    # 由于是脚本模式，直接调用 hermes 执行自学任务
    # 实际执行依赖 Hermes Agent 的 cron 调度能力，此处只做日志记录
    
    echo "   ✓ 记录已写入 $LOG_FILE"
    echo "   ⏳ 等待${INTERVAL}秒..."
    echo ""
    
    sleep $INTERVAL
done

# 生成报告
{
    echo "# 马拉松自学报告"
    echo "**生成时间**: $(date '+%Y-%m-%d %H:%M')"
    echo "**总循环次数**: $cycle"
    echo "" 
    echo "详见: $LOG_FILE"
} > "$REPORT_FILE"

echo ""
echo "📊 报告已生成: $REPORT_FILE"
cat "$REPORT_FILE"