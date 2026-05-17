#!/usr/bin/env python3
"""Track latest arXiv papers for AI/LLM topics with notification.

Usage:
    python track_arxiv.py                     # use default topics from config
    python track_arxiv.py --config custom.json
    python track_arxiv.py --topics "LLM,scaling laws,RLHF" --max 3
    python track_arxiv.py --watch              # watch mode (check every 30 min)
"""
import sys
import json
import time
import urllib.request
import urllib.parse
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

# Default config path
SCRIPT_DIR = Path(__file__).parent
DEFAULT_CONFIG = SCRIPT_DIR / ".." / "config" / "track_topics.json"

NS = {'a': 'http://www.w3.org/2005/Atom'}

TRACKING_FILE = SCRIPT_DIR / ".." / "data" / "seen_papers.json"

# Default AI/LLM topics to track
DEFAULT_TOPICS = [
    "large language model",
    "LLM reasoning",
    "RLHF",
    "chain-of-thought",
    "mixture of experts",
    "scaling laws",
    "transformer architecture",
    "GPT-4",
    "Claude",
    "Gemini",
    "multimodal model",
    "world model",
    "agentic AI",
    "synthetic data",
    "test-time compute",
]

CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "cs.CV"]

def load_seen():
    f = Path(TRACKING_FILE)
    if f.exists():
        with open(f) as fp:
            return set(json.load(fp))
    return set()

def save_seen(seen):
    TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKING_FILE, 'w') as fp:
        json.dump(sorted(seen), fp, indent=2)

def fetch_latest(topic, category=None, max_results=5, days_back=7):
    """Fetch latest papers for a topic within the last N days."""
    parts = [f'all:{urllib.parse.quote(topic)}']
    if category:
        parts.append(f'cat:{category}')
    
    params = {
        'search_query': '+AND+'.join(parts),
        'max_results': str(max_results * 3),  # fetch more to filter
        'sortBy': 'submittedDate',
        'sortOrder': 'descending',
    }
    
    url = "https://export.arxiv.org/api/query?" + "&".join(f"{k}={v}" for k, v in params.items())
    
    req = urllib.request.Request(url, headers={'User-Agent': 'HermesAgent/1.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
    
    root = ET.fromstring(data)
    entries = root.findall('a:entry', NS)
    
    cutoff = datetime.now() - timedelta(days=days_back)
    results = []
    
    for entry in entries:
        published_elem = entry.find('a:published', NS)
        published_str = published_elem.text[:10] if published_elem is not None and published_elem.text else 'unknown'
        try:
            published = datetime.strptime(published_str, '%Y-%m-%d')
        except:
            continue
        if published >= cutoff:
            results.append(entry)
            if len(results) >= max_results:
                break
    
    return results

def parse_entry(entry):
    title = entry.find('a:title', NS).text.strip().replace('\n', ' ')
    raw_id = entry.find('a:id', NS).text.strip()
    full_id = raw_id.split('/abs/')[-1] if '/abs/' in raw_id else raw_id
    arxiv_id = full_id.split('v')[0]
    version = full_id[len(arxiv_id):] if full_id != arxiv_id else ""
    published = entry.find('a:published', NS).text[:10]
    authors = ', '.join(a.find('a:name', NS).text for a in entry.findall('a:author', NS))
    summary = entry.find('a:summary', NS).text.strip().replace('\n', ' ')
    cats = ', '.join(c.get('term') for c in entry.findall('a:category', NS))
    return {
        'title': title,
        'arxiv_id': arxiv_id,
        'version': version,
        'full_id': arxiv_id + version,
        'published': published,
        'authors': authors,
        'summary': summary,
        'categories': cats,
        'url': f'https://arxiv.org/abs/{arxiv_id}',
        'pdf': f'https://arxiv.org/pdf/{arxiv_id}',
    }

def format_paper(paper, index=None):
    lines = []
    if index is not None:
        lines.append(f"[{index}] ")
    lines.append(f"**{paper['title']}**")
    lines.append(f"ID: `{paper['full_id']}` | Published: {paper['published']} | Categories: {paper['categories']}")
    lines.append(f"Authors: {paper['authors']}")
    lines.append(f"Abstract: {paper['summary'][:400]}{'...' if len(paper['summary']) > 400 else ''}")
    lines.append(f"🔗 [Abstract]({paper['url']}) | [PDF]({paper['pdf']})")
    return '\n'.join(lines)

def track_topics(topics=None, max_per_topic=5, days_back=7, config_path=None, verbose=False):
    """Main tracking function."""
    if config_path:
        with open(config_path) as f:
            cfg = json.load(f)
        topics = topics or cfg.get('topics', DEFAULT_TOPICS)
        max_per_topic = cfg.get('max_per_topic', max_per_topic)
        days_back = cfg.get('days_back', days_back)
    else:
        topics = topics or DEFAULT_TOPICS
    
    if isinstance(topics, str):
        topics = [t.strip() for t in topics.split(',')]
    
    seen = load_seen()
    new_papers = []
    
    for topic in topics:
        try:
            entries = fetch_latest(topic, max_results=max_per_topic, days_back=days_back)
            for entry in entries:
                paper = parse_entry(entry)
                if paper['full_id'] not in seen:
                    new_papers.append(paper)
                    seen.add(paper['full_id'])
        except Exception as e:
            print(f"⚠️  Error tracking '{topic}': {e}", file=sys.stderr)
            continue
    
    save_seen(seen)
    
    if not new_papers:
        print("No new papers found.")
        return []
    
    # Sort by published date, newest first
    new_papers.sort(key=lambda p: p['published'], reverse=True)
    
    print(f"🆕 Found {len(new_papers)} new paper(s) across {len(topics)} topic(s)\n")
    for i, paper in enumerate(new_papers):
        print(format_paper(paper, index=i+1))
        print()
    
    return new_papers

# Alias for backwards compat
def check_for_new(**kwargs):
    return track_topics(**kwargs)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Track latest arXiv AI/LLM papers")
    parser.add_argument('--topics', help='Comma-separated topics (overrides config)')
    parser.add_argument('--max', '--max-per-topic', dest='max_per_topic', type=int, default=5)
    parser.add_argument('--days', '--days-back', dest='days_back', type=int, default=7)
    parser.add_argument('--config', type=str, help='Path to config JSON file')
    parser.add_argument('--watch', action='store_true', help='Watch mode: run continuously')
    parser.add_argument('--interval', type=int, default=30, help='Watch interval in minutes (default: 30)')
    
    args = parser.parse_args()
    
    topics = args.topics.split(',') if args.topics else None
    
    if args.watch:
        print(f"Watching for new papers every {args.interval} minutes. Press Ctrl+C to stop.\n")
        while True:
            results = track_topics(topics=topics, max_per_topic=args.max_per_topic, 
                                   days_back=args.days_back, config_path=args.config)
            if results:
                print(f"\nNext check in {args.interval} minutes...")
            time.sleep(args.interval * 60)
    else:
        track_topics(topics=topics, max_per_topic=args.max_per_topic, 
                     days_back=args.days_back, config_path=args.config)

# Import ET late to avoid top-level import issues
import xml.etree.ElementTree as ET