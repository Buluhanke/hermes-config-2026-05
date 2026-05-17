---
name: himalaya
description: "Himalaya CLI: IMAP/SMTP email from terminal, with 1688询价邮件、供应商报价跟踪、邮件模板和自动跟进提醒"
version: 2.0.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Email, IMAP, SMTP, CLI, Communication, 1688, supplier, tracking]
    homepage: https://github.com/pimalaya/himalaya
prerequisites:
  commands: [himalaya]
---

# Himalaya Email CLI

Himalaya is a CLI email client that lets you manage emails from the terminal using IMAP, SMTP, Notmuch, or Sendmail backends.

## References

- `references/configuration.md` (config file setup + IMAP/SMTP authentication)
- `references/message-composition.md` (MML syntax for composing emails)

## Prerequisites

1. Himalaya CLI installed (`himalaya --version` to verify)
2. A configuration file at `~/.config/himalaya/config.toml`
3. IMAP/SMTP credentials configured (password stored securely)

### Installation

```bash
# Pre-built binary (Linux/macOS — recommended)
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh

# macOS via Homebrew
brew install himalaya

# Or via cargo (any platform with Rust)
cargo install himalaya --locked
```

## Configuration Setup

Run the interactive wizard to set up an account:

```bash
himalaya account configure
```

Or create `~/.config/himalaya/config.toml` manually:

```toml
[accounts.personal]
email = "you@example.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@example.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/imap"  # or use keyring

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.example.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@example.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/smtp"

# Folder aliases (himalaya v1.2.0+ syntax). Required whenever the
# server's folder names don't match himalaya's canonical names
# (inbox/sent/drafts/trash). Gmail is the common case — see
# `references/configuration.md` for the `[Gmail]/Sent Mail` mapping.
folder.aliases.inbox = "INBOX"
folder.aliases.sent = "Sent"
folder.aliases.drafts = "Drafts"
folder.aliases.trash = "Trash"
```

> **Heads up on the alias syntax.** Pre-v1.2.0 docs used a
> `[accounts.NAME.folder.alias]` sub-section (singular `alias`).
> v1.2.0 silently ignores that form — TOML parses fine, but the
> alias resolver never reads it, so every lookup falls through to
> the canonical name. On Gmail this means save-to-Sent fails *after*
> SMTP delivery succeeds, and `himalaya message send` exits non-zero.
> Any caller (agent, script, user) that retries on that exit code
> will re-run the entire send — including SMTP — producing duplicate
> emails to recipients. Always use `folder.aliases.X` (plural, dotted
> keys, directly under `[accounts.NAME]`).

## Hermes Integration Notes

- **Reading, listing, searching, moving, deleting** all work directly through the terminal tool
- **Composing/replying/forwarding** — piped input (`cat << EOF | himalaya template send`) is recommended for reliability. Interactive `$EDITOR` mode works with `pty=true` + background + process tool, but requires knowing the editor and its commands
- Use `--output json` for structured output that's easier to parse programmatically
- The `himalaya account configure` wizard requires interactive input — use PTY mode: `terminal(command="himalaya account configure", pty=true)`

## Common Operations

### List Folders

```bash
himalaya folder list
```

### List Emails

List emails in INBOX (default):

```bash
himalaya envelope list
```

List emails in a specific folder:

```bash
himalaya envelope list --folder "Sent"
```

List with pagination:

```bash
himalaya envelope list --page 1 --page-size 20
```

### Search Emails

```bash
himalaya envelope list from john@example.com subject meeting
```

### Read an Email

Read email by ID (shows plain text):

```bash
himalaya message read 42
```

Export raw MIME:

```bash
himalaya message export 42 --full
```

### Reply to an Email

To reply non-interactively from Hermes, read the original message, compose a reply, and pipe it:

```bash
# Get the reply template, edit it, and send
himalaya template reply 42 | sed 's/^$/\nYour reply text here\n/' | himalaya template send
```

Or build the reply manually:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: sender@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id>

Your reply here.
EOF
```

Reply-all (interactive — needs $EDITOR, use template approach above instead):

```bash
himalaya message reply 42 --all
```

### Forward an Email

```bash
# Get forward template and pipe with modifications
himalaya template forward 42 | sed 's/^To:.*/To: newrecipient@example.com/' | himalaya template send
```

### Write a New Email

**Non-interactive (use this from Hermes)** — pipe the message via stdin:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: recipient@example.com
Subject: Test Message

Hello from Himalaya!
EOF
```

Or with headers flag:

```bash
himalaya message write -H "To:recipient@example.com" -H "Subject:Test" "Message body here"
```

Note: `himalaya message write` without piped input opens `$EDITOR`. This works with `pty=true` + background mode, but piping is simpler and more reliable.

### Move/Copy Emails

