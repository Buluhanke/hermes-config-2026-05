#!/bin/bash
# idle_learning_wrapper.sh — 执行 idle_learning 完整循环（A→B→C→D→E）
set -e
HERMES_HOME="$HOME/.hermes"
OUT_DIR="$HERMES_HOME/cron/output/idle_learning"
mkdir -p "$OUT_DIR"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
LOG="$OUT_DIR/${DATE}.log"

# 内存守卫：确保至少 2GB 可用（idle_learning 仅 python+联网，2GB 余量足够），否则等待
check_memory() {
    TOTAL_MEM=$(sysctl -n hw.memsize 2>/dev/null || echo 0)
    TOTAL_GB=$((TOTAL_MEM / 1024 / 1024 / 1024))
    # macOS: 空闲内存 via vm_stat
    free_pages=$(vm_stat | grep "Pages free" | awk '{gsub(/[.Pages:]/,""); print $NF}')
    pagesize=$(pagesize 2>/dev/null || echo 4096)
    free_bytes=$((free_pages * pagesize))
    free_gb=$(python3 -c "print(${free_bytes} / 1024**3)")
    if [ "$(python3 -c "print(1 if $free_gb < 2 else 0)")" -eq 1 ]; then
        echo "[内存守卫] 空闲 ${free_gb}GB < 2GB，等待 10 分钟..."
        sleep 600
        free_pages=$(vm_stat | grep "Pages free" | awk '{gsub(/[.Pages:]/,""); print $NF}')
        free_bytes=$((free_pages * pagesize))
        free_gb=$(python3 -c "print(round(${free_bytes} / 1024**3, 1))")
        if [ "$(python3 -c "print(1 if $free_gb < 2 else 0)")" -eq 1 ]; then
            echo "[内存守卫] 仍不足 2GB，跳过本轮执行"
            exit 0
        fi
    fi
    echo "[内存守卫] 空闲 ${free_gb}GB，继续执行"
}

check_memory

{
    echo "=== idle_learning_wrapper $DATE ==="
    echo "A: ps aux 视觉产线检查"
    echo "B: arXiv 论文扫描（缓存优先）"
    echo "C: CVE 安全扫描（cve_lite，零依赖标准库）"
    echo "D: action_diversity 执行层检查"
    echo "E: Skill crystallizer（AgentFactory paradigm）"
    echo "---"

    # A+B+D：orchestrator 处理（快速，5s超时）
    python3 "$HERMES_HOME/scripts/idle_learning_orchestrator.py" 2>&1

    echo "---"
    echo "B_insight: arXiv 论文 → LLM 洞察 → fact_store"
    python3 "$HERMES_HOME/scripts/b_insight.py" 2>&1 || echo "  B_insight 跳过"

    echo "C: CVE 安全扫描（cve_lite 同步）:"
    python3 "$HERMES_HOME/scripts/cve_lite.py" scan \
        "$HERMES_HOME/hermes-agent/venv" \
        --severity HIGH --timeout 20 2>&1 || echo "  cve_lite 执行异常"

    echo "---"
    echo "E2: 反思消化（升级retrieval_count）:"
    python3 - << 'PYEOF'
import sqlite3, time
from pathlib import Path

DB = Path.home() / '.hermes' / 'memory_store.db'
conn = sqlite3.connect(str(DB))

# 把所有新知识（ret=0 或 ret=-999）立即升级 retrieval_count
new_facts = conn.execute('''
    SELECT fact_id, content, category, tags
    FROM facts
    WHERE (retrieval_count = 0 OR retrieval_count = -999)
      AND trust_score >= 0.60
    ORDER BY created_at DESC LIMIT 5
''').fetchall()

if not new_facts:
    print('  ⏭ 无新知识待反思')
else:
    print(f'  📖 {len(new_facts)}条新知识反思消化...')
    for fid, content, category, tags in new_facts:
        conn.execute('''
            UPDATE facts
            SET retrieval_count = retrieval_count + 1,
                helpful_count = helpful_count + 1,
                updated_at = ?
            WHERE fact_id = ?
        ''', (time.time(), fid))
        print(f'  ✅ {content[:80]}')
    conn.commit()

conn.close()
print('  E2 完成')
PYEOF

    echo "---"
    echo "E: 知识沉淀（→ knowledge/crystallized，不污染技能库）:"
    python3 "$HERMES_HOME/scripts/abcd_learner.py" 2>&1 || echo "  沉淀脚本异常"

    echo "---"
    echo "F: Auto junk cleanup (runs after each cycle):"
    python3 - << 'PYEOF'
import os, re
from pathlib import Path
import shutil

JUNK_PATTERNS = [r'^ai-圈', r'能力画像', r'search-results', r'-top-5-', r'-24h-', r'简报']
SKILLS = Path.home() / '.hermes' / 'skills'
removed = 0

# Top-level cleanup
for d in SKILLS.iterdir():
    if not d.is_dir() or d.name.startswith('.'):
        continue
    for pat in JUNK_PATTERNS:
        if re.search(pat, d.name, re.IGNORECASE):
            shutil.rmtree(d)
            removed += 1
            print(f"  🗑 已清理: {d.name}")
            break

# Nested cleanup
for root, dirs, files in os.walk(SKILLS):
    for name in list(dirs):
        for pat in JUNK_PATTERNS:
            if re.search(pat, name, re.IGNORECASE):
                p = os.path.join(root, name)
                shutil.rmtree(p)
                removed += 1
                print(f"  🗑 已清理(嵌套): {os.path.relpath(p, SKILLS)}")
                break

if removed == 0:
    print("  ✅ 无结晶垃圾")
PYEOF

    echo "---"
    echo "fact_store 统计:"
    python3 -c "
import sqlite3, pathlib
db = pathlib.Path('$HERMES_HOME/memory_store.db')
if db.exists():
    conn = sqlite3.connect(db)
    cur = conn.execute('SELECT COUNT(*) FROM facts WHERE trust_score > 0.15')
    active = cur.fetchone()[0]
    cur = conn.execute('SELECT COUNT(*) FROM facts WHERE trust_score BETWEEN 0.05 AND 0.15')
    low = cur.fetchone()[0]
    cur = conn.execute('SELECT COUNT(*) FROM facts WHERE trust_score <= 0.05')
    exp = cur.fetchone()[0]
    total = conn.execute('SELECT COUNT(*) FROM facts').fetchone()[0]
    print(f'活跃:{active} 低信任:{low} 过期:{exp} 总计:{total}')
    conn.close()
else:
    print('DB 不存在')
"

} 2>&1 | tee "$LOG"
echo "[wrapper 完成] → $LOG"
