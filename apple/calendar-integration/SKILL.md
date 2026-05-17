# Calendar Integration Skill

Complements `apple-reminders` — bridges Hermite AI's procurement tracking with macOS/iOS calendars for zero-miss deadline management.

---

## Core Capabilities

- Convert procurement milestones (RFQ, payment, delivery) into native calendar events
- Bi-directional sync with Mac Calendar.app and iPhone via iCloud
- n8n workflow automation for calendar event creation/updates
- Reusable event templates for common procurement scenarios

---

## 1. Procurement Key Date Calendar化

### Supported Date Types

| Type | Trigger | Default Reminder |
|------|---------|-----------------|
| `rfq_deadline` | 询价截止日期 | 3 days before |
| `payment_due` | 付款到期日 | 7 days before |
| `delivery_expected` | 预计到货日期 | 2 days before |
| `contract_expiry` | 合同到期 | 30 days before |
| `follow_up` | 跟进节点 | 1 day before |

### Calendar化 Flow

```
User prompt → Hermes analyzes dates → Creates Calendar.app event → Sets alert
```

### Implementation

```
Command: "把供应商 XYZ 的付款日期 5/25 加进日历，提前一周提醒"
→ Extract: payment_due, 2025-05-25, supplier=XYZ
→ Create event: "付款提醒 - XYZ" with alert 7 days prior
→ Output: Event link / confirmation
```

---

## 2. Mac/iPhone 日历同步

### Architecture

```
Mac Calendar.app ←→ iCloud ←→ iPhone Calendar
       ↑
   AppleScript / EventKit
       ↑
Hermes Agent
```

### iCloud Calendar Setup

- Calendar name: `Hermes Procurement`
- Subscribed automatically on Mac/iPhone when iCloud signed in
- Color code: Orange for payment, Blue for delivery, Red for urgent

### Calendar.app Event Creation (AppleScript)

```applescript
tell application "Calendar"
    tell calendar "Hermes Procurement"
        set newEvent to make new event with properties ¬
            {summary:"付款提醒 - [Supplier]", ¬
             start date:date "[Date]", ¬
             end date:date "[Date]", ¬
             description:"采购付款提醒\n供应商: [Supplier]\n金额: [Amount]\n备注: [Notes]", ¬
             allday events:true}
        
        -- Set reminder
        tell newEvent
            make new reminder at end of reminders with properties ¬
                {trigger interval:-604800, message:"付款到期前7天"} -- 7 days = 604800 sec
        end tell
    end tell
end tell
```

### macOS Calendar via CalendarKit (Programmatic)

For direct EventKit integration without AppleScript:

```swift
import EventKit

class CalendarManager {
    let eventStore = EKEventStore()
    
    func createProcurementEvent(
        title: String,
        date: Date,
        notes: String,
        reminderInterval: TimeInterval
    ) -> String? {
        let event = EKEvent(eventStore: eventStore)
        event.title = title
        event.startDate = date
        event.endDate = Calendar.current.date(byAdding: .hour, value: 1, to: date)
        event.notes = notes
        event.calendar = eventStore.defaultCalendarForNewEvents
        
        // Add alarm
        let alarm = EKAlarm(relativeOffset: -reminderInterval)
        event.addAlarm(alarm)
        
        do {
            try eventStore.save(event, span: .thisEvent)
            return event.eventIdentifier
        } catch {
            return nil
        }
    }
}
```

### iPhone Sync

- Events propagate via iCloud automatically
- No separate iPhone app required
- Works with any iCloud-signed iOS device

---

## 3. n8n 工作流触发日历事件

### n8n Calendar Node

Use `n8n-nodes-calendar` or native HTTP Request to Apple Calendar API.

### n8n Workflow: Procurement → Calendar Event

```
[Webhook Trigger] 
      ↓
[Parse JSON: supplier, date, type, amount]
      ↓
[Switch: type]
  ├── rfq_deadline  → [Create Event: RFQ截止提醒]
  ├── payment_due   → [Create Event: 付款到期提醒]
  └── delivery      → [Create Event: 到货提醒]
      ↓
[Send Notification to Hermes]
```

