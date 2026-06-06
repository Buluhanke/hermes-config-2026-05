#!/usr/bin/env python3
"""
memory_transfer.py — MEMORY.md 自动整理脚本

策略：
  keep      → 保留在 MEMORY.md（核心准则/用户偏好/硬教训）
  fact      → 写进 fact_store.db（技术细节/坑点/一次性发现）
  remove    → 直接删除（已过时/一次性/已在别处）

运行：python3 ~/.hermes/scripts/memory_transfer.py [--dry-run]
"""
import re, sqlite3, sys, os
from datetime import datetime

HERMES_HOME = os.path.expanduser("~/.hermes")
MEMORY_FILE = f"{HERMES_HOME}/memories/MEMORY.md"
DB_FILE     = f"{HERMES_HOME}/memory/fact_store.db"
BACKUP_FILE = f"{HERMES_HOME}/memories/MEMORY.md.bak.{int(datetime.now().timestamp())}"

# ── 分类规则 ────────────────────────────────────────────────────────────────
# keep: 留在 MEMORY.md（核心准则/用户偏好/硬教训）
# fact: 技术细节/坑点/一次性发现 → fact_store.db
RULES = [
    ("keep",  "浏览器控制"),
    ("keep",  "破坏性操作边界"),
    ("keep",  "浏览器硬规则"),
    ("keep",  "用户重复确认"),
    ("keep",  "模型解绑"),
    ("keep",  "skill固化纪律"),
    ("keep",  "用户反馈画像"),
    ("keep",  "terminal安全闸"),
    ("keep",  "SOUL.md增量"),
    ("keep",  "launchd cron三件套"),
    ("keep",  "搜索路由规则"),
    ("keep",  "联网搜索"),
    # 技术细节/坑点/一次性发现
    ("fact",  "三连修"),
    ("fact",  "Bash坑"),
    ("fact",  "进化系统健康度自查"),
    ("fact",  "主动学习脚本"),
]

def parse_entries(text: str) -> list[tuple[str, str, str]]:
    """返回 [(完整tag, 前20字, 完整内容), ...]"""
    entries = re.split(r'\n§\n?', text.strip())
    result = []
    for e in entries:
        e = e.strip()
        if not e:
            continue
        m = re.match(r"【(.+?)】", e)
        tag = m.group(1) if m else e[:30]
        result.append((tag, e[:20], e))
    return result

def classify(entry_tag: str) -> str:
    for cat, kw in RULES:
        if re.search(kw, entry_tag):
            return cat
    return "keep"  # 默认保留

def main():
    dry = "--dry-run" in sys.argv

    with open(MEMORY_FILE) as f:
        raw = f.read()

    entries = parse_entries(raw)
    kept, to_fact, removed = [], [], []

    for tag, prefix, content in entries:
        cat = classify(tag)
        if cat == "keep":
            kept.append(content)
        elif cat == "fact":
            to_fact.append(content)
        else:
            removed.append(content)

    # 写 fact_store
    if to_fact and not dry:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS facts (id INTEGER PRIMARY KEY, tag TEXT, content TEXT, created_at TEXT)")
        now = datetime.now().isoformat()
        for entry in to_fact:
            tag_match = re.search(r"【(.+?)】", entry)
            tag = tag_match.group(1) if tag_match else entry[:30]
            c.execute("INSERT OR IGNORE INTO facts (tag, content, created_at) VALUES (?, ?, ?)",
                      (tag, entry, now))
        conn.commit()
        conn.close()

    # 构建新 MEMORY.md
    new_content = "\n§\n\n".join(kept)
    new_size = len(new_content)
    old_size = len(raw)

    print(f"旧 MEMORY.md: {old_size} chars")
    print(f"新 MEMORY.md: {new_size} chars ({old_size-new_size:+d})")
    print(f"  保留:   {len(kept)} 条")
    print(f"  fact:   {len(to_fact)} 条 → fact_store.db")
    print(f"  删除:   {len(removed)} 条")

    if dry:
        print("\n[DRY-RUN] 无实际写入")
        print("\n── 新 MEMORY.md 预览（前500字）──")
        print(new_content[:500])
        return

    # 备份 + 写新文件
    with open(BACKUP_FILE, "w") as f:
        f.write(raw)
    with open(MEMORY_FILE, "w") as f:
        f.write(new_content)

    print(f"\n✅ 已备份到: {BACKUP_FILE}")
    print(f"✅ 新 MEMORY.md 已写入: {MEMORY_FILE}")

if __name__ == "__main__":
    main()
