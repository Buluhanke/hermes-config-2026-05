# Computer Use Agents Leaderboard 2026

## Source
https://gentic.news/computer-use (Updated April 24, 2026)

## Key Benchmark: OSWorld-Verified
- **Human-expert baseline**: 72.4%
- **Current SOTA**: Kimi K2.6 at 73.1% (first to beat human baseline)

## Agent Categories

### 1. Screen-level OS Control (Screenshot + Mouse + Keyboard)
| Rank | Agent | Maker | OSWorld-V | Notes |
|------|-------|-------|-----------|-------|
| 1 | Kimi K2.6 | Moonshot AI | 73.1% | 1T-param MoE (32B active), 13h continuous, 300 sub-agents, OSS |
| 2 | Claude Sonnet 4.5 | Anthropic | 62.9% | Sept 2025 release |

### 2. Browser-only (DOM + Pixels)
| Rank | Agent | Maker | Notes |
|------|-------|-------|-------|
| 1 | Project Mariner | Google DeepMind | Chrome-integrated, Gemini 2.0→3.x, 10 concurrent VMs, AI Ultra subscription |
| 2 | Playwright MCP | Microsoft | Official MCP server wrapping Playwright (Chromium/Firefox/WebKit) |

### 3. Sandboxed VM/Container
| Agent | Maker | Notes |
|-------|-------|-------|
| (1 agent tracked) | | Full Linux env with shell, browser, files |

### 4. Coding-focused (IDE + Terminal + Git)
| Rank | Agent | Maker | SWE-Bench Verified |
|------|-------|-------|---------------------|
| 1 | SWE-Agent | Princeton+Stanford | >74% (NeurIPS 2024, 100 lines Python) |
| 2 | Aider | OSS | Terminal-first, Git-integrated, BYO-LLM |

## Key Takeaways for Hermes
1. Kimi K2.6 is now the OSWorld leader and is open source; available on Ollama as `kimi-k2.6`
2. Playwright MCP (Microsoft) provides official browser automation via MCP
3. SWE-Agent achieves >74% on SWE-bench with just 100 lines of Python
4. 12 months ago all models scored <15% on OSWorld; now SOTA exceeds human baseline

## HN #1 Story (2026-06-03): Anthropic surpasses OpenAI
- Becomes highest-valued AI startup
- Score: 297pts on HN
- Correlates with Claude Sonnet 4.5's strong OSWorld performance (62.9%)

## References
- OSWorld-Verified: https://osworldbenchmark.com
- gentic.news leaderboard: https://gentic.news/computer-use
- SWE-Agent: https://github.com/princeton-nlp/SWE-agent
- Playwright MCP: https://github.com/microsoft/playwright-mcp
- Ollama Kimi K2.6: `ollama pull kimi-k2.6`
