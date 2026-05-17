---
name: arxiv
description: "Search arXiv papers by keyword, author, category, or ID."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Arxiv, Papers, Academic, Science, API]
    related_skills: [ocr-and-documents]
---

# arXiv Research

Search and retrieve academic papers from arXiv via their free REST API. No API key, no dependencies — just curl.

## Quick Reference

| Action | Command |
|--------|---------|
| Search papers | `curl "https://export.arxiv.org/api/query?search_query=all:QUERY&max_results=5"` |
| Get specific paper | `curl "https://export.arxiv.org/api/query?id_list=2402.03300"` |
| Track AI/LLM updates | `python scripts/track_arxiv.py` |
| Summarize a paper | `python scripts/summarize_paper.py 2402.03300` |
| Sync to Obsidian | `python scripts/sync_to_obsidian.py 2402.03300` |

## AI/LLM Research Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  1. TRACK     → track_arxiv.py    (自动监控新论文)           │
│  2. SUMMARIZE → summarize_paper.py (生成结构化摘要)          │
│  3. SYNC      → sync_to_obsidian.py (同步到Obsidian)        │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

The API returns Atom XML. Parse with `grep`/`sed` or pipe through `python3` for clean output.

### Basic search

```bash
curl -s "https://export.arxiv.org/api/query?search_query=all:GRPO+reinforcement+learning&max_results=5"
```

### Clean output (parse XML to readable format)

```bash
curl -s "https://export.arxiv.org/api/query?search_query=all:GRPO+reinforcement+learning&max_results=5&sortBy=submittedDate&sortOrder=descending" | python3 -c "
import sys, xml.etree.ElementTree as ET
ns = {'a': 'http://www.w3.org/2005/Atom'}
root = ET.parse(sys.stdin).getroot()
for i, entry in enumerate(root.findall('a:entry', ns)):
    title = entry.find('a:title', ns).text.strip().replace('\n', ' ')
    arxiv_id = entry.find('a:id', ns).text.strip().split('/abs/')[-1]
    published = entry.find('a:published', ns).text[:10]
    authors = ', '.join(a.find('a:name', ns).text for a in entry.findall('a:author', ns))
    summary = entry.find('a:summary', ns).text.strip()[:200]
    cats = ', '.join(c.get('term') for c in entry.findall('a:category', ns))
    print(f'{i+1}. [{arxiv_id}] {title}')
    print(f'   Authors: {authors}')
    print(f'   Published: {published} | Categories: {cats}')
    print(f'   Abstract: {summary}...')
    print(f'   PDF: https://arxiv.org/pdf/{arxiv_id}')
    print()
"
```

## Search Query Syntax

| Prefix | Searches | Example |
|--------|----------|---------|
| `all:` | All fields | `all:transformer+attention` |
| `ti:` | Title | `ti:large+language+models` |
| `au:` | Author | `au:vaswani` |
| `abs:` | Abstract | `abs:reinforcement+learning` |
| `cat:` | Category | `cat:cs.AI` |
| `co:` | Comment | `co:accepted+NeurIPS` |

### Boolean operators

```
# AND (default when using +)
search_query=all:transformer+attention

# OR
search_query=all:GPT+OR+all:BERT

# AND NOT
search_query=all:language+model+ANDNOT+all:vision

# Exact phrase
search_query=ti:"chain+of+thought"

# Combined
search_query=au:hinton+AND+cat:cs.LG
```

## Sort and Pagination

| Parameter | Options |
|-----------|---------|
| `sortBy` | `relevance`, `lastUpdatedDate`, `submittedDate` |
| `sortOrder` | `ascending`, `descending` |
| `start` | Result offset (0-based) |
| `max_results` | Number of results (default 10, max 30000) |

```bash
# Latest 10 papers in cs.AI
curl -s "https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=10"
```

## Fetching Specific Papers

```bash
# By arXiv ID
curl -s "https://export.arxiv.org/api/query?id_list=2402.03300"

# Multiple papers
curl -s "https://export.arxiv.org/api/query?id_list=2402.03300,2401.12345,2403.00001"
```

## BibTeX Generation

After fetching metadata for a paper, generate a BibTeX entry:

{% raw %}
```bash
curl -s "https://export.arxiv.org/api/query?id_list=1706.03762" | python3 -c "
import sys, xml.etree.ElementTree as ET
ns = {'a': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
root = ET.parse(sys.stdin).getroot()
entry = root.find('a:entry', ns)
if entry is None: sys.exit('Paper not found')
title = entry.find('a:title', ns).text.strip().replace('\n', ' ')
authors = ' and '.join(a.find('a:name', ns).text for a in entry.findall('a:author', ns))
year = entry.find('a:published', ns).text[:4]
raw_id = entry.find('a:id', ns).text.strip().split('/abs/')[-1]
cat = entry.find('arxiv:primary_category', ns)
primary = cat.get('term') if cat is not None else 'cs.LG'
last_name = entry.find('a:author', ns).find('a:name', ns).text.split()[-1]
print(f'@article{{{last_name}{year}_{raw_id.replace(\".\", \"\")},')
print(f'  title     = {{{title}}},')
print(f'  author    = {{{authors}}},')
print(f'  year      = {{{year}}},')
print(f'  eprint    = {{{raw_id}}},')
print(f'  archivePrefix = {{arXiv}},')
print(f'  primaryClass  = {{{primary}}},')
print(f'  url       = {{https://arxiv.org/abs/{raw_id}}}')
print('}')
"
```
{% endraw %}

## Reading Paper Content

After finding a paper, read it:

```
# Abstract page (fast, metadata + abstract)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper (PDF → markdown via Firecrawl)
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
```

For local PDF processing, see the `ocr-and-documents` skill.

## Common Categories

| Category | Field |
|----------|-------|
| `cs.AI` | Artificial Intelligence |
| `cs.CL` | Computation and Language (NLP) |
| `cs.CV` | Computer Vision |
| `cs.LG` | Machine Learning |
| `cs.CR` | Cryptography and Security |
| `stat.ML` | Machine Learning (Statistics) |
| `math.OC` | Optimization and Control |
| `physics.comp-ph` | Computational Physics |

Full list: https://arxiv.org/category_taxonomy

## Helper Script

The `scripts/search_arxiv.py` script handles XML parsing and provides clean output:

```bash
python scripts/search_arxiv.py "GRPO reinforcement learning"
python scripts/search_arxiv.py "transformer attention" --max 10 --sort date
python scripts/search_arxiv.py --author "Yann LeCun" --max 5
python scripts/search_arxiv.py --category cs.AI --sort date
python scripts/search_arxiv.py --id 2402.03300
python scripts/search_arxiv.py --id 2402.03300,2401.12345
```

No dependencies — uses only Python stdlib.

---

## Semantic Scholar (Citations, Related Papers, Author Profiles)

arXiv doesn't provide citation data or recommendations. Use the **Semantic Scholar API** for that — free, no key needed for basic use (1 req/sec), returns JSON.

### Get paper details + citations

```bash
# By arXiv ID
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.03300?fields=title,authors,citationCount,referenceCount,influentialCitationCount,year,abstract" | python3 -m json.tool

# By Semantic Scholar paper ID or DOI
curl -s "https://api.semanticscholar.org/graph/v1/paper/DOI:10.1234/example?fields=title,citationCount"
```

### Get citations OF a paper (who cited it)

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.03300/citations?fields=title,authors,year,citationCount&limit=10" | python3 -m json.tool
```

### Get references FROM a paper (what it cites)

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.03300/references?fields=title,authors,year,citationCount&limit=10" | python3 -m json.tool
```

### Search papers (alternative to arXiv search, returns JSON)

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=GRPO+reinforcement+learning&limit=5&fields=title,authors,year,citationCount,externalIds" | python3 -m json.tool
```

### Get paper recommendations

```bash
curl -s -X POST "https://api.semanticscholar.org/recommendations/v1/papers/" \
  -H "Content-Type: application/json" \
  -d '{"positivePaperIds": ["arXiv:2402.03300"], "negativePaperIds": []}' | python3 -m json.tool
```

### Author profile

```bash
curl -s "https://api.semanticscholar.org/graph/v1/author/search?query=Yann+LeCun&fields=name,hIndex,citationCount,paperCount" | python3 -m json.tool
```

### Useful Semantic Scholar fields

`title`, `authors`, `year`, `abstract`, `citationCount`, `referenceCount`, `influentialCitationCount`, `isOpenAccess`, `openAccessPdf`, `fieldsOfStudy`, `publicationVenue`, `externalIds` (contains arXiv ID, DOI, etc.)

---

## Complete Research Workflow

1. **Discover**: `python scripts/search_arxiv.py "your topic" --sort date --max 10`
2. **Assess impact**: `curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:ID?fields=citationCount,influentialCitationCount"`
3. **Read abstract**: `web_extract(urls=["https://arxiv.org/abs/ID"])`
4. **Read full paper**: `web_extract(urls=["https://arxiv.org/pdf/ID"])`
5. **Find related work**: `curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:ID/references?fields=title,citationCount&limit=20"`
6. **Get recommendations**: POST to Semantic Scholar recommendations endpoint
7. **Track authors**: `curl -s "https://api.semanticscholar.org/graph/v1/author/search?query=NAME"`

## Rate Limits

