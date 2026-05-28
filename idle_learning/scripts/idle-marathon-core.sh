#!/bin/bash
# idle-marathon-core.sh — 马拉松自学核心引擎（实际执行版）
# 由 hermes-agent 的 cronjob 调度，每30分钟循环一次
# 截止时间到后自动停止

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
    echo "[$timestamp] 循环#$cycle | 剩余${remaining}秒 | 方向: $topic"
    
    # ---- 联网搜索（必须走terminal，execute_code网络隔离）----
    search_results=""
    
    case $topic in
        screen_understanding_macos_2026)
            echo "  🔍 搜索: macOS AI屏幕感知方案..."
            search_results=$(curl -s --max-time 10 "https://api.duckduckgo.com/?q=site%3Agithub.com+mac+screen+understanding+AI+agent+2026&format=json" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); [print(r['Text']) for r in d.get('RelatedTopics',[])[:5]]" 2>/dev/null || echo "搜索失败")
            ;;
        ai_agent_browser_automation_humanization)
            echo "  🔍 搜索: 浏览器自动化真人化方案..."
            search_results=$(curl -s --max-time 10 "https://api.duckduckgo.com/?q=browser+automation+humanization+AI+agent+undetectable+2026&format=json" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); [print(r['Text']) for r in d.get('RelatedTopics',[])[:5]]" 2>/dev/null || echo "搜索失败")
            ;;
        1688_procurement_api_automation)
            echo "  🔍 搜索: 1688采购自动化方案..."
            search_results=$(curl -s --max-time 10 "https://api.duckduckgo.com/?q=1688+open+api+procurement+automation+python+2026&format=json" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); [print(r['Text']) for r in d.get('RelatedTopics',[])[:5]]" 2>/dev/null || echo "搜索失败")
            ;;
        captcha_bypass_ai_agent)
            echo "  🔍 搜索: AI验证码对抗方案..."
            search_results=$(curl -s --max-time 10 "https://api.duckduckgo.com/?q=CAPTCHA+bypass+AI+agent+visual+reasoning+2026&format=json" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); [print(r['Text']) for r in d.get('RelatedTopics',[])[:5]]" 2>/dev/null || echo "搜索失败")
            ;;
    esac
    
    echo "  📝 搜索结果: ${search_results:0:200}"
    
    # ---- 写入日志 ----
    {
        echo "---"
        echo "## 马拉松 #$cycle @ $timestamp"
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
        echo "  ⚠️ Gateway异常，尝试重启..."
        # 自愈逻辑已由 watchdog cronjob 处理，此处只记录
        echo "  [自愈] Gateway异常已由watchdog接管" >> $LOG_FILE
    fi
    
    echo "  ✅ 循环#$cycle完成，等待${INTERVAL}秒..."
    echo ""
    
    sleep $INTERVAL
done

echo "🏁 马拉松结束，共完成$CYCLE个循环" >> $LOG_FILE
echo "📊 报告: $LOG_FILE"