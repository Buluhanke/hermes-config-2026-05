#!/usr/bin/env python3
"""Adapt a third-party agent's SKILL.md to Hermes SKILL.md format.

External generators typically emit name + long description + allowed-tools +
{{value_id}} tokens + their own native tool names. Hermes needs a <=60 char
description, no allowed-tools, no residual tokens, and only tools it actually has.

This script compresses/drops/checks and REPORTS; it never silently rewrites tool
names. Zero dependencies. Usage:
  python3 external_skill_adapter.py in.md [-o out.md]
  python3 external_skill_adapter.py --selftest
"""
from __future__ import annotations

import argparse
import json
import re
import sys

DESC_MAX = 60
NAME_MAX = 64
# Tools that belong to other agents and do not exist in Hermes -> report, do not rewrite.
FOREIGN_TOOL = re.compile(
    r"\b(workiq_[a-z0-9_]+|microsoft_[a-z0-9_]+|scout_[a-z0-9_]+|copilot_[a-z0-9_]+)\b"
)


def split_frontmatter(text: str) -> tuple[list[str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing YAML frontmatter (first line must be ---)")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ValueError("missing YAML frontmatter closing ---")
    return lines[1:end], "\n".join(lines[end + 1 :])


def parse_fm(fm_lines: list[str]) -> dict:
    out = {"name": "", "description": "", "allowed_tools": [], "extra": []}
    cur = None
    for ln in fm_lines:
        if not ln.strip():
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", ln)
        if m:
            key, val = m.group(1), m.group(2).strip()
            cur = key
            if key == "name":
                out["name"] = val.strip("\"'")
            elif key == "description":
                try:
                    out["description"] = json.loads(val)
                except (ValueError, TypeError):
                    out["description"] = val.strip("\"'")
            elif key == "allowed-tools":
                if val:
                    out["allowed_tools"].append(val)
            else:
                out["extra"].append((key, val))
        elif ln.strip().startswith("-") and cur == "allowed-tools":
            out["allowed_tools"].append(ln.strip().lstrip("-").strip())
    return out


def hermes_name(raw: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (raw or "").lower()).strip("-")
    return (slug or "recorded-skill")[:NAME_MAX].rstrip("-")


def hermes_description(raw: str) -> str:
    s = " ".join((raw or "").split())
    if len(s) <= DESC_MAX:
        return s
    cut = s[:DESC_MAX]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,.;:") + "…"


def adapt(text: str) -> tuple[str, dict]:
    fm_lines, body = split_frontmatter(text)
    fm = parse_fm(fm_lines)
    residual = sorted(set(re.findall(r"\{\{([a-z0-9_]+)\}\}", body)))
    out_lines = [
        "---",
        f"name: {hermes_name(fm['name'])}",
        f"description: {json.dumps(hermes_description(fm['description']), ensure_ascii=False)}",
        "---",
    ]
    rendered = "\n".join(out_lines) + "\n\n" + body.strip() + "\n"
    report = {
        "name": hermes_name(fm["name"]),
        "description_original_len": len(fm["description"]),
        "description_final": hermes_description(fm["description"]),
        "description_truncated": len(fm["description"]) > DESC_MAX,
        "dropped_allowed_tools": fm["allowed_tools"],
        "ignored_frontmatter": fm["extra"],
        "residual_tokens": residual,
        "foreign_tools": sorted(set(FOREIGN_TOOL.findall(body))),
        "note": "Rewrite foreign tools to Hermes tools by hand; put Chinese trigger keywords at the front of description.",
    }
    return rendered, report


SELFTEST_SAMPLE = """---
name: reviewed-skill
description: "List GitHub issues for a repository using the gh CLI and report them."
allowed-tools:
 - Bash(gh *)
 - Glob
---

# Instructions

List issues for example/repository.

Use workiq_search_chats only if the user asks for a Teams summary.
"""


def selftest() -> int:
    rendered, rep = adapt(SELFTEST_SAMPLE)
    assert rendered.startswith("---\nname: reviewed-skill\n"), rendered
    assert "allowed-tools" not in rendered, rendered
    assert "List issues for example/repository" in rendered, rendered
    assert rep["dropped_allowed_tools"] == ["Bash(gh issue *)", "Glob"] or rep["dropped_allowed_tools"] == ["Bash(gh *)", "Glob"], rep
    assert rep["foreign_tools"] == ["workiq_search_chats"], rep
    assert len(rep["description_final"]) <= DESC_MAX, rep
    print("SELFTEST OK")
    print(rendered)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src", nargs="?", help="external SKILL.md input")
    ap.add_argument("-o", "--out", help="output path (default: stdout)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if not args.src:
        ap.error("give an input file or --selftest")
    with open(args.src, encoding="utf-8") as f:
        rendered, rep = adapt(f.read())
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(rendered)
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(rendered, end="")
    print(json.dumps(rep, ensure_ascii=False, indent=2), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
