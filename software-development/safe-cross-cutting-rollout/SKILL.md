---
name: safe-cross-cutting-rollout
description: |
  Phased rollout of high-risk cross-cutting changes — rhythm gates, system prompt
  rewrites, ACL changes, notification policy, auth middleware. Run a 4-stage
  protocol: scope-cut → dry-run → observe → enforce. Each stage has explicit
  go/no-go criteria and an env-flag kill switch. Triggers: "phased rollout",
  "staged deployment", "feature flag", "dry-run first", "kill switch", "不要一
  上来就 enforce", "scope-cut", "minimum viable change", "包裹在 X 外面".
---

# Safe Cross-Cutting Rollout

## Why this skill exists

Cross-cutting changes (rhythm gate, persona injection, ACL middleware, auth wrapper)
are **the highest-blast-radius changes** you can make to a system. A bug in a
single function crashes one path; a bug in the wrapper around every send crashes
**every** send. Big-bang ship → user gets 23:00 stuck alert, real message lost,
trust destroyed.

The 4-stage protocol below is what worked in the 2026-06-04 session when
`gateway/platforms/telegram.py::send` was modified to inject a rhythm gate.
The user explicitly broke the work into 4 numbered steps and called out
"先把时间节律接到 Telegram 推送上，其他三步等这一步落地验证完再做" —
**the user wants staged delivery** for cross-cutting changes.

## The 4-stage protocol

### Stage 1: Scope-cut (smallest viable touch point)

**Goal:** identify the single chokepoint that all paths flow through, and modify
ONLY that chokepoint. Resist scope creep.

**How:**
1. Trace the actual runtime call path. `grep -rn "adapter\.send\|self\.adapter\.send" gateway/`
   for the telegram case. **Don't trust** obvious-looking unified entry points —
   `DeliveryRouter.deliver()` looked unified but was dead code in that session.
2. Pick the SINGLE function/method whose modification covers the entire surface
   area. For telegram it was `TelegramAdapter.send()`. For LLM calls it might
   be `model_tools.handle_function_call()`. For network it might be
   `_shared_http_client.get_shared_client()`.
3. Plan the smallest possible diff. Goal: <50 lines of production code, all
   confined to the chokepoint.

**Output:** a one-sentence statement of the chokepoint, e.g.
"Modify `TelegramAdapter.send()` to gate by `should_send_message(urgency)`."

**Go/no-go for Stage 2:** user confirms the scope is acceptable. In our session
the user picked option "A" (minimum-invasive) over "B/C" (wider scope).

### Stage 2: Build with dry-run by default (fail-loud, not fail-open)

**Goal:** ship code that **never silently breaks the existing path**, even
when the new logic is wrong/missing/broken.

**How (5-layer defensive pattern, see `hermes-internal-architecture-patterns` §7):**

1. **Env flag default ON for dry-run**: `os.getenv("MY_FEATURE_DRY_RUN", "1") == "1"`.
   New feature observes, never acts, until flag flipped.
2. **Outer `if _AVAILABLE` guard**: new code is in a conditional that is False
   when the new module is missing/broken. Default behavior unchanged.
3. **Import-time try/except with stub fallbacks**: never let the new code's
   import failure cascade into the existing path. See the `telegram.py` snippet.
4. **Runtime try/except around the new logic**: if the new code raises ANYTHING,
   log and fall through to the original behavior. "Falling through" not "raising".
5. **Input whitelist for any caller-controlled knob**: `urgency` must be in
   {"low","medium","high","critical_only"}; reject anything else to default.

**Output:** the modified chokepoint passes `python3 -m py_compile` AND a
unit test that exercises both dry-run and enforce modes (using `object.__new__()`
+ monkey-patch for adapter testing — see `hermes-internal-architecture-patterns`).

**Go/no-go for Stage 3:** static check + unit test green; user can see the diff
and confirms "yes, this is the right shape".

### Stage 3: Observe (dry-run period, default 1 week)

**Goal:** accumulate evidence that the new logic makes correct decisions, without
any user-facing change.

**How:**
1. Deploy with `MY_FEATURE_DRY_RUN=1` (default). The chokepoint logs every
   decision ("would queue", "would inject", "would block") but does NOT act.
