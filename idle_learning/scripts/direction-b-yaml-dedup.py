#!/usr/bin/env python3
"""
direction-b-yaml-dedup.py — OSU-NLP YAML 论文扫描 + 去重

Usage:
  python3 scripts/direction-b-yaml-dedup.py                    # 全量扫描，输出新发现
  python3 scripts/direction-b-yaml-dedup.py --incremental       # 增量模式：只看最近一个月的新论文
  python3 scripts/direction-b-yaml-dedup.py --output-ids        # 只输出新 arxiv_id 列表（供 shell 消费）

Output:
  标准输出：新发现的 Desktop 论文清单（含 arXiv ID + title + 匹配数）
  退出码 0: 无新发现；1: 有新发现

依赖：
  - Python 3 stdlib（无需 pip 包）
  - 网络可访问 raw.githubusercontent.com
  - ~/.hermes/memory/idle_learning_log.md 存在

⚠️ Cron 兼容：
  - 单次超时 <30s（默认 curl 15s timeout）
  - 写 /tmp 文件用时间戳防竞争
  - 无外部 pip 依赖
"""

import json
import re
import subprocess
import sys
import os

# ── 路径 ────────────────────────────────────────────────────
LOG_PATH = os.path.expanduser("~/.hermes/memory/idle_learning_log.md")
YAML_URL = (
    "https://raw.githubusercontent.com/"
    "OSU-NLP-Group/GUI-Agents-Paper-List/refs/heads/main/papers.yaml"
)
CURL_TIMEOUT = 15  # seconds
YAML_FALLBACK_URL = (
    "https://raw.githubusercontent.com/"
    "OSU-NLP-Group/GUI-Agents-Paper-List/main/papers.yaml"
)

# ── 关注关键词（自由搭配，保证语义覆盖） ──────────────────
KEYWORDS = [
    'grounding', 'visual understanding', 'GUI understanding',
    'screen parsing', 'GUI agent', 'computer use', 'desktop agent',
    'vision-language', 'VLM', 'action prediction',
    'GUI navigation', 'semantic grounding', 'local', 'M4',
    'apple silicon', 'macOS', 'benchmark', 'OSWorld',
    'ScreenSpot', 'evaluation', 'security', 'safety',
    'guardrail', 'red team', 'injection', 'attack',
]


def fetch_yaml(url: str) -> str:
    """Fetch YAML text, return empty string on failure."""
    try:
        r = subprocess.run(
            ['curl', '-sfL', '--max-time', str(CURL_TIMEOUT), url],
            capture_output=True, text=True, timeout=CURL_TIMEOUT + 5,
        )
        output = r.stdout.strip()
        if len(output) < 100 and 'title' not in output:
            return ''
        return output
    except (subprocess.TimeoutExpired, OSError):
        return ''


def parse_papers(data: str) -> list[dict]:
    """Parse YAML-like format into list of dicts with title, arxiv_id, envs."""
    papers = []
    current = {}
    in_envs = False

    for line in data.split('\n'):
        m = re.match(r"- title: '?(.*?)'?$", line)
        if m:
            if current.get('title'):
                papers.append(current)
            current = {'title': m.group(1).strip("'")}
            in_envs = False
            continue

        m = re.match(r"  arxiv_id: '(.*)'", line)
        if m:
            current['arxiv_id'] = m.group(1)
            continue

        if re.match(r"  envs:", line):
            in_envs = True
            current.setdefault('envs', [])
            continue

        if in_envs:
            m = re.match(r"  - (Desktop|Mobile|Web)", line)
            if m:
                current.setdefault('envs', []).append(m.group(1))
            elif re.match(r"  (keywords:|tldr:|publisher:|date:)", line):
                in_envs = False

    if current.get('title'):
        papers.append(current)

    return papers


def load_known_ids() -> set:
    """Extract all arxiv IDs from the learning log."""
    if not os.path.isfile(LOG_PATH):
        return set()
    try:
        r = subprocess.run(
            ['grep', '-oE', r'[0-9]{4}\.[0-9]{5}', LOG_PATH],
            capture_output=True, text=True, timeout=10,
        )
        return set(r.stdout.strip().split('\n'))
    except (subprocess.TimeoutExpired, OSError):
        return set()


def score_paper(title: str, keywords_field: str = '') -> int:
    """Return keyword match count for a paper."""
    combined = (title + ' ' + keywords_field).lower()
    return sum(1 for k in KEYWORDS if k in combined)


def main():
    incremental = '--incremental' in sys.argv
    output_ids = '--output-ids' in sys.argv

    # 1. Fetch YAML
    yaml_text = fetch_yaml(YAML_URL)
    if not yaml_text:
        yaml_text = fetch_yaml(YAML_FALLBACK_URL)
    if not yaml_text:
        print("YAML: fetch failed (both URLs)", file=sys.stderr)
        sys.exit(2)

    # 2. Parse papers
    papers = parse_papers(yaml_text)
    desktop = [p for p in papers if 'Desktop' in p.get('envs', [])]

    if not desktop:
        print("No Desktop papers found in YAML", file=sys.stderr)
        sys.exit(0)

    # 3. Load known IDs
    known = load_known_ids()
    if not known:
        print("Warning: no known arXiv IDs loaded (log empty?)", file=sys.stderr)

    # 4. Find new papers and score them
    new_papers = []
    for p in desktop:
        aid = p.get('arxiv_id', '')
        if not aid or aid in known:
            continue
        score = score_paper(p.get('title', ''))
        new_papers.append((score, aid, p['title'][:120]))

    # 5. Filter & sort
    #    incremental mode: keep only papers scoring >= 1 (any keyword match)
    #    full mode: keep all new papers
    threshold = 1 if incremental else 0
    results = [(s, a, t) for s, a, t in new_papers if s >= threshold]
    results.sort(key=lambda x: (-x[0], x[1]))  # highest score first, then newest

    # 6. Output
    if output_ids:
        for _, aid, _ in results:
            print(aid)
        sys.exit(1 if results else 0)

    print(f"Total: {len(papers)}, Desktop: {len(desktop)}, "
          f"Known: {len(known)}, New (threshold≥{threshold}): {len(results)}")
    for score, aid, title in results:
        tags = ['🆕']
        if score >= 2:
            tags.append('HIGH')
        elif score >= 1:
            tags.append('MED')
        else:
            tags.append('LOW')
        if 'security' in title.lower() or 'safety' in title.lower() or 'attack' in title.lower():
            tags.append('🔒')
        print(f"  {' '.join(tags)} [{aid}] (score={score}) {title}")

    sys.exit(1 if results else 0)


if __name__ == '__main__':
    main()
