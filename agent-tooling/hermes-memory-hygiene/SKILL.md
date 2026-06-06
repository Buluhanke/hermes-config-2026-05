---
name: hermes-memory-hygiene
description: Hermes memory management — what to remember, what to discard, how to organize persistent memory across sessions. Activated when updating memory, managing fact_store, or cleaning up persistent state.
triggers:
  - "update memory"
  - "save to memory"
  - "remember this"
  - "forget this"
  - "clean memory"
  - "记忆"
---

# Hermes Memory Hygiene

## Core Principle
**Memory = what makes the NEXT session smarter. Not a log of what happened.**

Three storage layers, different purposes:

| Layer | Tool | Purpose | Size |
|-------|------|---------|------|
| fact_store | `fact_store` | Durable facts, entity knowledge, verified learnings | ~80KB |
| memory.md | `write_file` to `~/.hermes/memories/memory.md` | System config, tool state, ongoing constraints | <5KB |
| user.md | `write_file` to `~/.hermes/memories/user.md` | User preferences, communication style, hard constraints | <3KB |
| state.db | session_search | Session history, past conversations (auto, don't touch) | 1.2GB |

## What to SAVE (durable facts)
- User preferences that **won't change** (沟通风格, 技术偏好, 硬约束)
- System configuration that **won't be re-discovered** (CDP port, Chrome PID, tool paths)
- Verified learnings / non-obvious techniques that **next session would benefit from**
- Entity resolution facts (supplier names, product codes, company identifiers)

## What to DELETE (memory hygiene)
- Task-specific progress ("已完成第3步") — use pending_tasks mechanism
- Session-specific artifacts (temp file paths, one-off command outputs)
- Business context that belongs to the USER not Hermes (suppliers, prices, companies)
  → **When user says "clear procurement memory" → clean ALL business facts from fact_store + memory.md + user.md**
- Concluded workflows that won't recur

## Memory Cleanse Protocol
When user requests memory cleanup (any mention of "删除记忆" / "clear memory" / "忘记"):

1. **Files**: `rm -rf ~/.hermes/supplier_memory/ ~/.hermes/market_memory/ ~/.hermes/tactics_memory/ ~/.hermes/learning_logs/`
2. **fact_store**: `fact_store(action='list')` → identify business-related fact_ids → `fact_store(action='remove', fact_id=X)`
3. **memory.md**: Rewrite, removing all business-specific content (keep system config only)
4. **user.md**: Rewrite, removing user identity/company/business details
5. **Verify**: `fact_store(action='list')` — should show no business content

## Real Person Mode Memory Rules
- **No business memory**: Hermes does not own supplier databases, price databases, or procurement case logs
- **System memory only**: Tool configurations, browser state, software paths, learned techniques
- **User owns the business data**: Hermes has no right to remember what the user hasn't explicitly asked it to remember
- If user says "跟采购和1688相关全部删除" → treat as complete business memory cleanse

## File Update Pattern
```python
# Correct: rewrite entire file, don't patch
write_file(content=new_complete_content, path="~/.hermes/memories/memory.md")

# Wrong: trying to patch with old_string/new_string on non-existent content
patch(old_string="old content", new_string="new content", path="~/.hermes/memories/memory.md")
# → fails if exact string not found
```

## FTS5 Search Limitation
- AND query requires ALL terms to match
- Use OR or synonyms to expand recall
- Important conclusions MUST be written to memory.md — don't rely on cross-session search

## User Preferences (embed in body, not just memory)

When the user expresses a **communication-style** or **workflow** preference
("stop doing X", "remember this style", "default to Y"), the lesson
belongs in the relevant skill's body — not just in `user.md`. The skill
that governs the task should carry the preference so the next session
starts already knowing it. `user.md` captures *who* the user is;
skills capture *how* to do a class of task for that user.

Concrete defaults the user has set (verified 2026-06-05, see
`user.md` v2.2/v2.3):

- **v2.2 — Authorization popups default to YES.** Any
  "Command Approval Required" / terminal destructive op / delete-cleanup
  prompt: confirm and execute, do NOT pause to ask. Exception: truly
  irreversible ops (`rm -rf ~`, format system disk, change prod config).
- **v2.3 — Real-person assistant tone.** Say "我换个思路试试" not
  "出错了"; say "我刚才跑了 X, 修了 Y" not "完成"; say "我觉得..."
  not absolute conclusions; occasional fillers ("嗯", "按理说", "说实话")
  OK; on failure, say what was tried + observed + what to try next.

## Pending Tasks for Continuity
- Store incomplete tasks in fact_store with key `pending_tasks`
- Gateway restart → auto-restore from fact_store
- Each task: `task_id`, `description`, `status`, `created_at`, `updated_at`
- Cron checks for tasks stuck >24h and resets them

## Automatic Memory Compression (`memory_transfer.py`)

`memories/MEMORY.md` has a soft cap of ~6,600 chars. When it grows large, use
`~/.hermes/scripts/memory_transfer.py` to compress it.

### The Pattern: Transfer, Don't Just Delete

```
MEMORY.md entry
    ├── core rule / user preference / hard lesson → KEEP in MEMORY.md
    ├── technical detail / bug pattern / one-off discovery → FACT_STORE (durable)
    └── temporary / session-specific → DISCARD
```

### Classification Rules

| Category | What to do | Examples |
|---|---|---|
| `keep` | Stay in `memories/MEMORY.md` (full content) | Core behavior rules, user preferences, verified techniques |
| `fact` | Write to `fact_store.db` (permanent record) | Bash bugs, script quirks, tool failure patterns, one-off discoveries |
| `remove` | Delete entirely | Session-specific progress, temp file paths, one-off command outputs |

### Running the Transfer

```bash
# Dry run first — always
python3 ~/.hermes/scripts/memory_transfer.py --dry-run

# If preview looks right, run for real
python3 ~/.hermes/scripts/memory_transfer.py
```

### Embedding in Cron (Weekly)

Add to `self_evolution.sh` weekly流程 or as a standalone cron:

```bash
# Weekly memory compression (Sunday 22:00)
0 22 * * 0 /usr/bin/python3 ~/.hermes/scripts/memory_transfer.py >> ~/.hermes/logs/memory_compress.log 2>&1
```

### Target Size

After compression: `memories/MEMORY.md` should be **< 5,000 chars**.
The script backs up before writing (`MEMORY.md.bak.{timestamp}`).

**Script**: `scripts/memory_transfer.py` — classification rules are defined at the top of the file; add new rules to the `RULES` list.