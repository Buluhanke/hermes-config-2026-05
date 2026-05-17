---
name: notion
description: "Notion API via curl: pages, databases, blocks, search + 采购系统/供应商跟踪/1688订单同步/老板仪表盘/Obsidian双向同步"
version: 2.0.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Notion, Product Procurement, Supplier Management, 1688, Dashboard, Obsidian Sync]
    homepage: https://developers.notion.com
prerequisites:
  env_vars: [NOTION_API_KEY]
  skills: [note-taking/obsidian]
---

# Notion API

Use the Notion API via curl to create, read, update pages, databases (data sources), and blocks. No extra tools needed — just curl and a Notion API key.

## Prerequisites

1. Create an integration at https://notion.so/my-integrations
2. Copy the API key (starts with `ntn_` or `secret_`)
3. Store it in `~/.hermes/.env`:
   ```
   NOTION_API_KEY=ntn_your_key_here
   ```
4. **Important:** Share target pages/databases with your integration in Notion (click "..." → "Connect to" → your integration name)

## API Basics

All requests use this pattern:

```bash
curl -s -X GET "https://api.notion.com/v1/..." \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json"
```

The `Notion-Version` header is required. This skill uses `2025-09-03` (latest). In this version, databases are called "data sources" in the API.

## Common Operations

### Search

```bash
curl -s -X POST "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"query": "page title"}'
```

### Get Page

```bash
curl -s "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### Get Page Content (blocks)

```bash
curl -s "https://api.notion.com/v1/blocks/{page_id}/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### Create Page in a Database

```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"database_id": "xxx"},
    "properties": {
      "Name": {"title": [{"text": {"content": "New Item"}}]},
      "Status": {"select": {"name": "Todo"}}
    }
  }'
```

### Query a Database

```bash
curl -s -X POST "https://api.notion.com/v1/data_sources/{data_source_id}/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {"property": "Status", "select": {"equals": "Active"}},
    "sorts": [{"property": "Date", "direction": "descending"}]
  }'
```

### Create a Database

```bash
curl -s -X POST "https://api.notion.com/v1/data_sources" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "xxx"},
    "title": [{"text": {"content": "My Database"}}],
    "properties": {
      "Name": {"title": {}},
      "Status": {"select": {"options": [{"name": "Todo"}, {"name": "Done"}]}},
      "Date": {"date": {}}
    }
  }'
```

### Update Page Properties

```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"properties": {"Status": {"select": {"name": "Done"}}}}'
```

### Add Content to a Page

```bash
curl -s -X PATCH "https://api.notion.com/v1/blocks/{page_id}/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "children": [
      {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Hello from Hermes!"}}]}}
    ]
  }'
```

## Property Types

Common property formats for database items:

- **Title:** `{"title": [{"text": {"content": "..."}}]}`
- **Rich text:** `{"rich_text": [{"text": {"content": "..."}}]}`
- **Select:** `{"select": {"name": "Option"}}`
- **Multi-select:** `{"multi_select": [{"name": "A"}, {"name": "B"}]}`
- **Date:** `{"date": {"start": "2026-01-15", "end": "2026-01-16"}}`
- **Checkbox:** `{"checkbox": true}`
- **Number:** `{"number": 42}`
- **URL:** `{"url": "https://..."}`
- **Email:** `{"email": "user@example.com"}`
- **Relation:** `{"relation": [{"id": "page_id"}]}`

## Key Differences in API Version 2025-09-03

- **Databases → Data Sources:** Use `/data_sources/` endpoints for queries and retrieval
- **Two IDs:** Each database has both a `database_id` and a `data_source_id`
  - Use `database_id` when creating pages (`parent: {"database_id": "..."}`)
  - Use `data_source_id` when querying (`POST /v1/data_sources/{id}/query`)
- **Search results:** Databases return as `"object": "data_source"` with their `data_source_id`

## Notes

- Page/database IDs are UUIDs (with or without dashes)
- Rate limit: ~3 requests/second average
- The API cannot set database view filters — that's UI-only
- Use `is_inline: true` when creating data sources to embed them in pages
- Add `-s` flag to curl to suppress progress bars (cleaner output for Hermes)
- Pipe output through `jq` for readable JSON: `... | jq '.results[0].properties'`

---

## 1. 采购数据库模板 (Procurement Database Template)

创建"采购订单"主数据库，关联供应商、产品、价格记录：

### 创建采购订单数据库

