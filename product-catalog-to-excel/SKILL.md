---
name: product-catalog-to-excel
description: 产品目录图片转 Excel 表格。Use when 用户发送产品目录/报价单图片要求整理成表格
version: '1.0'
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [productivity, excel, ocr, image-processing]
    related_skills: [minimax-xlsx, defuddle]
---

# When to Use

用户发送产品目录/报价单图片要求整理成表格，或需要从图片提取商品信息并生成结构化 Excel 表格。

# Product Catalog to Excel

## Workflow

1. **Receive images** — User sends one or more product catalog/quotation images
2. **Extract data** — Use vision_analyze to read each image, extract: product name, weight, price, scent/flavor, carton qty, box dimensions, gross weight
3. **Compile** — Merge all products into a single structured list
4. **Generate Excel** — Create .xlsx with openpyxl, columns: 产品图片, 品名, 商品净重, 单价(元), 香味, 装箱数, 箱规格(cm), 整箱毛重(kg)
5. **Embed images** — Insert each product's source image into column A
6. **Send file** — Return MEDIA: path

## Excel Format

- Header row: bold, light blue fill
- Column A: product image (80×60px), row height 65
- Column widths: A=14, others=22
- Freeze panes: B2

## Key Rules

- Always include ALL products from ALL images, don't skip any
- Preserve original product names exactly as printed
- Use "-" for missing values, not empty cells
- Price as number (not string) for sorting
- Scent/flavor: join multiple with "/"

## Script Template

```python
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.drawing.image import Image as XLImage

wb = openpyxl.Workbook()
ws = wb.active
ws.title = '产品目录'
headers = ['产品图片', '品名', '商品净重', '单价(元)', '香味', '装箱数', '箱规格(cm)', '整箱毛重(kg)']
for i, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=i, value=h)
    cell.font = Font(bold=True)
    cell.fill = PatternFill(start_color='D9E2F3', end_color='D9E2F3', fill_type='solid')
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

# data: list of (img_path, name, weight, price, scent, carton, box_size, gross)
row = 2
for img_path, name, weight, price, scent, carton, box_size, gross in data:
    img = XLImage(img_path)
    img.width = 80; img.height = 60
    ws.add_image(img, f'A{row}')
    ws.row_dimensions[row].height = 65
    ws.cell(row=row, column=2, value=name)
    ws.cell(row=row, column=3, value=weight)
    ws.cell(row=row, column=4, value=price)
    ws.cell(row=row, column=5, value=scent)
    ws.cell(row=row, column=6, value=carton)
    ws.cell(row=row, column=7, value=box_size)
    ws.cell(row=row, column=8, value=gross)
    row += 1

ws.column_dimensions['A'].width = 14
for col in ['B','C','D','E','F','G','H']:
    ws.column_dimensions[col].width = 22
ws.freeze_panes = 'B2'
wb.save('/Users/aimac/.hermes/cache/scratch/产品目录.xlsx')
```