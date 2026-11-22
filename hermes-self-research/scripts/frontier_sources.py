#!/usr/bin/env python3
"""
frontier_sources.py — 三大权威前沿源结构化拉取器
供 hermes-self-research 每日自学直接吃全网最前沿，不靠 web_search 碰运气。

三个源（2026-11-22 实测可用性）：
  1. arXiv API          — http://export.arxiv.org/api/query  直连 ✅ (Atom feed)
  2. paperswithcode.co  — https://paperswithcode.co/api/v1/  直连 ✅ (REST JSON, 2052 papers)
  3. Awesome-AI4AI      — gh api repos/KaiWU5/Awesome-AI4AI/readme  走 api.github.com ✅ (415KB, 每周更新)

Hugging Face trending 本机 SSL 不通，已用 paperswithcode（同类论文+代码源）替代。

用法：
  frontier_sources.py                    # 拉全部，输出精简 markdown 摘要
  frontier_sources.py --json             # 输出结构化 JSON（供程序消费）
  frontier_sources.py --source arxiv     # 只拉某源 (arxiv|pwc|ai4ai)
  frontier_sources.py --days 2           # 只看最近 N 天（默认2）

设计：纯 stdlib + gh CLI，零第三方依赖，零 LLM，可被 subprocess 直接调。
"""
import argparse
import base64
import json
import re
import ssl
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "hermes-self-research/1.0"}

# 关注的 agent 关键词（命中才高亮，避免全量噪音）
HOT = ["agent", "memory", "harness", "self-improv", "self-evolv", "browser",
       "computer use", "benchmark", "tool use", "multi-agent", "reasoning", "rl"]


def http_get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read()


def fetch_arxiv(days=2, max_results=40):
    """arXiv cs.AI/cs.CL/cs.LG 最近论文。http/https 双端点重试。"""
    q = urllib.parse.quote("(cat:cs.AI OR cat:cs.CL OR cat:cs.LG)")
    out = []
    raw = None
    for base in ["https://export.arxiv.org/api/query", "http://export.arxiv.org/api/query"]:
        url = (f"{base}?search_query={q}"
               f"&sortBy=submittedDate&sortOrder=descending&max_results={max_results}")
        try:
            raw = http_get(url, timeout=30)
            break
        except Exception:
            continue
    try:
        if raw is None:
            raise RuntimeError("arxiv both endpoints failed")
        root = ET.fromstring(raw)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for e in root.findall("a:entry", ns):
            title = (e.findtext("a:title", "", ns) or "").strip().replace("\n", " ")
            summary = (e.findtext("a:summary", "", ns) or "").strip().replace("\n", " ")
            link = e.findtext("a:id", "", ns)
            published = e.findtext("a:published", "", ns)[:10]
            out.append({"title": title, "summary": summary[:240],
                        "url": link, "date": published,
                        "hot": any(k in title.lower() for k in HOT)})
    except Exception as ex:
        out.append({"error": str(ex)})
    return out


def fetch_pwc(limit=30):
    """Papers with Code 最新论文。"""
    out = []
    try:
        raw = http_get("https://paperswithcode.co/api/v1/papers/?page=1")
        data = json.loads(raw)
        for p in data.get("results", [])[:limit]:
            title = (p.get("title") or "").strip()
            out.append({"title": title,
                        "url": p.get("source_url") or p.get("paper_url") or "",
                        "source": p.get("source", ""),
                        "hot": any(k in title.lower() for k in HOT)})
    except Exception as ex:
        out.append({"error": str(ex)})
    return out


def fetch_ai4ai():
    """Awesome-AI4AI README，解析出最新榜单表格行。"""
    out = []
    try:
        r = subprocess.run(
            ["gh", "api", "repos/KaiWU5/Awesome-AI4AI/readme"],
            capture_output=True, timeout=40)
        data = json.loads(r.stdout)
        text = base64.b64decode(data["content"]).decode("utf-8", "replace")
        # 抓 Top Ranking 表格里的论文行（| Paper | Venue | ... |）
        rows = []
        for line in text.split("\n"):
            if line.startswith("|") and ("arXiv" in line or "ECAI" in line or "Nature" in line):
                cells = [c.strip() for c in line.split("|")]
                if len(cells) > 3 and cells[1] and cells[1] not in ("Paper", "---"):
                    rows.append(line[:220])
        out = rows[:15]
    except Exception as ex:
        out.append({"error": str(ex)})
    return out


def render(args, data):
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    lines = ["# 前沿源速览（hermes-self-research）\n"]
    arxiv = data.get("arxiv", [])
    hot = [a for a in arxiv if a.get("hot")]
    lines.append(f"## arXiv 最新（{len(arxiv)} 篇，命中关注 {len(hot)} 篇）")
    for a in (hot or arxiv)[:12]:
        if a.get("error"):
            lines.append(f"  ERR {a['error']}")
            continue
        lines.append(f"  - [{a['date']}] {a['title'][:110]}")
        lines.append(f"      {a['url']}")

    pwc = data.get("pwc", [])
    lines.append(f"\n## Papers with Code 最新（{len(pwc)} 篇）")
    for p in [x for x in pwc if x.get("hot")][:10] or pwc[:8]:
        if p.get("error"):
            lines.append(f"  ERR {p['error']}")
            continue
        lines.append(f"  - {p['title'][:110]}  ({p.get('source','')})")

    ai4ai = data.get("ai4ai", [])
    lines.append(f"\n## Awesome-AI4AI 高引榜单（{len(ai4ai)} 行）")
    for row in ai4ai[:12]:
        if isinstance(row, dict):
            lines.append(f"  ERR {row.get('error')}")
        else:
            lines.append(f"  {row}")

    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["arxiv", "pwc", "ai4ai"], help="只拉某源")
    ap.add_argument("--days", type=int, default=2, help="arXiv 关注天数（当前用于过滤提示）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    tasks = {"arxiv": lambda: fetch_arxiv(args.days),
             "pwc": fetch_pwc,
             "ai4ai": fetch_ai4ai}
    keys = [args.source] if args.source else list(tasks)
    data = {k: tasks[k]() for k in keys}
    render(args, data)


if __name__ == "__main__":
    sys.exit(main())
