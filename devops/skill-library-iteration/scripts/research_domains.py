#!/usr/bin/env python3
# 领域 SOTA 研究：对 9 个领域各做针对性搜索，整理 2025-2026 更优方案。
import os, sys, json
from hermes_tools import web_search

OUT = "/tmp/research_domains"
os.makedirs(OUT, exist_ok=True)

# 每个领域：调研方向 + 2-3 条精准查询
DOMAINS = {
    "web_scraping_research": [
        "best web scraping tool 2026 agentic crawl4ai scrapling browser-use comparison",
        "read logged-in website without headless browser accessibility tree 2026",
        "defuddle readability trafilatura extract article 2026 best",
    ],
    "sourcing_1688": [
        "1688 sourcing CLI agent 2026 opencli 1688-cli vs CDP chrome",
        "1688 product data API alternative 2026 open.1688.com enterprise",
        "1688 open source scraper 2026 sku price mtop",
    ],
    "coding_workflow": [
        "coding agent workflow best practice 2026 spec-driven subagent BMAD anthropic",
        "best TDD agentic refactoring tool 2026",
        "parallel subagent orchestration 2026 delegate task framework",
    ],
    "agent_memory": [
        "best agent memory system 2026 mem0 letta zep graphiti memobase cognee comparison",
        "long term memory rag agent open source 2026 sqlite graph",
        "context compression agent 2026",
    ],
    "office_ocr": [
        "best OCR document pipeline 2026 marker mineru docling olmocr comparison",
        "generate docx xlsx pptx programmatically 2026 best library python",
        "pdf table extraction 2026 best open source",
    ],
    "generative_media": [
        "best AI video generation 2025 2026 open source comfyui wan",
        "AI music generation 2026 suno alternative open source audiocraft",
        "infographic generation AI 2026 best tool",
    ],
    "local_infra_ml": [
        "local LLM inference Apple Silicon 2026 llama.cpp MLX ollama vllm comparison",
        "mlflow wandb alternative 2026 open source experiment tracking",
        "prometheus grafana alternative 2026 victoriametrics observability",
    ],
    "research_knowledge": [
        "deep research open source framework 2026 gpt-researcher open-deep-research",
        "literature review tool 2026 agentic",
        "personal knowledge management agent 2026 obsidian integration",
    ],
    "hermes_ops": [
        "ai agent self maintenance autonomous 2026 hermes openclaw skill management",
        "agent backup restore git 2026 best practice",
        "cron job reliability agent 2026",
    ],
}

for dom, queries in DOMAINS.items():
    collected = []
    for q in queries:
        try:
            r = web_search(q, limit=4)
            for it in r.get("data", {}).get("web", []):
                collected.append({
                    "query": q,
                    "url": it.get("url"),
                    "title": it.get("title"),
                    "desc": (it.get("description") or "")[:300],
                })
        except Exception as e:
            collected.append({"query": q, "error": str(e)})
    with open(os.path.join(OUT, f"{dom}.json"), "w") as f:
        json.dump({"domain": dom, "recs": collected}, f, ensure_ascii=False, indent=2)
    print(f"{dom}: {len(collected)} results")
print("DONE ->", OUT)
