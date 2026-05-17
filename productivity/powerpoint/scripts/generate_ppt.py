#!/usr/bin/env python3
"""
Automated PPT generator for 1688 supplier workflows.

Templates:
  1688_supplier_report    - 1688供应商汇报PPT
  purchase_order          - 采购订单确认PPT
  supplier_comparison     - 供应商比价PPT

Usage:
    python generate_ppt.py 1688_supplier_report --data data.json --output out.pptx
    python generate_ppt.py purchase_order --data data.json --output out.pptx
    python generate_ppt.py supplier_comparison --data data.json --output out.pptx

Data file format (JSON):
    {
        "supplier_name": "XXX公司",
        "contact": "张三",
        "phone": "138xxxx",
        "items": [...],
        "date": "2025-01-01",
        ...
    }

Each template type has required/optional fields - see template README.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = SKILL_DIR / "templates"
SCRIPTS_DIR = SKILL_DIR / "scripts"

TEMPLATE_SLIDES = {
    "1688_supplier_report": [
        "slide_cover.xml",
        "slide_summary.xml",
        "slide_product.xml",
        "slide_pricing.xml",
        "slide_quality.xml",
        "slide_contact.xml",
    ],
    "purchase_order": [
        "slide_cover.xml",
        "slide_order_info.xml",
        "slide_items.xml",
        "slide_terms.xml",
        "slide_sign.xml",
    ],
    "supplier_comparison": [
        "slide_cover.xml",
        "slide_overview.xml",
        "slide_comparison.xml",
        "slide_ranking.xml",
        "slide_recommendation.xml",
    ],
}


def cmd(args, cwd=None):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running: {' '.join(args)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout


def render_with_pptxgenjs(template_type: str, data: dict, output_path: str):
    """Use pptxgenjs to generate from template."""
    import tempfile, json as jsonmod

    workdir = tempfile.mkdtemp()
    spec_path = os.path.join(workdir, "spec.json")
    with open(spec_path, "w", encoding="utf-8") as f:
        jsonmod.dump(data, f, ensure_ascii=False, indent=2)

    template_dir = TEMPLATES_DIR / template_type
    if not template_dir.exists():
        print(f"Template '{template_type}' not found. Available: {list(TEMPLATE_SLIDES.keys())}", file=sys.stderr)
        sys.exit(1)

    render_script = template_dir / "render.js"
    if not render_script.exists():
        print(f"No render.js found in {template_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Running render script for {template_type}...")
    output = cmd(["node", str(render_script), spec_path, output_path], cwd=workdir)
    print(output)
    shutil.rmtree(workdir)


def build_from_template_xml(template_type: str, data: dict, output_path: str):
    """Build PPTX by unpacking a base template and injecting data via XML manipulation."""
    template_dir = TEMPLATES_DIR / template_type
    base_pptx = template_dir / "base.pptx"

    if not base_pptx.exists():
        print(f"No base.pptx found in {template_dir}. Use --pptxgenjs mode instead.", file=sys.stderr)
        sys.exit(1)

    workdir = tempfile.mkdtemp()
    unpacked = os.path.join(workdir, "unpacked")
    cmd(["python", str(SCRIPTS_DIR / "office" / "unpack.py"), str(base_pptx), unpacked])

    # Inject data into slides
    _inject_data(template_type, unpacked, data)

    cmd(["python", str(SCRIPTS_DIR / "office" / "pack.py"), unpacked, output_path])
    shutil.rmtree(workdir)


def _inject_data(template_type: str, unpacked_dir: str, data: dict):
    """Replace placeholder tokens in slide XML files with data values."""
    import re

    slides_dir = Path(unpacked_dir) / "ppt" / "slides"
    for slide_file in slides_dir.glob("slide*.xml"):
        content = slide_file.read_text(encoding="utf-8")
        original = content

        # Replace common placeholders
        replacements = {
            "{{SUPPLIER_NAME}}": data.get("supplier_name", ""),
            "{{CONTACT}}": data.get("contact", ""),
            "{{PHONE}}": data.get("phone", ""),
            "{{EMAIL}}": data.get("email", ""),
            "{{DATE}}": data.get("date", ""),
            "{{COMPANY}}": data.get("company", ""),
            "{{ORDER_NO}}": data.get("order_no", ""),
            "{{TOTAL_AMOUNT}}": data.get("total_amount", ""),
            "{{CURRENCY}}": data.get("currency", "CNY"),
        }

        for placeholder, value in replacements.items():
            content = content.replace(placeholder, str(value))

        # Handle item rows for purchase order / supplier comparison
        if template_type in ("purchase_order", "supplier_comparison"):
            content = _inject_table_data(content, template_type, data)

        if content != original:
            slide_file.write_text(content, encoding="utf-8")


def _inject_table_data(content: str, template_type: str, data: dict) -> str:
    """Replace table row placeholders with actual data rows."""
    items = data.get("items", [])
    if not items:
        return content

    if template_type == "purchase_order":
        # Build item rows for order confirmation
        row_template = '<a:tr><a:tc><a:p><a:r><a:rPr lang="zh-CN"/><a:t>{name}</a:t></a:r></a:p></a:tc><a:tc><a:p><a:r><a:rPr lang="en-US"/><a:t>{sku}</a:t></a:r></a:p></a:tc><a:tc><a:p><a:r><a:rPr lang="en-US"/><a:t>{qty}</a:t></a:r></a:p></a:tc><a:tc><a:p><a:r><a:rPr lang="en-US"/><a:t>{price}</a:t></a:r></a:p></a:tc><a:tc><a:p><a:r><a:rPr lang="en-US"/><a:t>{subtotal}</a:t></a:r></a:p></a:tc></a:tr>'
        rows = ""
        for item in items:
            rows += row_template.format(
                name=item.get("name", ""),
                sku=item.get("sku", ""),
                qty=item.get("qty", ""),
                price=item.get("price", ""),
                subtotal=item.get("subtotal", ""),
            )
        content = content.replace("{{ITEM_ROWS}}", rows)

    elif template_type == "supplier_comparison":
        # Build comparison rows for supplier comparison
        row_template = '<a:tr><a:tc><a:p><a:r><a:rPr lang="zh-CN"/><a:t>{supplier}</a:t></a:r></a:p></a:tc><a:tc><a:p><a:r><a:rPr lang="en-US"/><a:t>{price}</a:t></a:r></a:p></a:tc><a:tc><a:p><a:r><a:rPr lang="en-US"/><a:t>{moq}</a:t></a:r></a:p></a:tc><a:tc><a:p><a:r><a:rPr lang="en-US"/><a:t>{rating}</a:t></a:r></a:p></a:tc><a:tc><a:p><a:r><a:rPr lang="en-US"/><a:t>{lead_time}</a:t></a:r></a:p></a:tc></a:tr>'
        rows = ""
        for item in items:
            rows += row_template.format(
                supplier=item.get("supplier", ""),
                price=item.get("price", ""),
                moq=item.get("moq", ""),
                rating=item.get("rating", ""),
                lead_time=item.get("lead_time", ""),
            )
        content = content.replace("{{COMPARISON_ROWS}}", rows)

    return content


def main():
    parser = argparse.ArgumentParser(description="Generate procurement PPTs from templates")
    parser.add_argument("template", choices=list(TEMPLATE_SLIDES.keys()), help="Template type")
    parser.add_argument("--data", required=True, help="JSON data file")
    parser.add_argument("--output", required=True, help="Output .pptx path")
    parser.add_argument("--mode", choices=["pptxgenjs", "xml"], default="pptxgenjs", help="Generation mode")
    parser.add_argument("--title", help="Presentation title (overrides data)")
    parser.add_argument("--subtitle", help="Subtitle")
    parser.add_argument("--date", help="Date string (overrides data.date)")

    args = parser.parse_args()

    with open(args.data, encoding="utf-8") as f:
        data = json.load(f)

    # CLI overrides
    if args.title:
        data["title"] = args.title
    if args.subtitle:
        data["subtitle"] = args.subtitle
    if args.date:
        data["date"] = args.date

    if args.mode == "pptxgenjs":
        render_with_pptxgenjs(args.template, data, args.output)
    else:
        build_from_template_xml(args.template, data, args.output)

    print(f"Generated: {args.output}")


if __name__ == "__main__":
    main()
