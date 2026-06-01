# Browser and Computer-Use Agents in Practice (Youngju Kim, 2026-04-12)

**Source**: youngju.dev/blog/ai-platform/2026-04-12-browser-computer-use-agents-practical-guide.en
**Author**: Youngju Kim (@fjvbn20031)
**Retrieved**: 2026-06-02 (browser_navigate, CDP full-text extraction)

## Architecture

| Layer | Role | Practical note |
|-------|------|---------------|
| Planner | Breaks goal into steps | Short plans easier to verify |
| Browser/VM runtime | Interacts with UI | Isolation should be default |
| Observer | Reads DOM, screenshots, logs | Single signal is brittle |
| Action layer | Clicks, types, scrolls, commands | Needs policy checks + rate limits |
| Memory | Stores task state + constraints | Separate working from policy memory |
| Guardrails | Blocks sensitive actions | Design with security + ops together |

## Three Architecture Patterns
1. **Approval-gated single-task**: One bounded task, approved sites, ask approval before important actions.
2. **Research-then-execute pipeline**: Request → Research → Structured plan → Human approval → Execution → Verification → Audit log
3. **Policy-driven task queue**: Pre-approved task types, policy engine defines allowed environment per task.

## Guardrails (7-layer)
Runtime isolation / Low-privilege identity / Network allowlist / Data sensitivity blocking / Approval gates / Full audit logging / Post-action verification

## 5 Failure Modes
Screen prompt injection / Unstable selectors / Slow execution / False success reports / Expired sessions / Excess autonomy

## 5-Phase Adoption Plan
Phase 1: Pick 3 workflows → Phase 2: Read-only agent → Phase 3: Approval-gated writes → Phase 4: Policy enforcement → Phase 5: Optimization

## 10-Item Readiness Checklist
1. Task scope = 1-2 clear goals?
2. Approved + blocked sites explicitly listed?
3. Dedicated VM/container ready?
4. Runs without sensitive data by default?
5. Approval before deletion/transfer/purchase/permission changes?
6. Verification step after execution?
7. Safe handoff to human when confidence drops?
8. Success rates + failure types measured?
9. Audit logging stored and reviewed?
10. Process to update prompts/policy when UI changes?

## Hermes Relevance: HIGH
- DRY_RUN=False transition maps to Phases 2→3
- 10-item checklist = auto-execute readiness standard
- Failure modes directly applicable to screen_trigger_handler
