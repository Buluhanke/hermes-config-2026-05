#!/usr/bin/env python3
"""
abcd_learner.py — v3 知识沉淀器（不再是"技能升华"）
历史问题（2026-11-22 修复）：v2 把单条 fact 复述成 SKILL.md 塞进技能库，
污染技能索引；同时把 fact 的 retrieval_count 改成 -999，永久破坏知识召回。
v3 改造：产物写入 ~/.hermes/knowledge/crystallized/NOTE.md（知识库，非技能库），
不再改 retrieval_count；靠 NOTE.md 存在性去重。事实保持可检索。
"""
import sqlite3, time, re, json
from pathlib import Path

HERMES = Path.home()
DB = HERMES / ".hermes" / "memory_store.db"
NOTES_DIR = HERMES / ".hermes" / "knowledge" / "crystallized"
TEMPLATES_DIR = HERMES / ".hermes" / "skills" / "templates"

# Junk patterns — $ anchors added so ^ai-圈$ means "the exact slug 'ai-圈'" not "starts with ai-圈"
JUNK_PATTERNS = [
    r'^ai-圈$',         # 精确名: "AI圈" 新闻采集脚本（slug本身就是ai-圈）
    r'^能力画像$',        # 精确名: 能力画像类
    r'^search-results$', # 精确名: search-results抓取
    r'^top-5$',         # 精确名: Top 5 简报
    r'-24h-$',          # 24h简报脚本（有真实内容的才保留）
    r'^简报$',          # 完整名就是"简报"的占位符
    r'^characters$',    # 完整名: OCR中间产物
    r'^字节$',          # 完整名: 字节流产物
    r'chars$',          # 完整名以chars结尾的占位符
    r'^failed$',        # 完整名: failed状态名
    r'^error$',         # 完整名: error状态名
]

ALTAXYLIC_FIELDS = ["fact_id", "content", "category", "tags", "trust_score", "retrieval_count"]

def _parse_tags(tags_str):
    if not tags_str:
        return []
    try:
        return json.loads(tags_str)
    except Exception:
        return [t.strip() for t in str(tags_str).split(",") if t.strip()]

def _slug(name):
    """Generate a skill-safe slug from arbitrary text.
    
    Strategy: extract any English keywords first (they're better identifiers),
    then fall back to a sanitized prefix of the content. Never produce empty
    or generic names like 'auto-skill'.
    """
    # Try to extract English words/slug-worthy parts first
    en_words = re.findall(r'[a-zA-Z][a-zA-Z0-9_-]{3,}', name)
    if en_words:
        slug = '-'.join(en_words[:3])[:60]
        if slug and not _is_junk(slug):
            return slug
    
    # Fallback: sanitize the full content
    # Remove junk patterns first
    cleaned = name
    for pat in JUNK_PATTERNS:
        cleaned = re.sub(pat, '', cleaned, flags=re.IGNORECASE)
    
    # Keep Chinese chars but replace dangerous chars with space
    s = re.sub(r'[<>{}()|\\\/!@#$%^&*`~\'":;?]', ' ', cleaned)
    s = re.sub(r'[\s]+', '-', s).strip('-')
    
    # Trim
    s = s[:60].rstrip('-')
    
    # If somehow empty after cleanup, use category or hash
    if not s:
        return "crystallized"
    return s

def _is_junk(skill_name):
    """Check if skill name matches known junk patterns."""
    for pat in JUNK_PATTERNS:
        if re.search(pat, skill_name, re.IGNORECASE):
            return True
    return False

def _mark_sentinel(fact_id):
    """Mark a fact as sentinel (processed/skipped) to prevent repeat loops."""
    conn = sqlite3.connect(str(DB))
    conn.execute("UPDATE facts SET retrieval_count=-999 WHERE fact_id=?", (fact_id,))
    conn.commit()
    conn.close()

def _yaml_bool(val):
    return "true" if val else "false"

def distill():
    conn = sqlite3.connect(str(DB))
    rows = conn.execute("""
        SELECT fact_id, content, category, tags, trust_score, retrieval_count
        FROM facts
        WHERE retrieval_count >= 1
          AND trust_score >= 0.65
        LIMIT 50
    """).fetchall()
    conn.close()

    if not rows:
        print("  ⏭ 无待沉淀知识（ret>=1, trust>=0.65）")
        return

    print(f"  🎯 检测到 {len(rows)} 条可沉淀知识")
    created = 0
    skipped = 0
    for row in rows:
        fact_id, content, category, tags, trust_score, retrieval_count = row
        try:
            ok = write_note(fact_id, content, category, tags, trust_score)
            if ok:
                created += 1
            else:
                skipped += 1
                # v3：不再写 -999 sentinel，事实保持可检索；靠 NOTE.md 存在性去重
                print(f"  ⚠ 跳过(垃圾名称/已存在): {content[:60]}")
        except Exception as e:
            skipped += 1
            print(f"  ❌ 写入失败: {e}")

    print(f"  ✅ 新建笔记: {created}, 跳过: {skipped}")

def write_note(fact_id, content, category, tags, trust_score):
    tags_list = _parse_tags(tags) if tags else []
    skill_name = _slug(content[:80])
    
    # Filter out junk names
    if _is_junk(skill_name):
        return False
    
    note_dir = NOTES_DIR / skill_name
    note_file = note_dir / "NOTE.md"

    # 去重：靠笔记文件存在性，不改 fact 状态（v2 的 -999 sentinel 已废除）
    if note_file.exists():
        print(f"  ⏭ 已存在笔记: {skill_name}/")
        return False

    note_tags = tags_list if tags_list else ["idle-learning", "knowledge-note"]
    yaml_tags = ", ".join(f'"{t}"' for t in note_tags[:8])

    cat_name = (category or '').strip().lower() if category else ''
    display_name = cat_name[:50] if cat_name and not _is_junk(cat_name) else content[:80]

    note = f'''---
name: {skill_name}
kind: knowledge-note
generated_by: abcd_learner_v3
fact_id: {fact_id}
created: {time.strftime("%Y-%m-%d")}
tags: [{yaml_tags}]
---

# {display_name[:100]}

{content}

**来源**: fact_id={fact_id} | category={category} | trust={trust_score}
'''

    note_dir.mkdir(parents=True, exist_ok=True)
    note_file.write_text(note, encoding="utf-8")
    print(f"  ✅ 沉淀 → knowledge/crystallized/{skill_name}/NOTE.md")
    return True

if __name__ == "__main__":
    print("🌟 E阶段 知识沉淀器 v3 启动（产物进 knowledge/，不污染 skills/）")
    distill()
    print("🎉 本轮沉淀完成")
