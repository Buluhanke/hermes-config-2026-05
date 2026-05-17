#!/usr/bin/env python3
"""Generate structured summaries for arXiv papers using the arXiv API metadata.

Usage:
    python summarize_paper.py 2402.03300
    python summarize_paper.py --id 2402.03300
    python summarize_paper.py --id 2402.03300,2401.12345 --format short
    python summarize_paper.py --query "GRPO reinforcement learning" --max 3
    python summarize_paper.py --fetch-full --id 2402.03300

Output formats:
    short    - One-line summary (title | authors | date | cats)
    medium   - Abstract + metadata (default)
    full     - Structured markdown with all fields
    obsidian - Obsidian-ready note with frontmatter
"""
import sys
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
NS = {'a': 'http://www.w3.org/2005/Atom'}

# Well-known paper insights (pre-computed for reference)
PAPER_INSIGHTS = {
    # GPT series
    'GPT-3': 'Massive 175B parameter model with few-shot learning via in-context learning. No task-specific fine-tuning needed.',
    'GPT-4': 'Multimodal large language model with improved reasoning, instruction following, and safety. Uses RLHF.',
    'InstructGPT': 'RLHF applied to align language models with human preferences. Dramatically improves instruction following.',
    'ChatGPT': 'Reinforcement learning from human feedback (RLHF) to train a conversational agent.',
    
    # Claude series
    'Claude': 'Constitutional AI approach for AI alignment. Uses AI feedback for RLHF, reducing harm.',
    
    # Gemini
    'Gemini': 'Multimodal model from Google. Native multimodal training from the ground up.',
    
    # LLM reasoning
    'chain-of-thought': 'Chain-of-thought prompting elicits reasoning. Intermediate steps improve complex reasoning.',
    'CoT': 'Chain-of-thought prompting improves LLM performance on complex reasoning tasks.',
    'ReAct': 'Combines reasoning (CoT) with acting (tool use). Synergizes for complex tasks.',
    'STaR': 'Self-taught reasoner. Generates and learns from reasoning traces without annotated data.',
    'ToRA': 'Tool-integrated reasoning agent for mathematical problem solving.',
    
    # RLHF / Alignment
    'RLHF': 'Reinforcement Learning from Human Feedback. Uses human preference data to fine-tune LLMs.',
    'PPO': 'Proximal Policy Optimization. Used in RLHF for stable policy updates.',
    'DPO': 'Direct Preference Optimization. Stable alternative to PPO for preference learning.',
    'GRPO': 'Group Relative Policy Optimization. DeepSeek method for efficient RL without critic.',
    'KTO': 'Kahneman-Tversky Optimization. Alignment method based on loss aversion.',
    
    # Transformer architecture
    'transformer': 'Attention-based architecture. Replaced RNNs. Foundation of modern LLMs.',
    'attention': 'Core mechanism of transformers. Allows modeling long-range dependencies.',
    'FlashAttention': 'IO-aware exact attention. 2-4x speedup, reduced memory from O(N²) to O(N).',
    'RoPE': 'Rotary Position Embedding. Allows extrapolating to longer sequences at inference.',
    'GQA': 'Grouped Query Attention. Reduces KV head count while maintaining quality.',
    'MQA': 'Multi-Query Attention. Single KV head. Faster inference, lower memory.',
    'scaling': 'Scaling laws show LLM performance improves predictably with model size, data, compute.',
    
    # Mixture of Experts
    'mixtral': 'Mixtral 8x7B. Mixture of experts. Each token uses a subset of experts for efficiency.',
    'MoE': 'Mixture of Experts. Sparse activation. More parameters with less compute per token.',
    
    # Multimodal
    'LLaVA': 'Large Language and Vision Assistant. Connects vision encoder to LLM for multimodal tasks.',
    'GPT-4V': 'GPT-4 with vision. State-of-the-art multimodal understanding.',
    
    # Fine-tuning
    'LoRA': 'Low-Rank Adaptation. Freeze most weights, train small rank decomposition matrices.',
    'QLoRA': 'Quantized LoRA. 4-bit quantization + LoRA for memory-efficient fine-tuning.',
    'LORA': 'Low-Rank Adaptation. Memory-efficient fine-tuning for LLMs.',
    
    # RAG
    'RAG': 'Retrieval-Augmented Generation. Combines retrieval with generation for up-to-date answers.',
    
    # Agent
    'agent': 'LLM agent. Uses tools, plans actions, interacts with environment.',
    'tool use': 'LLM tool use. Enables agents to interact with external systems.',
}

