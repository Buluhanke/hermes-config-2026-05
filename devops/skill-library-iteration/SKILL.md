---
name: skill-library-iteration
description: Iterate skills; research 2026 SOTA, patch SKILL.md.
version: 1
author: hermes
license: MIT
metadata:
  hermes:
    tags: [skill-maintenance, research, sota, self-improvement]
    related_skills: [hermes-skills-management, self-maintenance, writing-skills]
---

# Skill Library Iteration

Keep the installed skill library current by decomposing each skill into its workflow
steps, researching whether a better tool/approach exists on the web, and recording the
finding inside the skill itself. This is a recurring maintenance class, not a one-off task.

## When to use
- User asks to iterate / improve / audit all installed skills.
- User asks to "find better solutions online" for skills, or to "keep skills up to date".
- You notice a skill's approach is older than the current SOTA and want to record the gap.

## Workflow
1. **Inventory + filter.** List `~/.hermes/skills/*/SKILL.md`. Most installs carry a large
   amount of auto-generated junk: filter it out first with
   `grep -rl "Auto-crystallized from fact_store" --include=SKILL.md .` — these are
   low-signal crystallized facts, NOT real skills. Iterate only the REAL ones (~131 of 429
   in one audit). Do not waste research budget on the garbage.
2. **Group by domain.** Bucket real skills into ~9 domains (web scraping/research, 1688/sourcing,
   coding-agent workflow, agent memory, office/OCR, generative media, local-infra/ML,
   research/knowledge, Hermes-ops). One targeted search per domain beats per-skill brute force.
3. **Cross-domain SOTA research.** For each domain, run 2-3 precise `web_search` queries of the
   form "<domain> best tool 2026 alternative to <current libs>". Prefer open-source, directly
   substitutable tools. Record condensed findings.
4. **Patch SKILL.md.** Append a `## 2026 更优方案` (or "## 2026 better approach") section to the
   relevant skills. APPEND — do not replace the existing working workflow; keep it as fallback.
   For user-owned / pinned skills you cannot edit via skill_manage, either write the file directly
   or recommend `hermes curator adopt <name>`; do NOT try to patch protected skills.
5. **Commit.** `cd ~/.hermes/skills && git add -A && git commit -q -m "iter: ..."` so the
   research is not lost (the daily backup only commits, does not push).

## Pitfalls (learned the hard way)
- **delegate_task subagents 402.** Spawning subagents via `delegate_task` makes them default to
  `anthropic/claude-sonnet-4`. When OpenRouter credits are exhausted you get `HTTP 402 ... can
  only afford 50`. The whole fan-out dies with zero output. **Workaround:** do the web research
  yourself inside `execute_code` using `from hermes_tools import web_search`. That path rides the
  free model channel (e.g. tencent/hy3:free) and does NOT consume OpenRouter LLM credits. Same
  `web_search` tool, no billing wall.
- **Mechanical per-skill search is noisy.** Searching "<skillname> better alternative" returns
  unrelated hits (e.g. audiocraft → doc2chunk). Search by DOMAIN + the specific libraries the
  skill depends on, extracted from its SKILL.md, instead.
- **Never present dead ends as best practice.** If a search/approach failed, record only a
  method you are independently confident works — never dress a failed attempt as validated guidance.
- **Don't delete auto-crystallized junk without asking.** The user may want it. Flag it; ask
  before bulk-deleting.

## Support files
- `scripts/research_domains.py` — runs the 9-domain SOTA web research, writes JSON to /tmp/research_domains/.
- `scripts/apply_upgrades.py` — appends the "2026 better approach" section to a hardcoded map of
  skill→upgrade-text (edit the UPGRADES dict to extend).
- `references/sota-2026-findings.md` — condensed cross-domain SOTA findings from the 2026-08 audit.

## Verification
After patching, confirm with `tail -5 <skill>/SKILL.md` and a `git log --oneline -1` in the
skills dir. Count patched vs skipped so the user sees coverage.
