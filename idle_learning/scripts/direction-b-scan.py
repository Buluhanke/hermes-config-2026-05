#!/usr/bin/env python3
"""
direction-b-scan.py -- Reusable OSU-NLP YAML scanner for Direction B paper discoveries.

Usage:
    python3 direction-b-scan.py [--incremental] [--debug]

If --incremental: only checks the first 30 entries (newest papers) for dedup.
Without --incremental: scans all Desktop papers with keyword scoring (full mode).

Output: prints scored Desktop papers to stdout, sorted by date desc.
Known papers marked [KNOWN], new papers marked [NEW].
Returns exit code: 0 if new finds exist, 1 if saturated.
"""

import urllib.request, sys, json, re

# === CONFIG ===
YAML_URL = "https://raw.githubusercontent.com/OSU-NLP-Group/GUI-Agents-Paper-List/main/papers.yaml"
FULL_KEYWORDS = [
    'grounding', 'visual understanding', 'GUI understanding',
    'screen parsing', 'GUI agent', 'computer use', 'desktop agent',
    'vision-language', 'VLM', 'action prediction',
    'GUI navigation', 'semantic grounding', 'local', 'M4',
    'apple silicon', 'macOS', 'benchmark', 'OSWorld',
    'ScreenSpot', 'evaluation', 'safety', 'guardrail',
    'reinforcement learning', 'small model', 'efficiency',
    'security', 'test-time', 'adaptation', 'continual learning',
    'world model', 'reward model', 'multi-turn',
    'robustness', 'perturbation', 'red teaming',
    'accessibility', 'observation', 'compression',
    'cross-application', 'modular', 'verification',
    'process reward', 'intent alignment'
]
MIN_SCORE = 2

# === KNOWN ARXIV IDs (extend this as references grow) ===
# Updated 2026-06-02 -- covers 3 full direction B scans
KNOWN_ARXIV = {
    # direction-b-papers-2026-06.md (first big scan, ~30 papers)
    '2604.09155', '2604.24441', '2604.10577', '2604.09815',
    '2604.07831', '2604.14113', '2604.08516', '2603.14707',
    '2603.08013', '2603.18429', '2502.08226', '2605.02630',
    '2512.14014', '2605.27365', '2605.28534', '2605.18048',
    '2605.24830', '2604.25380', '2605.19484', '2605.16024',
    '2604.18860', '2604.26020', '2604.07929', '2605.18747',
    '2604.21375',  # VLAA-GUI
    # direction-b-papers-2026-06-02.md (second scan, 11 papers)
    '2605.00551', '2506.04135', '2504.07981', '2603.10577',
    '2508.04037', '2504.04716', '2506.03095', '2508.04389',
    '2509.15221', '2604.05157', '2601.09923',
    # direction-b-papers-2026-06-02-r2.md (third scan, 9 papers)
    '2511.04307', '2512.16295', '2509.23866', '2508.14040',
    '2510.04673', '2510.02250', '2505.21964', '2505.18829',
    '2505.19897',
    # Known safety references (covers all discovered as of 2026-06-02)
    '2602.08995', '2602.08235',
    # direction-b-cross-domain: security/safety papers found via full scan after saturation
    '2510.06607',   # AdvCUA — MITRE ATT&CK CUA security benchmark
    '2506.00618',   # RiOSWorld — CU misuse risk benchmark
    # Known from other reference files
    '2508.05615', '2506.07672', '2503.15661',
}


def is_known(arxiv_id):
    """Check if an arxiv ID is already covered by existing references."""
    if not arxiv_id:
        return False
    aid_clean = arxiv_id.replace('.', '').replace('-', '')[:10]
    for known in KNOWN_ARXIV:
        k_clean = known.replace('.', '').replace('-', '')[:10]
        if not k_clean:
            continue
        # Check if first 7 chars overlap
        if len(aid_clean) >= 7 and len(k_clean) >= 7:
            if aid_clean[:7] == k_clean[:7]:
                return True
    return False


