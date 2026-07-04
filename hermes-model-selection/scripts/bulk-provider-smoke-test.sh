#!/bin/bash
# bulk-provider-smoke-test.sh — 一键并发审计所有 fallback_providers 状态
#
# 用法:
#   bash ~/.hermes/skills/hermes-model-selection/scripts/bulk-provider-smoke-test.sh
#
# 自动:
#   1. 从 ~/.hermes/.env 只读取 *_API_KEY（不用 source，用 grep 避免执行命令）
#   2. 从 ~/.hermes/config.yaml 的 fallback_providers 段解析 model+base_url
#   3. 并发跑所有 provider 的 curl (GET /v1/models + POST /v1/chat/completions)
#   4. 输出表格: provider | model | /models 状态 | /chat 状态 | 延迟
#
# 适用场景:
#   - 用户问 "现在有几个能用的 model" / "fallback 链都还活着吗"
#   - 批量换 key 后做体检
#   - cron 定期巡检
#
# 修复 (2026-07-04):
#   - 不再 source 整个 .env（.env 里有 Chrome.app 路径会触发"命令未找到"）
#   - 改用 grep/cut 只提取需要的 *_API_KEY 行
#   - 去掉 set -u（动态变量名会有空值问题）
#   - 修复 heredoc 嵌套语法错误

set -e

ENV_FILE="$HOME/.hermes/.env"
CONFIG_FILE="$HOME/.hermes/config.yaml"
PING_PROMPT='hi'
MAX_TOKENS=3
RESULTS_DIR=$(mktemp -d)
trap "rm -rf $RESULTS_DIR" EXIT

# 只从 .env 取 *_API_KEY，不执行其他行
get_key() {
  local var="$1"
  grep "^${var}=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo ""
}

NVIDIA_API_KEY=$(get_key NVIDIA_API_KEY)
CEREBRAS_API_KEY=$(get_key CEREBRAS_API_KEY)
GEMINI_API_KEY=$(get_key GEMINI_API_KEY)
OPENROUTER_API_KEY=$(get_key OPENROUTER_API_KEY)
GLM_API_KEY=$(get_key GLM_API_KEY)
AGNES_API_KEY=$(get_key AGNES_API_KEY)
MINIMAX_API_KEY=$(get_key MINIMAX_API_KEY)

# 清理代理环境（避免代理干扰 NV 直连）
unset https_proxy http_proxy HTTPS_PROXY HTTP_PROXY ALL_PROXY all_proxy

# 用 Python 解析 config.yaml 的 fallback_providers
PROVIDERS=$(python3 -c "
import yaml, json
from pathlib import Path
cfg = yaml.safe_load(open(Path.home() / '.hermes' / 'config.yaml'))
fps = cfg.get('fallback_providers') or []
seen = set()
out = []
for p in fps:
    provider = p.get('provider','')
    if provider in seen:
        continue
    seen.add(provider)
    raw_key = (p.get('api_key') or '').strip()
    env_var = raw_key.replace('\${','').replace('}','').replace('{','').replace('}','') if raw_key else ''
    out.append({
        'provider': provider,
        'model': p.get('model',''),
        'base_url': p.get('base_url',''),
        'env_var': env_var,
    })
print(json.dumps(out))
" 2>/dev/null)

COUNT=$(echo "$PROVIDERS" | python3 -c "import json,sys; print(len(json.loads(sys.stdin.read())))")

echo "=========================================="
echo "📡 Hermes Bulk Provider Audit ($COUNT 个)"
echo "=========================================="
printf "%-25s %-35s %-12s %-12s\n" "PROVIDER" "MODEL" "/models" "/chat"
echo "------------------------------------------"

PIDS=()

for i in $(seq 0 $((COUNT - 1))); do
  (
    # 解析第 i 个 provider
    READ=$(python3 -c "
import json, os, sys
d = json.loads('$PROVIDERS')
p = d[$i]
print(p['provider'], p['model'], p['base_url'], p['env_var'])
" 2>/dev/null)

    read -r PROVIDER MODEL BASE_URL ENV_VAR <<< "$READ"

    # 通过变量名取对应的 key
    case "$ENV_VAR" in
      NVIDIA_API_KEY) KEY="$NVIDIA_API_KEY" ;;
      CEREBRAS_API_KEY) KEY="$CEREBRAS_API_KEY" ;;
      GEMINI_API_KEY) KEY="$GEMINI_API_KEY" ;;
      OPENROUTER_API_KEY) KEY="$OPENROUTER_API_KEY" ;;
      GLM_API_KEY) KEY="$GLM_API_KEY" ;;
      AGNES_API_KEY) KEY="$AGNES_API_KEY" ;;
      MINIMAX_API_KEY) KEY="$MINIMAX_API_KEY" ;;
      *) KEY="" ;;
    esac

    if [[ -z "$BASE_URL" || -z "$KEY" ]]; then
      printf "%-25s %-35s %-12s %-12s\n" "$PROVIDER" "${MODEL:0:35}" "⚠️空" "⚠️空"
      exit 0
    fi

    # GET /v1/models
    T1=$(python3 -c 'import time; print(int(time.time()*1000))')
    M_CODE=$(curl -s --max-time 8 -o "$RESULTS_DIR/${PROVIDER}_models.json" \
      -w "%{http_code}" \
      -H "Authorization: Bearer $KEY" \
      "$BASE_URL/models" 2>/dev/null || echo "000")
    T2=$(python3 -c 'import time; print(int(time.time()*1000))')
    M_MS=$((T2 - T1))

    # POST /v1/chat/completions
    T3=$(python3 -c 'import time; print(int(time.time()*1000))')
    C_OUT=$(curl -s --max-time 20 -o "$RESULTS_DIR/${PROVIDER}_chat.json" \
      -w "%{http_code}" \
      -X POST \
      -H "Authorization: Bearer $KEY" \
      -H "Content-Type: application/json" \
      -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"$PING_PROMPT\"}],\"max_tokens\":$MAX_TOKENS}" \
      "$BASE_URL/chat/completions" 2>/dev/null || echo "000")
    T4=$(python3 -c 'import time; print(int(time.time()*1000))')
    C_MS=$((T4 - T3))

    M_SYM="❌"; [[ "$M_CODE" == "200" ]] && M_SYM="✅"
    C_SYM="❌"; [[ "$C_CODE" == "200" ]] && C_SYM="✅"

    printf "%-25s %-35s %-12s %-12s\n" \
      "$PROVIDER" "${MODEL:0:35}" "${M_SYM}(${M_CODE},${M_MS}ms)" "${C_SYM}(${C_CODE:0:3},${C_MS}ms)"

    # 失败时附错误摘要
    if [[ "$C_CODE" != "200" ]]; then
      ERR=$(python3 -c "
import json
try:
    d = json.load(open('$RESULTS_DIR/${PROVIDER}_chat.json'))
    e = d.get('error') or {}
    t = e.get('type','?')
    m = e.get('message','')[:80]
    print(f'    ⚠️  {t}: {m}')
except: pass
" 2>/dev/null)
      echo "$ERR"
    fi
  ) &
  PIDS+=($!)
done

# 等待所有子进程，最多 60 秒
for pid in "${PIDS[@]}"; do
  wait "$pid" 2>/dev/null || true
done

echo "------------------------------------------"
echo "✅ = 200  ❌ = 4xx/5xx/timeout"
echo ""
echo "任何 ❌ → 查 references/provider-token-verification.md"
