# Parallax: Why AI Agents That Think Must Never Act

**Source**: arXiv 2604.12986v1, April 2026
**Author**: Joel Forcu (Independent Researcher)
**Link**: https://arxiv.org/abs/2604.12986
**License**: CC BY 4.0

## Core Thesis

Prompt-level guardrailing is **architecturally insufficient** for AI agents with execution capability. The reasoning system and safety instructions share the same attention mechanism — structurally unable to distinguish trusted instructions from untrusted data. This is the "Prompt Guardrail Fallacy."

## Four Architectural Principles

### 1. Cognitive-Executive Separation
The system that **reasons** about actions must be structurally **unable** to execute them. The system that **executes** actions must be structurally **unable** to reason about them. An independent, immutable validator is interposed between the two.
- **Hermes mapping**: Currently Hermes' reasoning and execution share the same process. DRY_RUN=True is a behavioral constraint, not architectural.

### 2. Adversarial Validation with Graduated Determinism
A multi-tiered validation layer between reasoning and execution. Higher-risk actions require more deterministic (less model-dependent) verification.
- **Hermes mapping**: DRY_RUN=True is the extreme end (no execution → fully deterministic). The proposed action-level classifier for DRY_RUN=False would be graduated determinism.

### 3. Information Flow Control
Data sensitivity labels propagate through agent workflows to detect context-dependent threats. A compromised tool should not leak its sensitivity to untrusted data.
- **Hermes mapping**: No current data flow tracking. All tools have equal access.

### 4. Reversible Execution
Pre-destructive state capture before irreversible actions, enabling rollback on validation failure.
- **Hermes mapping**: No rollback mechanism. file_ops etc. are non-reversible.

## OpenParallax Implementation
- **Language**: Go
- **Architecture**: Process-isolated (separate processes for reasoning, validation, execution)
- **Validator**: 4-tiered "Shield" system
- **State capture**: "Chronicle" — pre-destructive state snapshots
- **Sandbox**: Integrity verification

## Evaluation Results
- **Methodology**: Assume-Compromise Evaluation (bypass reasoning system entirely, inject tool calls directly into execution boundary)
- **280 adversarial test cases across 9 attack categories**
- **Default config**: 98.9% block rate, **zero false positives**
- **Max-security config**: 100% block rate
- **Key insight**: When reasoning system is compromised, prompt-level guardrails offer **zero protection** because they exist only within the compromised system. Parallax's architectural boundaries remain effective.

## Attack Categories Covered
1. Direct prompt injection
2. Indirect prompt injection
3. Multi-step context manipulation
4. Tool-use chain attacks
5. Encoding and obfuscation exploits
6. Multi-agent compromise
7. Privilege escalation
8. Validation layer attacks
9. Information flow bypass

## Relevance to Hermes

| Principle | Hermes Status | Gap |
|-----------|--------------|-----|
| Cognitive-Executive Separation | ❌ Not implemented | Reasoning and execution share process |
| Adversarial Validation | ⚠️ Partial | DRY_RUN=True is behavioral, not architectural |
| Information Flow Control | ❌ Not implemented | No data sensitivity tracking |
| Reversible Execution | ❌ Not implemented | No rollback mechanism |

**Recommendation**: Study OpenParallax as prerequisite architecture before DRY_RUN=False transition.
