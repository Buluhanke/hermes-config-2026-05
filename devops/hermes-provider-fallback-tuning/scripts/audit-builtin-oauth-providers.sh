#!/usr/bin/env bash
# audit-builtin-oauth-providers.sh — 探测 hermes model picker 里那些不受 .env 控制的 provider
# 跑法: bash ~/.hermes/skills/devops/hermes-provider-fallback-tuning/scripts/audit-builtin-oauth-providers.sh
# 退出码: 0=全部 .env 可控, 1=有内置 OAuth provider (改 .env 无法消失)
#
# 输出格式:
#   [BUILTIN] provider_label → hermes_cli/<file>.py:<line>   ← 需 patch 源码
#   [ENV-DEP] provider_label → ~/.hermes/.env                ← 可改 .env 抑制
#
# 2026-07-04 实战: 清 MINIMAX_API_KEY / MINIMAX_CN_API_KEY / MINIMAX_CN_BASE_URL
#   三件套 .env 删除后, `hermes model` picker 仍列 3 条 `MiniMax ▸ (Global, OAuth Coding Plan & China endpoints)`
#   根因: hermes-cli 源码内置 OAuth-mode provider, .env 完全无效
set -uo pipefail

LOG="/tmp/hermes_model_audit_$$.log"
trap 'rm -f "$LOG"' EXIT

echo "🔍 Built-in OAuth Provider Audit"
echo "================================"
echo ""

if ! command -v script >/dev/null 2>&1; then
    echo "❌ 需要 'script' 命令 (macOS 自带)"
    exit 2
fi

echo "1. 跑 'hermes model --no-browser' 抓候选列表..."
# 用 script 模拟 TTY, 输入 ESC + 回车退出 (避免被 picker 卡住)
timeout 15 script -q "$LOG" hermes model --no-browser <<'EOF' >/dev/null 2>&1 || true
x
EOF

if [[ ! -s "$LOG" ]]; then
    echo "❌ 抓不到 picker 输出, 可能 gateway 没启动 — 查: pgrep -f 'hermes.*gateway'"
    exit 1
fi

# 2. 提取候选条目 (去 ANSI, 匹配 ○/● 标记的行)
RAW=$(perl -pe 's/\x1b\[[0-9;?]*[a-zA-Z]//g; s/\x1b\[\?[0-9]+[hl]//g; s/\r//g' "$LOG" \
        | grep -oE '[○●]\s*\S.*' || true)

if [[ -z "$RAW" ]]; then
    echo "⚠️  picker 输出解析失败, 原始 log 在 $LOG"
    exit 1
fi

echo ""
echo "2. 候选 Provider 分类:"
echo ""

ENV_FILE="${HOME}/.hermes/.env"
HERMES_BIN=$(which hermes 2>/dev/null || true)
[[ -n "$HERMES_BIN" ]] && HERMES_ROOT=$(dirname $(dirname "$HERMES_BIN")) || HERMES_ROOT=""

builtin_count=0
env_dep_count=0

while IFS= read -r line; do
    label=$(echo "$line" \
            | sed -E 's/^[○●]\s*//' \
            | sed -E 's/\s*\.\.\..*$//' \
            | awk '{print $1}' \
            | tr -d '[:space:]')
    [[ -z "$label" ]] && continue

    # 跳过 IP 类 (custom 代理)
    if [[ "$label" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+ ]]; then
        echo "  [CUSTOM]  $line"
        continue
    fi

    # 探测 .env key
    key_variants=""
    if [[ -f "$ENV_FILE" ]]; then
        UPPER=$(echo "$label" | tr '[:lower:]' '[:upper:]')
        key_variants=$(grep -iE "^${UPPER}_API_KEY=|^${label}_API_KEY=" "$ENV_FILE" 2>/dev/null | cut -d= -f1 | tr '\n' ' ')
    fi

    # 探测 hermes-cli 源码注册
    ocl_match=""
    ocl_line="?"
    if [[ -n "$HERMES_ROOT" && -d "$HERMES_ROOT/hermes_cli" ]]; then
        ocl_match=$(grep -rn -l "\"$label\"\|'$label'" "$HERMES_ROOT/hermes_cli/" --include="*.py" 2>/dev/null | head -1 || true)
        if [[ -n "$ocl_match" ]]; then
            ocl_line=$(grep -n "\"$label\"\|'$label'" "$ocl_match" 2>/dev/null | head -1 | cut -d: -f1)
        fi
    fi

    if [[ -n "$key_variants" ]]; then
        echo "  [ENV-DEP] $label  →  .env keys: $key_variants"
        env_dep_count=$((env_dep_count + 1))
    elif [[ -n "$ocl_match" ]]; then
        echo "  [BUILTIN] $label  →  $ocl_match:${ocl_line}"
        echo "           ⚠️  改 .env 删不掉, 需 patch hermes-cli 源码"
        builtin_count=$((builtin_count + 1))
    else
        echo "  [?DYN ] $label  →  源码无 static 注册, 可能走 OAuth 动态加载"
        builtin_count=$((builtin_count + 1))
    fi
done <<< "$RAW"

echo ""
echo "================================"
echo "📊  $env_dep_count 个 .env-可控, $builtin_count 个内置 OAuth"

if [[ $builtin_count -gt 0 ]]; then
    echo ""
    echo "🚨 有 $builtin_count 个 provider 改 .env 删不掉"
    echo "   完全抑制方案:"
    echo "     HERMES_ROOT=\$(dirname \$(dirname \$(which hermes)))"
    echo "     grep -rn '\"<provider>\"' \$HERMES_ROOT/hermes_cli/ --include='*.py'"
    echo "     sed 删对应注册块, 加 if label in BLOCKLIST: continue"
    echo "     ⚠️  hermes 升级会覆盖 patch, 需重打"
    exit 1
fi

echo "🎯 全部候选 .env 可控 — 改 .env + restart gateway 即可生效"
exit 0
