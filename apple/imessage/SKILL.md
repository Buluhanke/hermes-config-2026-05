---
name: imessage
description: Send and receive iMessages/SMS via the imsg CLI on macOS.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [iMessage, SMS, messaging, macOS, Apple]
prerequisites:
  commands: [imsg]
---

# iMessage

Use `imsg` to read and send iMessage/SMS via macOS Messages.app. Extended with business automation templates for quotes, order updates, and 1688 procurement inquiries.

## Prerequisites

- **macOS** with Messages.app signed in
- Install: `brew install steipete/tap/imsg`
- Grant Full Disk Access for terminal (System Settings → Privacy → Full Disk Access)
- Grant Automation permission for Messages.app when prompted

## When to Use

- User asks to send an iMessage or text message
- Reading iMessage conversation history
- Checking recent Messages.app chats
- Sending to phone numbers or Apple IDs

## When NOT to Use

- Telegram/Discord/Slack/WhatsApp messages → use the appropriate gateway channel
- Group chat management (adding/removing members) → not supported
- Bulk/mass messaging → always confirm with user first

## Quick Reference

### List Chats

```bash
imsg chats --limit 10 --json
```

### View History

```bash
# By chat ID
imsg history --chat-id 1 --limit 20 --json

# With attachments info
imsg history --chat-id 1 --limit 20 --attachments --json
```

### Send Messages

```bash
# Text only
imsg send --to "+14155551212" --text "Hello!"

# With attachment
imsg send --to "+14155551212" --text "Check this out" --file /path/to/image.jpg

# Force iMessage or SMS
imsg send --to "+14155551212" --text "Hi" --service imessage
imsg send --to "+14155551212" --text "Hi" --service sms
```

### Watch for New Messages

```bash
imsg watch --chat-id 1 --attachments
```

## Service Options

- `--service imessage` — Force iMessage (requires recipient has iMessage)
- `--service sms` — Force SMS (green bubble)
- `--service auto` — Let Messages.app decide (default)

## Rules

1. **Always confirm recipient and message content** before sending
2. **Never send to unknown numbers** without explicit user approval
3. **Verify file paths** exist before attaching
4. **Don't spam** — rate-limit yourself

---

## Business Automation Templates

Three business scenarios with ready-to-use message templates. Replace `{{variable}}` placeholders before sending.

---

### (1) 自动报价通知模板 / Auto Quote Notification

Used when you want to proactively send a price quote or quotation to a customer after reviewing their inquiry.

```bash
# Quote notification template variables
QUOTE_ID="QD-20250617-001"
CUSTOMER_NAME="张总"
PRODUCT_NAME="蓝牙耳机 TWS-200"
PRICE="¥128.00"
MOQ="500pcs"
LEAD_TIME="15天"
VALIDITY="7天"

# Full message template
MESSAGE="【报价单】尊敬的 ${CUSTOMER_NAME}，
您的询价已处理，详情如下：

📋 报价单号：${QUOTE_ID}
📦 产品：${PRODUCT_NAME}
💰 单价：${PRICE}
📊 最小起订量：${MOQ}
⏱️ 交期：${LEAD_TIME}
✅ 有效期：${VALIDITY}

如有任何疑问，欢迎随时联系。"

imsg send --to "{{recipient_phone}}" --text "$MESSAGE"
```

**Use when:**
- Customer submitted an inquiry and you want to proactively send a quote
- Price has been finalized and needs customer confirmation
- After a sales discussion where you committed to sending pricing

---

### (2) 订单状态推送 / Order Status Push

Used to proactively update customers on their order progress — from confirmation through shipping.

```bash
# Order status template variables
ORDER_ID="ORD-20250617-001"
CUSTOMER_NAME="李总"
STATUS="生产中"  # Options: 已确认/生产中/已发货/已到达/已完成
PROGRESS="60%"
ETA="2025-06-25"

# Status messages per stage
case "$STATUS" in
  "已确认")
    MESSAGE="【订单通知】尊敬的 ${CUSTOMER_NAME}，您的订单 ${ORDER_ID} 已确认，我们将尽快安排生产，感谢您的信任！"
    ;;
  "生产中")
    MESSAGE="【订单通知】尊敬的 ${CUSTOMER_NAME}，订单 ${ORDER_ID} 生产进度：${PROGRESS}，预计 ${ETA} 前完成。"
    ;;
  "已发货")
    MESSAGE="【订单通知】尊敬的 ${CUSTOMER_NAME}，订单 ${ORDER_ID} 已发货！预计 ${ETA} 送达，请保持手机畅通。"
    ;;
  "已到达")
    MESSAGE="【订单通知】尊敬的 ${CUSTOMER_NAME}，订单 ${ORDER_ID} 已到达您所在城市，派送员将尽快联系您签收。"
    ;;
  "已完成")
    MESSAGE="【订单通知】尊敬的 ${CUSTOMER_NAME}，订单 ${ORDER_ID} 已完成签收，感谢您的支持！如有任何问题请随时联系我们。"
    ;;
esac

imsg send --to "{{recipient_phone}}" --text "$MESSAGE"
```

**Use when:**
- Order has been confirmed by the factory
- Production milestone reached (50%, 80%, complete)
- Package has been shipped with tracking info
- Package arrived at local delivery hub
- Customer confirmed receipt

---

### (3) 1688询价自动发送 / 1688 Inquiry Auto-Send

Used when you need to send an inquiry to a 1688 supplier. Typically triggered after finding a product you want to quote to your own customer.

```bash
# 1688 inquiry template variables
SUPPLIER_NAME="深圳某某科技有限公司"
PRODUCT_NAME="无线蓝牙耳机"
SPEC="蓝牙5.2，支持降噪，黑色"
QTY="1000pcs"
TARGET_PRICE="¥85.00/pcs"
PAYMENT_TERM="月结30天"
REMARK="需要提供样品，请报FOB深圳价"

# Full inquiry message
MESSAGE="您好 ${SUPPLIER_NAME}，
我是某某公司的采购专员，想咨询以下产品：

📦 产品：${PRODUCT_NAME}
🔧 规格：${SPEC}
📊 数量：${QTY}
💰 目标价：${TARGET_PRICE}
💳 付款方式：${PAYMENT_TERM}
📝 备注：${REMARK}

请问贵司能做吗？期待您的回复，谢谢！"

imsg send --to "{{supplier_phone}}" --text "$MESSAGE"
```

**Use when:**
- You found a product on 1688 and need to quickly send an inquiry to the supplier
- You want to get supplier pricing to prepare a quote for your own customer
- Following up on a previous inquiry that didn't get response
- Requesting samples or prototype pricing

---

## Example Workflow

User: "Text mom that I'll be late"

```bash
# 1. Find mom's chat
imsg chats --limit 20 --json | jq '.[] | select(.displayName | contains("Mom"))'

# 2. Confirm with user: "Found Mom at +1555123456. Send 'I'll be late' via iMessage?"

# 3. Send after confirmation
imsg send --to "+1555123456" --text "I'll be late"
```
