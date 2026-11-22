#!/usr/bin/env python3
"""fact_gate.py — fact_store 写入门控 + 留存审计（零 LLM 依赖，纯 stdlib）

对应 2026-11 研究的两条记忆机制：
  - ARISE（2611.23588）：留出集准确率门控 —— 本地近似为「与已被召回过的
    高质量 fact 做 token Jaccard，过高判重复」。
  - Anchor（2611.10382）：源决策筛选 —— 本地近似为「只用 retrieval_count /
    helpful_count 证明被真正决策用过的记忆，未用过且低质者降级」。

两种用法：
  1. 写入前门控（调 fact_store add 之前先跑）：
     python3 fact_gate.py check --content "..." [--category ... --tags ...]
     输出 verdict=accept|review|reject，reject 就不要写。
  2. 存量审计（周期跑）：
     python3 fact_gate.py audit [--apply] [--json]
     --apply 只给 ARCHIVE_CANDIDATE 打标记（tags 追加 gate:archive-candidate），
     绝不删除、绝不改 content，可回滚。报告写 ~/.hermes/fact_gate_report.md。

设计铁律：宁可标记不可删除；门控是辅助判断，不替代用户决定。
"""
import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path.home() / ".hermes" / "memory_store.db"
REPORT = Path.home() / ".hermes" / "fact_gate_report.md"

# 可验证信号：数字 / 百分比 / 路径 / 仓库 / 版本号 / arXiv 号 / 命令
VERIFIABLE = re.compile(
    r"(\d+(?:\.\d+)?\s*%|\bv\d+\.\d+|https?://|github\.com|/Users/|~/[\w.]+"
    r"|\.py\b|\.md\b|\.sh\b|arXiv\s*:?\s*\d|fact_id\s*=\s*\d+|\b\d{3,}\b)",
    re.I,
)
NOISE_WORDS = re.compile(r"(^|[^\u4e00-\u9fff])(测试|修复验证|修复测试|调试记录)([^\u4e00-\u9fff]|$)")
VAGUE_LABEL = re.compile(r"^\[[^\]]{2,12}\]\s*[^\d]{8,70}$")
BARE_TITLE = re.compile(r"^[A-Z][A-Za-z\s'\-]{4,79}$")
NAMED_ENTITY = re.compile(r"\b[A-Z][A-Za-z0-9\-]{2,}\b")
NOISE_SIGNALS = {"test_noise", "vague_label_line", "bare_title", "auto_arxiv"}


def tokens(text: str) -> set:
    """中英混合 token：英文整词 + 中文 bi/tri-gram。"""
    s = (text or "").lower()
    out = set(re.findall(r"[a-z][a-z0-9_.-]{2,}", s))
    for seg in re.findall(r"[\u4e00-\u9fff]+", s):
        for i in range(len(seg) - 1):
            out.add(seg[i:i + 2])
        for i in range(len(seg) - 2):
            out.add(seg[i:i + 3])
    return out


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def score_fact(content: str, category: str = "", rc: int = 0, hc: int = 0,
               trust: float = 0.0, is_new: bool = False):
    """返回 (0-100 分, 命中理由列表)。新增事实用 is_new=True 跳过「未召回」惩罚。"""
    s, why = 0, []
    text = (content or "").strip()
    n = len(text)

    if re.search(r"\d", text):
        s += 20
        why.append("has_number")
    if VERIFIABLE.search(text):
        s += 18
        why.append("has_verifiable_ref")
    if NAMED_ENTITY.search(text):
        s += 18
        why.append("named_entity")

    if n >= 120:
        s += 15
    elif n >= 60:
        s += 10
    elif n >= 30:
        s += 5
    else:
        s -= 15
        why.append("too_short")

    if NOISE_WORDS.search(text):
        s -= 45
        why.append("test_noise")
    if VAGUE_LABEL.match(text):
        s -= 35
        why.append("vague_label_line")
    if BARE_TITLE.match(text):
        s -= 25
        why.append("bare_title")

    if rc > 0:
        s += 20
        why.append("was_recalled")
    if hc > 0:
        s += 15
        why.append("was_helpful")
    if trust >= 0.7:
        s += 8
    if not is_new and rc == 0 and hc == 0:
        s -= 12
        why.append("never_used")
    if "arXiv AI |" in (category or "") or "arXiv摘要" in (category or ""):
        s -= 20
        why.append("auto_arxiv")
    return max(0, min(100, s)), why


def band(score: int) -> str:
    if score >= 55:
        return "KEEP"
    if score >= 30:
        return "WATCH"
    return "ARCHIVE_CANDIDATE"


