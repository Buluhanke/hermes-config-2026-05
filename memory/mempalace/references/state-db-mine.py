#!/usr/bin/env python3
"""
从 Hermes state.db 提取全渠道对话，输出 JSONL 供 mempalace mine。
一次性脚本，提取完成后下次只需 mempalace mine。

用法:
    python3 references/state-db-mine.py
    # 输出: /tmp/hermes_all_channels.jsonl
"""

import sqlite3, json, os

HERMES_STATE = os.path.expanduser("~/.hermes/state.db")
OUTPUT = "/tmp/hermes_all_channels.jsonl"

def extract_all_channels():
    conn = sqlite3.connect(HERMES_STATE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT m.session_id, s.source, m.role, m.content, m.timestamp
        FROM messages m
        JOIN sessions s ON m.session_id = s.id
        WHERE m.content IS NOT NULL AND m.content != ''
        AND m.role IN ('user', 'assistant')
        ORDER BY s.source, m.timestamp
    """)

    records = []
    for row in cur.fetchall():
        records.append({
            "session_id": row["session_id"],
            "source":     row["source"],
            "role":      row["role"],
            "content":   row["content"][:2000],  # truncate long content
            "timestamp": row["timestamp"]
        })

    conn.close()

    with open(OUTPUT, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Print summary
    from collections import Counter
    counts = Counter(r["source"] for r in records)
    print(f"Extracted {len(records)} messages → {OUTPUT}")
    for src, cnt in counts.most_common():
        print(f"  {src}: {cnt} messages")

if __name__ == "__main__":
    extract_all_channels()
