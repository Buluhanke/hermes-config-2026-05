---
name: computer-use-agents-2026
description: "Code-first beats pixels for computer-use agents in 2026."
triggers:
  - computer use agent
  - 截图 vs 代码
  - web agent 策略
  - 1688 自动化 改进
  - CUA benchmark
---

# Computer-Use Agents 2026 — Landscape & Actionable Lessons

## Convergent meta-principle (the one thing to remember)
**Drive software through code/state, not pixels. Reserve screenshots/GUI for fallback only.**
Five independent 2026 results land on the same point:

1. **StateAct** (arxiv 2607.22798): main agent acts on program STATE (bash/Python/file-edit); a dedicated GUI subagent is used on only **1.1% of steps (28/108 tasks)**. Lifts Claude Opus 4.8 on OSWorld 2.0 binary 20.6%→26.9%, partial 54.8%→61.6%, at **~9× lower cost** ($7.8 vs $72/task). Gain came from *observation* (state) not agentic depth (recursion fired on only 7/108 tasks).
2. **Webwright** (Microsoft, github.com/microsoft/Webwright): terminal-native — agent writes **Playwright code + bash**, ~1K LOC, single loop, NO multi-agent. Online-Mind2Web **86.7%** (GPT-5.4), Odysseys **60.1%** (+26.6 over base GPT-5.4, +15.6 over prior SOTA). Code-as-action beats xy-coordinate prediction on every split. Task scripts reusable as CLIs in Claude Code/Codex/OpenClaw.
3. **Hybrid GUI-MCP** (arxiv 2608.03327): same MCP tools help a *reasoning* model +4.0pp but **hurt** a non-reasoning model −5.9pp — the "adoption gap" (reasoning model calls tools on only 23.9% of reachable tasks). Dropping the redundant post-tool screenshot + halving image history cuts input tokens ~1/3; retrained compressed agent hits **37.8% vs 33.0% at 53% input cost**.
4. **Qwen-CUA** (2026-08): screenshots-only native CUA scales with ~100k vCPU fleet + ~40k verifiable tasks, but **Bash augmentation cuts turns ~69→53 yet LOWERS accuracy** — tool-routing still an unsolved RL gap. Native CUA is the universal *fallback*, not the only interface.
5. **COMPUTERRL** (ICLR 2026): API-GUI hybrid + async RL over thousands of parallel desktops; GLM-COMPUTERRL-9B = **48.9% OSWorld** SOTA for 9B class.

## What this means for Hermes
- **Prefer driving actions via code/scripts/state** (bash, Playwright, file APIs, MCP) over click(x,y)/type for any task where the target exposes a programmatic path. Screenshots are the universal fallback for closed/visual UIs.
- **When using computer_use with screenshots, drop redundant frames and prune image history** — hybrid-routing shows ~33% token savings at equal-or-better accuracy once training/inference share the observation rule.
- **For 1688 / browser automation:** the cdp1688.py CDP approach already does code-driven DOM extraction (mtop skuMapOriginal) rather than pixel OCR — keep that; it matches the Webwright/StateAct finding. Extending it with reusable Playwright-style scripts (à la Webwright task_showcase) would compound.
- **Hybrid agents need routing competence:** a tool left unused (or misused) is worse than none. If Hermes exposes a tool, make the routing decision explicit, not implicit.

## 2026 benchmark scoreboard (for "is this solved yet?" gut-checks)
- Computer use: OSWorld-Verified Qwen-CUA 86.2 / Max 87.6; COMPUTERRL-9B 48.9%.
- Long-horizon web: Odysseys best 44.5% perfect (Opus 4.6), Webwright 60.1% (GPT-5.4). Trajectory Efficiency ~1.15%.
- Tool use: GTA-2-Workflow top 14.39% (Gemini-2.5-Pro); TOBench 41.0% (Qwen3.5-Plus, human 94%); E-Bench 73.79% Avg@3 (Kimi-K3); Toolathlon 38.6% (Claude-4.5-Sonnet); AppWorld-UL 48.6% (Opus 4.7, oracle 78.1%); ToolBench-X best ~50% under reliability hazards; AgencyBench 48.4% closed vs 32.1% open.
- **Read: every agentic frontier is far from saturated.** Long-horizon + tool composition + user-in-the-loop + unreliable tools are the open cliffs.

## Multi-agent orchestration trend (parallel finding)
2026 frameworks converge on self-evolution + governance + earned-autonomy + durable memory: Agent Evolution Kit (Reflexion/SCOPE/MARS, trust-gated writes), metaswarm (18 agents, 9-phase SDLC, BEADS, mandatory TDD), OpenHive (Queen+worker clones, shared ledger), Zouroboros (DAG swarm + multi-vendor consensus gate), organism-core (DoD→plan gate→earned autonomy per action type), PiFlow (self-designing DAG, sealed pi-agent nodes, Hermes-style memory), open-multi-agent (TS dynamic DAG, offline Run Viewer). Takeaway: orchestrators should *delegate/evolve*, not execute; verify subagent output independently (metaswarm: "trust nothing, verify everything").

## Verification
- Source facts in fact_store (IDs 1151–1165, 2026-08-25): qwen-cua, stateact, computerll, os-symphony, hybrid-agent, webwright, odysseys, gta-2, tobench, e-bench, toolathlon, appworld-ul, toolbench-x, agencybench, multi-agent.
- Spot-check any claim against its arxiv/GitHub URL before citing externally.
