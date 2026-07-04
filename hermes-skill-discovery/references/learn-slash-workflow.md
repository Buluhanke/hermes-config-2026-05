# `/learn` Slash Command — Full Workflow

> **Source:** https://hermes-agent.nousresearch.com/docs/user-guide/features/skills#learning-a-skill-from-sources-learn (verified 2026-07-02)
> **Status:** built-in Hermes feature, no install required, no separate CLI subcommand

## What it does

`/learn` is a slash command that turns existing knowledge or reference material into a reusable skill **without hand-writing `SKILL.md`**. It follows the house authoring standard:

- `description` ≤ 60 characters
- Standard section order (When to Use / Procedure / Pitfalls / etc.)
- Hermes-tool framing (refers to `browser_navigate`, `read_file`, `terminal`, not invented commands)
- No invented commands or APIs

## Three input forms

| Input | Syntax | When to use |
|---|---|---|
| Local directory | `/learn ~/projects/acme-sdk, focus on auth + pagination` | You have an SDK / codebase / doc dir on disk you want to crystallize into a skill |
| Online doc | `/learn https://docs.example.com/api/quickstart` | External API doc, blog post, or reference page you want a skill for |
| Conversation / notes | `/learn how I just deployed the staging server` / `/learn filing an expense: open the portal, New > Expense, attach the receipt, submit` | A workflow you just walked through, or pasted/described notes |

Also accepts plain text descriptions of procedures.

## Mechanism (what happens under the hood)

1. `/learn` builds a **standards-guided prompt** that tells the agent: "extract the reusable pattern from this input, write a SKILL.md that follows the house standard, save it via `skill_manage`."
2. The agent runs as a **normal turn** — no separate model-tool footprint, no special API path.
3. The agent calls `skill_manage(action='create', ...)` to save the result.
4. **If `skills.write_approval` is enabled**, the write is gated by user approval. The skill won't appear until approved.

This means: `/learn` is **just a prompt shortcut**. Anything the agent could write as a skill from scratch, it can write via `/learn`. The value is in the prompt structure forcing standards-compliance.

## Where it works

- CLI: `/learn <input>`
- Any messaging platform (Telegram, Discord, Slack, WeChat, etc.) — same syntax
- TUI: same
- Dashboard: Skills page → "Learn a skill" button → directory/URL/text fields

No CLI subcommand exists (`hermes learn` does NOT work — `/learn` is slash-only).

## Verification (after every `/learn`)

```bash
hermes skills list | grep <skill-name>
ls -d ~/.hermes/skills/<skill-name>/
head -20 ~/.hermes/skills/<skill-name>/SKILL.md   # spot-check description, sections
```

If the skill doesn't appear:
- `skills.write_approval` may have silently blocked the write → check approval queue / disable gate temporarily
- The agent's output may have been conversational (described the skill) rather than calling `skill_manage` → ask it to "save that as a skill"
- The prompt may have been too vague → be more specific about what workflow to capture

## Common failures (verified 2026-07-02 patterns)

1. **Silent no-op when `skills.write_approval` blocks the write** — agent describes the skill in chat but no file is created. Symptom: the assistant reply reads like a SKILL.md but `ls ~/.hermes/skills/` shows nothing new. Fix: approve the write in Dashboard or temporarily `hermes skills opt-out` (don't actually do this — find the approval queue instead).
2. **Description too long** — `/learn` enforces the 60-char description limit. If your input is too broad, the generated skill will be rejected by the spec validator. Fix: be specific in the input (e.g. "focus on the retry logic, not the whole SDK").
3. **Vague input → vague skill** — `/learn "general python tips"` produces a skill that just says "follow Python best practices". Fix: include the exact workflow, the tools used, the failure modes. Garbage in → garbage out, same as hand-writing.
4. **Skill name collision** — if a skill with the generated name already exists, `skill_manage` may overwrite it or refuse. Check `hermes skills list` first.
5. **Web-extracted content is JS-SPA** — some URLs (e.g. SPA doc sites) return empty content via `web_extract`. Pick a static doc URL or paste the content directly.

## Cron idle learning use case

For cron prompts like "find one useful tip" or "learn something new today":

| Old pattern (wasteful) | New pattern (with `/learn`) |
|---|---|
| 1. `mcp_searxng_web_search` × 6 (empty) | 1. `/learn https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban` |
| 2. `web_extract` against guess URLs | 2. agent captures workflow into a skill in one turn |
| 3. `hermes skills search <kw>` | 3. verify `hermes skills list \| grep kanban-workflow` |
| 4. inspect / install / scaffold | |
| 5. patch MEMORY.md with summary | |
| **~13 tool calls** | **1 turn** |

The "useful tip" cron prompt should default to: **does the official docs have a built-in for this? If yes → `/learn` to capture it as a skill; if no → community sources.**

## Recipe: cron idle learning, single-turn version

```bash
# Inside a chat session (cron agent, CLI, etc.):
/learn https://hermes-agent.nousresearch.com/docs/user-guide/features/<feature-name>

# Verify
hermes skills list | grep <feature-name>
```

If the resulting skill is too generic, refine by running `/learn` again with more context, or hand-edit the resulting `SKILL.md` to add Pitfalls / Verification steps.

## Verified example (2026-07-02 15:00 cron)

Topic: "find one useful tip for Hermes". Result via 13 tool calls:
- Discovered `/learn` (auto-skill-from-knowledge) and `execute_code` (PTC) as built-in features
- Wrote finding to MEMORY.md with the doc URLs
- Skipped installing any community skill (no install needed — they're built-in)

**Topic re-captured via `/learn` in a hypothetical single turn**:
```
/learn the /learn slash command workflow: input forms, prompt internals, write-approval gate, common failures, verification step. Source: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills (the "Learning a Skill from Sources" section).
```

Would produce `~/.hermes/skills/learn-slash-workflow/SKILL.md` containing the same content as this reference doc.
