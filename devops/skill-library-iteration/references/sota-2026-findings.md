# SOTA 2026 Cross-Domain Findings (audit 2026-08)

Condensed from 9-domain `web_search` research. Use as the upgrade reference when iterating
skills in each domain. Each item = current approach → better 2026 option + source.

## web_scraping_research
- Content extraction: defuddle / trafilatura / readability still fine; Readability leaks boilerplate on ~12% of pages at scale (thunderbit benchmark). VLM extractors emerging.
- Real logged-in browser automation (non-headless): Quay (CDP+AX tree), Eyebrowse (MCP), pi-browser-harness. Matches our "front real Chrome, no headless" constraint.

## sourcing_1688
- 1688-cli (superjack2050, MIT) — reuses real Chrome login, structured JSON, agent-friendly. Complementary, not a replacement for CDP+mtop skuMapOriginal.
- Official API (open.1688.com) still enterprise-only. MTop signing difficulty 4/5; needs residential proxy — not viable locally.
- Paid: ShopAPIS, HioBuy. Reverse: QuoVadis86/ai-reverse (MTOP SDK + MCP).

## coding_workflow
- TDD enforcement: tdd-ai, karajan-code (22 roles + SonarQube), SAM (autonomous TDD for Claude Code).
- Subagent orchestration: LangChain dynamic subagents, OpenHands delegation, AOrchestra (arXiv:2602.03786). Hermes delegate_task is equivalent.
- Anthropic advanced patterns: CLAUDE.md + Hooks + parallel subagents.

## agent_memory
- Zep Graphiti: 63.8% on LongMemEval vs Mem0 49.0% — graph memory beats vector for relational reasoning.
- Local single-file: sqlite-graphrag, bripin123/rag-memory-epf-mcp (KG + vector + FTS5 in one SQLite).
- Context compression: Microsoft ACON (acon), Open330/context-compress MCP.

## office_ocr
- PDF parsing SOTA (VLM): MinerU, olmOCR, Docling — beat pymupdf/marker on complex layouts/tables/formulas.
- Table extraction: gmft (lightweight, performant), camelot, pdfplumber.
- Unified Office gen: documind SDK (PPTX/DOCX/XLSX/MD, Apache-2.0) — replaces scattered minimax-* libs.

## generative_media
- Video: Wan2.2 / Wan2.7 (Apache-2.0, ComfyUI) rivals Sora/Veo. Math/algorithm animation still Manim.
- Music: ACE-Step 1.5 (local, Suno-class), YuE (full-song open), tencent-ailab/SongGeneration (LeVo2).
- Infographics: Venngage / Canva AI generators (2026 roundups), baoyu-infographic skill still valid for hand-authored.

## local_infra_ml
- Apple Silicon inference: MLX native fastest (M5 Max Llama70B Q4 ~85 tok/s), Ollama 4% slower but simplest, vLLM for multi-GPU. llama.cpp cross-platform fallback.
- Experiment tracking: litemlflow (MLflow-API-compatible, 143x faster cold start), trackio (HF Datasets based).
- Monitoring: VictoriaMetrics drop-in replacement for Prometheus (lower resource, higher cardinality).

## research_knowledge
- Deep research: gpt-researcher (29k★), langchain-ai/open_deep_research.
- Literature review: thoth (8-stage LangGraph + cite_check per-claim verification), ResearchPilot, LiRA (AAAI).
- PKM + Obsidian: mingrath/obsidian-ai-knowledge-agent, AgriciDaniel/claude-obsidian (self-organizing second brain).

## hermes_ops
- Hermes v0.12.0 ships Curator (aux-model background skill maintenance) — PR #17277. Can take over periodic tidy.
- Backup: Dicklesworthstone/agent_settings_backup_script (git-versioned, size-rotated, easy restore).
- Cron reliability: silentwatch-mcp (catches exit-0-but-empty, retry storms, budget leaks).
