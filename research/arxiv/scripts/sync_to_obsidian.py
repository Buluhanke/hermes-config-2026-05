#!/usr/bin/env python3
"""Sync arXiv papers to Obsidian vault as structured notes.

Usage:
    python sync_to_obsidian.py 2402.03300
    python sync_to_obsidian.py --id 2402.03300
    python sync_to_obsidian.py --id 2402.03300,2401.12345
    python sync_to_obsidian.py "transformer attention" --max 5
    python sync_to_obsidian.py --query "RLHF training" --max 3
    python sync_to_obsidian.py --config config/obsidian_sync.json
    python sync_to_obsidian.py --watch

Config (config/obsidian_sync.json):
{
  "vault_path": "~/Obsidian/迅龙贸易",
  "papers_folder": "Papers/AI-LLM",
  "auto_tag": true,
  "add_bibtex": true,
  "add_summary": true,
  "frontmatter_template": "default"
}
"""
import sys
import json
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
DEFAULT_CONFIG = SCRIPT_DIR / ".." / "config" / "obsidian_sync.json"

# Default Obsidian vault path (macOS)
DEFAULT_VAULT = Path.home() / "Obsidian" / "迅龙贸易"
DEFAULT_FOLDER = "Papers/AI-LLM"

NS = {'a': 'http://www.w3.org/2005/Atom'}

def get_config(config_path=None):
    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            return json.load(f)
    if DEFAULT_CONFIG.exists():
        with open(DEFAULT_CONFIG) as f:
            return json.load(f)
    return {
        'vault_path': str(DEFAULT_VAULT),
        'papers_folder': DEFAULT_FOLDER,
        'auto_tag': True,
        'add_bibtex': True,
        'add_summary': False,
    }

