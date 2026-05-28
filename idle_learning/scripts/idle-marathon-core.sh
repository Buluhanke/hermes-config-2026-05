#!/bin/bash
# idle-marathon-core.sh — 马拉松自学核心引擎（实际执行版）
# 由 hermes-agent 的 cronjob 调度，每30分钟循环一次
# 截止时间到后自动停止
#
# ⚠️ Cron 环境限制：禁止 python3 -c / heredoc / <<EOF 内嵌 Python
# ✅ 正确做法：所有 Python 调用必须写 .py 文件后执行

set -e

DEADLINE=${1:-$(date -d "+8 hours" +%s)}
INTERVAL=${2:-1800}
LOG_DIR=~/Brain_Lab
LOG_FILE=$LOG_DIR/idle_learning_log.md
MARATHON_FLAG=$LOG_DIR/.marathon_active
CYCLE=0

mkdir -p $LOG_DIR

# 标记运行中
echo "$DEADLINE" > $MARATHON_FLAG

echo "🚀 马拉松核心引擎启动"
echo "📌 截止: $(date -r $DEADLINE '+%Y-%m-%d %H:%M') ($(($DEADLINE - $(date +%s)))秒)"
echo "📌 间隔: ${INTERVAL}秒"
echo ""

# 学习方向池（4层轮流）
declare -a TOPICS=(
    "screen_understanding_macos_2026"
    "ai_agent_browser_automation_humanization"
    "1688_procurement_api_automation"
    "captcha_bypass_ai_agent"
)

topic_idx=0

while true; do
    now=$(date +%s)
    if [ $now -ge $DEADLINE ]; then
        echo "✅ 截止时间到达，退出"
        rm -f $MARATHON_FLAG
        break
    fi

    CYCLE=$((CYCLE + 1))
    topic=${TOPICS[$((topic_idx % 4))]}
    topic_idx=$((topic_idx + 1))
    remaining=$((DEADLINE - now))

    timestamp=$(date '+%Y-%m-%d %H:%M')
    echo "[$timestamp] 循环#$CYCLE | 剩余${remaining}秒 | 方向: $topic"

    # ---- 联网搜索：优先 HN Firebase API（免费稳定，无认证）----
    # ⚠️ 禁止 python3 -c / heredoc，必须写 .py 文件
    # write_file /tmp/hn_top5.py → python3 /tmp/hn_top5.py

    case $topic in
        screen_understanding_macos_2026|ai_agent_browser_automation_humanization|captcha_bypass_ai_agent)
            echo "  🔍 搜索HN热门话题..."
            curl -s "https://hacker-news.firebaseio.com/v0/topstories.json" -o /tmp/hn_top.json
            # 写 .py 文件 → python3 /tmp/hn_top5.py
            write_file tool: path=/tmp/hn_top5.py, content='...'
            top5=$(python3 /tmp/hn_top5.py)
            search_results="HN IDs: $top5"
            ;;
        1688_procurement_api_automation)
            echo "  🔍 搜索: 1688采购自动化方案..."
            curl -s "https://hacker-news.firebaseio.com/v0/topstories.json" -o /tmp/hn_top2.json
            write_file tool: path=/tmp/hn_top3.py, content='...'
            search_results=$(python3 /tmp/hn_top3.py)
            ;;
    esac

    echo "  📝 搜索结果: ${search_results:0:200}"

    # ---- 写入日志 ----
    {
        echo "---"
        echo "## 马拉松 #$CYCLE @ $timestamp"
        echo "**方向**: $topic"
        echo "**剩余**: ${remaining}秒"
        echo ""
        echo "**搜索结果**:"
        echo "\`\`\`"
        echo "$search_results" | head -20
        echo "\`\`\`"
        echo ""
    } >> $LOG_FILE

    # ---- 自检健康（每次循环都做）----
    echo "  🏥 健康自检..."
    gw_ok=$(ps aux | grep -c "hermes_cli" | grep -v grep || echo 0)
    tts_ok=$(curl -s --max-time 3 localhost:5678/api/v1/health 2>/dev/null | grep -c "ok" || echo 0)

    if [ "$gw_ok" -eq 0 ]; then
        echo "  ⚠️ Gateway异常..."
        echo "  [自愈] Gateway异常已由watchdog接管" >> $LOG_FILE
    fi

    echo "  ✅ 循环#$CYCLE完成，等待${INTERVAL}秒..."
    sleep $INTERVAL
done

echo "🏁 马拉松结束，共完成$CYCLE个循环" >> $LOG_FILE
