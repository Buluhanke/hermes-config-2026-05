#!/usr/bin/env python3
"""
read_page.py — CLI entry point for browser-read-funnel

Usage:
  python3 read_page.py <url> [options]

Examples:
  python3 read_page.py https://example.com
  python3 read_page.py https://example.com --format md
  python3 read_page.py https://example.com --force crawl4ai
  python3 read_page.py https://example.com --shadow-dom
  python3 read_page.py https://example.com -o output.md
"""

import argparse, asyncio, json, pathlib, sys, textwrap
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from browser_read_funnel import read_page, ReadResult

MAX_PREVIEW = 3000


def fmt_result(r: ReadResult, fmt: str = "text") -> str:
    if fmt == "json":
        return json.dumps({
            "success": r.success,
            "source": r.source,
            "via": r.via,
            "markdown": r.markdown,
            "error": r.error,
            "url": r.url,
        }, ensure_ascii=False, indent=2)

    if not r.success:
        return f"❌ [{r.via}]\n   错误: {r.error}"

    md = r.markdown
    preview = len(md) > MAX_PREVIEW
    if preview:
        md = md[:MAX_PREVIEW] + f"\n\n…（省略 {len(r.markdown)-MAX_PREVIEW:,} 字符）"

    sep = "─" * 80
    return (
        f"✅ [{r.via}]\n"
        f"   字符数: {len(r.markdown):,}\n"
        f"   来源:   {r.url}\n"
        f"\n{sep}\n"
        f"{md}\n"
        f"{sep}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="browser-read-funnel CLI — 统一网页内容读取",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            读取优先级（默认 auto 模式）:
              1. Firecrawl（云端，快速）
              2. Scrapling（反反爬，动态页面）
              3. Crawl4AI（本地，Shadow DOM 专用）
              4. 截图 OCR（最终降级兜底）

            示例:
              python3 read_page.py https://example.com
              python3 read_page.py https://example.com --force firecrawl
              python3 read_page.py https://example.com -o out.md
        """),
    )
    parser.add_argument("url", help="目标 URL")
    parser.add_argument("-o", "--output", dest="output", metavar="FILE",
                        help="输出到文件（默认打印到 stdout）")
    parser.add_argument("-f", "--format", dest="format", choices=["text", "json"],
                        default="text", help="输出格式（默认 text）")
    parser.add_argument("--force", dest="force",
                        choices=["firecrawl", "scrapling", "crawl4ai", "auto"],
                        default="auto", help="强制使用指定工具（默认 auto）")
    parser.add_argument("--shadow-dom", dest="shadow_dom", action="store_true",
                        help="强制开启 Shadow DOM 递归展开（仅 Crawl4AI）")
    parser.add_argument("--timeout", dest="timeout", type=int, default=60,
                        help="每步超时秒数（默认 60）")
    parser.add_argument("--selector", dest="selector", metavar="CSS",
                        help="[预留] CSS 选择器过滤")

    args = parser.parse_args()
    url = args.url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    r: ReadResult = asyncio.run(
        read_page(
            url=url,
            prefer=args.force,
            flatten_shadow_dom=args.shadow_dom,
            timeout=args.timeout,
        )
    )

    output = fmt_result(r, fmt=args.format)

    if args.output:
        pathlib.Path(args.output).write_text(
            r.markdown if args.format == "text" else output, encoding="utf-8"
        )
        print(f"✅ 已写入: {args.output}（{len(r.markdown):,} 字符）", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