def check(content: str, category: str = "", tags: str = "", probe: bool = True):
    """写入前门控。返回结构化 verdict，不抛异常。"""
    result: dict = {"verdict": "accept", "score": 0, "reasons": [],
                    "max_similarity": 0.0, "similar_to": None}
    try:
        score, why = score_fact(content, category, is_new=True)
        result["score"], result["reasons"] = score, why
        if probe and DB.exists():
            conn = sqlite3.connect(str(DB), timeout=10)
            # ARISE 近似：只跟「被召回过」的高质量事实比，避免跟噪声比出假重复
            rows = conn.execute(
                "SELECT fact_id, content FROM facts WHERE retrieval_count > 0"
            ).fetchall()
            conn.close()
            cand = tokens(content)
            best, best_id = 0.0, None
            for fid, text in rows:
                r = jaccard(cand, tokens(text or ""))
                if r > best:
                    best, best_id = r, fid
            result["max_similarity"] = round(best, 3)
            result["similar_to"] = best_id
            if best >= 0.78:
                why.append("near_duplicate")
        if result["max_similarity"] >= 0.78 or score < 25:
            result["verdict"] = "reject"
        elif score < 50:
            result["verdict"] = "review"
    except Exception as e:
        result["reasons"].append("gate_error: " + str(e)[:80])
    return result


def audit(apply: bool = False, as_json: bool = False):
    """存量审计。只读；--apply 仅打标记不删除。"""
    if not DB.exists():
        print("DB_NOT_FOUND:", DB)
        return 2
    conn = sqlite3.connect(str(DB), timeout=15)
    rows = conn.execute(
        "SELECT fact_id, content, category, tags, trust_score, retrieval_count, helpful_count "
        "FROM facts"
    ).fetchall()
    scored = []
    for fid, content, cat, tags, trust, rc, hc in rows:
        s, why = score_fact(content or "", cat or "", rc or 0, hc or 0, trust or 0)
        b = band(s)
        # 收窄归档：只标记带明确噪声信号（或极低分且从未使用）的条目。
        # 防止误伤「无数字但有实质内容」的有效知识（框架名/基准名/概念）。
        if s < 30:
            noise_hit = bool(NOISE_SIGNALS.intersection(why))
            if not noise_hit and not (s < 12 and "never_used" in why):
                b = "WATCH"
        scored.append({
            "fact_id": fid, "score": s, "band": b, "reasons": why,
            "category": cat, "retrieval_count": rc, "helpful_count": hc,
            "content": (content or "")[:120],
        })
    counts = {b: sum(1 for x in scored if x["band"] == b)
              for b in ("KEEP", "WATCH", "ARCHIVE_CANDIDATE")}
    marked = 0
    if apply:
        for x in scored:
            if x["band"] != "ARCHIVE_CANDIDATE":
                continue
            row = conn.execute("SELECT tags FROM facts WHERE fact_id=?",
                               (x["fact_id"],)).fetchone()
            tg = row[0] or ""
            if "gate:archive-candidate" in tg:
                continue
            new = (tg + " | gate:archive-candidate") if tg else "gate:archive-candidate"
            conn.execute("UPDATE facts SET tags=? WHERE fact_id=?", (new, x["fact_id"]))
            marked += 1
        conn.commit()
    conn.close()

    payload = {
        "generated_at": datetime.now().isoformat(),
        "total": len(scored), "bands": counts, "marked_this_run": marked,
        "archive_candidates": [x for x in scored if x["band"] == "ARCHIVE_CANDIDATE"],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if as_json:
        # stdout 只给精简摘要（完整明细在 REPORT 文件里），避免大 payload 被截断
        summary = {
            "generated_at": payload["generated_at"],
            "total": payload["total"],
            "bands": payload["bands"],
            "marked_this_run": payload["marked_this_run"],
            "archive_ids": [x["fact_id"] for x in payload["archive_candidates"]],
            "report": str(REPORT),
        }
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print(f"FACTS={len(scored)}  KEEP={counts['KEEP']}  WATCH={counts['WATCH']}  "
              f"ARCHIVE_CANDIDATE={counts['ARCHIVE_CANDIDATE']}")
        print(f"MARKED_THIS_RUN={marked}  REPORT={REPORT}")
        for x in payload["archive_candidates"][:25]:
            print(f"  #{x['fact_id']:>4} score={x['score']:>3} {','.join(x['reasons'])[:45]:<45} "
                  f"{x['content'][:55]}")
    return 0


def restore_buried():
    """恢复被旧 sentinel 机制埋掉的事实，返回恢复条数。"""
    conn = sqlite3.connect(str(DB), timeout=15)
    n = conn.execute("SELECT COUNT(*) FROM facts WHERE retrieval_count=-999").fetchone()[0]
    conn.execute("UPDATE facts SET retrieval_count=1 WHERE retrieval_count=-999")
    conn.commit()
    conn.close()
    return n


def main():
    ap = argparse.ArgumentParser(description="fact_store 写入门控 + 留存审计")
    sub = ap.add_subparsers(dest="cmd")
    chk = sub.add_parser("check", help="写入前门控")
    chk.add_argument("--content", required=True)
    chk.add_argument("--category", default="")
    chk.add_argument("--tags", default="")
    chk.add_argument("--no-probe", action="store_true")
    au = sub.add_parser("audit", help="存量审计")
    au.add_argument("--apply", action="store_true")
    au.add_argument("--json", action="store_true")
    sub.add_parser("restore", help="恢复被 -999 sentinel 埋掉的事实")
    args = ap.parse_args()
    if args.cmd == "check":
        print(json.dumps(check(args.content, args.category, args.tags,
                               probe=not args.no_probe), ensure_ascii=False))
        return 0
    if args.cmd == "audit":
        return audit(apply=args.apply, as_json=args.json)
    if args.cmd == "restore":
        print("RESTORED:", restore_buried())
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
