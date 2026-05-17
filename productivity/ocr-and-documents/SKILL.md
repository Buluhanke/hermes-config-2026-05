---
name: ocr-and-documents
description: "Extract text from PDFs/scans (pymupdf, marker-pdf)."
version: 2.3.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [powerpoint]
---

# PDF & Document Extraction

> **NOTE**: `ocr-and-documents` only covers PDF and scanned OCR. For structured tabular data (CSV/Excel), use the `data-analyzer` skill. For images (screenshots, receipts), see `baidu-ocr` or `hermes-fast-ocr-ssim`.

For DOCX: use `python-docx` (parses actual document structure, far better than OCR).
For PPTX: see the `powerpoint` skill (uses `python-pptx` with full slide/notes support).
This skill covers **PDFs and scanned documents**.

## Step 1: Remote URL Available?

If the document has a URL, **always try `web_extract` first**:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

This handles PDF-to-markdown conversion via Firecrawl with no local dependencies.

Only use local extraction when: the file is local, web_extract fails, or you need batch processing.

## Step 2: Choose Local Extractor

| Feature | pymupdf (~25MB) | marker-pdf (~3-5GB) |
|---------|-----------------|---------------------|
| **Text-based PDF** | ✅ | ✅ |
| **Scanned PDF (OCR)** | ❌ | ✅ (90+ languages) |
| **Tables** | ✅ (basic) | ✅ (high accuracy) |
| **Equations / LaTeX** | ❌ | ✅ |
| **Code blocks** | ❌ | ✅ |
| **Forms** | ❌ | ✅ |
| **Headers/footers removal** | ❌ | ✅ |
| **Reading order detection** | ❌ | ✅ |
| **Images extraction** | ✅ (embedded) | ✅ (with context) |
| **Images → text (OCR)** | ❌ | ✅ |
| **EPUB** | ✅ | ✅ |
| **Markdown output** | ✅ (via pymupdf4llm) | ✅ (native, higher quality) |
| **Install size** | ~25MB | ~3-5GB (PyTorch + models) |
| **Speed** | Instant | ~1-14s/page (CPU), ~0.2s/page (GPU) |

**Decision**: Use pymupdf unless you need OCR, equations, forms, or complex layout analysis.

> **⚠️ Disk space check before marker-pdf**: marker-pdf needs ~5GB free. Run `python scripts/extract_marker.py --check` first. If insufficient: use pymupdf for text PDFs, or use `baidu-ocr` for image-based OCR (receipts, photos, screenshots) — no local model install needed.

> **📌 Chinese / 1688 document priority**: For 1688 order forms, logistics receipts, and Chinese supplier documents, **prefer `marker-pdf` with `--json`** over `pymupdf`. 1688 documents are often scanned images with mixed Chinese + English + tables. marker-pdf handles all three simultaneously. `baidu-ocr` is the fallback for casual photos of documents.

If the user needs marker capabilities but the system lacks ~5GB free:
> "This document needs OCR/advanced extraction (marker-pdf), which requires ~5GB for PyTorch and models. Your system has [X]GB free. Options: free up space, provide a URL so I can use web_extract, or I can try pymupdf which works for text-based PDFs but not scanned documents or equations."

---

## pymupdf (lightweight)

```bash
pip install pymupdf pymupdf4llm
```

