# Skill on Disk But Broken Invocation — Diagnosis Guide

## The Problem
Skill files exist on disk but can't be invoked — `skill_view` loads fine, CLI doesn't work, or cron job silently fails.

## Two Distinct Failure Modes (2026-06-06 实战)

### Mode A: CLI Works, Path Mismatch
**Symptom**: `skill_view` loads SKILL.md, but CLI invocation fails with "can't open file" or wrong path.
**Root cause**: The skill's entry point script is in a different location than expected.

**Case: last30days**
- Main script `last30days.py` was in skill root, NOT in `scripts/`
- Cron job / skill loader expected it at a different path
- Running from wrong working directory → `/private/tmp/last30days-skill-repo/...` (stale symlink)
- Also requires API keys (SCRAPECREATORS_API_KEY + LLM key) — anonymous access doesn't work

### Mode B: Cron Job Missing
**Symptom**: Skill files exist but no cron job references them.
**Root cause**: Backup/migration only saved partial `jobs.json`. Anysearch + last30days scheduled searches were dropped.
**Verification**: `cronjob(action='list')` — if not in list, cron is dead even if skill is alive.

## Diagnostic Procedure

```bash
# Step 1: Skill files exist?
ls ~/.hermes/skills/<skill-name>/SKILL.md
ls ~/.hermes/skills/<skill-name>/scripts/

# Step 2: CLI actually works?
cd ~/.hermes/skills/<skill-name> && python3 scripts/<script> --help  # or whatever runtime.conf says

# Step 3: runtime.conf present and correct?
cat ~/.hermes/skills/<skill-name>/runtime.conf

# Step 4: Required env vars present?
env | grep -i <KEY_NAME>
# Or check skill's SKILL.md for required credentials

# Step 5: Cron job loaded?
cronjob(action='list')
# If not listed, skill can't run on schedule
```

## Fast Fix by Mode

### If Mode A (path/entry mismatch):
1. Check what `runtime.conf` says vs actual file locations
2. Fix `runtime.conf` to point to correct CLI path
3. Test CLI directly before re-creating cron

### If Mode B (cron missing):
1. Read SKILL.md's "Trigger" section for what prompt to use
2. Re-create cron with `cronjob(action='create')`
3. Attach the skill via `skills: ["<skill-name>"]` parameter

## Prevention
- After migration/backup, **always verify**: `cronjob(list)` + CLI smoke test
- Any skill with external API dependencies → note required env vars in MEMORY.md
- Cron jobs that depend on skills → verify both skill CLI AND cron listing