### n8n HTTP Request Node (Apple Calendar Server)

```json
POST https://caldav.icloud.com/[calendar-uuid]/VEVENT
Authorization: Basic [base64(user:password)]
Content-Type: text/calendar; charset=utf-8

BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Hermes Procurement//EN
BEGIN:VEVENT
UID:[uuid]@hermes
DTSTAMP:[ISO timestamp]
DTSTART;VALUE=DATE:[YYYYMMDD]
SUMMARY:[Event Title]
DESCRIPTION:[Description]
BEGIN:VALARM
TRIGGER:-P7D
ACTION:DISPLAY
DESCRIPTION:[Reminder text]
END:VALARM
END:VEVENT
END:VCALENDAR
```

### n8n Sub-Workflow: Calendar Event Update

```
[Calendar Update Trigger]
      ↓
[Find existing event by UID]
      ↓
[Update: new date / new reminder]
      ↓
[Delete old event if date changed]
      ↓
[Create new event at updated date]
      ↓
[Notify via Hermes]
```

### n8n Expression Examples

```
# Extract date from procurement record
{{ $json.orderDate }}
{{ $json.supplier }}
{{ $json.amount }}

# Calculate reminder date (7 days before)
{{ new Date($json.paymentDue).addDays(-7) }}

# Format for iCalendar
{{ $now.format('YYYYMMDD') }}
```

---

## 4. 日历事件模板

### Template Store

All templates live in `~/.hermes/skills/apple/calendar-integration/templates/`

### Payment Reminder Template

```
Title: 付款提醒 - {supplier}
Date: {payment_date}
All Day: true
Alert: 7 days before
Notes:
---
供应商: {supplier}
采购单号: {po_number}
金额: {currency} {amount}
付款方式: {payment_method}
银行账户: {bank_account}
备注: {notes}
---
```

### RFQ Deadline Template

```
Title: 询价截止 - {project_name}
Date: {rfq_deadline}
All Day: true
Alert: 3 days before
Notes:
---
项目: {project_name}
询价单号: {rfq_number}
供应商数量: {supplier_count}
预算: {currency} {budget}
技术要求: {requirements_summary}
---
```

### Delivery Expected Template

```
Title: 到货预期 - {po_number}
Date: {expected_delivery}
All Day: true
Alert: 2 days before
Notes:
---
采购单: {po_number}
供应商: {supplier}
货物描述: {items}
物流号: {tracking_number}
仓库: {warehouse_location}
---
```

### Follow-up Reminder Template

```
Title: 跟进 - {topic}
Date: {follow_up_date}
Time: {follow_up_time}
Alert: 1 day before
Notes:
---
类型: {follow_up_type}
关联单号: {reference_number}
负责人: {owner}
待确认事项: {pending_items}
---
```

### Contract Expiry Template

```
Title: 合同到期 - {contract_name}
Date: {expiry_date}
All Day: true
Alert: 30 days before, 7 days before
Notes:
---
合同编号: {contract_number}
签约方: {counterparty}
合同金额: {currency} {value}
续约条款: {renewal_terms}
---
```

---

## Usage Examples

### Create Event from User Prompt

```
User: "把供应商顺发电子的付款日6月15号加入日历，提前一周提醒"
→ Parse: { supplier: "顺发电子", date: 2025-06-15, type: payment_due, reminder: 7 }
→ Generate event from payment template
→ Execute AppleScript / EventKit call
→ Return: "已添加：付款提醒 - 顺发电子 (6月15日) - 提前7天提醒"
```

### Batch Import from CSV

```
User: "把这批订单的到货日期批量导入日历"
→ Parse CSV with columns: po_number, supplier, delivery_date, items
→ Generate one event per row using delivery template
→ Execute batch insert
→ Return: summary of created events
```

### n8n Integration

```
External procurement system → n8n webhook → Calendar event
```

---

## Related Skills

- `apple-reminders` — Complementary reminder/Task management
- `n8n-automation` — Workflow automation patterns