---
name: skill-authoring-principles
description: Authoring or auditing Hermes skills — write new SKILL.md, patch existing skills, design skill descriptions for better triggering, or apply progressive disclosure / degrees-of-freedom frameworks. Use when creating a skill from scratch, editing or improving a skill, optimizing a skill's description for triggering accuracy, or auditing an existing skill's structure quality.
---

# Skill Authoring Principles

Core principles for authoring high-quality Hermes skills. Applies when creating a new skill, patching an existing one, or evaluating whether a skill is well-structured.

## Progressive Disclosure (Anthropic 2025 Standard)

Skills use a three-level loading system. Design each level deliberately:

**L1 — Metadata (name + description)**: Always pre-loaded into system prompt at startup. ~100 words. This is the *only* thing Claude uses to decide whether to load the skill. The description is the trigger — it must be specific, include trigger keywords, and state both *what* the skill does and *when* to use it. Max 1024 chars. Description gets pre-loaded for ALL skills at startup — even skills not yet triggered.

**L2 — SKILL.md body**: Loaded only when skill is relevant. ~500 lines ideal; prune ruthlessly. Every paragraph must justify its token cost. Use L2 for: the core workflow, critical guardrails, output format specs, and essential context the model genuinely lacks.

**L3 — Bundled resources (`references/`, `scripts/`)**: Read as needed, unlimited capacity. Scripts execute without loading into context. Use L3 for: detailed reference docs, error transcripts, provider quirks, reproducible scripts, and anything that would bloat L2 without being universally needed.

**"Claude is already very smart" default**: Challenge every piece of information. Ask — Does Claude really need this? Can I assume it knows this? Does this paragraph justify its token cost? Verbosity ≠ helpfulness.

## Degrees of Freedom Framework

Match instruction specificity to task fragility and variability:

**High freedom** (open guidance, heuristic-based): Multiple valid approaches exist; context determines the best path. Example: "Review the code for bugs, readability issues, and adherence to project conventions."

**Medium freedom** (pseudocode/scripts with parameters): A preferred pattern exists but variation is acceptable. Example: `def generate_report(data, format="markdown", include_charts=True):` with parameter documentation.

**Low freedom** (exact scripts, no variation): Operations are fragile, sequence-dependent, or consistency-critical. Example: "Run exactly: `python scripts/migrate.py --verify --backup`. Do not modify."

Navigation analogy: narrow bridge with cliffs on both sides → low freedom (precise guardrails). Open field with no hazards → high freedom (trust the model).

## Description Field Design

The `description` in YAML frontmatter is the primary triggering mechanism. Rules:

- Max 1024 characters
- Include both *what* it does AND *when* to use it — specific contexts and trigger phrases
- Use "pushy" language to counter under-triggering: "Make sure to use this skill whenever the user mentions X, even if they don't explicitly ask for it."
- Include numbered use cases: `(1) ..., (2) ..., (3) ...`
- Do NOT include XML tags
- name field: lowercase, hyphens, max 64 chars, no reserved words ("anthropic", "claude")

**Trigger quality check**: Would a real user phrase their request this way? Include edge cases, casual phrasings, and cases where the user doesn't name the skill explicitly but clearly needs it. Avoid generic queries that Claude can handle without the skill.

## SKILL.md Structure

Required:
- YAML frontmatter with `name` + `description`
- Core workflow (the actual how-to)

Recommended:
- Trigger guidance (when this skill fires and when it doesn't)
- Output format specification
- Pitfalls / common mistakes
- Quick diagnostic (pass/fail checklist)
- `See references/<file>.md` pointers at point of need (not a trailing roster)

**Under 500 lines** is the target for L2. If approaching that limit, push detail into L3 references and add a clear pointer.

## Skill Naming

- Gerund form preferred (verb + -ing): `processing-pdfs`, `analyzing-logs`
- Acceptable: noun phrases or action-oriented names
- Avoid: vague names (`helper`, `utils`), reserved words, or names that only make sense for today's task
- Max 64 chars, lowercase only, hyphens for spaces

## Testing Across Models

Skill effectiveness depends on the underlying model. If the skill will be used across multiple models (Haiku/Sonnet/Opus), test with all of them — what works perfectly for Opus may need more detail for Haiku. Aim for instructions that work across the target model range.

## Key Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Explaining what the model already knows | Wastes context tokens, buries signal | "Claude is already very smart" — only add genuinely new context |
| Generic descriptions | Under-triggers | Use specific trigger phrases, "pushy" language, edge cases |
| Everything in L2 | Bloats context for every invocation | Push detail to L3 references, keep L2 lean |
| Rigid MUST/NEVER without reasoning | Over-constrains capable models | Explain the *why* — models with theory of mind respond better to reasoning than rules |
| No output format specified | Inconsistent results | Define exact output structure, file naming conventions, success criteria |
| Missing trigger boundary | Competes with other skills incorrectly | Clarify what this skill is NOT for, near-miss cases |
| **Behavior skill = rules only, no enforcement** | Skill preaches X (e.g. "立即动手") but provides no gate to detect/prevent violation. Agent loads it, reads it, then proceeds as if it didn't exist. Worst case: the agent *writing* the skill falls into the violation itself (meta-failure). | Every behavior skill must include: (a) **Pre-Action self-check** — concrete questions the agent asks itself *before* the next action, with "what to do if it fails"; (b) **Execution flow** — mechanical steps, not principles; (c) **Watchdog hook** — cron/file-scan that detects violations of the behavior the skill preaches. Rules without enforcement = documentation, not a skill. See `references/behavior-skills-enforcement.md` for the proactive-execution case study. |
| **Storing learned knowledge in `memory` tool** | Knowledge stored in MEMORY.md or fact_store gets blocked by threat patterns (API keys) and hits character limits (2200/6600). Next session doesn't benefit. | Learned procedures, rules, and techniques belong in **skills** (`skill_manage create/patch`), not `memory`. `memory` = current state (config, health, process status). `skill` = how to do X for this user. Failure 72 case: user said "固化起来" → instinct was `memory tool` → failed 4× → skill was the right vehicle all along. |

## Research References

For 2025-2026 industry developments (Anthropic Agent Skills, OTel+eBPF, Ponytail ecosystem), see:
→ `references/2025-2026-research.md`

For the principle that **behavior skills require enforcement mechanisms (Pre-Action + Execution Flow + Watchdog)** — not just rule lists — see:
→ `references/behavior-skills-enforcement.md` (Failure 64 case study from `proactive-execution` v2.0 → v2.1.0)