2. Watch the log volume. In our session the rhythm gate produced
   `[rhythm DRY-RUN] would queue: urgency=medium zone=night ...` for every
   off-hours message — easy to grep, easy to verify against intent.
3. Set a calendar reminder / cron to flip to enforce after 1 week. Don't
   trust your own memory.
4. **Periodically check**: did any dry-run log look wrong? Did the gate
   block things that should have passed (or vice versa)? If yes, fix in
   Stage 2 code, restart the clock.

**Output:** a log sample showing correct decisions, the user's implicit OK to
flip, OR a bug found and fixed in Stage 2 code (then re-observe).

**Go/no-go for Stage 4:** at least 1 week of clean dry-run logs AND user
confirms "looks right, you can flip the flag".

### Stage 4: Enforce (flip the kill switch)

**Goal:** make the new logic actually do the thing.

**How:**
1. Set `MY_FEATURE_DRY_RUN=0` in `~/.hermes/.env` (or wherever the
   chokepoint reads env). One line change.
2. Restart the affected process (gateway, daemon, etc.). Verify with one
   test call that the new path actually fires (e.g. queue actually grows).
3. Keep the `import_time` and `runtime` try/excepts in place — they protect
   against future regressions. Just because we trust the feature now doesn't
   mean it can't break later.
4. If anything goes wrong post-enforce: set `MY_FEATURE_DRY_RUN=1` and
   restart. The kill switch is the rollback.

**Output:** feature is now live; kill switch documented in env file; user
informed.

## When the protocol breaks down

- **You can't find a single chokepoint.** The change genuinely needs to touch
  N places. Then either (a) accept larger blast radius and do N small dry-runs
  in parallel, or (b) refactor first to introduce a chokepoint, THEN apply
  the protocol.
- **The change has no observable "dry-run" output** (e.g. it's a pure
  computation with no side effect to log). Consider whether dry-run is even
  meaningful — maybe skip to enforce with a one-shot test trigger.
- **User says "ship it" and refuses Stage 3.** Comply, but keep the kill
  switch in place and document the decision in the changelog / memory.
  When the user pushes back on process, the kill switch is your safety net.

## When NOT to use this protocol

- **The change is local** (one function, no cross-cutting). Just TDD + ship.
- **The change has complete test coverage** (CI catches regressions). The
  protocol's value is in production observation; if tests are exhaustive
  enough, you're done after Stage 2.
- **The change is a pure refactor** (no runtime behavior change). Then there's
  nothing to dry-run; just verify with existing tests.
- **The change is reversible by feature flag in the data layer** (e.g. config
  in DB). The protocol still applies for first deploy, but rollback is faster
  via config flip rather than env flag.

## Anti-patterns to avoid

- ❌ **Big-bang ship with no dry-run period.** "I'll just turn it on and
  watch carefully" — this is what loses 23:00 messages.
- ❌ **Dry-run with no actionable output.** Logging "considered blocking"
  without saying what the decision was and why. Need: gate input, gate
  decision, gate context (zone/cap/whatever), in one structured log line.
- ❌ **Stage 2 code that fails-closed on import error.** `except ImportError:
  pass` (old pattern) means: if someone deletes the script dir, the
  gate silently vanishes and you're back to no gate. **Always** fail-loud
  in import errors: log warning + force-dry-run + stub.
- ❌ **Stage 4 without restarting the process.** Env flag is read at import
  time in some cases, not per-call. Verify the chokepoint re-reads env on
  every decision, or restart cleanly.
- ❌ **Skipping Stage 1 scope-cut because "while I'm in there..."** This
  is how cross-cutting changes become 500-line PRs. One chokepoint per
  change. Save the next 4 for the next protocol run.

## Cross-references

- `hermes-internal-architecture-patterns` § 7 — actual production code
  (5-layer defensive pattern + adapter test via `object.__new__()`)
- `hermes-internalization-stack` — the "what to inject" side (rhythm,
  relationship, persona, blind_spots modules)
- `notification-rhythm-pipeline` — full rhythm→queue→drain pipeline that
  the rhythm gate feeds into
- `proactive-execution` rule 18 — `if __name__ == "__main__":` guard
  discipline (unrelated, but a pitfall that can break Stage 2 testing)