```bash
curl -s -X POST "https://api.notion.com/v1/data_sources" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "你的父页面ID"},
    "title": [{"text": {"content": "采购订单"}}],
    "properties": {
      "名称": {"title": {}},
      "供应商": {"select": {"options": [{"name": "供应商A"}, {"name": "供应商B"}, {"name": "供应商C"}]}},
      "产品类别": {"select": {"options": [{"name": "纸箱"}, {"name": "胶带"}, {"name": "气泡膜"}, {"name": "珍珠棉"}]}},
      "订单状态": {"select": {"options": [{"name": "待询价"}, {"name": "询价中"}, {"name": "待下单"}, {"name": "已下单"}, {"name": "已到货"}, {"name": "已完成"}]}},
      "采购数量": {"number": {"format": "number"}},
      "单位": {"select": {"options": [{"name": "个"}, {"name": "卷"}, {"name": "米"}, {"name": "箱"}, {"name": "吨"}]}},
      "单价": {"number": {"format": "dollar"}},
      "总价": {"formula": {"formula": {"type": "number", "expression": "prop(\"采购数量\") * prop(\"单价\")"}}},
      "询价日期": {"date": {}},
      "预计到货": {"date": {}},
      "实际到货": {"date": {}},
      "1688订单号": {"rich_text": []},
      "备注": {"rich_text": []},
      "紧急程度": {"select": {"options": [{"name": "低"}, {"name": "普通"}, {"name": "高"}, {"name": "紧急"}]}},
      "老板审批": {"checkbox": false}
    }
  }'
```

### 常用查询

```bash
# 查询所有待下单订单
curl -s -X POST "https://api.notion.com/v1/data_sources/{数据源ID}/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -d '{"filter": {"property": "订单状态", "select": {"equals": "待下单"}}}'

# 查询紧急采购
curl -s -X POST "https://api.notion.com/v1/data_sources/{数据源ID}/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -d '{"filter": {"and": [{"property": "紧急程度", "select": {"equals": "紧急"}}, {"property": "订单状态", "select": {"does_not_equal": "已完成"}}]}}'
```

### 创建采购订单条目

```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -d '{
    "parent": {"database_id": "你的采购数据库ID"},
    "properties": {
      "名称": {"title": [{"text": {"content": "紧急纸箱采购-深圳仓"}}]},
      "供应商": {"select": {"name": "供应商A"}},
      "产品类别": {"select": {"name": "纸箱"}},
      "订单状态": {"select": {"name": "待询价"}},
      "采购数量": {"number": 500},
      "单位": {"select": {"name": "个"}},
      "询价日期": {"date": {"start": "2026-05-17"}},
      "紧急程度": {"select": {"name": "高"}}
    }
  }'
```

---

## 2. 供应商跟踪数据库 (Supplier Tracking Database)

### 创建供应商数据库

```bash
curl -s -X POST "https://api.notion.com/v1/data_sources" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -d '{
    "parent": {"page_id": "你的父页面ID"},
    "title": [{"text": {"content": "供应商跟踪"}}],
    "properties": {
      "供应商名称": {"title": {}},
      "联系人": {"rich_text": []},
      "电话": {"phone_number": {}},
      "微信": {"rich_text": []},
      "1688店铺": {"url": {}},
      "主营产品": {"multi_select": [{"name": "纸箱"}, {"name": "胶带"}, {"name": "气泡膜"}]},
      "合作状态": {"select": {"options": [{"name": "潜在"}, {"name": "合作中"}, {"name": "暂停"}, {"name": "淘汰"}]}},
      "评分": {"number": {"format": "number", "max": 5}},
      "平均交期(天)": {"number": {"format": "number"}},
      "最低起订量": {"rich_text": []},
      "账期": {"select": {"options": [{"name": "现结"}, {"name": "周结"}, {"name": "月结"}]}},
      "创建日期": {"date": {}},
      "最近联系": {"date": {}},
      "备注": {"rich_text": []}
    }
  }'
```

### 更新供应商联系记录

```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{供应商页面ID}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -d '{
    "properties": {
      "最近联系": {"date": {"start": "2026-05-17"}},
      "合作状态": {"select": {"name": "合作中"}}
    }
  }'
```

---

## 3. 自动同步1688订单 (1688 Order Auto-Sync)

1688没有公开API，需通过浏览器自动化或CSV导入方式同步订单。

### 同步工作流

```
1688我的订单页面（浏览器）
    ↓（手动导出CSV或截图记录）
本地 /tmp/1688-orders.csv
    ↓（Hermes解析处理）
Notion 采购订单数据库
    ↓
老板仪表盘看板
```