def fetch_paper(arxiv_id):
    """Fetch paper metadata from arXiv API."""
    clean_id = arxiv_id.split('v')[0]
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
    journal_ref = entry.find('a:journal_ref', NS).text if entry.find('a:journal_ref', NS) is not None else None
    
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
        'journal_ref': journal_ref,
        'url': f'https://arxiv.org/abs/{arxiv_id}',
        'pdf': f'https://arxiv.org/pdf/{arxiv_id}',
        'html': f'https://arxiv.org/html/{arxiv_id}',
    }

def extract_key_insights(paper):
    """Extract key insights based on title/abstract keywords."""
    text = (paper['title'] + ' ' + paper['summary']).lower()
    insights = []
    
    for keyword, insight in PAPER_INSIGHTS.items():
        if keyword.lower() in text:
            if insight not in insights:
                insights.append(insight)
    
    return insights[:5]  # max 5 insights

def detect_methods(paper):
    """Detect methods/techniques mentioned in the paper."""
    text = (paper['title'] + ' ' + paper['summary']).lower()
    
    methods = {
        'RLHF': 'Reinforcement Learning from Human Feedback',
        'DPO': 'Direct Preference Optimization',
        'PPO': 'Proximal Policy Optimization',
        'GRPO': 'Group Relative Policy Optimization',
        'KTO': 'Kahneman-Tversky Optimization',
        'LoRA': 'Low-Rank Adaptation',
        'QLoRA': 'Quantized LoRA',
        'CoT': 'Chain-of-Thought Prompting',
        'ReAct': 'Reasoning + Acting',
        'RAG': 'Retrieval-Augmented Generation',
        'MoE': 'Mixture of Experts',
        'GNN': 'Graph Neural Network',
        'SFT': 'Supervised Fine-Tuning',
        'SFT ': 'Supervised Fine-Tuning',
        'attention': 'Attention Mechanism',
        'transformer': 'Transformer Architecture',
        'diffusion': 'Diffusion Model',
        'VAE': 'Variational Autoencoder',
        'GAN': 'Generative Adversarial Network',
        'CLIP': 'Contrastive Language-Image Pretraining',
        'LSTM': 'Long Short-Term Memory',
        'RM': 'Reward Model',
        'RM ': 'Reward Model',
        'reward model': 'Reward Model',
        'KL divergence': 'KL Divergence',
        'Bradley-Terry': 'Bradley-Terry Model',
    }
    
    found = []
    for method, full_name in methods.items():
        if method.lower() in text:
            if full_name not in found:
                found.append(full_name)
    
    return found[:6]

def detect_tasks(paper):
    """Detect tasks the paper addresses."""
    text = (paper['title'] + ' ' + paper['summary']).lower()
    
    tasks = {
        'reasoning': 'Reasoning',
        'code generation': 'Code Generation',
        'code generation': 'Code Generation',
        'translation': 'Machine Translation',
        'summarization': 'Summarization',
        'question answering': 'Question Answering',
        'qa ': 'Question Answering',
        'dialogue': 'Dialogue',
        'conversation': 'Conversation',
        'text generation': 'Text Generation',
        'image generation': 'Image Generation',
        'object detection': 'Object Detection',
        'segmentation': 'Segmentation',
        'classification': 'Classification',
        'recommendation': 'Recommendation',
        'planning': 'Planning',
        'agent': 'Agent',
        'tool use': 'Tool Use',
        'mathematics': 'Mathematics',
        'theorem proving': 'Theorem Proving',
        'world model': 'World Model',
    }
    
    found = []
    for task, full_name in tasks.items():
        if task.lower() in text:
            if full_name not in found:
                found.append(full_name)
    
    return found[:4]

