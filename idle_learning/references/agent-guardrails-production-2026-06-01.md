# Supergood Solutions — Agent Guardrails Field Guide (March 2026)

**URL**: https://supergood.solutions/blog/future-friday-agent-guardrails-production-2026/
**Accessed**: 2026-06-01 03:40 idle_learning direction C
**Tags**: agent-safety, production-guardrails, runtime-safety

## Key Data
- **80%** orgs deploying AI agents reported risky behaviors (AIUC-1, Stanford)
- **Only 21%** have complete permission/access visibility

## Four Failure Modes
1. Direct Prompt Injection — well-understood, input filtering suffices
2. Indirect Prompt Injection — through retrieved data, no token separation. OWASP LLM Top 10 #1 vulnerability
3. Privilege Creep — agents accumulate access, no entity maps full toolchain
4. Behavioral Drift — hallucinations, out-of-domain advice, inconsistencies

## Four Guardrail Layers
| Layer | Function | Hermes Equivalent |
|-------|----------|-------------------|
| Input | Sanitize before model | Scene classification prompt |
| Action | Constrain what agent does | ACTION_WHITELIST, DRY_RUN=True |
| Output | Monitor before reach | auto_execute verify (missing) |
| Behavior | Detect drift over time | Dry-run log analysis (partial) |

## Key Quote
> "Human-in-the-loop is not a guardrail at scale. For agents running at machine speed, you need deterministic enforcement — not approval queues everyone learns to bypass."

Validates SafeGround uncertainty-based deferral over HITL for Hermes auto_execute.

## Relevance to DRY_RUN=False
- 4-layer guardrail stack maps to 6 condition framework (conditions ④⑤ = Action constraints layer)
- Binary DRY_RUN=True/False insufficient — graded constraints needed per AgentRunner
