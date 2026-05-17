---
name: apple-notes
description: "Manage Apple Notes via memo CLI: create, search, edit."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Notes, Apple, macOS, note-taking]
    related_skills: [obsidian]
prerequisites:
  commands: [memo]
---

# Apple Notes

Use `memo` to manage Apple Notes directly from the terminal. Notes sync across all Apple devices via iCloud.

## Prerequisites

- **macOS** with Notes.app
- Install: `brew tap antoniorodr/memo && brew install antoniorodr/memo/memo`
- Grant Automation access to Notes.app when prompted (System Settings → Privacy → Automation)

## When to Use

- User asks to create, view, or search Apple Notes
- Saving information to Notes.app for cross-device access
- Organizing notes into folders
- Exporting notes to Markdown/HTML

## When NOT to Use

- Obsidian vault management → use the `obsidian` skill
- Bear Notes → separate app (not supported here)
- Quick agent-only notes → use the `memory` tool instead

## Quick Reference

### View Notes

```bash
memo notes                        # List all notes
memo notes -f "Folder Name"       # Filter by folder
memo notes -s "query"             # Search notes (fuzzy)
```

### Create Notes

```bash
memo notes -a                     # Interactive editor
memo notes -a "Note Title"        # Quick add with title
```

### Edit Notes

```bash
memo notes -e                     # Interactive selection to edit
```

### Delete Notes

```bash
memo notes -d                     # Interactive selection to delete
```

### Move Notes

```bash
memo notes -m                     # Move note to folder (interactive)
```

### Export Notes

```bash
memo notes -ex                    # Export to HTML/Markdown
```

## Limitations

- Cannot edit notes containing images or attachments
- Interactive prompts require terminal access (use pty=true if needed)
- macOS only — requires Apple Notes.app

## Templates

### 采购快速笔记模板 (Procurement Quick Note)

```bash
memo notes -a "采购-[日期]-[品名]"

# 自动填入模板内容:
# ═══════════════════════════════════
# 【采购单】日期: YYYY-MM-DD
# ═══════════════════════════════════
# 品名:
# 规格:
# 数量:
# 单价:
# 总价:
# 供应商:
# 1688链接:
# 备注:
# ═══════════════════════════════════
```

### 供应商联系记录模板 (Supplier Contact Record)

```bash
memo notes -a "供应商-[公司名]"

# 自动填入模板内容:
# ═══════════════════════════════════
# 【供应商档案】公司: [公司名]
# ═══════════════════════════════════
# 联系人:
# 职务:
# 电话:
# 微信:
# 邮箱:
# 地址:
# 主营产品:
# 合作状态: [新增/洽谈中/已合作/暂停]
# 备注:
# ═══════════════════════════════════
```

### 1688订单备注格式 (1688 Order Note Format)

```bash
memo notes -a "1688-[订单号]"

# 自动填入模板内容:
# ═══════════════════════════════════
# 【1688订单】订单号: [订单号]
# 日期: YYYY-MM-DD
# ═══════════════════════════════════
# 店铺:
# 商品:
# SKU:
# 数量: X件 | 单价: ¥XX
# 实付: ¥XX | 优惠: ¥XX
# 物流:
# 运单号:
# 状态: [待付款/待发货/已发货/已完成]
# 验货: [ ]合格 [ ]不合格
# 备注:
# ═══════════════════════════════════
```

## Auto-Archiving Rules

Create a script at `~/.hermes/scripts/auto_archive_notes.sh`:

```bash
#!/bin/bash
# auto_archive_notes.sh — 自动归档旧笔记
# Usage: ./auto_archive_notes.sh

ARCHIVE_FOLDER="归档"

# 按日期归档采购单（超过30天移至归档文件夹）
ARCHIVE_DAYS=30

memo notes -s "采购-" | while read -r note; do
  # 提取日期并检查是否超过30天
  # 超过则移动到归档文件夹
  # memo notes -m "$note" "$ARCHIVE_FOLDER"
done

# 按状态归档1688订单（已完成订单自动归档）
memo notes -s "1688-" | while read -r note; do
  # 检查状态为"已完成"则移动到归档文件夹
done
```

### 自动归档使用方式

```bash
# 手动执行归档
~/.hermes/scripts/auto_archive_notes.sh

# 或使用 cron 每周自动执行
# crontab -e
# 0 2 * * 0 /Users/aimac/.hermes/scripts/auto_archive_notes.sh
```

## Rules

1. Prefer Apple Notes when user wants cross-device sync (iPhone/iPad/Mac)
2. Use the `memory` tool for agent-internal notes that don't need to sync
3. Use the `obsidian` skill for Markdown-native knowledge management
4. 采购笔记使用 `采购-YYYY-MM-DD-品名` 命名格式
5. 供应商记录使用 `供应商-公司名` 命名格式
6. 1688订单使用 `1688-订单号` 命名格式
7. 归档文件夹默认命名为 `归档`，可在Notes.app中手动创建