def fetch_paper(arxiv_id):
    """Fetch paper metadata from arXiv API."""
    clean_id = arxiv_id.split('v')[0]  # strip version
    url = f"https://export.arxiv.org/api/query?id_list={clean_id}"
    req = urllib.request.Request(url, headers={'User-Agent': 'HermesAgent/1.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
    
    root = ET.fromstring(data)
    entry = root.find('a:entry', NS)
    if entry is None:
        raise ValueError(f"Paper {arxiv_id} not found")
    return parse_entry(entry)

def parse_entry(entry):
    title = entry.find('a:title', NS).text.strip().replace('\n', ' ')
    raw_id = entry.find('a:id', NS).text.strip()
    full_id = raw_id.split('/abs/')[-1] if '/abs/' in raw_id else raw_id
    arxiv_id = full_id.split('v')[0]
    version = full_id[len(arxiv_id):] if full_id != arxiv_id else ""
    published = entry.find('a:published', NS).text[:10] if entry.find('a:published', NS) is not None else 'unknown'
    updated = entry.find('a:updated', NS).text[:10] if entry.find('a:updated', NS) is not None else published
    authors = [a.find('a:name', NS).text for a in entry.findall('a:author', NS)]
    summary = entry.find('a:summary', NS).text.strip().replace('\n', ' ') if entry.find('a:summary', NS) is not None else ''
    cats = [c.get('term') for c in entry.findall('a:category', NS)]
    comment = entry.find('a:comment', NS).text if entry.find('a:comment', NS) is not None else None
    doi_elem = entry.find('{http://arxiv.org/schemas/atom}doi')
    doi = doi_elem.text if doi_elem is not None else None
    
    return {
        'title': title,
        'arxiv_id': arxiv_id,
        'version': version,
        'full_id': arxiv_id + version,
        'published': published,
        'updated': updated,
        'authors': authors,
        'author_str': ', '.join(authors),
        'summary': summary,
        'categories': cats,
        'primary_category': cats[0] if cats else 'cs.AI',
        'comment': comment,
        'doi': doi,
        'url': f'https://arxiv.org/abs/{arxiv_id}',
        'pdf': f'https://arxiv.org/pdf/{arxiv_id}',
        'html': f'https://arxiv.org/html/{arxiv_id}',
    }

def sanitize_filename(name):
    """Convert title to safe Obsidian filename."""
    safe = re.sub(r'[\\/:*?"<>|]', '', name)
    safe = re.sub(r'\s+', ' ', safe).strip()
    if len(safe) > 100:
        safe = safe[:97] + '...'
    return safe

def generate_frontmatter(paper, tags=None, folder=None):
    """Generate YAML frontmatter for Obsidian note."""
    fm = ['---']
    fm.append(f"title: \"{paper['title']}\"")
    fm.append(f"arxivid: {paper['arxiv_id']}")
    fm.append(f"arxiv_url: {paper['url']}")
    fm.append(f"pdf_url: {paper['pdf']}")
    if paper.get('doi'):
        fm.append(f"doi: {paper['doi']}")
    fm.append(f"published: {paper['published']}")
    fm.append(f"updated: {paper['updated']}")
    fm.append(f"authors: [{', '.join(f'\"{a}\"' for a in paper['authors'])}]")
    fm.append(f"categories: [{', '.join(f'\"{c}\"' for c in paper['categories'])}]")
    if tags:
        fm.append(f"tags: [{', '.join(f'\"{t}\"' for t in tags)}]")
    else:
        fm.append("tags: [paper, arxiv]")
    fm.append(f"folder: {folder or 'Papers/AI-LLM'}")
    fm.append('---')
    fm.append('')
    return '\n'.join(fm)

def generate_bibtex(paper):
    """Generate BibTeX entry."""
    last_name = paper['authors'][0].split()[-1] if paper['authors'] else 'Unknown'
    year = paper['published'][:4]
    key = f"{last_name}{year}_{paper['arxiv_id'].replace('.', '')}"
    
    lines = ['```bibtex',
             f'@article{{{key},',
             f'  title     = {{{paper["title"]}}},',
             f'  author    = {{{paper["author_str"]}}},',
             f'  year      = {{{year}}},',
             f'  eprint    = {{{paper["full_id"]}}},',
             f'  archivePrefix = {{arXiv}},',
             f'  primaryClass  = {{{paper["primary_category"]}}},',
             f'  url       = {{https://arxiv.org/abs/{paper["arxiv_id"]}}}']
    if paper.get('doi'):
        lines.append(f'  doi       = {{{paper["doi"]}}}')
    lines.append('}')
    lines.append('```')
    return '\n'.join(lines)

def generate_obsidian_note(paper, config):
    """Generate full Obsidian note content."""
    parts = []
    folder = config.get('papers_folder', DEFAULT_FOLDER)
    
    # Frontmatter with tags
    tags = []
    if config.get('auto_tag', True):
        tags.extend([
            'paper',
            'arxiv',
            paper['primary_category'].replace('.', '-'),
        ])
        # Add topic tags based on common keywords
        title_lower = paper['title'].lower()
        topic_tags = {
            'llm': 'LLM', 'language model': 'LLM', 'gpt': 'GPT', 'claude': 'Claude',
            'multimodal': 'multimodal', 'vision': 'vision', 'image': 'vision',
            'reasoning': 'reasoning', 'chain-of-thought': 'CoT', 'cot': 'CoT',
            'rlhf': 'RLHF', 'reinforcement': 'RL', 'reward': 'RL',
            'transformer': 'transformer', 'attention': 'attention', 'attention': 'attention',
            'scaling': 'scaling', 'mixture of experts': 'MoE', 'moe': 'MoE',
            'fine-tuning': 'fine-tuning', 'instruction': 'instruction-tuning',
            'retrieval': 'retrieval', 'rag': 'RAG', 'agent': 'agent',
            'synthetic': 'synthetic-data', 'test-time': 'test-time-compute',
        }
        for kw, tag in topic_tags.items():
            if kw in title_lower or kw in paper['summary'].lower():
                tags.append(tag)
        tags = list(dict.fromkeys(tags))  # deduplicate preserve order
    
    parts.append(generate_frontmatter(paper, tags=tags, folder=folder))
    
    # Title
    parts.append(f"# {paper['title']}\n")
    
    # Metadata block
    parts.append(f"**arXiv ID:** `{paper['full_id']}`  ")
    parts.append(f"**Published:** {paper['published']}  ")
    parts.append(f"**Updated:** {paper['updated']}  ")
    parts.append(f"**Categories:** {', '.join(f'`{c}`' for c in paper['categories'])}\n")
    
    # Authors
    parts.append("## Authors\n")
    for author in paper['authors']:
        parts.append(f"- {author}")
    parts.append('')
    
    # Abstract
    parts.append("## Abstract\n")
    parts.append(f"{paper['summary']}\n")
    
    # Links
    parts.append("## Links\n")
    parts.append(f"- [Abstract]({paper['url']})")
    parts.append(f"- [PDF]({paper['pdf']})")
    parts.append(f"- [HTML]({paper['html']})")
    if paper.get('doi'):
        parts.append(f"- [DOI](https://doi.org/{paper['doi']})")
    parts.append('')
    
    # BibTeX
    if config.get('add_bibtex', True):
        parts.append("## Citation\n")
        parts.append(generate_bibtex(paper))
        parts.append('')
    
    # Notes section
    parts.append("## Notes\n")
    parts.append("> Add your notes here...\n")
    
    return '\n'.join(parts)

def save_to_obsidian(paper, config=None, dry_run=False):
    """Save paper as Obsidian markdown note."""
    config = config or get_config()
    vault_path = Path(config.get('vault_path', DEFAULT_VAULT)).expanduser()
    folder = config.get('papers_folder', DEFAULT_FOLDER)
    
    # Create folder if needed
    note_dir = vault_path / folder
    if not dry_run:
        note_dir.mkdir(parents=True, exist_ok=True)
    
    # Filename: arxivID - title.md
    safe_title = sanitize_filename(paper['title'])
    filename = f"{paper['arxiv_id']} - {safe_title}.md"
    filepath = note_dir / filename
    
    content = generate_obsidian_note(paper, config)
    
    if dry_run:
        print(f"[DRY RUN] Would create: {filepath}")
        print(content[:500] + "...")
        return str(filepath)
    
    # Check if already exists
    if filepath.exists():
        existing = filepath.read_text()
        # Check if it's the same paper (compare arxiv ID in frontmatter)
        if f"arxivid: {paper['arxiv_id']}" in existing:
            print(f"⏭️  Already exists: {filepath.name}")
            return str(filepath)
    
    filepath.write_text(content)
    print(f"✅ Saved: {filepath.relative_to(vault_path)}")
    return str(filepath)

def search_and_sync(query=None, max_results=5, config=None, dry_run=False):
    """Search arXiv and sync results to Obsidian."""
    config = config or get_config()
    
    params = {
        'search_query': f'all:{urllib.parse.quote(query)}',
        'max_results': str(max_results),
        'sortBy': 'submittedDate',
        'sortOrder': 'descending',
    }
    
    url = "https://export.arxiv.org/api/query?" + "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(url, headers={'User-Agent': 'HermesAgent/1.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
    
    root = ET.fromstring(data)
    entries = root.findall('a:entry', NS)
    
    if not entries:
        print("No results found.")
        return []
    
    print(f"Found {len(entries)} papers for '{query}'\n")
    saved = []
    for entry in entries:
        paper = parse_entry(entry)
        path = save_to_obsidian(paper, config=config, dry_run=dry_run)
        saved.append(path)
    
    return saved

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sync arXiv papers to Obsidian vault")
    parser.add_argument('--id', help='arXiv ID(s), comma-separated')
    parser.add_argument('--query', help='Search query')
    parser.add_argument('--max', type=int, default=5, help='Max results for search (default: 5)')
    parser.add_argument('--config', type=str, help='Path to config JSON')
    parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
    
    args = parser.parse_args()
    
    config = get_config(args.config) if args.config else get_config()
    
    if args.id:
        ids = [i.strip() for i in args.id.split(',')]
        for i, paper_id in enumerate(ids):
            print(f"[{i+1}/{len(ids)}] Processing {paper_id}")
            try:
                paper = fetch_paper(paper_id)
                save_to_obsidian(paper, config=config, dry_run=args.dry_run)
            except Exception as e:
                print(f"❌ Error: {e}")
    elif args.query:
        search_and_sync(query=args.query, max_results=args.max, config=config, dry_run=args.dry_run)
    else:
        print(__doc__)
        sys.exit(1)
