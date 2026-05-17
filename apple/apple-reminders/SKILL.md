---
name: apple-reminders
description: "Apple Reminders via remindctl: add, list, complete."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Reminders, tasks, todo, macOS, Apple]
prerequisites:
  commands: [remindctl]
---

# Apple Reminders

Use `remindctl` to manage Apple Reminders directly from the terminal. Tasks sync across all Apple devices via iCloud.

## Prerequisites

- **macOS** with Reminders.app
- Install: `brew install steipete/tap/remindctl`
- Grant Reminders permission when prompted
- Check: `remindctl status` / Request: `remindctl authorize`

## When to Use

- User mentions "reminder" or "Reminders app"
- Creating personal to-dos with due dates that sync to iOS
- Managing Apple Reminders lists
- User wants tasks to appear on their iPhone/iPad

## When NOT to Use

- Scheduling agent alerts → use the cronjob tool instead
- Calendar events → use Apple Calendar or Google Calendar
- Project task management → use GitHub Issues, Notion, etc.
- If user says "remind me" but means an agent alert → clarify first

## Quick Reference

### View Reminders

```bash
remindctl                    # Today's reminders
remindctl today              # Today
remindctl tomorrow           # Tomorrow
remindctl week               # This week
remindctl overdue            # Past due
remindctl all                # Everything
remindctl 2026-01-04         # Specific date
```

### Manage Lists

```bash
remindctl list               # List all lists
remindctl list Work          # Show specific list
remindctl list Projects --create    # Create list
remindctl list Work --delete        # Delete list
```

### Create Reminders

```bash
remindctl add "Buy milk"
remindctl add --title "Call mom" --list Personal --due tomorrow
remindctl add --title "Meeting prep" --due "2026-02-15 09:00"
```

### Complete / Delete

```bash
remindctl complete 1 2 3          # Complete by ID
remindctl delete 4A83 --force     # Delete by ID
```

### Output Formats

```bash
remindctl today --json       # JSON for scripting
remindctl today --plain      # TSV format
remindctl today --quiet      # Counts only
```

## Date Formats

Accepted by `--due` and date filters:
- `today`, `tomorrow`, `yesterday`
- `YYYY-MM-DD`
- `YYYY-MM-DD HH:mm`
- ISO 8601 (`2026-01-04T12:34:56Z`)

## Rules

1. When user says "remind me", clarify: Apple Reminders (syncs to phone) vs agent cronjob alert
2. Always confirm reminder content and due date before creating
3. Use `--json` for programmatic parsing

---

## 采购流程提醒模板

### 采购阶段提醒链

采购流程有多个关键时间节点，每个节点需要对应的 Apple Reminders 提醒：

```bash
# 采购需求发起
remindctl add --title "【采购】提交 ${商品名称} 需求单" --list 采购流程 --due "${下单日期}"
remindctl add --title "【采购】供应商报价确认" --list 采购流程 --due "${报价截止日}"
remindctl add --title "【采购】合同签署" --list 采购流程 --due "${签约日期}"
remindctl add --title "【采购】预付款支付" --list 采购流程 --due "${付款日期}"
remindctl add --title "【采购】收货验收" --list 采购流程 --due "${到货日期}"
remindctl add --title "【采购】尾款结算" --list 采购流程 --due "${结算日期}"
```

### 快速创建采购提醒

| 场景 | 命令模板 |
|------|---------|
| 新建采购需求 | `remindctl add --title "【采购】${商品} 需求发起" --list 采购流程 --due ${date}` |
| 报价截止前1天 | `remindctl add --title "【采购】${供应商} 报价截止提醒" --list 采购流程 --due ${date -1d}` |
| 合同签署 | `remindctl add --title "【采购】${供应商} 合同待签署" --list 采购流程 --due ${sign_date}` |
| 付款到期 | `remindctl add --title "【采购】${订单号} 付款到期" --list 采购流程 --due ${pay_date}` |
| 到货验收 | `remindctl add --title "【采购】${商品} 到货待验收" --list 采购流程 --due ${arrive_date}` |

### 采购 List 创建

```bash
remindctl list 采购流程 --create
# 添加备注标签（通过重复创建不同阶段 list）
remindctl list 采购-报价 --create
remindctl list 采购-合同 --create
remindctl list 采购-付款 --create
```

---

## 供应商跟进提醒

### 供应商管理四阶段

```bash
# 第一阶段：初次接触后 3 天跟进
remindctl add --title "【供应商】跟进 ${供应商名} 初次接触" --list 供应商跟进 --due "today"
remindctl add --title "【供应商】确认 ${供应商名} 样品需求" --list 供应商跟进 --due "tomorrow"

# 第二阶段：每周定期检查
remindctl add --title "【供应商】检查 ${供应商名} 交货状态" --list 供应商跟进 --due "friday"

# 第三阶段：月度评估
remindctl add --title "【供应商】${供应商名} 本月绩效评估" --list 供应商跟进 --due "${last_day_of_month}"

# 第四阶段：季度复盘
remindctl add --title "【供应商】${供应商名} 季度合作复盘" --list 供应商跟进 --due "${quarter_end}"
```