def fetch_yaml():
    r = urllib.request.urlopen(YAML_URL, timeout=15)
    return r.read().decode('utf-8')


def parse_papers(raw_yaml):
    """Parse YAML without pyyaml dependency. Returns list of paper dicts."""
    papers = []
    current = None
    in_tldr = False
    tldr_lines = []
    for line in raw_yaml.split('\n'):
        if line.startswith('- title:'):
            if current:
                if in_tldr and tldr_lines:
                    current['tldr'] = ' '.join(tldr_lines).strip()
                papers.append(current)
            current = {'title': '', 'link': '', 'date': '', 'envs': [], 'keywords': [], 'tldr': '', 'arxiv_id': ''}
            in_tldr = False
            tldr_lines = []
            # Handle both quoted and unquoted titles
            title_part = line.split('title:')[1].strip() if 'title:' in line else ''
            current['title'] = title_part.strip("'\"")
        elif current is not None:
            s = line.strip()
            if s.startswith('link:'):
                current['link'] = s.split('link:')[1].strip().strip("'\"")
            elif s.startswith('date:'):
                current['date'] = s.split('date:')[1].strip().strip("'\"")
            elif s.startswith('arxiv_id:'):
                current['arxiv_id'] = s.split('arxiv_id:')[1].strip().strip("'\"")
            elif s == '- Desktop' and 'Desktop' not in current['envs']:
                current['envs'].append('Desktop')
            elif s.startswith('tldr: |'):
                in_tldr = True
                tldr_lines = []
            elif in_tldr:
                if s == '' or s.startswith('bibtex') or s.startswith('sources') or s.startswith('keywords'):
                    current['tldr'] = ' '.join(tldr_lines).strip()
                    in_tldr = False
                else:
                    tldr_lines.append(s)

    if current:
        if in_tldr and tldr_lines:
            current['tldr'] = ' '.join(tldr_lines).strip()
        papers.append(current)
    return papers


def score_paper(p):
    title = p.get('title', '')
    keywords = ' '.join(p.get('keywords', []))
    tldr = p.get('tldr', '')
    combined = (title + ' ' + keywords + ' ' + tldr).lower()
    return sum(1 for k in FULL_KEYWORDS if k.lower() in combined)


def main():
    incremental = '--incremental' in sys.argv
    debug = '--debug' in sys.argv

    print(f"Fetching OSU-NLP YAML from {YAML_URL}...", file=sys.stderr)
    raw = fetch_yaml()
    papers = parse_papers(raw)
    print(f"Total papers: {len(papers)}", file=sys.stderr)

    # In incremental mode, only check the first 30 (newest) entries
    if incremental:
        papers = papers[:30]
        print("Incremental mode: checking only first 30 entries", file=sys.stderr)

    # Filter: must be Desktop-relevant + score >= MIN_SCORE
    candidates = []
    for p in papers:
        if 'Desktop' not in p.get('envs', []):
            continue
        s = score_paper(p)
        if s >= MIN_SCORE:
            candidates.append((s, p))

    # Sort: newest first, then by relevance score
    candidates.sort(key=lambda x: (x[1].get('date', '0000-00-00'), x[0]), reverse=True)

    new_count = 0
    known_count = 0
    for score, p in candidates:
        is_new = not is_known(p.get('arxiv_id', ''))
        if is_new:
            new_count += 1
        else:
            known_count += 1

        if not is_new and not debug:
            continue

        tag = "NEW" if is_new else "KNOWN"
        print(f"[{tag}][{score}] {p.get('date', '?')} | {p.get('title', '?')[:80]}")
        print(f"     arxiv: {p.get('link', '?')}")

    print(f"\nResults: {new_count} new + {known_count} known = {len(candidates)} Desktop papers (score>={MIN_SCORE})", file=sys.stderr)

    if new_count == 0:
        print("\n[SATURATED] No new Desktop papers found. Direction B can skip full scan next round.", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
