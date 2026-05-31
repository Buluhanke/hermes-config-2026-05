# arXiv 2605.10223 — Dynamic Tiered AgentRunner: Controlled Execution Protocol

**Published**: May 11, 2026
**Authors**: Kai Pan, Rong Hou
**arXiv**: https://arxiv.org/abs/2605.10223
**Tags**: agent-safety, risk-adaptive, separation-of-powers, verifier-recovery

## Summary

Proposes the Dynamic Tiered AgentRunner, a controlled execution protocol distilled from a production-grade multi-tenant SaaS platform. Introduces three core mechanisms directly relevant to Hermes auto_execute DRY_RUN=False transition.

## Three Core Mechanisms

### 1. Risk-Adaptive Tiering
Dynamically allocates computational resources and review intensity based on task risk profiles. Achieves Pareto-optimal trade-offs between safety and efficiency.

**Relevance to Hermes**: Maps to Silent/Logged/Confirmed/Blocked action grading. Current binary separation (idle→none vs business→wininfo) is a minimal 2-tier version; AgentRunner validates multi-tier direction.

**Key quote**: "High-risk write operations proceed without independent review, complex tasks lack acceptance verification."

### 2. Separation of Powers
Proposal, review, execution, and verification by independent agents with physically isolated boundaries.

**Relevance to Hermes**: Handler combines scene classification + action dispatch in same process. AgentRunner suggests splitting. Verify stage entirely missing from auto_execute.

### 3. Verifier-Recovery Closed Loop
Failure as a first-class system state, not an exception.

**Relevance to Hermes**: handler negation detection is primitive verification. Full version would add post-action state verification, recovery trajectory generation, failure classification.

## Production Evidence
- Distilled from production multi-tenant SaaS platform (real-world validation)
- 9 pages, 2 figures, 3 tables

## Key Takeaways
1. Risk-Adaptive Tiering validates binary→multi-tier action grading direction
2. Separation of Powers suggests splitting handler's combined stages
3. Verifier-Recovery = missing Verify stage in observe→plan→dispatch loop

**Discovered**: 2026-06-01 03:40 idle_learning direction C
**Accessed via**: browser_navigate to arxiv.org/abs/2605.10223
