# gentic.news Computer Use Agents 2026 Leaderboard (Updated April 24, 2026)

**Source**: https://gentic.news/computer-use
**Verified**: 2026-06-02 via browser_navigate + browser_console JS extraction
**Status**: Live leaderboard tracking 6 agents across 8 benchmarks

## Quick Summary

| Metric | Value |
|--------|-------|
| OSWorld-Verified SOTA | Claude Sonnet 4.5 at **62.9%** |
| Strongest Open-Source | Kimi K2.6 (Moonshot AI) at **73.1%** |
| Human Expert Baseline | 72.4% |
| Best Browser Agent | Surfer 2 (WebVoyager 97.1%) |
| Best Coding Agent | Claude Opus 4.7 (SWE-Bench Pro 64.3%, SWE-Bench Verified 87.6%) |

## 4 Agent Categories Tracked

### Screen-Level OS Control (1 agent)
1. **Claude Sonnet 4.5** (Anthropic, Sept 2025) — 62.9% OSWorld-Verified

### Browser-Only (2 agents)
1. **Project Mariner** (Google DeepMind, Dec 2024) — Chrome-integrated, Gemini 2.0→3.x
2. **Playwright MCP** (Microsoft, Mar 2025) — MCP server wrapping Playwright

### Sandboxed VM / Container (1 agent)
1. **Lovable** (formerly GPT Engineer, Nov 2024) — AI full-stack app builder

### Coding-Focused (2 agents)
1. **SWE-Agent** (Princeton+Stanford, Apr 2024) — Open-source, NeurIPS 2024
2. **Aider** (OSS, May 2023) — Terminal-first AI pair programmer

## Key Benchmarks & SOTA

| Benchmark | SOTA % | Human | Holder | Tasks |
|-----------|--------|-------|--------|-------|
| OSWorld-Verified | 62.9% | 72.4% | Claude Sonnet 4.5 | — |
| BrowseComp | 86.9% | 80% | Claude Mythos Preview | 1,266 |
| Terminal-Bench 2.0 | 92.1% | — | Claude Mythos | — |
| WebVoyager | 97.1% | — | Surfer 2 | 643 |
| SWE-Bench Verified | 87.6% | — | Claude Opus 4.7 | 500 |
| SWE-Bench Pro | 64.3% | — | Claude Opus 4.7 | 731 |
| GDPval | 47.6% | — | GPT-5.4 | 220 |

## Core Triad (2026 consensus)
OSWorld-Verified + BrowseComp + Terminal-Bench 2.0 = weighted agentic score.

## Relevance to Hermes
- Screen-level OS Control category maps directly to Hermes screen_trigger_handler + auto_execute
- No local/open-source agents tracked in Screen-level category — gap opportunity
- Claude Sonnet 4.5 (62.9% OSWorld-V) is cloud-only; Hermes needs local alternatives
- Playwright MCP pattern (MCP-wrapped browser control) is architecturally similar to Hermes browser tools