Move to folder:

```bash
himalaya message move 42 "Archive"
```

Copy to folder:

```bash
himalaya message copy 42 "Important"
```

### Delete an Email

```bash
himalaya message delete 42
```

### Manage Flags

Add flag:

```bash
himalaya flag add 42 --flag seen
```

Remove flag:

```bash
himalaya flag remove 42 --flag seen
```

## Multiple Accounts

List accounts:

```bash
himalaya account list
```

Use a specific account:

```bash
himalaya --account work envelope list
```

## Attachments

Save attachments from a message:

```bash
himalaya attachment download 42
```

Save to specific directory:

```bash
himalaya attachment download 42 --dir ~/Downloads
```

## Output Formats

Most commands support `--output` for structured output:

```bash
himalaya envelope list --output json
himalaya envelope list --output plain
```

## Debugging

Enable debug logging:

```bash
RUST_LOG=debug himalaya envelope list
```

Full trace with backtrace:

```bash
RUST_LOG=trace RUST_BACKTRACE=1 himalaya envelope list
```

## Tips

- Use `himalaya --help` or `himalaya <command> --help` for detailed usage.
- Message IDs are relative to the current folder; re-list after folder changes.
- For composing rich emails with attachments, use MML syntax (see `references/message-composition.md`).
- Store passwords securely using `pass`, system keyring, or a command that outputs the password.

---

# 扩展功能：1688询价 + 供应商报价跟踪 + 邮件模板 + 自动跟进

## 目录

