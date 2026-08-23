#!/usr/bin/env python3
"""Query Hermes audit.db to see what model/provider each platform actually used.

This is the authoritative way to answer 'what model is platform X really running?'
because config.yaml `model.default` is only a global default and platform routing
may diverge (e.g. QQ defaulted to hy3 but actually called MiniMax 735+ times).

Usage:
  python3 audit_platform_models.py            # all platforms, provider/model dist
  python3 audit_platform_models.py qqbot      # filter platform LIKE %qqbot%
  python3 audit_platform_models.py telegram   # filter platform LIKE %telegram%

DB: ~/.hermes/plugins/audit_to_db/data/audit.db  (table: api_calls)
"""
import sqlite3
import sys

DB = "/Users/aimac/.hermes/plugins/audit_to_db/data/audit.db"


def main():
    filt = sys.argv[1] if len(sys.argv) > 1 else None
    c = sqlite3.connect(DB)
    try:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_calls'").fetchone()
    except sqlite3.Error as e:
        print(f"audit.db error: {e}")
        return

    if filt:
        q = """SELECT platform, provider, model, COUNT(*) n
               FROM api_calls WHERE platform LIKE ?
               GROUP BY platform, provider, model ORDER BY n DESC"""
        rows = c.execute(q, (f"%{filt}%",)).fetchall()
        print(f"=== platform LIKE '%{filt}%' ===")
    else:
        q = """SELECT platform, provider, model, COUNT(*) n
               FROM api_calls GROUP BY platform, provider, model
               ORDER BY platform, n DESC"""
        rows = c.execute(q).fetchall()
        print("=== all platforms: provider/model distribution ===")

    for r in rows:
        print(f"{r[0]:12} {r[1]:16} {r[2]:30} calls={r[3]}")

    print("\n=== most recent call per platform ===")
    rq = """SELECT platform, provider, model, MAX(timestamp)
            FROM api_calls GROUP BY platform"""
    for r in c.execute(rq).fetchall():
        print(f"{r[0]:12} {r[1]:16} {r[2]:30} last={r[3]}")


if __name__ == "__main__":
    main()
