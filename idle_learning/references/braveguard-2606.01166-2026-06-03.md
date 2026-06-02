# BraveGuard (arXiv 2606.01166) — Computer-Use Agent Safety Framework

**Discovered**: 2026-06-03 (arXiv upload: ~3 days ago)
**Source**: ddgs search "computer use agent safety prompt injection guardrail 2026"

## Core Contribution
- **Self-evolving defense framework** for training guard models against open-world threats
- Addresses: multi-step execution traces where individual actions appear locally benign but the full sequence is harmful
- Defends against: indirect prompt injection, context poisoning, benign-looking action sequences that accumulate into harm

## Key Insight
> "Harm often emerges only through multi-step execution traces whose individual actions appear locally benign."

This is the **exact risk profile of Hermes screen_trigger execution layer**:
- Each `screencapture` + `wininfo` + `nclick` sequence looks locally innocent
- But a poisoned screen context → bad action recommendation → destructive operation = real harm
- BraveGuard's guard model trains on execution traces, not single prompts

## Relevance to Hermes
- **Direct**: BraveGuard's trace-level defense maps to Hermes screen_trigger handler's multi-step loop (observe → classify → recommend → execute)
- **Trace entropy detection**: BraveGuard detects locally-benign sequences by accumulated trajectory analysis — suggests adding "consecutive action sequence entropy check" to screen_trigger_handler
- **Guard model training**: If Hermes had a guard model trained on dry-run traces, it could catch anomalous action patterns before execution

## Risk Matrix
| Dimension | Assessment |
|-----------|------------|
| Direct risk | MED — screen_trigger dry-run traces are exactly the execution traces BraveGuard protects against |
| Indirect risk | LOW — Hermes is localhost-only, but a poisoned screen context from a malicious page is plausible |
| Action | Add to Direction B watchlist; consider implementing trace entropy detection in handler |

## arXiv Metadata
- URL: https://arxiv.org/abs/2606.01166
- Title: "BraveGuard: From Open-World Threats to Safer Computer-Use Agents"
- Expected sections: Introduction / Background / Threat Model / BraveGuard Framework / Experiments / Related Work / Conclusion
