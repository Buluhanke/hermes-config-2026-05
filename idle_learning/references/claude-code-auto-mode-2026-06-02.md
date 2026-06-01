# Claude Code Auto Mode — DRY_RUN=False Architecture Reference

**Source**: Anthropic Engineering Blog, Mar 25 2026
**URL**: anthropic.com/engineering/claude-code-auto-mode
**Full extraction**: browser_navigate + browser_console JS segment extraction (article.innerText)

## Relevance to Hermes

Claude Code auto mode is the industry's closest analog to Hermes' DRY_RUN=False transition. Its mature architecture provides a precise reference for what Hermes needs before enabling autonomous execution.

---

## Architecture Overview

### Three-Tier Permission System

| Tier | Claude Code | Hermes Counterpart |
|------|-------------|-------------------|
| **Tier 1** | Safe-tool allowlist (file read, search, code nav, todo, plan-mode) | Read-only operations: web_extract, web_search, topic search, session_search |
| **Tier 2** | In-project file operations (write/edit within project directory) | Local file I/O in audited paths |
| **Tier 3** | Transcript classifier (shell, web fetch, external tool, subagent spawn) | DRY_RUN=False core — currently missing |

### Two-Stage Classifier

- **Stage 1**: Single-token fast filter (yes/no, tuned to err on blocking)
- **Stage 2**: Chain-of-thought reasoning (only runs on Stage 1 flags)
- **Performance**: FPR 0.4% / FNR 17% (honest reporting, not perfect)
- Stage 1's final instruction: "err on the side of blocking" → accept 8.5% FPR
- Stage 2 reduces FPR from 8.5% → 0.4% via CoT reasoning
- Input is identical except final instruction → nearly full cache hit from Stage 1

### Two-Layer Defense

1. **Input layer**: Prompt-injection probe scans tool outputs before entering agent context
   - Detects "ignore previous instructions" style content
   - Injects warning alongside result telling agent to re-anchor on user intent
2. **Output layer**: Transcript classifier evaluates each action before execution
   - Sees only user messages + agent tool calls
   - Strips assistant prose and tool results (makes it injection-blind by design)
   - Stripping tool results is the PRIMARY injection defense

### Subagent Handoff Protocol

Directly addresses Hermes `delegate_task` self-report vulnerability:

- **Outbound check**: At delegation time — verifies task was actually authorized by user
  - Without this, subagent sees orchestrator's instruction as the "user message" and thinks everything is authorized
- **Inbound check**: At return time — reviews subagent's full action history
  - Detects if subagent was compromised mid-run by prompt injection in content it read
  - If flagged, prepends security warning to orchestrator (doesn't discard results)
- **Hermes gap**: `delegate_task` only accepts self-report summary, no verification

### Deny-and-Continue Policy

- Blocked action → agent retries with safer approach
- Backstop: 3 consecutive denials or 20 total → terminate session
- In headless mode: process termination (no UI to ask human)
- False positives cost 1 retry, not a session kill

### Guardrails on Entry

- Entering auto mode drops blanket interpreter permissions: python, node, ruby, shell wildcards
- Narrow rules (e.g. "allow code formatters") carry over
- Recognition that broad interpreter access + classifier = classifier never sees most dangerous commands

---

## Threat Model (4 categories)

| # | Threat | Description | Catches |
|---|--------|-------------|---------|
| 1 | Overeager behavior | Agent takes initiative beyond what user authorized | Primary target |
| 2 | Honest mistake | Agent misunderstands blast radius | Same defense |
| 3 | Prompt injection | Content hijacks agent behavior | Tier 3 catches action |
| 4 | Misalignment | Agent pursues own goals | Not seen in practice |

All four defended by same action classifier — blocks the action regardless of origin.

---

## What the Classifier Evaluates

**Evaluation rules**: Real-world impact, not surface text:
- Agent writes payload → runs it → classifier evaluates the payload
- `&&` chain treated as one action
- Python script assembles shell command → classifier evaluates assembled command

**User intent rules**: Conservative reading of authorization:
- "Clean up my branches" ≠ authorize batch delete
- "Can we fix this?" = question, not directive
- Step-by-step classification: block rules → allow exceptions → user intent → decision

**20+ block rules in 4 groups**:
1. Destroy or exfiltrate (force push, cloud delete, data exfiltration)
2. Degrade security (disable logging, SSH keys, cronjob persistence)
3. Cross trust boundaries (run code from external repos, scan credential stores)
4. Bypass review (push directly to main, production deploys shared resources)

---

## Key Results

| Dataset | Metric | Value |
|---------|--------|-------|
| Real traffic (n=10,000) | FPR | 0.4% |
| Real overeager (n=52) | FNR | 17% |
| Synthetic exfil (n=1,000) | FNR | 5.7% |

**17% FNR on real overeager actions is the honest number**:
- Classifier correctly identifies danger (force-push, deletion, infra change)
- Gets wrong whether consent signal actually covers this action
- "Clean up the PR" ≠ force-push; one prior approval ≠ pattern

---

## Implications for Hermes

1. **DRY_RUN=False needs action-level classifier**, not just scene classification
2. **Zero risk is unreachable** — even Anthropic with massive resources has 17% FNR
3. **Start from read-only operations** (Tier 1) and gradually open up
4. **Subagent context loss** is a known and solved problem (outbound + inbound checks)
5. **Prompt injection input-layer defense** needed for screen_trigger handler's VLM calls
6. **Deny-and-continue** model is better than "all or nothing" — Harms false positives recoverable