| API | Rate | Auth |
|-----|------|------|
| arXiv | ~1 req / 3 seconds | None needed |
| Semantic Scholar | 1 req / second | None (100/sec with API key) |

## Notes

- arXiv returns Atom XML — use the helper script or parsing snippet for clean output
- Semantic Scholar returns JSON — pipe through `python3 -m json.tool` for readability
- arXiv IDs: old format (`hep-th/0601001`) vs new (`2402.03300`)
- PDF: `https://arxiv.org/pdf/{id}` — Abstract: `https://arxiv.org/abs/{id}`
- HTML (when available): `https://arxiv.org/html/{id}`
- For local PDF processing, see the `ocr-and-documents` skill

## ID Versioning

- `arxiv.org/abs/1706.03762` always resolves to the **latest** version
- `arxiv.org/abs/1706.03762v1` points to a **specific** immutable version
- When generating citations, preserve the version suffix you actually read to prevent citation drift (a later version may substantially change content)
- The API `<id>` field returns the versioned URL (e.g., `http://arxiv.org/abs/1706.03762v7`)

## AI/LLM Latest Research Tracking

Track the newest papers on AI/LLM topics automatically.

### Quick Start

```bash
# Check for new papers on default AI/LLM topics (last 7 days)
python scripts/track_arxiv.py

# Custom topics
python scripts/track_arxiv.py --topics "GRPO,RLHF,scaling laws" --max 5

# Watch mode (check every 30 minutes)
python scripts/track_arxiv.py --watch --interval 30
```

### Config File

Edit `config/track_topics.json` to customize your tracked topics:

```json
{
  "topics": [
    "large language model",
    "LLM reasoning",
    "RLHF",
    "chain-of-thought",
    "mixture of experts",
    "scaling laws",
    "transformer architecture",
    "multimodal model",
    "world model",
    "agentic AI",
    "synthetic data",
    "test-time compute",
    "Direct Preference Optimization",
    "GRPO",
    "constitutional AI",
    "KTO",
    "LoRA fine-tuning",
    "RAG retrieval augmented generation"
  ],
  "categories": ["cs.AI", "cs.CL", "cs.LG", "cs.CV"],
  "max_per_topic": 5,
  "days_back": 7,
  "check_interval_minutes": 60,
  "notify_on_new": true
}
```

### Cron Setup for Automated Monitoring

```bash
# Run every hour via cron
0 * * * * cd /Users/aimac/.hermes/skills/research/arxiv && python scripts/track_arxiv.py >> logs/track.log 2>&1

# Run every morning at 8am
0 8 * * * cd /Users/aimac/.hermes/skills/research/arxiv && python scripts/track_arxiv.py >> logs/track.log 2>&1

# Daily digest at 9am on weekdays
0 9 * * 1-5 cd /Users/aimac/.hermes/skills/research/arxiv && python scripts/track_arxiv.py --days 1 >> logs/daily.log 2>&1
```

### Output Example

```
🆕 Found 3 new paper(s) across 18 topic(s)

[1] **DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning**
ID: `2501.00015v1` | Published: 2025-01-03 | Categories: cs.AI, cs.CL, cs.LG
Authors: DeepSeek-AI
Abstract: We present DeepSeek-R1-Zero and DeepSeek-R1, two models that achieve...
🔗 [Abstract](https://arxiv.org/abs/2501.00015) | [PDF](https://arxiv.org/pdf/2501.00015)
```

---

## Paper Summarization

Generate structured summaries with auto-detected methods, tasks, benchmarks, and key insights.

### Usage

```bash
# Summarize a single paper
python scripts/summarize_paper.py 2402.03300

# Multiple papers
python scripts/summarize_paper.py --id 2402.03300,2401.12345

# Search and summarize
python scripts/summarize_paper.py --query "GRPO reinforcement learning" --max 3

# Output formats
python scripts/summarize_paper.py --id 2402.03300 --format short      # One-liner
python scripts/summarize_paper.py --id 2402.03300 --format medium     # Default (default)
python scripts/summarize_paper.py --id 2402.03300 --format full      # HTML table
python scripts/summarize_paper.py --id 2402.03300 --format obsidian  # Obsidian note
```

### Auto-Detected Fields

The summarizer automatically detects:
- **Methods**: RLHF, DPO, GRPO, LoRA, QLoRA, CoT, ReAct, MoE, FlashAttention, etc.
- **Tasks**: reasoning, code generation, translation, dialogue, tool use, etc.
- **Benchmarks**: MMLU, GSM8K, HumanEval, MATH, BIG-Bench, etc.
- **Key Insights**: Pre-computed insights for 50+ known papers/models

### Example Output (medium format)