def detect_benchmarks(paper):
    """Detect benchmarks/datasets mentioned."""
    text = (paper['title'] + ' ' + paper['summary']).lower()
    
    benchmarks = {
        'MMLU': 'MMLU (Massive Multitask Language Understanding)',
        'GSM8K': 'GSM8K (Grade School Math 8K)',
        'HumanEval': 'HumanEval (Code Generation)',
        'MATH': 'MATH Benchmark',
        'BIG-Bench': 'BIG-Bench',
        'HELM': 'HELM',
        'MT-Bench': 'MT-Bench',
        'AlpacaEval': 'AlpacaEval',
        'LLMBar': 'LLMBar',
        'TrustGPT': 'TrustGPT',
        'BBQ': 'BBQ (Bias Benchmark for QA)',
        'BOLD': 'BOLD',
        'HellaSwag': 'HellaSwag',
        'Arc': 'ARC (Abstraction and Reasoning Corpus)',
        'C4': 'C4 Dataset',
        'The Pile': 'The Pile',
        'Red Pajama': 'Red Pajama',
    }
    
    found = []
    for bm, full_name in benchmarks.items():
        if bm.lower() in text:
            if full_name not in found:
                found.append(full_name)
    
    return found[:5]

def summarize_paper(paper, format='medium'):
    """Generate a structured summary of a paper."""
    
    if format == 'short':
        cats = ', '.join(paper['categories'][:3])
        return f"{paper['title']} | {paper['author_str'][:60]} | {paper['published']} | {cats}"
    
    insights = extract_key_insights(paper)
    methods = detect_methods(paper)
    tasks = detect_tasks(paper)
    benchmarks = detect_benchmarks(paper)
    
    if format == 'medium':
        lines = []
        lines.append(f"# {paper['title']}")
        lines.append(f"**arXiv:** `{paper['full_id']}` | **Published:** {paper['published']} | **Updated:** {paper['updated']}")
        lines.append(f"**Authors:** {paper['author_str']}")
        lines.append(f"**Categories:** {', '.join(paper['categories'])}\n")
        lines.append(f"## Abstract\n{paper['summary']}\n")
        
        if methods:
            lines.append(f"## Methods\n" + '\n'.join(f"- {m}" for m in methods) + '\n')
        if tasks:
            lines.append(f"## Tasks\n" + ', '.join(f"`{t}`" for t in tasks) + '\n')
        if benchmarks:
            lines.append(f"## Benchmarks\n" + ', '.join(f"`{b}`" for b in benchmarks) + '\n')
        if insights:
            lines.append(f"## Key Insights\n" + '\n'.join(f"- {i}" for i in insights) + '\n')
        
        lines.append(f"## Links\n- [Abstract]({paper['url']}) | [PDF]({paper['pdf']}) | [HTML]({paper['html']})")
        return '\n'.join(lines)
    
    elif format == 'full':
        cats_html = ', '.join(f'<code>{c}</code>' for c in paper['categories'])
        methods_html = '\n'.join(f'<li>{m}</li>' for m in methods) if methods else '<li>Not detected</li>'
        tasks_html = ', '.join(f'<code>{t}</code>' for t in tasks) if tasks else 'Not detected'
        benchmarks_html = ', '.join(f'<code>{b}</code>' for b in benchmarks) if benchmarks else 'Not detected'
        insights_html = '\n'.join(f'<li>{i}</li>' for i in insights) if insights else '<li>None detected</li>'
        
        return f"""# {paper['title']}

| Field | Value |
|-------|-------|
| **arXiv ID** | `{paper['full_id']}` |
| **Published** | {paper['published']} |
| **Updated** | {paper['updated']} |
| **Primary Category** | {paper['primary_category']} |
| **All Categories** | {cats_html} |
| **Authors** | {paper['author_str']} |

## Abstract
{paper['summary']}

## Authors
{' | '.join(paper['authors'])}

## Methods
<ul>{methods_html}</ul>

## Tasks
{tasks_html}

## Benchmarks
{benchmarks_html}

## Key Insights
<ul>{insights_html}</ul>

## Links
- [Abstract]({paper['url']})
- [PDF]({paper['pdf']})
- [HTML]({paper['html']})
{f'- [DOI](https://doi.org/{paper["doi"]})' if paper.get('doi') else ''}
{f'- [Journal Reference]({paper["journal_ref"]})' if paper.get('journal_ref') else ''}
{f'- [Author Comment]({paper["comment"]})' if paper.get('comment') else ''}
"""
    
    elif format == 'obsidian':
        # Auto-detect tags
        tags = ['paper', 'arxiv', paper['primary_category'].replace('.', '-')]
        title_lower = paper['title'].lower()
        
        topic_tags = {
            'llm': 'LLM', 'language model': 'LLM', 'gpt': 'GPT', 'claude': 'Claude',
            'multimodal': 'multimodal', 'vision': 'vision', 'image': 'vision',
            'reasoning': 'reasoning', 'chain-of-thought': 'CoT', 'cot': 'CoT',
            'rlhf': 'RLHF', 'reinforcement': 'RL', 'reward': 'RL',
            'transformer': 'transformer', 'attention': 'attention',
            'scaling': 'scaling', 'mixture of experts': 'MoE', 'moe': 'MoE',
            'fine-tuning': 'fine-tuning', 'instruction': 'instruction-tuning',
            'retrieval': 'retrieval', 'rag': 'RAG', 'agent': 'agent',
        }
        for kw, tag in topic_tags.items():
            if kw in title_lower or kw in paper['summary'].lower():
                tags.append(tag)
        tags = list(dict.fromkeys(tags))
        
        fm = ['---']
        fm.append(f"title: \"{paper['title']}\"")
        fm.append(f"arxivid: {paper['arxiv_id']}")
        fm.append(f"arxiv_url: {paper['url']}")
        fm.append(f"pdf_url: {paper['pdf']}")
        if paper.get('doi'): fm.append(f"doi: {paper['doi']}")
        fm.append(f"published: {paper['published']}")
        fm.append(f"updated: {paper['updated']}")
        fm.append(f"authors: [{', '.join(f'\"{a}\"' for a in paper['authors'])}]")
        fm.append(f"categories: [{', '.join(f'\"{c}\"' for c in paper['categories'])}]")
        fm.append(f"tags: [{', '.join(f'\"{t}\"' for t in tags)}]")
        fm.append('---')
        fm.append('')
        
        lines = []
        lines.extend(fm)
        lines.append(f"# {paper['title']}\n")
        
        lines.append(f"**arXiv:** `{paper['full_id']}` | **Published:** {paper['published']} | **Categories:** {', '.join(paper['categories'][:3])}\n")
        
        lines.append("## Authors\n" + '\n'.join(f"- {a}" for a in paper['authors']) + '\n')
        lines.append("## Abstract\n" + paper['summary'] + '\n')
        
        if methods:
            lines.append("## Methods\n" + '\n'.join(f"- {m}" for m in methods) + '\n')
        if tasks:
            lines.append("## Tasks\n" + ', '.join(f"`{t}`" for t in tasks) + '\n')
        if benchmarks:
            lines.append("## Benchmarks\n" + ', '.join(f"`{b}`" for b in benchmarks) + '\n')
        if insights:
            lines.append("## Key Insights\n" + '\n'.join(f"- {i}" for i in insights) + '\n')
        
        lines.append("## Links\n")
        lines.append(f"- [Abstract]({paper['url']}) | [PDF]({paper['pdf']}) | [HTML]({paper['html']})")
        if paper.get('doi'):
            lines.append(f"- [DOI](https://doi.org/{paper['doi']})")
        lines.append('\n## Notes\n> Add your notes here...\n')
        
        return '\n'.join(lines)
    
    return str(paper)

