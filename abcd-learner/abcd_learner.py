#!/usr/bin/env python3
"""
abcd_learner.py — AgentFactory Skill Crystallizer
fact检索>=3次 → 升华为可执行skill文件

来源: AgentFactory ACL2026 paradigm
      github.com/zzatpku/AgentFactory (57 stars)
"""
import sqlite3, json, time, re
from pathlib import Path

HERMES = Path.home()
DB = HERMES / ".hermes" / "memory_store.db"
SKILL_DIR = HERMES / ".hermes" / "skills"
RETRIEVAL_THRESHOLD = 3
TRUST_THRESHOLD = 0.70


def get_hot_facts():
    """检索retrieval_count>=3、trust>=0.70的fact"""
    conn = sqlite3.connect(str(DB))
    rows = conn.execute("""
        SELECT fact_id, content, category, tags, trust_score, retrieval_count
        FROM facts
        WHERE retrieval_count >= ? AND trust_score >= ?
        ORDER BY retrieval_count DESC, trust_score DESC
        LIMIT 10
    """, (RETRIEVAL_THRESHOLD, TRUST_THRESHOLD)).fetchall()
    conn.close()
    return rows


def slugify(text):
    """content前40字 -> 安全目录名"""
    s = text[:40].lower()
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "unnamed-skill"


def write_skill(fact):
    fid, content, category, tags_json, trust, ret_count = fact
    def _parse_tags(raw):
        if not raw or not raw.strip():
            return []
        if raw[0] in '["':
            try:
                return json.loads(raw)
            except Exception:
                pass
        return [t.strip() for t in raw.split(',') if t.strip()]

    tags = _parse_tags(tags_json)
    name = slugify(content)
    skill_path = SKILL_DIR / name
    skill_path.mkdir(parents=True, exist_ok=True)
    today = time.strftime("%Y-%m-%d")
    trust_str = "%.2f" % trust
    # category字段存的是fact的text（长描述）
    body = content if content else (category or "")
    desc_short = content.replace("|", "-").replace("\n", " ")[:200]
    frontmatter = "\n".join([
        "---",
        f"name: {name}",
        "version: 0.1",
        f"description: |",
        f"  {desc_short}",
        "triggers:",
        f'  - "{name}"',
        "trigger_type: auto_crystallized",
        f"tags: {tags}",
        f"created: {today}",
        f"来源: fact_store (id={fid}, ret={ret_count}, trust={trust_str})",
        "---",
        f"# {name}",
        "",
        body,
    ])
    (skill_path / "SKILL.md").write_text(frontmatter)
    return name


def mark_crystallized(fact_id):
    """retrieval_count=-999 标记为已固化"""
    conn = sqlite3.connect(str(DB))
    conn.execute("UPDATE facts SET retrieval_count=-999 WHERE fact_id=?", (fact_id,))
    conn.commit()
    conn.close()


def main():
    facts = get_hot_facts()
    if not facts:
        print("⏭  无retrieval_count>=3的fact，跳过skill升华")
        return
    print(f"🔥 发现{len(facts)}个高价值fact，开始升华:")
    for fact in facts:
        name = write_skill(fact)
        mark_crystallized(fact[0])
        print(f"  ✅ {name}")
    print(f"\n📦 skill已写入~/.hermes/skills/")


if __name__ == "__main__":
    main()
