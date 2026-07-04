#!/usr/bin/env bash
# audit-deepseek-leak.sh — 5-链 deepseek 残留体检
# 跑法: bash ~/.hermes/skills/devops/hermes-provider-fallback-tuning/scripts/audit-deepseek-leak.sh
# 退出码: 0=clean, 1=有残留(输出 location)
#
# 覆盖 5 处 deepseek 残留:
#   1. model.fallback_chain
#   2. fallback_providers[]
#   3. moa.models / moa.aggregator
#   4. auxiliary.<task>.fallback_chain
#   5. ~/.hermes/.env 里的 DEEPSEEK_API_KEY
#
# 2026-07-03 实战: 用户清前 3 处后报"删干净了", 实际漏 .env + auxiliary, 辅助任务偷调
set -euo pipefail

CONFIG="${HOME}/.hermes/config.yaml"
ENV_FILE="${HOME}/.hermes/.env"
TARGET_REGEX='deepseek|DEEPSEEK|DeepSeek'

leaks=0
report() {
    local chain="$1" location="$2" matches="$3"
    if [[ -n "$matches" ]]; then
        echo "❌ [$chain] LEAK @ $location"
        echo "$matches" | head -3 | sed 's/^/    /'
        leaks=$((leaks + 1))
    else
        echo "✅ [$chain] clean"
    fi
}

# 1. model.fallback_chain
matches=$(grep -nE "fallback_chain" "$CONFIG" 2>/dev/null | grep -iE "$TARGET_REGEX" || true)
report "1.fallback_chain" "$CONFIG" "$matches"

# 2. fallback_providers[] (查 provider/model 行)
matches=$(grep -nE "provider:.*deepseek|model:.*deepseek" "$CONFIG" 2>/dev/null || true)
report "2.fallback_providers" "$CONFIG" "$matches"

# 3. moa.*
matches=$(grep -nE "^  models:|aggregator:" "$CONFIG" 2>/dev/null | grep -iE "$TARGET_REGEX" || true)
report "3.moa" "$CONFIG" "$matches"

# 4. auxiliary.<task>.fallback_chain (块扫描)
matches=$(grep -nB1 -A6 "^auxiliary:" "$CONFIG" 2>/dev/null | grep -iE "$TARGET_REGEX" || true)
report "4.auxiliary" "$CONFIG" "$matches"

# 5. ~/.hermes/.env
matches=$(grep -nE "DEEPSEEK_API_KEY|DEEPSEEK_BASE_URL" "$ENV_FILE" 2>/dev/null || true)
report "5.env" "$ENV_FILE" "$matches"

echo
if [[ $leaks -eq 0 ]]; then
    echo "🎯 ALL CLEAN — 5 链 0 匹配, deepseek 已彻底隔离"
    exit 0
else
    echo "🚨 $leaks LEAK(S) — 修法: 跑完 5 链 grep + sed/python 删 + restart gateway"
    echo "   参考: hermes-provider-fallback-tuning skill '5-place audit' 节"
    exit 1
fi
