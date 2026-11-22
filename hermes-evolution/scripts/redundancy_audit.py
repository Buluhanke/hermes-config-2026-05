#!/usr/bin/env python3
"""只读审计技能库冗余 + fact_store 检索健康度。纯 stdlib，不改任何数据。

用法：python3 <本 skill>/scripts/redundancy_audit.py [--json]
"""
import argparse
import collections
import hashlib
import json
import re
import sqlite3
from pathlib import Path

HOME = Path.home()
SKILLS = HOME / '.hermes' / 'skills'
DB = HOME / '.hermes' / 'memory_store.db'


def _md5(p):
    s = re.sub(r'\s+', ' ', p.read_text(encoding='utf-8', errors='ignore')).strip()
    return hashlib.md5(s.encode()).hexdigest()[:12]


def audit_skills():
    active, auto, no_desc, small = [], [], [], []
    by_hash = collections.defaultdict(list)
    for p in SKILLS.rglob('SKILL.md'):
        sp = str(p)
        if '/.git/' in sp or '/.archive/' in sp:
            continue
        active.append(sp)
        s = p.read_text(encoding='utf-8', errors='ignore')
        if 'Auto-crystallized from fact_store' in s[:900]:
            auto.append(sp)
        if not re.search(r'^description:\s*\S', s, re.M):
            no_desc.append(sp)
        if len(s.strip()) < 200:
            small.append(sp)
        by_hash[_md5(p)].append(sp)
    dups = {h: v for h, v in by_hash.items() if len(v) > 1}
    return {
        'active_skills': len(active),
        'auto_crystallized': len(auto),
        'no_description': len(no_desc),
        'small_under_200_chars': len(small),
        'exact_duplicate_groups': len(dups),
        'exact_duplicate_extra_copies': sum(len(v) - 1 for v in dups.values()),
        'duplicate_samples': {h: v for h, v in list(dups.items())[:5]},
    }


def audit_facts():
    if not DB.exists():
        return {'error': 'memory_store.db not found'}
    c = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=10)
    try:
        return {
            'facts': c.execute('select count(*) from facts').fetchone()[0],
            'without_keywords': c.execute(
                "select count(*) from facts where tags is null or tags not like 'keywords:%'"
            ).fetchone()[0],
            'buried_sentinel_facts': c.execute(
                'select count(*) from facts where retrieval_count=-999'
            ).fetchone()[0],
        }
    finally:
        c.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    report = {'skills': audit_skills(), 'facts': audit_facts()}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    s, f = report['skills'], report['facts']
    print(f"active SKILL.md        : {s['active_skills']}")
    print(f"auto-crystallized junk : {s['auto_crystallized']}")
    print(f"no description         : {s['no_description']}")
    print(f"small (<200 chars)     : {s['small_under_200_chars']}")
    print(f"exact dup groups/extra : {s['exact_duplicate_groups']} / {s['exact_duplicate_extra_copies']}")
    print(f"facts                  : {f.get('facts')}")
    print(f"without keywords       : {f.get('without_keywords')}")
    print(f"buried (-999) facts    : {f.get('buried_sentinel_facts')}")
    if s['duplicate_samples']:
        print('dup samples:')
        for h, paths in s['duplicate_samples'].items():
            rel = [Path(x).relative_to(SKILLS).as_posix() for x in paths]
            print(' ', h, '->', rel)


if __name__ == '__main__':
    main()
