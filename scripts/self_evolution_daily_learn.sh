#!/bin/bash
# self_evolution_daily_learn.sh — 每日自我学习块
# v2.1 — 2026-07-17
# 重写: 基于真实 Hermes 架构 (MEMORY.md 非 facts 表)
# 功能:
#   A. 抓 AI 资讯 → 追加到 MEMORY.md
#   B. 记录 Hermes 能力状态 → 追加到 MEMORY.md

set -uo pipefail

HERMES_HOME="${HOME:-/Users/kk}/.hermes"
HERMES="$HERMES_HOME/hermes-agent/venv/bin/hermes"
MEMORY_FILE="$HERMES_HOME/memories/MEMORY.md"
LOG="$HERMES_HOME/logs/self_evolution.log"
TMP_PY="/tmp/self_evolution_ai_brief_$$.py"
mkdir -p "$(dirname $LOG)"

log() { echo "$(date '+%m-%d %H:%M:%S') [daily-learn] $1"; }

# ── 辅助: 安全追加到 MEMORY.md ──────────────────────────────
# macOS 无 flock，用 set -C (noclobber) + >> 追加写入
append_memory() {
    local category="$1"
    local content="$2"
    local tag="$3"
    local entry="
§

## [$category] $(date '+%Y-%m-%d')

$content

_tags: ${tag}
"
    set -C
    {
        echo "$entry" >> "$MEMORY_FILE"
    } 2>/dev/null
    set +C
}

# ── A. AI 资讯抓取 ─────────────────────────────────────────
log "🅰️ 抓 AI 资讯..."

cat > "$TMP_PY" <<'PYEOF'
import urllib.request, ssl, json, re, sys
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
try:
    req = urllib.request.Request(
        "https://www.v2ex.com/api/topics/latest.json?node_name=AI",
        headers={"User-Agent": "curl/7.68.0"}
    )
    with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
        topics = json.loads(r.read())
    items = []
    for t in topics[:5]:
        title = re.sub(r'<[^>]+>', '', t.get('title', ''))
        items.append("- " + title)
    print("\n".join(items) if items else "")
except Exception as e:
    print("AI资讯获取失败: " + str(e), file=sys.stderr)
    sys.exit(1)
PYEOF

AI_BRIEF=$("$HERMES_HOME/hermes-agent/venv/bin/python" "$TMP_PY" 2>/dev/null)
rm -f "$TMP_PY"

if [ -n "$AI_BRIEF" ] && [ ${#AI_BRIEF} -gt 20 ]; then
    append_memory "AI圈24h动态" "$AI_BRIEF" "ai_news_daily,self_learning"
    log "  ✅ AI资讯已落 MEMORY.md (${#AI_BRIEF}字节)"
else
    log "  ⚠ AI资讯抓取失败或内容过短: ${#AI_BRIEF}字节"
fi

# ── B. Hermes 能力状态快照 ────────────────────────────────
log "🅱️ 查 Hermes 能力状态..."
CAPTURE=$("$HERMES" status 2>/dev/null | head -20 || echo "(hermes status 失败)")
if [ -n "$CAPTURE" ]; then
    append_memory "Hermes能力状态" "$CAPTURE" "hermes_status_daily,capability"
    log "  ✅ 能力状态已落 MEMORY.md"
else
    log "  ⚠ hermes status 无输出"
fi

log "✅ 自我学习块完成"