```markdown
# DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning
**arXiv:** `2501.00015v1` | **Published:** 2025-01-03 | **Updated:** 2025-01-22
**Authors:** DeepSeek-AI
**Categories:** cs.AI, cs.CL, cs.LG

## Abstract
We present DeepSeek-R1-Zero and DeepSeek-R1, two large language models...

## Methods
- Reinforcement Learning from Human Feedback
- Group Relative Policy Optimization
- Chain-of-Thought Prompting

## Tasks
`Reasoning`, `Mathematics`, `Code Generation`

## Benchmarks
`MMLU`, `GSM8K`, `HumanEval`, `MATH`

## Key Insights
- GRPO: DeepSeek method for efficient RL without critic.
- Chain-of-thought prompting elicits reasoning.

## Links
- [Abstract](https://arxiv.org/abs/2501.00015) | [PDF](https://arxiv.org/pdf/2501.00015) | [HTML](https://arxiv.org/html/2501.00015)
```

---

## Obsidian Sync

Save papers directly to your Obsidian vault with full metadata, tags, and BibTeX.

### Usage

```bash
# Sync single paper
python scripts/sync_to_obsidian.py 2402.03300

# Multiple papers
python scripts/sync_to_obsidian.py --id 2402.03300,2401.12345

# Search and sync
python scripts/sync_to_obsidian.py --query "RLHF training" --max 5

# Dry run (preview)
python scripts/sync_to_obsidian.py --id 2402.03300 --dry-run

# With custom config
python scripts/sync_to_obsidian.py --id 2402.03300 --config config/my_config.json
```

### Obsidian Config

Edit `config/obsidian_sync.json`:

```json
{
  "vault_path": "~/Obsidian/迅龙贸易",
  "papers_folder": "Papers/AI-LLM",
  "auto_tag": true,
  "add_bibtex": true,
  "add_summary": true,
  "add_methods": true,
  "add_benchmarks": true,
  "create_backlinks": true,
  "filename_template": "{arxiv_id} - {title}",
  "overwrite_existing": false
}
```

### Generated Note Structure

```markdown
---
title: "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning"
arxivid: 2501.00015
arxiv_url: https://arxiv.org/abs/2501.00015
pdf_url: https://arxiv.org/pdf/2501.00015
published: 2025-01-03
updated: 2025-01-22
authors: ["DeepSeek-AI"]
categories: ["cs.AI", "cs.CL", "cs.LG"]
tags: ["paper", "arxiv", "cs-AI", "LLM", "RL", "reasoning"]
folder: Papers/AI-LLM
---

# DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning

**arXiv ID:** `2501.00015v1`  
**Published:** 2025-01-03  
**Updated:** 2025-01-22  
**Categories:** `cs.AI`, `cs.CL`, `cs.LG`

## Authors
- DeepSeek-AI

## Abstract
We present DeepSeek-R1-Zero and DeepSeek-R1, two large language models...

## Links
- [Abstract](https://arxiv.org/abs/2501.00015)
- [PDF](https://arxiv.org/pdf/2501.00015)
- [HTML](https://arxiv.org/html/2501.00015)

## Citation
```bibtex
@article{DeepSeekAI2025_2501.00015,
  title     = {DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning},
  ...
}
```

## Notes
> Add your notes here...
```

### Auto-Tag Detection

Papers are automatically tagged based on content:

| Keyword | Tag |
|---------|-----|
| LLM, language model, GPT | `LLM` |
| multimodal, vision | `multimodal` |
| reasoning, chain-of-thought | `CoT` |
| RLHF, reinforcement | `RL` |
| transformer, attention | `transformer` |
| mixture of experts, moe | `MoE` |
| fine-tuning, instruction | `fine-tuning` |
| retrieval, rag | `RAG` |
| agent, tool use | `agent` |

---

## Complete Workflow

Combine all tools for a full research pipeline:

### 1. Morning Digest (Cron)

```bash
# ~/.hermes/skills/research/arxiv/run_daily.sh
#!/bin/bash
cd ~/.hermes/skills/research/arxiv

# Track new papers
python scripts/track_arxiv.py --config config/track_topics.json

# Sync new papers to Obsidian
python scripts/sync_to_obsidian.py --query "large language model" --max 10
```

### 2. One-Off Research

```bash
# Search and read
python scripts/search_arxiv.py "test-time compute scaling" --sort date --max 10

# Summarize top papers
python scripts/summarize_paper.py --id 2501.00015,2408.12345 --format obsidian

# Add to Obsidian
python scripts/sync_to_obsidian.py --id 2501.00015
```

### 3. Track Specific Author

```bash
# Find and sync papers from a specific author
python scripts/search_arxiv.py --author "Yann LeCun" --max 5
python scripts/sync_to_obsidian.py --query "author:Yann LeCun" --max 5
```

---

## Withdrawn Papers
