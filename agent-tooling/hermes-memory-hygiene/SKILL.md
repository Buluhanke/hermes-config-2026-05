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

## Pending Tasks for Continuity
- Store incomplete tasks in fact_store with key `pending_tasks`
- Gateway restart → auto-restore from fact_store
- Each task: `task_id`, `description`, `status`, `created_at`, `updated_at`
- Cron checks for tasks stuck >24h and resets them