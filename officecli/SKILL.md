---
name: officecli
description: OfficeCLI — AI友好的Office文档CLI工具，读写编辑Word(.docx)/Excel(.xlsx)/PowerPoint(.pptx)，无需安装Microsoft
  Office。用于：创建文档、填表、格式化、渲染预览、查询内容。触发词：Word编辑/Excel处理/PPT生成/Office文档操作/docx/xlsx/pptx
version: '1.0'
license: MIT
platforms:
- macos
- linux
- windows
tags:
- office
- word
- excel
- powerpoint
- docx
- xlsx
- pptx
- document
author: OfficeCLI / Hermes
triggers:
- Use when officecli
trigger_type: general
---

# OfficeCLI Skill

## 核心能力
- **读**：解析文档结构，提取文本/表格/图片
- **写**：创建和修改 docx/xlsx/pptx
- **渲染**：文档转HTML/PNG，AI直接看懂内容
- **热预览**：watch模式修改后实时刷新预览

## 环境检查
```bash
officecli --version  # 确认已安装 v1.0+
which officecli || npm install -g @officecli/officecli
```

## 文档读取流程
```bash
# 1. 打开文档（启动常驻进程）
officecli open report.xlsx

# 2. 查询文档内容（CSS选择器语法）
officecli query report.xlsx "table row:nth-child(2) cell:nth-child(3)"
officecli get report.xlsx "/"  # 根节点

# 3. 查看渲染结果
officecli view report.xlsx html  # 输出HTML
officecli view report.xlsx png   # 输出PNG base64

# 4. 关闭
officecli close report.xlsx
```

## 文档写入流程
```bash
# 添加内容
officecli add <file> <parent_path> [options]

# 示例：给Word文档添加段落
officecli add doc.docx "/body" --type paragraph --text "新内容"

# 设置属性
officecli set <file> <path> --<property> <value>

# 示例：设置Excel单元格值
officecli set sheet.xlsx "/sheet[1]/table.row[2]/cell[3]" --value 999
```

## Word文档处理
```bash
# 读取Word内容
officecli get doc.docx "/" | officecli --json get doc.docx /body

# 查询段落
officecli query doc.docx "p"           # 所有段落
officecli query doc.docx "table"        # 所有表格
officecli query doc.docx "table row"    # 表格行

# 添加标题
officecli add doc.docx /body/ --type heading --text "第一章" --level 1
```

## Excel处理
```bash
# 读取Excel
officecli get sheet.xlsx "/sheet[1]"    # 第一个sheet
officecli query sheet.xlsx "table"       # 查询表格

# 读取CSV
officecli get data.csv "/"

# 写入单元格
officecli set sheet.xlsx "/sheet[1]/table.row[3]/cell[2]" --value "总计"
```

## PowerPoint处理
```bash
# 读取PPT
officecli get slides.pptx "/"

# 列出所有幻灯片
officecli query slides.pptx "slide"

# 查看某页内容
officecli view slides.pptx slide[1]
```

## 渲染预览（最有用）
```bash
# 启动预览服务
officecli watch report.xlsx
# 打开 http://localhost:PORT 查看实时预览

# 渲染为静态HTML
officecli view report.xlsx html > output.html

# 渲染为图片
officecli view report.xlsx png
```

## 常用路径格式
- Word: `/body/p[1]` 第1段, `/body/table[1]/row[1]/cell[2]` 表格第1行第2列
- Excel: `/sheet[1]/table.row[2]/cell[3]` sheet1第2行第3列
- PPT: `/slide[1]/shape[2]` 第1页第2个图形

## 注意事项
- 修改后用 `officecli view <file> html` 验证输出
- 复杂格式建议用 minimax-docx/minimax-pdf skill 处理最终渲染
- OfficeCLI擅长结构和数据操作，样式细节用OpenXMLSDK
- watch模式在修改文档后自动刷新预览窗口
