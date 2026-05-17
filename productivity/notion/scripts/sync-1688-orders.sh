# 1688订单同步脚本
# 用法: ./sync-1688-orders.sh /path/to/1688-orders.csv
# 依赖: jq, curl, NOTION_API_KEY 环境变量

set -euo pipefail

NOTION_API_KEY="${NOTION_API_KEY:?请设置 NOTION_API_KEY 环境变量}"
PROCUREMENT_DB_ID="${NOTION_PROCUREMENT_DB_ID:?请设置 PROCUREMENT_DB_ID 环境变量}"
LOG_FILE="${LOG_FILE:-/Users/aimac/logs/1688-sync.log}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }

CSV_FILE="${1:-/tmp/1688-orders.csv}"
[[ ! -f "$CSV_FILE" ]] && { log "错误: CSV文件不存在: $CSV_FILE"; exit 1; }

log "开始同步1688订单: $CSV_FILE"

while IFS=, read -r order_no supplier product qty price total date status; do
  # 跳过表头
  [[ "$order_no" == "订单号" ]] && continue

  # 映射1688状态 → Notion状态
  case "$status" in
    待付款)   notion_status="待询价" ;;
    待发货)   notion_status="待下单" ;;
    已发货)   notion_status="已下单" ;;
    运输中)   notion_status="已下单" ;;
    已签收)   notion_status="已到货" ;;
    已完成)   notion_status="已完成" ;;
    已取消)   notion_status="已取消" ;;
    *)        notion_status="待询价" ;;
  esac

  # 替换空值为0
  qty="${qty:-0}"; total="${total:-0}"

  log "同步订单: $order_no | $product | $notion_status"

  curl -s -X POST "https://api.notion.com/v1/pages" \
    -H "Authorization: Bearer $NOTION_API_KEY" \
    -H "Notion-Version: 2025-09-03" \
    -H "Content-Type: application/json" \
    -d "{
      \"parent\": {\"database_id\": \"$PROCUREMENT_DB_ID\"},
      \"properties\": {
        \"名称\": {\"title\": [{\"text\": {\"content\": \"$product\"}}]},
        \"供应商\": {\"select\": {\"name\": \"$supplier\"}},
        \"订单状态\": {\"select\": {\"name\": \"$notion_status\"}},
        \"采购数量\": {\"number\": $qty},
        \"总价\": {\"number\": $total},
        \"询价日期\": {\"date\": {\"start\": \"$date\"}},
        \"1688订单号\": {\"rich_text\": [{\"text\": {\"content\": \"$order_no\"}}]}
      }
    }" | jq -r '.id // .message' || true

done < "$CSV_FILE"

log "1688订单同步完成"