### 批量导入1688 CSV到Notion

```bash
# 读取1688订单CSV，批量创建Notion页面
# 假设CSV格式：订单号,供应商,商品,数量,单价,总额,下单时间,状态
while IFS=, read -r order_no supplier product qty price total date status; do
  # 映射1688状态 → Notion状态
  case "$status" in
    待付款) notion_status="待询价" ;;
    待发货) notion_status="待下单" ;;
    已发货) notion_status="已下单" ;;
    已签收) notion_status="已到货" ;;
    已完成) notion_status="已完成" ;;
    *) notion_status="待询价" ;;
  esac

  curl -s -X POST "https://api.notion.com/v1/pages" \
    -H "Authorization: Bearer $NOTION_API_KEY" \
    -H "Notion-Version: 2025-09-03" \
    -d "{
      \"parent\": {\"database_id\": \"你的采购数据库ID\"},
      \"properties\": {
        \"名称\": {\"title\": [{\"text\": {\"content\": \"${product}\"}}]},
        \"供应商\": {\"select\": {\"name\": \"${supplier}\"}},
        \"订单状态\": {\"select\": {\"name\": \"${notion_status}\"}},
        \"采购数量\": {\"number\": ${qty}},
        \"总价\": {\"number\": ${total}},
        \"询价日期\": {\"date\": {\"start\": \"${date}\"}},
        \"1688订单号\": {\"rich_text\": [{\"text\": {\"content\": \"${order_no}\"}}]}
      }
    }"
done < /tmp/1688-orders.csv
```

### 定时同步（Cron）

```bash
# 每天早上9点同步昨日订单
# 0 9 * * * /Users/aimac/scripts/sync-1688-orders.sh >> /Users/aimac/logs/1688-sync.log 2>&1
```

### 1688状态 → Notion状态映射表

| 1688状态 | Notion 订单状态 |
|---------|----------------|
| 待付款 | 待询价 |
| 待发货 | 待下单 |
| 已发货 | 已下单 |
| 运输中 | 已下单 |
| 已签收 | 已到货 |
| 已完成 | 已完成 |
| 已取消 | 已取消 |

---

## 4. 老板仪表盘看板 (Boss Dashboard)

### 查询关键指标

```bash
curl -s -X POST "https://api.notion.com/v1/data_sources/{数据源ID}/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -d '{"page_size": 100}' | jq '{
    总订单数: .results | length,
    待下单: [.results[] | select(.properties.订单状态.select.name == "待下单")] | length,
    已下单: [.results[] | select(.properties.订单状态.select.name == "已下单")] | length,
    已到货: [.results[] | select(.properties.订单状态.select.name == "已到货")] | length,
    紧急订单: [.results[] | select(.properties.紧急程度.select.name == "紧急")] | length,
    待审批: [.results[] | select(.properties.老板审批.checkbox == false and .properties.订单状态.select.name != "已完成")] | length,
    总金额: [.results[] | select(.properties.总价.number != null) | .properties.总价.number] | add
  }'
```

### 老板最关注视图（数据库Filter配置）

| 视图名称 | Filter条件 |
|---------|-----------|
| 待审批 | 老板审批=false, 订单状态≠已完成 |
| 紧急处理 | 紧急程度=紧急, 订单状态≠已完成 |
| 本周新增 | 询价日期>=7天前 |
| 超期未到 | 预计到货<今天, 订单状态=已下单 |

### 添加仪表盘内容

```bash
curl -s -X PATCH "https://api.notion.com/v1/blocks/{仪表盘页面ID}/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -d '{
    "children": [
      {"object": "block", "type": "heading_1", "heading_1": {"rich_text": [{"text": {"content": "📊 老板仪表盘"}}]}},
      {"object": "block", "type": "callout", "callout": {"rich_text": [{"text": {"content": "紧急订单: 3单 | 待审批: 5单 | 本周到货: 12单"}}], "icon": {"emoji": "⚠️"}}},
      {"object": "block", "type": "divider", "divider": {}},
      {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "待询价: 2单 | 待下单: 5单 | 已下单: 8单 | 已到货: 12单 | 总金额: ¥45,230"}}]}}
    ]
  }'
```

---

## 5. Notion ↔ Obsidian 双向同步

Obsidian vault: `~/Obsidian/迅龙贸易/`
同步原则：Notion（采购/供应商/订单）为准数据源，Obsidian为本地参考副本。

### 5a. Notion 供应商 → Obsidian 笔记