**Via helper script**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Inline**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (high-quality OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Via helper script**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata — BEST for 1688 orders
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (installed with marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## Arxiv Papers

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Split, Merge & Search

pymupdf handles these natively — use `execute_code` or inline Python:

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

No extra dependencies needed — pymupdf covers split, merge, search, and text extraction in one package.

- For PowerPoint: see the `powerpoint` skill (uses python-pptx)

---

## 模块6: 批量处理流程

### 场景
多个PDF/图片需要批量OCR识别，输出结构化结果（如CSV、JSON）。

### 核心流程
```
输入目录 → 文件枚举 → 并行OCR → 结果合并 → 输出结构化文件
```

### 实现脚本 (scripts/batch_ocr.py)

```python
#!/usr/bin/env python3
"""批量OCR处理 - 支持pymupdf/marker-pdf并行"""
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

def ocr_file(file_path: str, method: str = "marker", output_dir: str = None) -> dict:
    """单文件OCR，返回结构化结果"""
    path = Path(file_path)
    result = {"file": str(path), "success": False, "pages": 0, "text": "", "error": ""}

    try:
        if method == "marker":
            from marker import convert
            result_md = convert_single_pdf(str(path), output_dir or str(path.parent))
            result["text"] = str(result_md)
            result["pages"] = 1
        else:
            import pymupdf
            doc = pymupdf.open(str(path))
            texts = []
            for page in doc:
                texts.append(page.get_text())
            result["text"] = "\n".join(texts)
            result["pages"] = len(doc)
        result["success"] = True
    except Exception as e:
        result["error"] = str(e)

    return result

def batch_ocr(input_dir: str, output_file: str = "batch_results.json",
              method: str = "marker", workers: int = 4, pattern: str = "*.pdf"):
    """批量OCR主函数"""
    input_path = Path(input_dir)
    files = sorted(input_path.glob(pattern))
    print(f"Found {len(files)} files matching {pattern}")

    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(ocr_file, str(f), method): f for f in files}
        for i, future in enumerate(as_completed(futures), 1):
            r = future.result()
            results.append(r)
            status = "✓" if r["success"] else "✗"
            print(f"[{i}/{len(files)}] {status} {r['file']}")

    # 写入结果
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to {output_file}")

    # 统计
    success = sum(1 for r in results if r["success"])
    print(f"Success: {success}/{len(results)}")

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch OCR")
    parser.add_argument("input_dir", help="Input directory with PDFs/images")
    parser.add_argument("--output", default="batch_results.json")
    parser.add_argument("--method", default="marker", choices=["marker", "pymupdf"])
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--pattern", default="*.pdf")
    args = parser.parse_args()

    batch_ocr(args.input_dir, args.output, args.method, args.workers, args.pattern)
```

### 使用方法

```bash
# 批量OCR整个目录（marker，4并行）
python scripts/batch_ocr.py ./documents/

# 批量OCR整个目录（pymupdf，8并行）
python scripts/batch_ocr.py ./documents/ --method pymupdf --workers 8

# 只处理jpg/png图片
python scripts/batch_ocr.py ./scans/ --pattern "*.jpg"

# 合并为单个CSV
python -c "
import json, csv
results = json.load(open('batch_results.json'))
with open('batch_results.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['file', 'pages', 'success', 'text_length', 'error'])
    for r in results:
        w.writerow([r['file'], r['pages'], r['success'], len(r['text']), r['error']])
"
```

### 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--method` | 引擎：marker（OCR）/ pymupdf（文本PDF） | marker |
| `--workers` | 并行数（CPU-bound建议4，IO-bound可更高） | 4 |
| `--pattern` | 文件匹配模式（glob） | *.pdf |
| `--output` | 输出JSON路径 | batch_results.json |

### 注意事项

- marker-pdf批量处理时GPU可显著加速（~10x），无GPU时CPU约1-14s/页
- 图片类输入（jpg/png）只有marker支持，pymupdf会返回空
- 内存：批量处理大文件时限制workers=2避免OOM
- 输出JSON包含完整text，可后续用jq/yq提取

---

## 模块7: 表格结构化提取

### 场景
从PDF/扫描件中提取表格，输出CSV/JSON结构化数据，用于数据分析、Excel录入。

### 方案对比

| 方案 | 适用类型 | 精度 | 依赖 |
|------|---------|------|------|
| pymupdf `page.find_tables()` | 原生PDF表格 | 高 | pymupdf |
| marker-pdf + tabula-py | 扫描件/复杂表格 | 较高 | marker + tabula |
| camelot | 复杂PDF表格 | 高 | camelot-py |
| marker-pdf (内置) | marker输出自带表格JSON | 最高 | marker-pdf |

### 方案A: pymupdf 表格提取（原生PDF）

```python
import pymupdf

doc = pymupdf.open("document.pdf")
for page_num, page in enumerate(doc, 1):
    tables = page.find_tables()
    for table in tables:
        print(f"--- Page {page_num} Table {table.number} ---")
        for row in table.extract():
            print(row)
```

### 方案B: marker-pdf 表格提取（扫描件/最高精度）

```bash
python scripts/extract_marker.py document.pdf --json
# 输出包含 tables 字段，每表有 bbox + cells
```

```python
# 解析marker输出JSON中的表格
import json

with open("document.md.json") as f:
    data = json.load(f)

for page in data.get("pages", []):
    for table in page.get("tables", []):
        print("Table:", table["bbox"])
        for row in table["cells"]:
            print(row)
```

### 方案C: 提取表格并输出CSV

```python
import pymupdf
import csv

doc = pymupdf.open("document.pdf")
with open("tables_output.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    for page_num, page in enumerate(doc, 1):
        tables = page.find_tables()
        for table in tables:
            for row in table.extract():
                writer.writerow(row)
            writer.writerow([])  # 空行分隔表
```

### 方案D: camelot 精确提取（复杂表格）

```bash
pip install camelot-py
```

```python
import camelot

# lattice: 格子线清晰的表格 / stream: 无格线的表
tables = camelot.read_pdf("document.pdf", pages="all", flavor="lattice")
for i, table in enumerate(tables):
    table.to_csv(f"table_{i}.csv")  # 或 table.df for DataFrame
    print(table.parsing_report)
```

### 校验表格完整性

```python
# 检查表格行列一致性
def validate_table(table_data: list[list[str]]) -> dict:
    if not table_data:
        return {"valid": False, "reason": "empty"}
    row_lens = [len(row) for row in table_data]
    mode_len = max(set(row_lens), key=row_lens.count)
    inconsistent = sum(1 for l in row_lens if l != mode_len)
    return {
        "valid": inconsistent == 0,
        "rows": len(table_data),
        "cols": mode_len,
        "inconsistent_rows": inconsistent
    }
```

---

## 模块8: 1688订单识别

### 场景
从1688订单截图/PDF中自动提取：订单号、供应商、商品名称、数量、价格、收货信息。

### 1688订单页结构特征

- 订单号：数字/字母混合，格式如 `2026071612345678`
- 商品列表：多行，每行包含商品图片(小)、名称、SKU、数量、单价
- 金额：人民币符号¥，常有折扣划线价
- 供应商：公司名称（旺旺名）
- 收货信息：地址、电话、收货人

### 识别流程

```
1688截图/PDF → marker-pdf OCR → 正则/规则提取 → 结构化JSON
```

### 关键提取脚本 (scripts/extract_1688_order.py)

```python
#!/usr/bin/env python3
"""1688订单识别 - 从OCR文本提取结构化订单信息"""
import re
import json
import sys

def extract_1688_order(text: str) -> dict:
    """从OCR文本提取1688订单字段"""
    lines = text.split("\n")

    order = {
        "order_id": "",
        "supplier": "",
        "products": [],
        "total_amount": "",
        "receiver": "",
        "phone": "",
        "address": "",
        "status": "",
    }

    # 订单号：2025071612345678 格式（16-20位）
    id_match = re.search(r"(?:订单号|Order)[：:]\s*([A-Z0-9]{16,22})", text, re.I)
    if not id_match:
        id_match = re.search(r"\b(20\d{14,20})\b", text)
    if id_match:
        order["order_id"] = id_match.group(1).strip()

    # 供应商
    sup_match = re.search(r"(?:供应商|卖家)[：:]\s*(.+?)(?:\n|$)", text)
    if sup_match:
        order["supplier"] = sup_match.group(1).strip()

    # 电话（手机/固话）
    phone_match = re.search(r"1[3-9]\d{9}", text)
    if phone_match:
        order["phone"] = phone_match.group(0)

    # 收货人（通常在地址前）
    recv_match = re.search(r"收货人[：:]\s*(.+?)(?:\n|手机)", text)
    if recv_match:
        order["receiver"] = recv_match.group(1).strip()

    # 地址
    addr_match = re.search(r"收货地址[：:]\s*(.+?)(?:\n|$)", text)
    if addr_match:
        order["address"] = addr_match.group(1).strip()

    # 总金额（¥符号）
    amount_match = re.search(r"¥\s*([\d,]+\.?\d*)", text)
    if amount_match:
        order["total_amount"] = amount_match.group(1).strip()

    # 商品行解析（带数量×单价格式）
    # 格式示例: 2024夏季新款 童趣恐龙短袖 蓝色/120 数量×2 单价¥15.00
    product_pattern = re.compile(
        r"(.+?)\s+(\S+/[A-Z0-9/]+)\s+数量[×x](\d+)\s+单价[¥￥]?([\d.]+)"
    )
    for match in product_pattern.finditer(text):
        product = {
            "name": match.group(1).strip(),
            "sku": match.group(2).strip(),
            "qty": int(match.group(3)),
            "unit_price": float(match.group(4)),
        }
        product["subtotal"] = product["qty"] * product["unit_price"]
        order["products"].append(product)

    # 状态识别
    if "交易成功" in text or "已完成" in text:
        order["status"] = "已完成"
    elif "待付款" in text:
        order["status"] = "待付款"
    elif "待发货" in text:
        order["status"] = "待发货"
    elif "待收货" in text:
        order["status"] = "待收货"

    return order

if __name__ == "__main__":
    # 从stdin读取OCR文本
    ocr_text = sys.stdin.read()
    order = extract_1688_order(ocr_text)
    print(json.dumps(order, ensure_ascii=False, indent=2))
```

### 使用方法

```bash
# Step 1: 截图或PDF提取
python scripts/extract_marker.py 1688_order.png --json > order_raw.json

# Step 2: 提取结构化订单
cat order_raw.json | python scripts/extract_1688_order.py

# 或一条命令
python scripts/extract_marker.py 1688_order.png | python scripts/extract_1688_order.py
```

### 1688识别要点

| 字段 | 正则/规则 | 备注 |
|------|---------|------|
| 订单号 | `20\d{14,20}` | 1688订单号以20开头 |
| 供应商 | 找"供应商"标签 | 旺旺名/公司名 |
| 商品 | `名称 + SKU + 数量×单价` | 注意多行商品 |
| 金额 | `¥[\d,]+` | 找最大金额（总价） |
| 电话 | `1[3-9]\d{9}` | 手机号优先 |
| 地址 | "收货地址"标签后 | 省市县+详细地址 |
| 状态 | 关键词匹配 | 待付款/待发货/待收货/已完成 |

### 注意事项

- 1688页面经常有滑动验证，截图最好在已打开订单详情页时截取
- 订单截图建议1920px以上宽度，过小会影响OCR精度
- 多商品订单逐行解析，注意换行导致商品信息分拆问题
- 价格常有划线折扣价，正则优先匹配「小计」或「合计」行的金额

---

## 模块9: 多语言混排处理

### 场景
PDF含中/英/日/韩等多语言混排，OCR需要正确识别各语言区域，避免乱码和串行。

### 多语言处理策略

| 语言组合 | 推荐方案 | 说明 |
|---------|---------|------|
| 中文+英文（最常见） | marker-pdf + OCR | 默认支持 |
| 中文+日/韩 | marker-pdf (90+语言) | 设置 `--languages` |
| 欧洲语（德/法/俄等） | marker-pdf | 设置 `--languages` |
| 阿拉伯语/希伯来语 | marker-pdf + RTL支持 | 设置 `--languages` |
| 混合复杂排版 | marker-pdf `--use_llm` | LLM辅助理解上下文 |

### marker-pdf 多语言配置

```bash
# 中文+英文
marker_single document.pdf --output_dir ./out --languages chi_sim+eng

# 中文+日文+韩文+英文
marker_single document.pdf --output_dir ./out --languages chi_sim+jpn+kor+eng

# 欧洲多语（德+法+俄+英）
marker_single document.pdf --output_dir ./out --languages deu+fra+rus+eng

# 阿拉伯语（RTL）
marker_single document.pdf --output_dir ./out --languages ara

# 自动检测语言（默认）
marker_single document.pdf --output_dir ./out --languages auto
```

### Python多语言OCR脚本

```python
#!/usr/bin/env python3
"""多语言PDF OCR - 自动检测并识别"""
import argparse
import sys
from pathlib import Path

LANG_MAP = {
    "zh": "chi_sim", "cn": "chi_sim", "chs": "chi_sim",
    "en": "eng", "english": "eng",
    "ja": "jpn", "jp": "jpn", "japanese": "jpn",
    "ko": "kor", "kr": "kor", "korean": "kor",
    "de": "deu", "deu": "deu", "german": "deu",
    "fr": "fra", "fra": "fra", "french": "fra",
    "ru": "rus", "rus": "rus", "russian": "rus",
    "ar": "ara", "ara": "ara", "arabic": "ara",
}

def build_lang_param(langs: list[str]) -> str:
    resolved = []
    for lang in langs:
        key = lang.lower().replace("-", "_").replace(" ", "_")
        resolved.append(LANG_MAP.get(key, lang))
    return "+".join(resolved)

def ocr_multilang(input_file: str, langs: list[str], use_llm: bool = False):
    from marker import convert

    lang_param = "+".join(LANG_MAP.get(l.lower(), l) for l in langs)
    print(f"OCR with languages: {lang_param}")

    result = convert(
        input_file,
        langs=lang_param,
        use_llm=use_llm,
    )
    return str(result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input PDF/image file")
    parser.add_argument("--langs", nargs="+", default=["auto"],
                        help="Languages: zh en ja ko de fr ru ar ...")
    parser.add_argument("--use-llm", action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    text = ocr_multilang(args.input, args.langs, args.use_llm)
    output_path = args.output or (Path(args.input).stem + "_ocr.md")
    Path(output_path).write_text(text, encoding="utf-8")
    print(f"Saved to {output_path}")
```

### 多语言混排文本后处理

```python
import re

def split_multilang_blocks(text: str) -> dict[str, list[str]]:
    """按语言分离文本块（启发式方法）"""
    blocks = {"zh": [], "en": [], "other": []}

    # 提取中文段落
    zh_paragraphs = re.findall(r"[\u4e00-\u9fff]{2,}[^\n]*", text)
    blocks["zh"] = zh_paragraphs

    # 提取英文段落
    en_paragraphs = re.findall(r"[a-zA-Z]{2,}[^\n]*", text)
    blocks["en"] = en_paragraphs

    return blocks

def fix_mixed_chunks(text: str) -> str:
    """修复混排时常见OCR错误：数字/英文被误识别为乱码"""
    # 修复：连续的单个中文字符（如被误识别的英文）
    text = re.sub(r"([a-zA-Z])\s+([a-zA-Z])\s+([a-zA-Z])", r"\1\2\3", text)
    # 修复：多余空格
    text = re.sub(r"\s+", " ", text)
    return text
```

### 语言检测与分离示例

```python
# 基于字符编码范围检测语言
def detect_lang_by_chars(text: str) -> str:
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    en = len(re.findall(r"[a-zA-Z]", text))
    total = cjk + en
    if total == 0:
        return "unknown"
    if cjk / total > 0.5:
        return "zh-dominant"
    if en / total > 0.5:
        return "en-dominant"
    return "mixed"

# 对混排段落进行语言比例分析
for i, para in enumerate(paragraphs):
    lang = detect_lang_by_chars(para)
    print(f"Para {i}: {lang} ({len(para)} chars)")
```

### 常见问题处理

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 日文汉字被识别为中文 | 字符集重叠 | 叠加 `jpn+chi_sim`，后处理分离 |
| 韩文被识别为乱码 | 模型不支持 | 确认安装了 `kor` 语言包 |
| 英文全大写 | 扫描件质量问题 | marker加 `--use_llm` 改善 |
| 阿拉伯语从右往左 | RTL语言 | marker默认处理，但需确认输出方向 |
| 数字串被误识别 | 原PDF数字模糊 | 人工校验或LLM后处理 |

---

## 模块10: 识别结果后校验

### 场景
OCR输出可能存在漏字、错字、顺序混乱，需要系统性校验。

### 校验流程

```
OCR结果 → 完整性校验 → 格式校验 → 业务规则校验 → 可选LLM校验 → 输出报告
```

### 校验脚本 (scripts/verify_ocr.py)

```python
#!/usr/bin/env python3
"""OCR结果后校验 - 多层检查"""
import argparse
import json
import re
import sys
from pathlib import Path

class OcrValidator:
    def __init__(self, text: str, expected_fields: list[str] = None):
        self.text = text
        self.expected_fields = expected_fields or []
        self.errors = []
        self.warnings = []

    def check_empty(self):
        """空内容检测"""
        stripped = self.text.strip()
        if not stripped:
            self.errors.append("OCR结果为空，可能是文件损坏或无法识别")
        elif len(stripped) < 10:
            self.warnings.append(f"结果过短（{len(stripped)}字符），可能识别失败")
        return self

    def check_encoding(self):
        """编码异常检测"""
        # 检测乱码特征
        garbled_patterns = [
            r"[\u0000-\u001f]{5,}",  # 控制字符过多
            r"�{3,}",  # 替换字符过多
            r"□{3,}",  # 方框字符过多
        ]
        for pattern in garbled_patterns:
            if re.search(pattern, self.text):
                self.errors.append(f"检测到可能的乱码: {pattern}")
        return self

    def check_language_consistency(self, expected_lang: str = "zh"):
        """语言一致性检测"""
        cjk_ratio = len(re.findall(r"[\u4e00-\u9fff]", self.text)) / max(len(self.text), 1)
        if expected_lang == "zh" and cjk_ratio < 0.1 and len(self.text) > 50:
            self.warnings.append(f"中文比例仅{cjk_ratio:.1%}，可能OCR语言配置错误")
        return self

    def check_required_fields(self, fields: dict):
        """必需字段完整性检测"""
        for field_name, pattern in fields.items():
            if not re.search(pattern, self.text):
                self.errors.append(f"缺少必需字段或内容: {field_name}")

    def check_phone_numbers(self):
        """电话号码格式校验"""
        phones = re.findall(r"1[3-9]\d{9}", self.text)
        for phone in phones:
            if not is_valid_phone(phone):
                self.warnings.append(f"可疑电话号码: {phone}")
        return self

    def check_amounts(self):
        """金额格式校验"""
        amounts = re.findall(r"[¥￥$]\s*([\d,]+\.?\d*)", self.text)
        for amt_str in amounts:
            try:
                val = float(amt_str.replace(",", ""))
                if val > 1_000_000:
                    self.warnings.append(f"金额异常大: {amt_str}")
            except ValueError:
                self.errors.append(f"金额格式错误: {amt_str}")
        return self

    def check_order_id(self):
        """订单号格式校验"""
        order_ids = re.findall(r"\b(20\d{14,20})\b", self.text)
        if len(order_ids) > 1:
            self.warnings.append(f"检测到多个订单号: {order_ids}")
        return self

    def generate_report(self) -> dict:
        status = "PASS" if not self.errors else "FAIL"
        if not self.errors and self.warnings:
            status = "WARN"

        return {
            "status": status,
            "errors": self.errors,
            "warnings": self.warnings,
            "text_length": len(self.text),
            "lines": len(self.text.split("\n")),
        }

def is_valid_phone(phone: str) -> bool:
    """校验手机号合法性"""
    if len(phone) != 11:
        return False
    # 三大运营商号段校验（简化版）
    valid_prefixes = ["13", "14", "15", "16", "17", "18", "19"]
    return phone[:2] in valid_prefixes

def verify_ocr_file(file_path: str, field_patterns: dict = None) -> dict:
    """主验证函数"""
    path = Path(file_path)
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        text = data.get("text", data.get("markdown", ""))
    else:
        text = path.read_text(encoding="utf-8")

    field_patterns = field_patterns or {
        "订单号": r"20\d{14,20}",
        "金额": r"[¥￥]\s*[\d,]+\.?\d*",
        "电话": r"1[3-9]\d{9}",
    }

    validator = OcrValidator(text)
    report = (validator
              .check_empty()
              .check_encoding()
              .check_language_consistency()
              .check_required_fields(field_patterns)
              .check_phone_numbers()
              .check_amounts()
              .check_order_id()
              .generate_report())

    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OCR结果校验")
    parser.add_argument("file", help="OCR结果文件 (.txt/.json/.md)")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    args = parser.parse_args()

    report = verify_ocr_file(args.file)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Status: {report['status']}")
        print(f"文字长度: {report['text_length']} 字符, {report['lines']} 行")
        if report["errors"]:
            print("\n❌ Errors:")
            for e in report["errors"]:
                print(f"  - {e}")
        if report["warnings"]:
            print("\n⚠️  Warnings:")
            for w in report["warnings"]:
                print(f"  - {w}")
        if not report["errors"] and not report["warnings"]:
            print("\n✅ 校验通过，无错误或警告")

    sys.exit(0 if report["status"] == "PASS" else 1)
```

### 使用方法

```bash
# 基本校验（文本文件）
python scripts/verify_ocr.py result.txt

# JSON格式校验
python scripts/verify_ocr.py result.json --json

# 退出码：0=PASS, 1=FAIL
python scripts/verify_ocr.py result.txt
echo "Exit code: $?"

# 对比两个OCR版本差异
diff <(python scripts/extract_marker.py doc.pdf) \
     <(python scripts/extract_marker.py doc.pdf --use_llm) \
     | head -50
```

### LLM辅助校验（可选）

```python
def llm_validate(text: str, rules: list[str]) -> dict:
    """使用LLM进行语义级校验（需要LLM接口）"""
    prompt = f"""以下是一份OCR识别结果，请检查是否有明显错误：

    === OCR结果 ===
    {text[:2000]}

    === 校验规则 ===
    {chr(10).join(f"{i+1}. {r}" for i, r in enumerate(rules))}

    请返回JSON格式：{{"issues": ["问题1", "问题2"], "overall_quality": "good/mediocre/poor"}}
    """
    # 调用LLM接口（如OpenAI、Claude等）
    # response = openai.ChatCompletion.create(...)
    return {"issues": [], "overall_quality": "good"}
```

### 校验规则总结

| 校验项 | 类型 | 严重程度 |
|-------|------|---------|
| 空内容检测 | 完整性 | 错误 |
| 乱码检测 | 完整性 | 错误 |
| 必需字段缺失 | 完整性 | 错误 |
| 电话号码格式 | 格式 | 警告 |
| 金额异常大 | 业务规则 | 警告 |
| 多订单号 | 业务规则 | 警告 |
| 语言比例异常 | 质量 | 警告 |
| 结果过短 | 完整性 | 警告 |

---

## Batch Processing

Process multiple PDFs in one pass — useful for invoice batches, multi-page scans, or supplier document folders.

### pymupdf batch

```python
# Extract text from all PDFs in a folder
import pymupdf
from pathlib import Path

folder = Path("docs/")
for pdf_path in sorted(folder.glob("*.pdf")):
    doc = pymupdf.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    print(f"=== {pdf_path.name} ===")
    print(text[:500])  # preview
    doc.close()
```

### marker-pdf batch (parallel workers)

```bash
marker /path/to/folder --workers 4    # Parallel conversion
```

### marker batch with JSON output (structured extraction)

```bash
for f in *.pdf; do
  python scripts/extract_marker.py "$f" --json > "${f%.pdf}.json"
done
```

### Batch + table extraction + 1688 order processing

See `references/batch-ocr-workflow.md` for a complete pipeline that:
- Detects scanned vs text-based PDFs automatically
- Routes to marker-pdf or pymupdf accordingly
- Extracts tables as CSV
- Parses 1688 order fields (order ID, amounts, SKU codes)

---

## Table Structured Extraction

### pymupdf (basic tables)

```bash
python scripts/extract_pymupdf.py document.pdf --tables
```

```python
import pymupdf
doc = pymupdf.open("document.pdf")
for i, page in enumerate(doc):
    tables = page.find_tables()
    for j, table in enumerate(tables.tables):
        df = table.to_pandas()
        print(f"Page {i+1}, Table {j+1}:")
        print(df.to_markdown(index=False))
        df.to_csv(f"table_p{i+1}_t{j+1}.csv", index=False)  # save
```

### marker-pdf (high-accuracy tables)

marker-pdf extracts tables as markdown with cell boundaries. Parse like this:

```python
import re

def parse_table_from_markdown(md_text):
    """Parse a markdown table into a list of dicts (rows)."""
    lines = [l.strip() for l in md_text.splitlines() if l.strip().startswith("|")]
    # Skip separator line (|---|---|)
    data_lines = [l for l in lines if not re.match(r"^\|[\s|-]+\|$", l)]
    if len(data_lines) < 2:
        return []

    # Parse header
    header = [cell.strip() for cell in data_lines[0].strip("|").split("|")]
    rows = []
    for line in data_lines[2:]:  # skip header + separator
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == len(header):
            rows.append(dict(zip(header, cells)))
    return rows

# Use with marker output:
# result = converter("scanned_invoice.pdf")
# rows = parse_table_from_markdown(result.markdown)
```

### Table detection fallback: camelot + tabula

```bash
pip install camelot-py
```

```python
import camelot

tables = camelot.read_pdf("document.pdf", pages="1-end", flavor="stream")
for i, table in enumerate(tables):
    print(f"Table {i+1}:")
    print(table.df.to_markdown())
    table.to_csv(f"table_{i}.csv")
```

---

## 1688 Order Recognition

1688 order confirmations and supplier receipts are typically:
- Scanned PDFs (not text-based)
- Mixed Chinese + English
- Contain tables: SKU codes, quantities, unit prices, totals
- Often have red stamps / seals

**Best pipeline**:

```bash
# Step 1: Convert with marker-pdf (OCR + layout)
python scripts/extract_marker.py 1688_order.pdf --json

# Step 2: Parse the JSON/markdown for key fields
```

**Key fields to extract from 1688 orders**:
- `订单号` (Order ID)
- `供应商` (Supplier name)
- `下单时间` (Order date)
- `商品名称` / `SKU` / `数量` / `单价` / `金额`
- `合计` / `总金额` (Total amount)
- `运费`
- `实付金额` (Actual paid)

**Regex patterns for common fields**:

```python
import re

def extract_1688_order(text):
    patterns = {
        "order_id":     r"订单号[：:]\s*([A-Z0-9]{10,})",
        "total_amount":  r"合计[：:]\s*￥?([\d,]+\.?\d*)",
        "actual_paid":   r"实付金额[：:]\s*￥?([\d,]+\.?\d*)",
        "freight":       r"运费[：:]\s*￥?([\d,]+\.?\d*)",
        "order_date":    r"下单时间[：:]\s*(\d{4}[-/]\d{2}[-/]\d{2})",
    }
    result = {}
    for field, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            result[field] = m.group(1).strip()
    return result
```

**⚠️ Pitfall: red stamp areas cause OCR errors on numbers**
1688 orders often have red official stamps that obscure amount fields. The OCR may produce `￥1,2OO.OO` instead of `￥1,200.00`. Always normalize digit-like characters:
```python
def normalize_ocr_digits(s):
    """Fix common OCR misreads of digits."""
    replacements = {"O": "0", "o": "0", "l": "1", "I": "1", "S": "5", "s": "5"}
    return "".join(replacements.get(c, c) for c in s)
```

---

## Multi-language Mixed-content Processing

Documents with Chinese + English + numbers (e.g. 1688 orders, shipping docs) need special handling.

### Language detection

```bash
pip install langdetect
```

```python
from langdetect import detect, detect_langs

def detect_lang(text):
    return detect(text[:500])  # 'zh-cn', 'en', 'ja', etc.

def detect_langs_full(text):
    return detect_langs(text[:500])  # [(lang, confidence), ...]
```

### Segment by language before parsing

```python
import re

def split_mixed_markdown(md_text):
    """Split markdown into Chinese and non-Chinese blocks."""
    # Chinese character range
    chinese_parts = re.findall(r"[\u4e00-\u9fff]+[^\n]*", md_text)
    english_parts = re.split(r"[\u4e00-\u9fff]+[^\n]*", md_text)
    return {"chinese": chinese_parts, "english": english_parts}
```

### Chinese + English table headers (common in 1688)

```python
# Normalize table headers that mix Chinese and English
def normalize_table_header(header):
    """Unify common Chinese/English header variants."""
    mapping = {
        "商品名称": "product_name", "品名": "product_name",
        "SKU": "sku", "规格": "spec", "规格型号": "spec",
        "数量": "quantity", "数量(PCS)": "quantity", "Qty": "quantity",
        "单价": "unit_price", "单价(元)": "unit_price",
        "金额": "amount", "金额(元)": "amount", "总金额": "total_amount",
        "下单时间": "order_date", "创建时间": "created_at",
        "供应商": "supplier", "店铺": "shop",
    }
    return mapping.get(header.strip(), header.strip())
```

---

## Post-OCR Validation & Quality Checks

Always validate OCR results — errors are common, especially in scanned documents.

### Mandatory checks after OCR

```python
def validate_ocr_result(text, min_chars=50):
    """Basic sanity checks on OCR output."""
    issues = []

    # Check 1: Is it empty or too short?
    if not text or len(text) < min_chars:
        issues.append(f"Text too short ({len(text)} chars)")

    # Check 2: Excessive garbled characters (unrecognized glyphs)
    garbled_ratio = sum(1 for c in text if ord(c) > 0x3000 and ord(c) < 0x9fff) / max(len(text), 1)
    if garbled_ratio > 0.5:
        issues.append("High CJK garbled character ratio — possible OCR failure")

    # Check 3: Suspicious digit normalization needed
    suspicious = re.findall(r"[OIls]{4,}", text)
    if suspicious:
        issues.append(f"Possible digit OCR errors: {suspicious[:3]}")

    # Check 4: Expected fields present (customize per document type)
    # For 1688 orders:
    if "订单号" in text and not re.search(r"[A-Z0-9]{10,}", text):
        issues.append("Order ID pattern not found — OCR may have misread it")

    return issues

def ocr_with_validation(pdf_path, expected_fields=None):
    """Full pipeline: extract + validate + report."""
    import pymupdf4llm
    import re

    md = pymupdf4llm.to_markdown(pdf_path)
    issues = validate_ocr_result(md)

    # Check specific fields if provided
    if expected_fields:
        for field in expected_fields:
            if field not in md:
                issues.append(f"Expected field not found: {field}")

    return {"text": md, "issues": issues, "pass": len(issues) == 0}
```

### Whitespace / layout sanity

```python
# Check for common layout failures
def check_layout_issues(text):
    issues = []
    lines = text.split("\n")

    # Too many empty lines = column detection failure
    empty_ratio = sum(1 for l in lines if not l.strip()) / max(len(lines), 1)
    if empty_ratio > 0.4:
        issues.append(f"High empty line ratio ({empty_ratio:.0%}) — possible column merge error")

    # Line too long = table cell spillover
    for i, line in enumerate(lines):
        if len(line) > 500:
            issues.append(f"Line {i+1} too long ({len(line)} chars) — possible table spillover")

    return issues
```

### Validate extracted amounts

```python
def validate_amounts(text):
    """Check for common OCR amount errors in financial documents."""
    issues = []

    # Find all currency amounts
    amounts = re.findall(r"[￥$€£]?\s*([\d,]+\.?\d*)", text)

    for amt in amounts:
        # OCR sometimes reads '2' as 'Z' or 'S'
        if re.match(r"^[ZSOls]{3,}$", amt.replace(",", "")):
            issues.append(f"Suspicious amount (OCR error?): {amt}")

    # Check for obviously wrong totals (e.g. total < line items)
    money_vals = []
    for amt in amounts:
        try:
            money_vals.append(float(amt.replace(",", "")))
        except ValueError:
            pass

    if len(money_vals) >= 2:
        max_val, second_max = sorted(money_vals)[-2:]
        if max_val > second_max * 10:
            issues.append(f"Largest amount ({max_val}) >> second largest ({second_max}) — possible OCR misread")

    return issues
```

### Validation pipeline with retry

```python
def ocr_with_retry(pdf_path, max_attempts=2):
    """
    Try marker-pdf first, fall back to pymupdf, validate each result.
    Returns the best result with validation report.
    """
    import pymupdf4llm
    import shutil

    free_gb = shutil.disk_usage("/").free / (1024**3)

    if free_gb < 5:
        # Fall back to pymupdf
        doc = pymupdf.open(pdf_path)
        text = "\n".join(page.get_text() for page in doc)
        issues = validate_ocr_result(text)
        return {"text": text, "issues": issues + ["marker-pdf skipped: insufficient disk"], "engine": "pymupdf"}

    # Try marker-pdf
    for attempt in range(max_attempts):
        md = pymupdf4llm.to_markdown(pdf_path)
        issues = validate_ocr_result(md)
        layout_issues = check_layout_issues(md)

        if len(issues) == 0 and len(layout_issues) == 0:
            return {"text": md, "issues": [], "engine": "marker-pdf"}

    return {
        "text": md,
        "issues": issues + layout_issues,
        "engine": "marker-pdf",
        "warning": "Validation issues found but returning best effort"
    }
```

---

## Notes

- `web_extract` is always first choice for URLs
- pymupdf is the safe default — instant, no models, works everywhere
- marker-pdf is for OCR, scanned docs, equations, complex layouts — install only when needed
- Both helper scripts accept `--help` for full usage
- marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on first use
- For Word docs: `pip install python-docx` (better than OCR — parses actual structure)
- For PowerPoint: see the `powerpoint` skill (uses python-pptx)