- [1688询价邮件自动发送](#1688询价邮件自动发送)
- [供应商报价跟踪](#供应商报价跟踪)
- [邮件模板集成](#邮件模板集成)
- [自动跟进提醒](#自动跟进提醒)

---

## 1688询价邮件自动发送

### 工作流程

```
1688产品链接 → 提取供应商邮箱 → 填充询价模板 → 自动发送
```

### 发送1688询价邮件

```bash
# 标准询价邮件（非交互式）
cat << 'EOF' | himalaya template send
From: you@example.com
To: supplier@1688.com
Subject: 【询价】产品型号 XXX，数量 500件
X-Template: 1688-inquiry

您好，

我司有意采购以下产品，麻烦报价：

产品名称：XXX
型号规格：XXX
采购数量：500件
目标单价：XXX元
交货地点：深圳
付款方式：月结30天

麻烦提供含税含运费报价，谢谢！

Best regards,
XXX
EOF
```

### 批量发送1688询价

```bash
# 从CSV文件批量发送（supplier_list.csv 格式：name,email,product,qty）
#!/bin/bash
while IFS=, read -r name email product qty; do
  cat << MAIL | himalaya template send
From: you@example.com
To: $email
Subject: 【询价】$product，数量 $qty件
X-Template: 1688-inquiry

您好 $name，

我司有意采购以下产品，请帮忙报价：

产品：$product
数量：$qty件

期待您的回复，谢谢！

Best regards
MAIL
  echo "已发送询价邮件至: $email"
done < supplier_list.csv
```

### 1688询价邮件模板变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `{{supplier_name}}` | 供应商名称 | 深圳市XXX公司 |
| `{{product_name}}` | 产品名称 | 蓝牙耳机 |
| `{{product_url}}` | 1688产品链接 | https://detail.1688.com/... |
| `{{qty}}` | 采购数量 | 500 |
| `{{target_price}}` | 目标单价 | 25 |
| `{{delivery}}` | 交货地点 | 深圳 |
| `{{payment}}` | 付款方式 | 月结30天 |

---

## 供应商报价跟踪

### 报价数据结构

供应商报价跟踪使用本地CSV文件存储：

```csv
# ~/.hermes/data/suppliers.csv
supplier_id,supplier_name,email,product,quote_price,currency,moq,lead_time,valid_until,status,notes,last_contact,followup_date
S001,深圳XX电子,seller@1688.com,蓝牙耳机,25.00,CNY,500,7天,2026-06-01,pending,样品已申请,2026-05-10,2026-05-17
S002,广州YY贸易,gztrade@163.com,数据线,3.50,CNY,2000,5天,2026-06-15,quoted,报价含税,2026-05-12,
```

### 供应商报价命令

```bash
# 查看所有供应商报价
himalaya supplier list

# 查看待跟进供应商
himalaya supplier list --status pending

# 添加新供应商报价
himalaya supplier add --email seller@1688.com --product "蓝牙耳机" --price 25.00 --qty 500

# 更新报价状态
himalaya supplier update S001 --status quoted --price 24.50

# 导出报价对比表
himalaya supplier export --format markdown
```

### 供应商报价对比

```bash
# 获取某产品的所有报价
himalaya supplier list --product "蓝牙耳机" --output json
```

### 报价邮件自动归档

收到供应商报价邮件时，自动标记并提取信息：

```bash
# 搜索报价相关邮件
himalaya envelope list from @1688.com subject 报价

# 标记为已读并归档到供应商文件夹
himalaya message move <id> "Suppliers"
himalaya flag add <id> --flag seen
```

### 报价跟踪脚本

```bash
#!/bin/bash
# ~/.hermes/scripts/supplier-track.sh
# 用途：检查报价有效期，跟进即将过期的报价

DATA_FILE="$HOME/.hermes/data/suppliers.csv"
TODAY=$(date +%Y-%m-%d)
WARN_DATE=$(date -d "+3 days" +%Y-%m-%d)

echo "=== 报价有效期检查 ($TODAY) ==="
while IFS=, read -r id name email product price currency moq lead valid status notes lastContact followup; do
  # 跳过标题行
  [[ "$id" == "supplier_id" ]] && continue
  
  # 检查是否需要跟进
  if [[ "$valid" < "$WARN_DATE" && "$valid" > "$TODAY" ]]; then
    echo "⚠️  $name 的 $product 报价将在 $valid 过期"
  elif [[ "$valid" < "$TODAY" ]]; then
    echo "❌ $name 的 $product 报价已过期"
  fi
done < "$DATA_FILE"
```

---

## 邮件模板集成

### 模板文件位置

```
~/.hermes/templates/
├── 1688-inquiry.mml      # 1688询价模板
├── supplier-followup.mml  # 供应商跟进模板
├── price-negotiation.mml  # 价格谈判模板
├── sample-request.mml     # 样品申请模板
└── order-confirm.mml      # 订单确认模板
```

### 使用模板发送邮件

```bash
# 使用模板发送（通过环境变量或X-Template头指定）
himalaya template send --template 1688-inquiry

# 或者直接用模板文件
cat ~/.hermes/templates/1688-inquiry.mml | sed 's/{{supplier_name}}/张三/g; s/{{product}}/蓝牙耳机/g' | himalaya template send
```

### 模板变量替换

```bash
# 变量替换函数
template_render() {
  local template=$1
  local output=$2
  shift 2
  
  cp "$template" "$output"
  while [[ $# -gt 0 ]]; do
    local key="${1%%=*}"
    local val="${1#*=}"
    sed -i "s/{{$key}}/$val/g" "$output"
    shift
  done
}

# 使用示例
template_render ~/.hermes/templates/1688-inquiry.mml /tmp/inquiry.mml \
  supplier_name="深圳XX电子" \
  product="蓝牙耳机" \
  qty="500"
```

### 常用邮件模板

#### 1688询价模板 (`1688-inquiry.mml`)

```mml
From: {{sender_email}}
To: {{supplier_email}}
Subject: 【询价】{{product_name}}，数量 {{qty}}件
X-Template: 1688-inquiry
X-Supplier-ID: {{supplier_id}}

您好{{supplier_name}}，

我司是专业的批发采购商，对贵司产品有兴趣，详情如下：

产品名称：{{product_name}}
产品链接：{{product_url}}
采购数量：{{qty}}件
目标单价：{{target_price}}元（含税含运）
交货地点：{{delivery}}
付款方式：{{payment}}

期待您的报价，谢谢！

Best regards,
{{sender_name}}
{{sender_company}}
电话：{{sender_phone}}
```

#### 供应商跟进模板 (`supplier-followup.mml`)

```mml
From: {{sender_email}}
To: {{supplier_email}}
Subject: 【跟进】关于 {{product_name}} 的报价
X-Template: supplier-followup

您好{{supplier_name}}，

上次联系后一直没有收到您对以下产品的报价，想确认一下：

产品：{{product_name}}
数量：{{qty}}件
咨询日期：{{last_contact}}

请问方便提供报价吗？期待您的回复，谢谢！

Best regards,
{{sender_name}}
```

#### 样品申请模板 (`sample-request.mml`)

```mml
From: {{sender_email}}
To: {{supplier_email}}
Subject: 【样品申请】{{product_name}}
X-Template: sample-request

您好{{supplier_name}}，

我司想申请以下产品的样品：

产品名称：{{product_name}}
产品链接：{{product_url}}
数量：{{sample_qty}}件
样品费用：{{sample_fee}}元（含运费）
收货地址：{{shipping_address}}

请告知是否可以安排，谢谢！

Best regards,
{{sender_name}}
```

---

## 自动跟进提醒

### 跟进提醒系统架构

```
邮件发送 → 记录到跟进数据库 → 定时检查 → 到期提醒 → 自动发送跟进邮件
```

### 跟进数据库

```csv
# ~/.hermes/data/followups.csv
followup_id,supplier_id,supplier_name,email,product,action,send_date,due_date,status,reminder_sent,notes
F001,S001,深圳XX电子,seller@1688.com,蓝牙耳机,报价跟进,2026-05-10,2026-05-17,pending,no,等待报价
F002,S002,广州YY贸易,gztrade@163.com,数据线,样品确认,2026-05-12,2026-05-19,pending,no,样品已发货
```

### 跟进命令

```bash
# 查看所有跟进任务
himalaya followup list

# 查看今日待跟进
himalaya followup list --due today

# 查看逾期跟进
himalaya followup list --overdue

# 创建跟进任务
himalaya followup add \
  --supplier S001 \
  --action "报价跟进" \
  --due "2026-05-17" \
  --notes "等待第一轮报价"

# 标记跟进完成
himalaya followup complete F001

# 删除跟进任务
himalaya followup delete F001
```

### 自动跟进检查脚本

```bash
#!/bin/bash
# ~/.hermes/scripts/followup-check.sh
# 用途：检查到期的跟进任务，自动发送跟进邮件

DATA_FILE="$HOME/.hermes/data/followups.csv"
TODAY=$(date +%Y-%m-%d)
TEMPLATE_DIR="$HOME/.hermes/templates"
LOG_FILE="$HOME/.hermes/logs/followup.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }

log "开始检查跟进任务..."

while IFS=, read -r fid sid sname email product action send_date due status reminder notes; do
  [[ "$fid" == "followup_id" ]] && continue
  [[ "$status" == "completed" ]] && continue
  
  if [[ "$due" == "$TODAY" && "$reminder_sent" == "no" ]]; then
    log "📧 发送跟进提醒: $sname - $action"
    
    # 渲染模板
    template_render "$TEMPLATE_DIR/supplier-followup.mml" /tmp/followup_$fid.mml \
      supplier_name="$sname" \
      supplier_email="$email" \
      product="$product" \
      action="$action" \
      notes="$notes"
    
    # 发送邮件
    cat /tmp/followup_$fid.mml | himalaya template send 2>> "$LOG_FILE"
    
    # 标记已发送
    sed -i "s/$fid,\([^,]*\),\([^,]*\),\([^,]*\),\([^,]*\),\([^,]*\),\([^,]*\),\([^,]*\),\([^,]*\),pending,no,\(.*\)/$fid,\1,\2,\3,\4,\5,\6,\7,\8,pending,yes,\9/" "$DATA_FILE"
    
    log "✅ 跟进提醒已发送: $fid"
  fi
done < "$DATA_FILE"

log "跟进检查完成"
```

### Cron定时任务配置

```bash
# 每天早上9点检查跟进任务
0 9 * * * /Users/aimac/.hermes/scripts/followup-check.sh >> /Users/aimac/.hermes/logs/cron.log 2>&1

# 每周一早上生成报价跟踪报告
0 8 * * 1 /Users/aimac/.hermes/scripts/supplier-report.sh | mail -s "本周供应商报价跟踪报告" your@email.com
```

### 逾期未跟进警告

```bash
#!/bin/bash
# 逾期超过3天自动提醒
OVERDUE_DAYS=3
TODAY=$(date +%Y-%m-%d)

himalaya followup list --output json | jq -r '.[] | select(.status == "pending" and .due_date < "'$(date -d "-$OVERDUE_DAYS days" +%Y-%m-%d)'") | "⚠️ 逾期\(.overdue_days)天: \(.supplier_name) - \(.action)"'
```

### 跟进状态机

```
                    ┌──────────────┐
         ┌─────────→│   pending    │←─────────┐
         │          └──────┬───────┘          │
         │                 │ 到期              │完成后再创建
         │                 ▼                   │
         │          ┌──────────────┐          │
         │    3天内未回复   │   follow_up   │          │
         │          └──────┬───────┘          │
         │                 │                   │
         ▼                 ▼                   │
  ┌──────────────┐   ┌──────────────┐          │
  │   overdue   │   │   waiting    │──────────┘
  └──────┬───────┘   └──────────────┘
         │
         │ 超过N天无回复
         ▼
  ┌──────────────┐
  │   dropped    │
  └──────────────┘
```

---

## 数据存储结构

```
~/.hermes/
├── config.yaml              # 技能配置（可选）
├── data/
│   ├── suppliers.csv        # 供应商报价数据
│   ├── followups.csv        # 跟进任务数据
│   └── templates/           # 邮件模板
│       ├── 1688-inquiry.mml
│       ├── supplier-followup.mml
│       └── ...
├── scripts/
│   ├── supplier-track.sh    # 供应商跟踪脚本
│   ├── followup-check.sh    # 跟进检查脚本
│   └── render-template.sh   # 模板渲染脚本
└── logs/
    ├── followup.log         # 跟进日志
    └── mail.log             # 邮件发送日志
```
