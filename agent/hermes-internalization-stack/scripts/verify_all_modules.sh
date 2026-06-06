#!/bin/bash
# verify_all_modules.sh — 一次性跑所有 ~/.hermes/scripts/*.py 的 __main__ 块。
#
# 用途：每次在 stack 里加新模块/改老模块，跑一次确保 import 静默 + __main__ 退出 0。
# 这会**真的**触发 module 里的 demo（包括写入状态文件），所以测试前后用 git/手动备份。
#
# Usage:
#   ~/.hermes/skills/agent/hermes-internalization-stack/scripts/verify_all_modules.sh
#   ~/.hermes/skills/agent/hermes-internalization-stack/scripts/verify_all_modules.sh --dry-run  # 只 import 不跑 __main__

set -uo pipefail

SCRIPTS_DIR="${HERMES_SCRIPTS_DIR:-$HOME/.hermes/scripts}"
DRY_RUN=false
[ "${1:-}" = "--dry-run" ] && DRY_RUN=true

PASS=0
FAIL=0
NOISY=0
MODULES=()

echo "=== hermes-internalization-stack verification ==="
echo "scripts dir: $SCRIPTS_DIR"
echo "mode: $([ "$DRY_RUN" = true ] && echo 'dry-run (import only)' || echo 'full (runs __main__ block)')"
echo

for f in "$SCRIPTS_DIR"/*.py; do
    [ -f "$f" ] || continue
    name=$(basename "$f" .py)
    MODULES+=("$name")

    # 1. Import must be silent (no print to stdout)
    if [ "$DRY_RUN" = true ]; then
        out=$(python3 -c "import sys; sys.path.insert(0, '$SCRIPTS_DIR'); import $name" 2>&1)
    else
        out=$(python3 "$f" 2>&1)
    fi
    rc=$?

    if [ $rc -ne 0 ]; then
        echo "  [FAIL] $name  (exit=$rc)"
        echo "$out" | head -3 | sed 's/^/         /'
        FAIL=$((FAIL+1))
        continue
    fi

    # Check: first 2 lines of output should NOT be the "demo" print
    # (this is a heuristic — false positives possible)
    if echo "$out" | head -2 | grep -qE "当前时区|当前|可主动|自测"; then
        echo "  [NOISY] $name  (looks like top-level demo print leaked)"
        echo "$out" | head -3 | sed 's/^/         /'
        NOISY=$((NOISY+1))
        continue
    fi

    echo "  [PASS] $name"
    PASS=$((PASS+1))
done

echo
echo "=== summary ==="
echo "  PASS:   $PASS"
echo "  FAIL:   $FAIL"
echo "  NOISY:  $NOISY  (top-level print detected — see hermes-rhythm-gate pitfall #8)"
echo "  total:  $((PASS+FAIL+NOISY))"
[ $FAIL -eq 0 ] && [ $NOISY -eq 0 ] && exit 0 || exit 1