def search_and_summarize(query, max_results=3, format='medium'):
    """Search arXiv and summarize results."""
    import urllib.request
    import urllib.parse
    
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
        print(f"No results found for '{query}'.")
        return []
    
    print(f"Found {len(entries)} papers for '{query}'\n")
    results = []
    for i, entry in enumerate(entries):
        paper = parse_entry(entry)
        print(f"--- Paper {i+1}/{len(entries)} ---")
        print(summarize_paper(paper, format=format))
        print()
        results.append(paper)
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Summarize arXiv papers")
    parser.add_argument('--id', help='arXiv ID(s), comma-separated')
    parser.add_argument('--query', help='Search query')
    parser.add_argument('--max', type=int, default=3, help='Max results for search (default: 3)')
    parser.add_argument('--format', choices=['short', 'medium', 'full', 'obsidian'], default='medium')
    
    args = parser.parse_args()
    
    if args.id:
        ids = [i.strip() for i in args.id.split(',')]
        for i, paper_id in enumerate(ids):
            print(f"--- Paper {i+1}/{len(ids)} ---")
            try:
                paper = fetch_paper(paper_id)
                print(summarize_paper(paper, format=args.format))
                print()
            except Exception as e:
                print(f"❌ Error: {e}\n")
    elif args.query:
        search_and_summarize(args.query, max_results=args.max, format=args.format)
    else:
        print(__doc__)
        sys.exit(1)
