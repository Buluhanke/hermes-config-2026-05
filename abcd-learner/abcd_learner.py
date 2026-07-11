#!/usr/bin/env python3
"""
abcd_learner.py — AgentFactory-style ABCD knowledge → skill crystallizer

从 orchestrator 日志提取知识 → fact_store → 高频fact升华为skill
Inspired by AgentFactory (ACL 2026): executable subagent > textual experience
"""
import json, re, time, sqlite3, os
from pathlib import Path

HERMES = Path.home()
DB_PATH = HERMES / ".hermes" / "memory_store.db"
LOG_DIR = HERMES / ".hermes" / "cron" / "output" / "idle_learning"
SKILL_OUT = HERMES / ".hermes" / "skills"
RETRIEVAL_THRESHOLD = 3


def get_recent_logs(n=7):
    logs = sorted(LOG_DIR.glob("*.log"), key=os.path.getmtime, reverse=True)
    return logs[:n]


def parse_log(log_path):
    content = log_path.read_text()
    abcd = {}
    for m in re.findall(r"[✅❌⚠️] ([ABCD]_\w+): (.+)", content):
        abcd[m[0]] = m[1].strip()
    b = re.search(r"✅ 新写入 (\d+) 条 fact", content)
    s = re.search(r"⏭️ 跳过 (\d+) 条", content)
    t = re.search(r"fact_store 总计: (\d+) 条", content)
    return {
        "abcd": abcd,
        "batch": {
            "new": int(b.group(1)) if b else -1,
            "skip": int(s.group(1)) if s else 0,
            "total": int(t.group(1)) if t else 0,
        },
        "log_name": log_path.name
    }


def read_facts(min_retrievals=3):
    if not DB_PATH.exists():
        return []
    db = sqlite3.connect(str(DB_PATH))
    cur = db.execute(
        "SELECT fact_id, content, tags, trust_score, retrieval_count "
        "FROM facts WHERE retrieval_count >= ? ORDER BY retrieval_count DESC",
        (min_retrievals,)
    )
    facts = cur.fetchall()
    db.close()
    return facts


def write_skill(safe_name, content, tags, description):
    skill_path = SKILL_OUT / safe_name
    skill_path.mkdir(parents=True, exist_ok=True)
    skill_md = f"""---
name: {safe_name}
description: {description}
entry_file: {safe_name}.py
---
# {safe_name}

## Description
**Problem Category**: {description}
**Tags**: {', '.join(tags)}
**Crystallized from**: fact_store (retrieval_count >= {RETRIEVAL_THRESHOLD})

## AgentFactory Paradigm
Converted from textual fact → executable subagent code.
Portable across any Python-capable system.

## Usage
```bash
python3 ~/.hermes/skills/{safe_name}/{safe_name}.py
```
"""
    (skill_path / "SKILL.md").write_text(skill_md)
    (skill_path / "__init__.py").write_text("")
    stub_py = f