```bash
NOTION_SUPPLIER_DB_ID="你的供应商数据库ID"
curl -s -X POST "https://api.notion.com/v1/data_sources/${NOTION_SUPPLIER_DB_ID}/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -d '{"page_size": 100}' | jq -r '.results[] | @base64' | while read -r entry; do
  _jq() { echo "${entry}" | base64 -d | jq -r "$1"; }
  NAME=$(_jq '.properties.供应商名称.title[0].plain_text')
  STATUS=$(_jq '.properties.合作状态.select.name // "未知"')
  CONTACT=$(_jq '.properties.联系人.rich_text[0].plain_text // ""')
  mkdir -p ~/Obsidian/迅龙贸易/供应商/默认供应商
  cat > "~/Obsidian/迅龙贸易/供应商/默认供应商/${NAME}.md" << EOF
---
notion_id: $(_jq '.id')
notion_synced: $(date -u +%Y-%m-%dT%H:%M:%SZ)
---

# ${NAME}

- 合作状态: ${STATUS}
- 联系人: ${CONTACT}

> 自动同步自 Notion 供应商数据库
EOF
done
```

### 5b. Obsidian 笔记 → Notion 供应商

```bash
for file in ~/Obsidian/迅龙贸易/供应商/默认供应商/*.md; do
  NOTION_ID=$(grep -oP 'notion_id: \K[A-Za-z0-9-]+' "$file" 2>/dev/null)
  [[ -z "$NOTION_ID" ]] && continue
  STATUS=$(grep -oP '合作状态: \K.+' "$file")
  curl -s -X PATCH "https://api.notion.com/v1/pages/${NOTION_ID}" \
    -H "Authorization: Bearer $NOTION_API_KEY" \
    -H "Notion-Version: 2025-09-03" \
    -d "{\"properties\": {\"合作状态\": {\"select\": {\"name\": \"${STATUS}\"}}}}"
done
```

### 5c. 1688采购要点同步

```bash
# Obsidian 1688采购要点 → Notion 采购订单备注
CONTENT=$(head -20 ~/Obsidian/迅龙贸易/wiki/concept/1688采购要点.md | tr '\n' ' ' | cut -c1-2000)
curl -s -X POST "https://api.notion.com/v1/data_sources/${NOTION_PROCUREMENT_DB_ID}/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -d '{"filter": {"property": "订单状态", "select": {"equals": "待询价"}}}' | \
  jq -r '.results[].id' | while read -r page_id; do
  curl -s -X PATCH "https://api.notion.com/v1/pages/${page_id}" \
    -H "Authorization: Bearer $NOTION_API_KEY" \
    -H "Notion-Version: 2025-09-03" \
    -d "{\"properties\": {\"备注\": {\"rich_text\": [{\"text\": {\"content\": \"${CONTENT}\"}}]}}}"
done
```

### 5d. 定时同步脚本

创建 `/Users/aimac/scripts/notion-obsidian-sync.sh`：

```bash
#!/bin/bash
NOTION_API_KEY="${NOTION_API_KEY}"
NOTION_SUPPLIER_DB_ID="你的供应商数据库ID"
NOTION_PROCUREMENT_DB_ID="你的采购订单数据库ID"
OBSIDIAN_VAULT="~/Obsidian/迅龙贸易"
LOG_FILE="/Users/aimac/logs/notion-obsidian-sync.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }

log "=== Notion → Obsidian 供应商同步 ==="
curl -s -X POST "https://api.notion.com/v1/data_sources/${NOTION_SUPPLIER_DB_ID}/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -d '{"page_size": 100}' | jq -r '.results[] | @base64' | while read -r entry; do
  _jq() { echo "${entry}" | base64 -d | jq -r "$1"; }
  NAME=$(_jq '.properties.供应商名称.title[0].plain_text')
  mkdir -p "${OBSIDIAN_VAULT}/供应商/默认供应商"
  # 写入 Obsidian...
done

log "=== Obsidian → Notion 供应商同步 ==="
for file in "${OBSIDIAN_VAULT}/供应商/默认供应商"/*.md; do
  # 读取并更新 Notion...
done

log "=== 同步完成 ==="
```

### 同步冲突处理规则

| 场景 | 处理方式 |
|-----|---------|
| Notion 供应商状态变更 | Notion 优先，自动覆盖 Obsidian |
| Obsidian 本地备注变更 | 保留，两地共存 |
| 订单状态冲突 | Notion 审批流优先，Obsidian 标记冲突 |
| 时间戳冲突 | 以较新者为准，记录到 `notion-obsidian-conflicts.md` |