### 供应商 List 初始化

```bash
remindctl list 供应商跟进 --create
remindctl list 供应商池 --create
```

### 供应商分级提醒策略

| 供应商等级 | 跟进频率 | 提醒提前量 |
|-----------|---------|-----------|
| A级（战略合作） | 每周 | 到期前 3 天 |
| B级（优选供应商） | 每两周 | 到期前 5 天 |
| C级（备选供应商） | 每月 | 到期前 7 天 |

```bash
# A级供应商每周跟进
remindctl add --title "【A级】${供应商名} 周度跟进" --list 供应商-A级 --due "every monday 09:00"

# B级供应商每两周跟进
remindctl add --title "【B级】${供应商名} 双周跟进" --list 供应商-B级 --due "biweekly"

# C级供应商月度跟进
remindctl add --title "【C级】${供应商名} 月度跟进" --list 供应商-C级 --due "monthly"
```

---

## 自动到期提醒

### 到期前自动提醒机制

使用 `remindctl` 结合 macOS cron 或 launchd 实现自动到期提醒：

```bash
# 创建到期提醒 cron 脚本
cat > ~/bin/reminder-check.sh << 'EOF'
#!/bin/bash
source ~/.hermes/env.sh

# 检查今天到期的采购订单
echo "=== 今日到期提醒 ==="
remindctl today --plain | grep "【采购】" || echo "今日无采购到期"

# 检查即将到期（3天内）
echo ""
echo "=== 3天内即将到期 ==="
remindctl all --json | jq -r '.[] | select(.dueDate != null) | select(.dueDate | contains("2026-05-20") or contains("2026-05-21") or contains("2026-05-22")) | .title'

# 检查已逾期
echo ""
echo "=== 已逾期提醒 ==="
remindctl overdue --plain || echo "无逾期项"
EOF

chmod +x ~/bin/reminder-check.sh

# 添加到 crontab（每天 08:00 检查）
# crontab -e 添加：
# 0 8 * * * ~/bin/reminder-check.sh >> ~/logs/reminder-check.log 2>&1
```

### 到期提醒自动化模板

```bash
# 函数：创建带递归提醒的到期提醒
create_due_reminder() {
  local title="$1"
  local due_date="$2"
  local list="${3:-默认}"
  local early_days="${4:-3}"

  # 主提醒（到期当天）
  remindctl add --title "$title" --list "$list" --due "$due_date"

  # 提前提醒（提前 N 天）
  local early_date=$(date -j -v+${early_days}d -f "%Y-%m-%d" "$due_date" +%Y-%m-%d 2>/dev/null || \
    date -d "$due_date +$early_days days" +%Y-%m-%d)
  remindctl add --title "【提前】$title" --list "$list" --due "$early_date"

  # 逾期检查（到期后第2天仍显示）
  remindctl add --title "【逾期】$title" --list "$list" --due "$(date -d "$due_date +2 days" +%Y-%m-%d)"
}

# 使用示例
create_due_reminder "【采购】样品检测报告提交" "2026-05-25" "采购流程" 3
create_due_reminder "【供应商】季度合同续签" "2026-06-30" "供应商跟进" 7
```

### 到期状态检查脚本

```bash
#!/bin/bash
# remind-due-status.sh — 检查到期状态并输出摘要

TODAY=$(date +%Y-%m-%d)
TOMORROW=$(date -v+1d +%Y-%m-%d 2>/dev/null || date -d "+1 day" +%Y-%m-%d)

echo "=== 今日到期 (${TODAY}) ==="
remindctl all --json 2>/dev/null | jq -r --arg today "$TODAY" \
  '.[] | select(.dueDate != null) | select(.dueDate | startswith($today)) | "✓ " + .title' 2>/dev/null || \
  remindctl today --plain

echo ""
echo "=== 明日到期 (${TOMORROW}) ==="
remindctl all --json 2>/dev/null | jq -r --arg tomorrow "$TOMORROW" \
  '.[] | select(.dueDate != null) | select(.dueDate | startswith($tomorrow)) | "→ " + .title' 2>/dev/null

echo ""
echo "=== 逾期项目 ==="
remindctl overdue --plain || echo "无"

echo ""
echo "=== 本周待办 ==="
remindctl week --plain
```

---

## n8n 集成

### 架构概览

```
n8n Schedule/Webhook → Apple Reminders 同步
Hermes Agent → n8n API → 创建/更新 Reminders
Apple Reminders → iCloud → 所有 Apple 设备同步
```

### n8n 创建采购提醒工作流

在 n8n Editor UI 中创建以下工作流：

```
Schedule Trigger (每天 08:00)
  → Code (生成采购提醒数据)
  → HTTP Request (调用 Hermes MCP 执行 remindctl)
  → Respond to Webhook
```

