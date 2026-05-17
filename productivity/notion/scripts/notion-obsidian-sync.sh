#!/bin/bash
# Notion ↔ Obsidian 双向同步脚本
# 用法: ./notion-obsidian-sync.sh
# 依赖: jq, curl, NOTION_API_KEY

set -euo pipefail

NOTION_API_KEY="${NOTION_API_KEY:?请设置 NOTION_API_KEY 环境变量}"
NOTION_SUPPLIER_DB_ID="${NOTION_SUPPLIER_DB_ID:?请设置供应商数据库ID}"
NOTION_PROCUREMENT_DB_ID="${NOTION_PROCUREMENT_DB_ID:?请设置采购订单数据库ID}"
OBSIDIAN_VAULT="/Users/aimac/Obsidian/迅龙贸易"
LOG_FILE="/Users/aimac/logs/notion-obsidian-sync.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }
safe_jq() { echo "$1" | base64 -d | jq -r "$2" 2>/dev/null || echo ""; }

# ============================================================
# 阶段1: Notion 供应商 → Obsidian 笔记（单向推送）
# ============================================================
log "=== 阶段1: Notion → Obsidian 供应商同步 ==="

mkdir -p "${OBSIDIAN_VAULT}/供应商/默认供应商"

curl -s -X POST "https://api.notion.com/v1/data_sources/${NOTION_SUPPLIER_DB_ID}/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -d '{"page_size": 100}' | jq -r '.results[] | @base64' | while read -r entry; do
  NAME=$(safe_jq "$entry" '.properties.供应商名称.title[0].plain_text')
  [[ -z "$NAME" ]] && continue

  STATUS=$(safe_jq "$entry" '.properties.合作状态.select.name') || echo "未知"
  CONTACT=$(safe_jq "$entry" '.properties.联系人.rich_text[0].plain_text') || echo ""
  PHONE=$(safe_jq "$entry" '.properties.电话.phone_number') || echo ""
  WECHAT=$(safe_jq "$entry" '.properties.微信.rich_text[0].plain_text') || echo ""
  SCORE=$(safe_jq "$entry" '.properties.评分.number') || echo ""
  NOTE=$(safe_jq "$entry" '.properties.备注.rich_text[0].plain_text') || echo ""
  NOTION_ID=$(safe_jq "$entry" '.id')

  cat > "${OBSIDIAN_VAULT}/供应商/默认供应商/${NAME}.md" << EOF
---
notion_id: ${NOTION_ID}
notion_synced: $(date -u +%Y-%m-%dT%H:%M:%SZ)
---

# ${NAME}

- 合作状态: ${STATUS}
- 联系人: ${CONTACT}
- 电话: ${PHONE}
- 微信: ${WECHAT}
- 评分: ${SCORE}/5
- 备注: ${NOTE}

> 自动同步自 Notion 供应商数据库
EOF
  log "  已同步供应商: $NAME"
done

# ============================================================
# 阶段2: Obsidian 笔记 → Notion 供应商（回写状态变更）
# ============================================================
log "=== 阶段2: Obsidian → Notion 供应商回写 ==="

for file in "${OBSIDIAN_VAULT}/供应商/默认供应商"/*.md; do
  [[ ! -f "$file" ]] && continue
  NOTION_ID=$(grep -oP 'notion_id: \K[A-Za-z0-9-]+' "$file" 2>/dev/null) || continue
  STATUS=$(grep -oP '合作状态: \K.+' "$file" | head -1) || continue
  STATUS=$(echo "$STATUS" | xargs)
  [[ -z "$STATUS" ]] && continue

  log "  回写供应商状态: notion_id=${NOTION_ID}, status=${STATUS}"
  curl -s -X PATCH "https://api.notion.com/v1/pages/${NOTION_ID}" \
    -H "Authorization: Bearer $NOTION_API_KEY" \
    -H "Notion-Version: 2025-09-03" \
    -H "Content-Type: application/json" \
    -d "{\"properties\": {\"合作状态\": {\"select\": {\"name\": \"${STATUS}\"}}}}" \
    | jq -r '.id // .message' || true
done

# ============================================================
# 阶段3: 1688采购要点 → Notion 待询价订单备注
# ============================================================
log "=== 阶段3: 1688采购要点同步到Notion ==="

if [[ -f "${OBSIDIAN_VAULT}/wiki/concept/1688采购要点.md" ]]; then
  CONTENT=$(head -30 "${OBSIDIAN_VAULT}/wiki/concept/1688采购要点.md" | sed 's/"/\\"/g' | tr '\n' ' ' | cut -c1-2000)
  CONTENT="${CONTENT//\'/}"

  curl -s -X POST "https://api.notion.com/v1/data_sources/${NOTION_PROCUREMENT_DB_ID}/query" \
    -H "Authorization: Bearer $NOTION_API_KEY" \
    -H "Notion-Version: 2025-09-03" \
    -d '{"filter": {"property": "订单状态", "select": {"equals": "待询价"}}}' | \
    jq -r '.results[].id' | while read -r page_id; do
    [[ -z "$page_id" ]] && continue
    curl -s -X PATCH "https://api.notion.com/v1/pages/${page_id}" \
      -H "Authorization: Bearer $NOTION_API_KEY" \
      -H "Notion-Version: 2025-09-03" \
      -H "Content-Type: application/json" \
      -d "{\"properties\": {\"备注\": {\"rich_text\": [{\"text\": {\"content\": \"${CONTENT}\"}}]}}}" > /dev/null || true
  done
  log "  1688采购要点已同步到所有待询价订单"
fi

# ============================================================
# 阶段4: 老板偏好同步到仪表盘
# ============================================================
log "=== 阶段4: 老板偏好 → Notion 仪表盘 ==="

if [[ -f "${OBSIDIAN_VAULT}/老板/偏好/偏好.md" ]]; then
  BOSS_CONTENT=$(head -10 "${OBSIDIAN_VAULT}/老板/偏好/偏好.md" | sed 's/"/\\"/g' | tr '\n' ' ' | cut -c1-500)
  BOSS_CONTENT="${BOSS_CONTENT//\'/}"
  DASHBOARD_PAGE_ID="${NOTION_DASHBOARD_PAGE_ID:-}"

  if [[ -n "$DASHBOARD_PAGE_ID" ]]; then
    curl -s -X PATCH "https://api.notion.com/v1/blocks/${DASHBOARD_PAGE_ID}/children" \
      -H "Authorization: Bearer $NOTION_API_KEY" \
      -H "Notion-Version: 2025-09-03" \
      -H "Content-Type: application/json" \
      -d "{\"children\": [{\"object\": \"block\", \"type\": \"callout\", \"callout\": {\"rich_text\": [{\"text\": {\"content\": \"老板偏好(${date}): ${BOSS_CONTENT}\"}}], \"icon\": {\"emoji\": \"👔\"}}}]}" > /dev/null || true
    log "  老板偏好已追加到仪表盘"
  fi
fi

log "=== 同步完成 ==="
