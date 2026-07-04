#!/usr/bin/env bash
# idle_round_runner.sh — 一键跑完 A→B→C→D + fact_store + 3 工具验证
# 退出码: 0 = 健康, 1 = 任一关键步骤失败, 2 = fact_store 健康度不达标

set -uo pipefail

SCRIPTS_DIR="$HOME/.hermes/scripts"
RESULTS_FILE="$(mktemp /tmp/idle_round.XXXXXX.log)"
trap 'rm -f "$RESULTS_FILE"' EXIT

section() {
    echo ""
    echo "=== $1 ==="
}

run_check() {
    local label="$1"
    local cmd="$2"
    echo "[$label] $cmd"
    if eval "$cmd" >> "$RESULTS_FILE" 2>&1; then
        echo "  ✅ exit 0"
    else
        echo "  ❌ exit $? — 见 $RESULTS_FILE"
        return 1
    fi
}

FAIL=0

section "A 视觉产线"
ps aux | grep -E 'screen_watcher|ollama|trigger_handler|vision_cache|idle_learning' | grep -v grep | awk '{print $2, $11, $12, $13}' | head -10 || true

section "B 论文 / AI 知识"
run_check "B" "python3 $SCRIPTS_DIR/ai_radar_brief.py" || FAIL=1

section "C 安全 CVE"
run_check "C" "python3 $SCRIPTS_DIR/cve_scan.py" || FAIL=1

section "D 执行层"
run_check "D" "python3 $SCRIPTS_DIR/action_diversity.py" || FAIL=1

section "fact_store 写入"
run_check "fact_store" "python3 $SCRIPTS_DIR/batch_facts_from_log.py" || FAIL=1

section "衰减检查"
DECAY_OUTPUT=$(python3 $SCRIPTS_DIR/fact_decay.py 2>&1)
echo "$DECAY_OUTPUT"
# 健康判定: 活跃 ≥ 95% 且 平均 trust ≥ 0.4
ACTIVE=$(echo "$DECAY_OUTPUT" | grep "活跃" | head -1 | awk '{print $NF}')
TOTAL=$(echo "$DECAY_OUTPUT" | grep "衰减统计" | awk -F'[()]' '{print $2}' | awk '{print $1}')
AVG_TRUST=$(echo "$DECAY_OUTPUT" | grep "平均 trust" | awk '{print $NF}')

if [ -n "$ACTIVE" ] && [ -n "$TOTAL" ] && [ "$TOTAL" -gt 0 ]; then
    RATIO=$(awk "BEGIN {printf \"%.0f\", ($ACTIVE/$TOTAL)*100}")
    if [ "$RATIO" -lt 95 ] || awk "BEGIN {exit !($AVG_TRUST < 0.4)}"; then
        echo "  ⚠️  fact_store 健康度不达标: 活跃 $ACTIVE/$TOTAL ($RATIO%), 平均 trust $AVG_TRUST"
        FAIL=2
    else
        echo "  ✅ fact_store 健康: 活跃 $ACTIVE/$TOTAL ($RATIO%), 平均 trust $AVG_TRUST"
    fi
fi

section "3 工具实测验证"
run_check "fact_decay --score" "python3 $SCRIPTS_DIR/fact_decay.py --score" || FAIL=1
run_check "vision_cache stats" "python3 $SCRIPTS_DIR/vision_cache.py stats" || FAIL=1
run_check "rollback_manager list" "python3 $SCRIPTS_DIR/rollback_manager.py list" || FAIL=1

echo ""
echo "============================================"
if [ $FAIL -eq 0 ]; then
    echo "✅ idle_learning 轮次全部通过 (exit 0)"
    exit 0
elif [ $FAIL -eq 2 ]; then
    echo "⚠️  idle_learning 轮次部分通过 — fact_store 健康度需关注"
    exit 2
else
    echo "❌ idle_learning 轮次失败 — 见 $RESULTS_FILE"
    exit 1
fi