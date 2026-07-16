---
name: skill-curation
description: "Use when auditing, reviewing, or curating the Hermes skill library — evaluating orphan skills for recovery, checking active skills for staleness, or identifying gaps. Triggers: check skills, audit skills, review orphans, skill library health, 哪些skill可以恢复."
---

# Skill Curation

Systematically evaluate skills to decide: keep active, recover from archive, or prune.

## Orphan Audit Criteria

For each skill under review, assess ALL three dimensions:

### 1. Has substantive steps?
Read first 20 lines. Then check:
- **Has steps:** Frontmatter + body has numbered/runnable instructions, not just description
- **Pure placeholder:** body equals title, no actionable content (auto_crystallized fact dump)
- **Needs full read:** First 20 lines inconclusive (complex skill needs deeper inspection)

### 2. Duplicate of active skill?
Cross-reference against active skill list. If yes, tag as duplicate.

### 3. Unique value?
Ask: does this cover a trigger scenario, operation method, or knowledge that NO active skill covers?
- **Unique trigger:** Covers a genuinely distinct use case
- **Unique method:** Has runnable steps for something not documented elsewhere
- **Unique knowledge:** Domain expertise not in any active skill

## Categorization Labels

| Label | Meaning |
|-------|---------|
| 有价值可恢复 | Substantive steps + unique value + not duplicate |
| 纯占位符/过时 | Pure placeholder OR duplicate of active OR superseded version |
| 旧版本已存在活跃版 | Duplicate of active skill |

## Decision Rules

**Recover:** Substance + Unique value + Not duplicate
**Archive permanently:** Any of:
- Title equals body (auto_crystallized fact with no steps)
- Duplicate of active skill
- Superseded by newer active version
- Empty directory (no SKILL.md)
- Marketplace content not adapted for Hermes (sales copy, generic README)

## Batch Audit SOP

1. List all orphans: `ls .archive/*/`
2. List active: compare against skills_list output
3. Compute orphans = archive minus active
4. For each orphan, read SKILL.md first 20 lines
5. Apply criteria above
6. For inconclusive: read full file
7. Report format:
   - 有价值可恢复: 技能名 — 理由
   - 纯占位符/过时: 技能名 — 理由
   - 旧版本已存在活跃版: 技能名
8. Count totals

## Useful One-Liners

```bash
# Count orphan skill directories
ls -1d ~/.hermes/skills/.archive/*/ | wc -l

# List orphans vs active (set algebra)
comm -23 <(ls -1d ~/.hermes/skills/.archive/*/ | xargs -I{} basename {} | sort) \
         <(echo -e "skill1\nskill2\n..." | sort) > /tmp/orphans.txt

# Empty SKILL.md check
for d in ~/.hermes/skills/.archive/*/; do
  [ ! -s "$d/SKILL.md" ] && echo "EMPTY: $d"
done

# Auto-crystallized placeholder check (body == title)
for f in ~/.hermes/skills/.archive/*/SKILL.md; do
  lines=$(wc -l < "$f")
  [ "$lines" -le 15 ] && echo "SHORT/PLACEHOLDER: $f"
done
```

## Post-Audit Actions

### Recovery Commands (run via terminal in ~/.hermes/skills)

```bash
# Restore 11 recoverable skills
for skill in \
  "1password-cli-agents" \
  "3-statement-model" \
  "afrexai-observability-engine" \
  "agent-rdp" \
  "agentmail" \
  "browser-use" \
  "writing-plans" \
  "writing-skills" \
  "ponytail" \
  "macos-automation" \
  "brainstorming"; do
  [ -d ".archive/$skill" ] && mv ".archive/$skill" "$skill" && echo "Restored: $skill"
done

# Delete empty directories (orphans with no SKILL.md)
for dir in \
  "_community" \
  "agent-tooling" \
  "productivity" \
  "note-taking" \
  "smart-home" \
  "wondelai-skills" \
  "web" \
  "core"; do
  [ -d ".archive/$dir" ] && rm -rf ".archive/$dir" && echo "Deleted: $dir"
done
```

## Actual Post-Audit State (2026-07-16)
- **Active skills: 72** (all depth=1, all with SKILL.md)
- **Archive: ~116** (placeholders + superseded versions)
- **0 missing SKILL.md** in active library

## Revised Batch Restore Pattern (verified working)
```bash
# Some archived skills buried 3 levels deep — must use multi-level find
for skill in secrets-management memory-cn siyuan perception-decision-engine; do
  path=$(find ~/.hermes/skills/.archive -maxdepth 4 -type d -name "$skill" 2>/dev/null | head -1)
  [ -n "$path" ] && cp -r "$path" ~/.hermes/skills/ && echo "Restored: $skill from $path"
done

# Verify all active skills have SKILL.md
for d in ~/.hermes/skills/*/; do
  name=$(basename "$d"); [[ "$name" == .* ]] && continue
  [[ -f "$d/SKILL.md" ]] || echo "MISSING: $name"
done
```

