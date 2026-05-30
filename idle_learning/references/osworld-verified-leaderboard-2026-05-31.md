# OSWorld-Verified Leaderboard (May 28, 2026)

**Source**: [BenchLM.ai OSWorld-Verified](https://benchlm.ai/benchmarks/osWorldVerified)，scraped via `browser_navigate` + `browser_snapshot` (Firecrawl 402, bypassed)

**Benchmark**: OSWorld-Verified — verified subset of OSWorld focused on computer-use tasks in desktop-like environments (navigation, editing, workflow completion). Complex multi-step tasks. Updated quarterly. 20 models evaluated.

**Top 20 scores**：

| Rank | Model | Vendor | Type | Score |
|------|-------|--------|------|-------|
| 1 | Claude Opus 4.8 | Anthropic | Closed | **83.4%** |
| 2 | Holo3-35B-A3B | H Company | Open | **82.6%** |
| 3 | Claude Mythos Preview | Anthropic | Closed | **79.6%** |
| 4 | Holo3-122B-A10B | H Company | Closed | **78.8%** |
| 5 | GPT-5.5 | OpenAI | Closed | **78.7%** |
| 6 | Gemini 3.5 Flash | Google | Closed | **78.4%** |
| 7 | Claude Opus 4.7 (Adaptive) | Anthropic | Closed | **78.0%** |
| 8 | GPT-5.4 | OpenAI | Closed | **75.0%** |
| 9 | Kimi K2.6 | Moonshot AI | Open | **73.1%** |
| 10 | Claude Opus 4.6 | Anthropic | Closed | **72.7%** |
| 11 | Claude Sonnet 4.6 | Anthropic | Closed | **72.1%** |
| 12 | GPT-5.4 mini | OpenAI | Closed | **72.1%** |
| 13 | Claude Opus 4.5 | Anthropic | Closed | **66.3%** |
| 14 | GPT-5.3 Codex | OpenAI | Closed | **64.7%** |
| 15 | Claude Sonnet 4.5 | Anthropic | Closed | **61.4%** |
| 16 | Qwen3.5-122B-A10B | Alibaba | Open | **58.0%** |
| 17 | Qwen3.5-27B | Alibaba | Open | **56.2%** |
| 18 | Qwen3.5-35B-A3B | Alibaba | Open | **54.5%** |
| 19 | GPT-5.2 | OpenAI | Closed | **47.3%** |
| 20 | GPT-5.4 nano | OpenAI | Closed | **39.0%** |

**Key observations**:
- Claude family dominates top 10 (6/10 entries)
- Open-source top performer: **Holo3-35B-A3B at 82.6%** (rank 2)，接近顶级闭源
- GPT-5 family spread：78.7% (5.5) → 75.0% (5.4) → 72.1% (5.4 mini) → 47.3% (5.2) → 39.0% (5.4 nano) — **同一家族内差距高达40pp**
- Qwen3.5 open-source family：58.0% → 56.2% → 54.5%，全部在下半区
- Human baseline on OSWorld: ~72.4% → GPT-5.4 already surpassed (75.0%)

**对 Hermes 的意义**：
- 本地模型目标：Qwen3.5 级别（54-58%）是 M4 24G 合理期望
- GUI grounding 能力（ScreenSpot-V2）与 OSWorld 高度相关，Holo1.5-3B (91.7% ScreenSpot) 可关注
- GPT-5.4 nano 仅 39% 再次证明模型尺寸不是唯一因素，架构和训练方法同样关键