**Code 节点生成提醒**：
```javascript
// n8n Code 节点 - 生成采购到期提醒
const dueDates = [
  { title: "【采购】样品检测报告提交", days: 7, list: "采购流程" },
  { title: "【采购】供应商报价确认", days: 3, list: "采购流程" },
  { title: "【供应商】${supplierName} 周度跟进", days: 1, list: "供应商-A级" }
];

const reminders = dueDates.map(item => {
  const dueDate = new Date();
  dueDate.setDate(dueDate.getDate() + item.days);
  return {
    title: item.title,
    dueDate: dueDate.toISOString().split('T')[0],
    list: item.list
  };
});

return reminders.map(r => ({ json: r }));
```

### Hermes 调用 n8n 创建 Reminders

当 Hermes 执行任务完成后，通过 n8n API 记录到 Apple Reminders：

```python
# Hermes Task 完成 → n8n 同步到 Apple Reminders
import requests, subprocess, json

N8N_API_KEY = "eyJhbGciOiJI..."
N8N_BASE = "http://localhost:5678"

def create_reminder_via_n8n(title: str, due_date: str, list_name: str = "默认"):
    """
    通过 n8n Webhook 触发 Apple Reminders 创建
    n8n 工作流：Webhook → Code(构建remindctl命令) → Execute Command
    """
    payload = {
        "action": "add_reminder",
        "title": title,
        "due": due_date,
        "list": list_name
    }
    resp = requests.post(
        f"{N8N_BASE}/webhook/hermes-reminder",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    return resp.status_code == 200

def create_reminder_direct(title: str, due_date: str, list_name: str = "默认"):
    """
    Hermes 直接执行 remindctl 创建提醒
    """
    cmd = ["remindctl", "add", "--title", title, "--due", due_date]
    if list_name != "默认":
        cmd.extend(["--list", list_name])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

# 使用示例
create_reminder_direct(
    "【采购】1688订单 PO-2026-001 到货提醒",
    "2026-05-25",
    "采购流程"
)
```

### n8n Webhook 触发 Apple Reminders（Hermes 作为中转）

n8n 发送 Webhook → Hermes Agent → 执行 remindctl → 结果回传 n8n：

```bash
# Hermes 监听 n8n Webhook 端点
# 端点：POST http://localhost:5679/webhook/n8n-reminder

# n8n Webhook 请求格式
{
  "type": "add_reminder",
  "title": "【采购】订单 PO-2026-001 待收货",
  "due": "2026-05-25",
  "list": "采购流程",
  "notes": "供应商：深圳XX科技 | 订单金额：¥5,800"
}

# Hermes 收到后执行
remindctl add --title "【采购】订单 PO-2026-001 待收货" \
  --due "2026-05-25" \
  --list 采购流程 \
  --notes "供应商：深圳XX科技 | 订单金额：¥5,800"
```

### n8n 读取 Apple Reminders 状态

n8n 可以轮询 Hermes 获取当前 Reminders 状态用于工作流决策：

```bash
# Hermes 提供状态查询端点
remindctl today --json | jq '.[] | {title, dueDate, completed}'

# 输出格式
[
  {"title": "【采购】样品检测", "dueDate": "2026-05-20", "completed": false},
  {"title": "【供应商】A公司跟进", "dueDate": "2026-05-21", "completed": false}
]
```

n8n Code 节点轮询示例：
```javascript
const exec = require('child_process').execSync;
const result = exec('remindctl today --json').toString();
const reminders = JSON.parse(result);

// 检查是否有紧急采购提醒
const urgent = reminders.filter(r => 
  r.title.includes('【采购】') && !r.completed
);

if (urgent.length > 0) {
  // 触发 Telegram 通知
  return [{ json: { alert: true, items: urgent } }];
}
return [{ json: { alert: false } }];
```

### n8n + Apple Reminders 完整工作流模板

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Schedule   │────▶│    Code     │────▶│   HTTP RQ   │
│  每日检查    │     │  构建命令   │     │ Hermes MCP  │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │ Apple       │
                                        │ Reminders   │
                                        └─────────────┘
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │ iCloud 同步  │─────▶ iPhone/iPad/Mac
                                        └─────────────┘
```

### 环境变量配置

```bash
# ~/.hermes/env.sh
export N8N_API_KEY="eyJhbGciOiJI..."
export N8N_BASE_URL="http://localhost:5678"
export N8N_WEBHOOK_HERMES="http://localhost:5678/webhook/hermes-reminder"
```

### 安全注意事项

| 场景 | 风险 | 缓解 |
|------|------|------|
| n8n → Hermes webhook | 命令注入 | 验证 payload，只允许预定义字段 |
| Hermes 执行 remindctl | 权限过大 | remindctl 本身已限制为 Apple Reminders 操作 |
| API Key 存储 | Key 泄露 | 使用环境变量，不写入工作流代码 |

---

## Related Skills

- `n8n-hermes-integration` — n8n 与 Hermes 完整集成架构（含 Webhook 触发、API 调用、工作流设计模式）
- `apple-notes` — Apple Notes 管理（与 Reminders 配合使用）
- `hermes-rpa` — Hermes 桌面代理核心能力（可扩展到其他 Apple 应用自动化）