## Key Lesson: Size ≠ Substance
| Size | Likelihood | Action |
|------|-----------|--------|
| <1KB | ~95% placeholder | Skip unless name is obviously critical |
| 1-3KB | ~50/50 | Read 20 lines |
| 3-10KB | ~70% substantive | Read 20 lines |
| >10KB | ~90% substantive | Check for raw dumps vs steps |

**Counter-examples:** `prism-3way` (2.8KB) real framework; `perception-decision-engine` (12KB) richest content but not biggest file.

## Decision Rules (Revised)
1. **Always read first 20 lines** — do not trust size as proxy
2. **Distinguish auto_crystallized fact dumps from real skills** — fact dumps have body=title, no runnable steps
3. **Recover if: substance + unique trigger/method + not duplicate of active**
4. **Move recovered skill to depth=1** — `~/.hermes/skills/<name>/SKILL.md`
5. **Archive permanently:** pure placeholder OR duplicate OR superseded OR empty directory

| Skill | Unique Value |
|-------|-------------|
| 1password-cli-agents | 1Password CLI secrets management — no active skill covers this |
| 3-statement-model | Excel financial modeling (IS/BS/CF) — not covered by minimax-xlsx |
| afrexai-observability-engine | Full SRE stack (logging/metrics/tracing/SLO) — richer than hermes-observability |
| agent-rdp | Windows RDP remote control — unique platform target |
| agentmail | Agent-owned email inbox — unique communication channel |
| browser-use | CLI browser automation — complements computer-use |
| writing-plans | TDD-style implementation planning — not covered by plan |
| writing-skills | TDD skill-authoring methodology — unique meta-skill |
| ponytail | YAGNI/stdlib/native coding philosophy — not in any active skill |
| macos-automation | AppleScript/JXA/Shortcuts reference — not in any active skill |
| brainstorming | Design-first workflow with HARD-GATE — not in any active skill |

### Post-Recovery State (OUTDATED — see updated audit below)
- Active skills: 31 → 42
- Archive: 137 → 115 (11 restored + 12 deleted empty dirs)

## 2026-07-16 Full Audit Results

**Actual outcome: 72 active skills, 116 archived, 0 missing SKILL.md.**

### Actual Recovery (26 skills restored)
**From large-content orphans (>5KB):**
`secrets-management` `memory-cn` `siyuan` `perception-decision-engine` `memray-memory-profiler` `subagent-driven-development` `skill-creator` `writing-skills` `browser-use` `3-statement-model` `context-compression` `dcf-model` `agent-rdp`

**From wondelai-skills (8):**
`clean-code` `refactoring-patterns` `software-design-philosophy` `pragmatic-programmer` `working-with-legacy-code` `system-design` `clean-architecture` `team-topologies`

**From research/skills (2):**
`qmd` `scrapling`

**From other orphans (3):**
`kepano-defuddle→defuddle` `courier-notification-skills` `open-source-skill-harvesting`

### Key Lesson: Size ≠ Substance
| Size | Conclusion |
|------|-----------|
| <1KB | Almost always placeholder (auto_crystallized fact dump) |
| 1-3KB | Mixed — must read first 20 lines |
| 3-10KB | Often substantive, but must verify (some thin descriptions) |
| >10KB | Usually substantive, but check for raw dumps vs real steps |

**Counter-examples found:**
- `afrexai-observability-engine` (46KB) — real content
- `context-compression` (12KB) — real content  
- `skill-creator` (33KB) — real content
- `avoid-ai-writing` (69KB, archived version) — real content
- Many <3KB orphans ARE placeholders despite being substantive-sounding names

### Revised Decision Rules
1. **Always read first 20 lines** — do not trust size as proxy
2. **Distinguish auto_crystallized fact dumps from real skills** — fact dumps have body=title, no runnable steps
3. **Recover if: substance + unique trigger/method + not duplicate of active**
4. **Archive permanently: pure placeholder OR duplicate OR superseded version OR empty directory**
5. **Move recovered skill to depth=1** — `~/.hermes/skills/<name>/SKILL.md`

### Batch Restore Pattern (verified working)
```bash
# Multi-level find needed — some skills buried 3 levels deep in archive
find ~/.hermes/skills/.archive -maxdepth 3 -type d -name "$SKILL_NAME" -exec cp -r {} ~/.hermes/skills/ \;
```
