# Batch OCR Workflow — Complete Pipeline

End-to-end pipeline for processing a folder of mixed PDFs (scanned invoices, 1688 orders, supplier receipts).

## Decision Tree

```
PDF folder
    │
    ├─ Is it scanned? (image-based, not text)
    │     YES → marker-pdf (OCR engine)
    │     NO  → pymupdf (fast text extraction)
    │
    └─ Contains tables?
          YES → extract tables as CSV
          NO  → plain text

    └─ 1688 order?
          YES → parse key fields (order_id, amounts, SKU)
          NO  → generic extraction
```

## Auto-detect scanned vs text-based

```python
import pymupdf
from pathlib import Path

def is_scanned_pdf(pdf_path):
    """Return True if PDF is image-based (scanned), False if text-based."""
    doc = pymupdf.open(pdf_path)
    for page in doc:
        text = page.get_text()
        if text and len(text.strip()) > 50:
            doc.close()
            return False  # has real text
    doc.close()
    return True  # no readable text → likely scanned
```

## Full batch pipeline

```python
import pymupdf
import pymupdf4llm
from pathlib import Path
import json
import re

INPUT_DIR = Path("input_orders/")
OUTPUT_DIR = Path("extracted_orders/")
OUTPUT_DIR.mkdir(exist_ok=True)

# Normalize OCR digit errors (common in 1688 documents)
OCR_DIGIT_MAP = str.maketrans({"O": "0", "o": "0", "l": "1", "I": "1", "S": "5", "s": "5"})

def normalize_amount(s):
    if not s:
        return None
    cleaned = s.translate(OCR_DIGIT_MAP).replace(",", "").replace(" ", "")
    try:
        return float(cleaned)
    except ValueError:
        return None

def extract_1688_fields(text):
    """Extract key fields from 1688 order OCR text."""
    patterns = {
        "order_id":     r"订单号[：:]\s*([A-Z0-9]{10,})",
        "total_amount": r"合计[：:]\s*￥?([\d,]+\.?\d*)",
        "actual_paid":  r"实付金额[：:]\s*￥?([\d,]+\.?\d*)",
        "freight":      r"运费[：:]\s*￥?([\d,]+\.?\d*)",
        "order_date":   r"下单时间[：:]\s*(\d{4}[-/]\d{2}[-/]\d{2})",
        "supplier":     r"供应商[：:]\s*(.+?)(?:\n|$)",
    }
    result = {}
    for field, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            val = m.group(1).strip()
            if field in ("total_amount", "actual_paid", "freight"):
                val = normalize_amount(val)
            result[field] = val
    return result

def process_pdf(pdf_path):
    """Process a single PDF: detect type, extract, return structured result."""
    result = {
        "file": pdf_path.name,
        "engine": None,
        "text": "",
        "tables": [],
        "fields": {},
        "is_scanned": None,
        "issues": [],
    }

    is_scanned = is_scanned_pdf(pdf_path)
    result["is_scanned"] = is_scanned

    if is_scanned:
        # Use marker-pdf for OCR
        try:
            md = pymupdf4llm.to_markdown(str(pdf_path))
            result["engine"] = "marker-pdf"
            result["text"] = md
        except Exception as e:
            result["issues"].append(f"marker-pdf failed: {e}")
            doc = pymupdf.open(pdf_path)
            result["text"] = "\n".join(p.get_text() for p in doc)
            result["engine"] = "pymupdf-fallback"
    else:
        doc = pymupdf.open(pdf_path)
        result["text"] = "\n".join(p.get_text() for p in doc)
        result["engine"] = "pymupdf"

    # Extract tables
    try:
        doc = pymupdf.open(pdf_path)
        for i, page in enumerate(doc):
            tables = page.find_tables()
            for j, table in enumerate(tables.tables):
                df = table.to_pandas()
                csv_path = OUTPUT_DIR / f"{pdf_path.stem}_p{i+1}_t{j+1}.csv"
                df.to_csv(csv_path, index=False)
                result["tables"].append(str(csv_path))
        doc.close()
    except Exception as e:
        result["issues"].append(f"table extraction failed: {e}")

    # Try 1688 field extraction
    fields = extract_1688_fields(result["text"])
    if fields:
        result["fields"] = fields

    # Validate
    if len(result["text"]) < 50:
        result["issues"].append("Text suspiciously short — possible OCR failure")

    return result

def run_batch(input_dir):
    """Process all PDFs in a folder."""
    results = []
    for pdf_path in sorted(Path(input_dir).glob("*.pdf")):
        print(f"Processing: {pdf_path.name}")
        r = process_pdf(pdf_path)
        results.append(r)

        out_json = OUTPUT_DIR / f"{pdf_path.stem}.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)

        print(f"  → engine={r['engine']}, tables={len(r['tables'])}, issues={len(r['issues'])}")

    print("\n=== BATCH SUMMARY ===")
    for r in results:
        status = "PASS" if not r["issues"] else f"ISSUES({len(r['issues'])})"
        print(f"  [{status}] {r['file']} | engine={r['engine']}")

    return results
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `Text too short` on a scanned PDF | marker-pdf not installed | Install marker-pdf or use baidu-ocr |
| Amount shows `1,2OO.OO` | Red stamp OCR error | Use `normalize_amount()` with OCR_DIGIT_MAP |
| Table CSV empty | Table borders not detected | Try `camelot` fallback or manual extraction |
| `order_id` pattern not found | Chinese colon vs English colon | Regex uses `[：:]` to match both `：` and `:` |
| Mixed Chinese/English header | 1688 tables use mixed headers | Use `normalize_table_header()` to map to English keys |
