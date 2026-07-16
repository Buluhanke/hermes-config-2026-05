#!/usr/bin/env python3
"""每小时扫描最近会话，抓反问模式入库 fact_store"""
import sqlite3, os, re
from datetime import datetime, timedelta

HERMES_DIR = os.path.expanduser("~/.hermes")
DB = os.path.join(HERMES_DIR, "memory_store.db")

PATTERNS = [
    r"要不要", r"需不需要", r"你想", r"你看",
    r"帮你", r"需要我", r"要继续吗", r"我建议",
    r"要不要顺手", r"你看怎么办", r"你觉得呢"
]

def scan_sessions():
    sessions_dir = os.path.join(HERMES_DIR, "sessions")
    if not os.path.exists(sessions_dir):
        return []

    findings = []
    cutoff = datetime.now() - timedelta(days=1)
    pattern_regex = re.compile("|".join(PATTERNS))

    for sid in os.listdir(sessions_dir):
        sid_path = os.path.join(sessions_dir, sid)
        if not os.path.isdir(sid_path):
            continue
        # skip sessions older than 1 day
        mtime = datetime.fromtimestamp(os.path.getmtime(sid_path))
        if mtime < cutoff:
            continue
        # scan jsonl files
        for fname in os.listdir(sid_path):
            if not fname.endswith(".jsonl"):
                continue
            fpath = os.path.join(sid_path, fname)
            try:
                with open(fpath) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        import json
                        try:
                            msg = json.loads(line)
                        except:
                            continue
                        content = str(msg.get("content", ""))
                        role = msg.get("role", "")
                        if role == "assistant" and pattern_regex.search(content):
                            findings.append({
                                "session": sid,
                                "snippet": content[:200]
                            })
            except Exception:
                pass
    return findings

def write_to_fact_store(findings):
    if not findings:
        print(f"[anti-counter-question-scan] ✅ 无反问案例 ({datetime.now().strftime('%H:%M')})")
        return

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    now = datetime.now().isoformat()
    for f in findings:
        content = f"[反问案例] session={f['session']}\n{f['snippet']}"
        # avoid dup within 7 days
        cur.execute(
            "SELECT id FROM memories WHERE content LIKE ? AND created_at > ?",
            (f"%session={f['session']}%", (datetime.now()-timedelta(days=7)).isoformat())
        )
        if cur.fetchone():
            continue
        cur.execute("""
            INSERT INTO memories
            (content, category, tags, trust_score, retrieval_count, helpful_count, created_at, updated_at)
            VALUES (?, 'case', '["anti-counter-question","反问被抓"]', 0.5, 0, 0, ?, ?)
        """, (content, now, now))
    conn.commit()
    conn.close()
    print(f"[anti-counter-question-scan] ⚠️  发现 {len(findings)} 条反问，已入库")

if __name__ == "__main__":
    findings = scan_sessions()
    write_to_fact_store(findings)
