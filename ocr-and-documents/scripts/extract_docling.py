#!/usr/bin/env python3
"""
extract_docling.py — 用 Docling 把任意文档(PDF/DOCX/PPTX/图片)转成结构化 Markdown/JSON。
优于分散的 pymupdf/marker：单依赖、版面+表格+公式+OCR 全内置，自动检测。
用法:
  python extract_docling.py doc.pdf                 # 打印 Markdown
  python extract_docling.py doc.pdf --json          # 打印 JSON(含结构/表格)
  python extract_docling.py doc.pdf --out out/      # 落盘 .md/.json
  python extract_docling.py a.pdf b.docx --out out/ # 批量
  python extract_docling.py doc.pdf --no-ocr        # 关闭 OCR(纯文本 PDF 更快)
  python extract_docling.py doc.pdf --pages 0-4     # 限定页(可选)
"""
import argparse, sys, os, glob, json

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", help="PDF/DOCX/PPTX/图片路径或 URL")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--out", help="输出目录(落盘而非打印)")
    ap.add_argument("--no-ocr", action="store_true", help="禁用 OCR")
    ap.add_argument("--pages", help="页范围 如 0-4")
    args = ap.parse_args()

    from docling.document_converter import DocumentConverter
    from docling.datamodel.pipeline_options import PdfPipelineOptions

    pipeline_opts = None
    if args.no_ocr or args.pages:
        pipeline_opts = PdfPipelineOptions()
        pipeline_opts.do_ocr = not args.no_ocr
        if args.pages:
            a, b = args.pages.split("-")
            pipeline_opts.page_range = (int(a), int(b))

    conv_args = {}
    if pipeline_opts is not None:
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import PdfFormatOption
        conv_args["format_options"] = {InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_opts)}

    converter = DocumentConverter(**conv_args)
    files = []
    for inp in args.inputs:
        if os.path.isdir(inp):
            files.extend(glob.glob(os.path.join(inp, "*")))
        else:
            files.append(inp)

    for f in files:
        try:
            res = converter.convert(f)
            doc = res.document
            if args.out:
                os.makedirs(args.out, exist_ok=True)
                base = os.path.splitext(os.path.basename(str(f)))[0]
                if args.json:
                    with open(os.path.join(args.out, base + ".json"), "w") as fh:
                        json.dump(doc.export_to_dict(), fh, ensure_ascii=False, indent=2)
                else:
                    with open(os.path.join(args.out, base + ".md"), "w") as fh:
                        fh.write(doc.export_to_markdown())
                print(f"[OK] {f} -> {args.out}/{base}.{'json' if args.json else 'md'}", file=sys.stderr)
            else:
                if args.json:
                    print(json.dumps(doc.export_to_dict(), ensure_ascii=False, indent=2))
                else:
                    print(doc.export_to_markdown())
        except Exception as e:
            print(f"[ERR] {f}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
