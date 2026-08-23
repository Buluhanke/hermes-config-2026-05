# Skills Depth Audit — 2026-07-16

## Trigger

User demanded: "所有技能要一个不落在最前面文件夹"，prompting a full depth audit.

## Findings

### `agent-human-level-computer-use/` — nested umbrella (depth 3-4)

**Source:** came from `engineering/` dir in `hermes-export.tar.gz`
**Structure:**
```
agent-human-level-computer-use/        (depth=1, umbrella container)
  SKILL.md                            (depth=2, skill itself)
  apple/                              (depth=2, sub-umbrella)
    apple-notes/SKILL.md              (depth=3 — WRONG)
    apple-reminders/SKILL.md          (depth=3 — WRONG)
    findmy/SKILL.md                   (depth=3 — WRONG)
    imessage/SKILL.md                 (depth=3 — WRONG)
  creative/                           (same)
    ascii-art/SKILL.md
    baoyu-infographic/SKILL.md
    ...
  autonomous-ai-agents/opencode/SKILL.md
  email/himalaya/SKILL.md
  github/codebase-inspection/SKILL.md
  ...
```

**Root cause:** sub-categories apple/, creative/, etc. already existed at top-level from the earlier flat installation. The umbrella in engineering/ was a stale copy with deeper nesting.

**Fix applied:**
1. `mv ~/.hermes/skills/agent-human-level-computer-use/SKILL.md ~/.hermes/skills/agent-human-level-computer-use/SKILL.md` — skill itself is now at depth=2 (no-op, already correct)
2. Removed all redundant sub-categories (apple/, creative/, email/, github/, etc.) — skills already at top-level
3. Deleted the now-empty umbrella directory

### `node-inspect-debugger/` — nested duplicate (depth 3)

**Structure:**
```
node-inspect-debugger/
  SKILL.md                           (depth=2, correct)
  node-inspect-debugger/             (extra layer)
    SKILL.md                         (depth=3, duplicate)
```

**Fix:** `rm -rf ~/.hermes/skills/node-inspect-debugger/node-inspect-debugger/`

## Verification Commands

```bash
# Must return 0 — any number > 0 means umbrella nesting still exists
find ~/.hermes/skills -mindepth 3 -name 'SKILL.md' | \
  grep -v '/.hub/' | grep -v '/.curator_backups/' | wc -l

# Should return 176 (active skill count)
find ~/.hermes/skills -maxdepth 1 -type d | while read d; do
  [ -f "${d}/SKILL.md" ] && basename "$d"
done | wc -l

# Hermes online index — should show 176
hermes skills list 2>&1 | grep -c '│'
```

## Lesson

**Umbrellas can hide inside exported packages.** When importing from a compressed skill library, the `engineering/` or similar category directories can contain full umbrella structures that pre-exist the flat installation. Always run the depth audit immediately after any bulk import, before reporting completion to the user.

## Backups

- Original backup: `~/.hermes/skills.bak.20260716_173142/` (49 MB)
- Deleted umbrella copies: `/tmp/skills_orphan_174252/` (504 KB)
