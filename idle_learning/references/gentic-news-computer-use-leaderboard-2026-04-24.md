# gentic.news Computer Use Agents Leaderboard (Apr 24, 2026)

**Source**: https://gentic.news/computer-use
**Reviewed**: Jun 2, 2026

## Key SOTA Scores

| Benchmark | SOTA | Score | Model |
|-----------|------|-------|-------|
| OSWorld-Verified | 🏆 | 80.4% | Holo3-35B-A3B (H Company) |
| OSWorld-Verified | 🥈 | 73.1% | Kimi K2.6 (Moonshot AI) — open-source, beats human baseline |
| OSWorld-Verified | 🥉 | 72.1% | Claude Sonnet 4.6 (tied with human 72.4%) |
| BrowseComp | 🏆 | 86.9% | Claude Mythos Preview |
| Terminal-Bench 2.0 | 🏆 | — | Claude Code / Anthropic |
| WebVoyager | 🏆 | 97.1% | Surfer 2 (H Company) |
| SWE-Bench Verified | 🏆 | 87.6% | Claude Opus 4.7 |
| SWE-Bench Pro | 🏆 | 64.3% | Claude Opus 4.7 |
| GDPval | 🏆 | 47.6% | GPT-5.4 |
| AndroidWorld | 🏆 | 75.8% | UI-TARS-2 (ByteDance) |
| WorkArena++ | 🏆 | — | Microsoft Copilot Studio |

## Key Insight (citable in Direction A/B/D)
> "The harness — scaffold + sandbox + verifier + recovery — matters more than the model."
> "Independent tests show Cursor's scaffold adds 16pp over the raw model."
> "2026 is the year computer use stopped being a demo and started being a line item."

Validates Hermes' screen_trigger + RPA architecture approach — the framework around the model drives actual capability.

## Hermes Relevance
- **Holo3-35B-A3B** (80.4% OSWorld-V) — inaccessible (too large for M4 24GB).
- **Kimi K2.6** (73.1% OSWorld-V, open-source) — likely too large for M4 24GB.
- **UI-TARS-2** — practical choice for M4 24GB at ~53% OSWorld-V.
- **"Harness > model"** — validates screen_trigger + RPA architecture direction.
- **OpenCUA** (NeurIPS 2025 Spotlight, 45.0% OSWorld-V) — best resource-constrained option.
