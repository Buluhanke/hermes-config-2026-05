---
name: systematic-debugging
description: "4-phase root cause debugging: understand bugs before fixing."
version: 1.2.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation]
    related_skills: [test-driven-development, writing-plans, subagent-driven-development]
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Someone wants it fixed NOW (systematic is faster than thrashing)

## The Four Phases

You MUST complete each phase before proceeding to the next.

---

## Phase 0: Binary Search Localization

**Before diving deep, narrow the problem space with binary search.**

### When to Use

- Error occurs in a large codebase or complex pipeline
- Problem is reproducible but location is unknown
- Multiple possible failure points in a chain (e.g., build pipeline, service mesh)
- Log/output is too large to scan manually

### Techniques

#### 1. Codebase Binary Search

```bash
# Halve the codebase — comment out or temporarily revert half the changes
git bisect start
git bisect bad HEAD
git bisect good <last-known-good-commit>
# Git automatically tests the midpoint — narrow until root commit found
```

#### 2. Input/Environment Binary Search

- Take the failing input, split it in half
- Does it still fail with half the input? → Problem is in that half
- Narrow until you isolate the exact triggering condition

#### 3. Pipeline Binary Search

For chains like `build → test → deploy`:
```
Isolate Stage 1?     → Run Stage 1 alone, mock others
Isolate Stage 2?     → Run Stage 2 with known-good Stage 1 output
...
```
Each stage being independently runnable is the key. If a stage is opaque, inject diagnostic output at its boundaries.

#### 4. Log/Binary Search on Output

For verbose or binary output:
```bash
# Find the exact line/byte range where behavior changes
head -n N file.log | tail -n M   # inspect middle section
sed -n '50p,100p' file.log        # inspect rows 50-100
dd if=binary bs=1 skip=500 count=100 2>/dev/null | hexdump -C
```

#### 5. Divide and Recombine

1. Comment out half the code → still fails? → root cause in the other half
2. Comment out quarter → still fails? → root cause in the remaining three quarters
3. Repeat until isolated

### Binary Search vs. Full Trace

| Scenario | Approach |
|----------|----------|
| Narrow range, known component | Trace data flow (Phase 1) |
| Wide codebase, unknown location | Binary search first (Phase 0) |
| Complex pipeline | Binary search on stages, then trace |

**Phase 0 is a preamble to Phase 1 — use it to narrow before you deep-dive.**

---

## Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

### 1. Read Error Messages Carefully

- Don't skip past errors or warnings
- They often contain the exact solution
- Read stack traces completely
- Note line numbers, file paths, error codes

**Action:** Use `read_file` on the relevant source files. Use `search_files` to find the error string in the codebase.

### 2. Reproduce Consistently

- Can you trigger it reliably?
- What are the exact steps?
- Does it happen every time?
- If not reproducible → gather more data, don't guess

**Action:** Use the `terminal` tool to run the failing test or trigger the bug:

```bash
# Run specific failing test
pytest tests/test_module.py::test_name -v

# Run with verbose output
pytest tests/test_module.py -v --tb=long
```

### 3. Check Recent Changes

- What changed that could cause this?
- Git diff, recent commits
- New dependencies, config changes

**Action:**

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes
git diff

# Changes in specific file
git log -p --follow src/problematic_file.py | head -100
```

### 4. Gather Evidence in Multi-Component Systems

**WHEN system has multiple components (API → service → database, CI → build → deploy):**

**BEFORE proposing fixes, add diagnostic instrumentation:**

For EACH component boundary:
- Log what data enters the component
- Log what data exits the component
- Verify environment/config propagation
- Check state at each layer

Run once to gather evidence showing WHERE it breaks.
THEN analyze evidence to identify the failing component.
THEN investigate that specific component.

### 5. Trace Data Flow

**WHEN error is deep in the call stack:**

- Where does the bad value originate?
- What called this function with the bad value?
- Keep tracing upstream until you find the source
- Fix at the source, not at the symptom

**Action:** Use `search_files` to trace references:

```python
# Find where the function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where the variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")
```

### Phase 1 Completion Checklist

- [ ] Error messages fully read and understood
- [ ] Issue reproduced consistently
- [ ] Recent changes identified and reviewed
- [ ] Evidence gathered (logs, state, data flow)
- [ ] Problem isolated to specific component/code
- [ ] Root cause hypothesis formed

**STOP:** Do not proceed to Phase 2 until you understand WHY it's happening.

---

## Log Mining Techniques

### Reading Logs Strategically

**Never scan logs top-to-bottom blindly.** Know what you're looking for:

1. **Locate the error entry first** — search for `ERROR`, `FATAL`, `Exception`, `Traceback`
2. **Extract the stack trace** — the deepest frame is usually the root cause
3. **Read the causal chain** — lines above the error explain what led to it
4. **Identify the process/thread ID** — isolate logs belonging to the failing unit

```bash
# Find error lines with context (3 lines before/after)
grep -B 3 -A 3 "ERROR" app.log

# Find entries by timestamp range
sed -n '/2026-05-17 14:30:00/,/2026-05-17 14:35:00/p' app.log

# Extract stack traces
grep -A 20 "Traceback" app.log | head -60

# Filter by process ID (useful for multi-process apps)
grep "\[PID:12345\]" app.log
```

### Log Level Filtering

| Level | Meaning | Action |
|-------|---------|--------|
| `FATAL` / `CRITICAL` | System unusable | Immediate attention |
| `ERROR` | Operation failed | Investigate root cause |
| `WARN` | Unexpected but recoverable | Review impact |
| `INFO` | Normal operations | Context only |
| `DEBUG` / `TRACE` | Detailed flow | Deep investigation |

```bash
# Show only ERROR and FATAL
grep -E "ERROR|FATAL" app.log

# Remove noise — hide DEBUG/TRACE/INFO
grep -vE "DEBUG|TRACE|INFO" app.log | less
```

### Structured Log Extraction

For JSON logs (common in containerized apps):
```bash
# Extract error messages from JSON logs
cat app.json.log | jq 'select(.level=="ERROR") | .message'

# Extract field across all entries
cat app.json.log | jq '.level, .timestamp, .msg' | paste - - -

# Find entries with specific correlation ID
cat app.json.log | jq 'select(.correlation_id=="abc-123")'
```

### Time-Based Correlation

1. Find the timestamp of the error
2. Look backward 30-60 seconds for earlier anomalies (warnings, retries)
3. Look forward to see cleanup behavior or cascading failures

```bash
# Find timestamps around an error
awk '/ERROR/ {found=1; print} found && /^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}/ && !/ERROR/ {if (++cnt > 10) exit}' app.log
```

### Log Deduplication

Repeated identical errors → find unique root cause, not every occurrence:
```bash
# Show unique error messages with counts
grep "ERROR" app.log | cut -d'|' -f4 | sort | uniq -c | sort -rn | head -20
```

### When Logs Are Missing

- **No logs at all** → Check if logging is actually enabled (config, env vars)
- **Logs truncated** → Log rotation config (`logrotate`), disk full
- **Old logs only** → Process may be writing to a different file/path
- **No timestamps** → Add timestamps if missing; clock skew in distributed systems

### Log Enrichment

If logs are insufficient, inject temporary diagnostic logging:

```python
import logging
logging.debug(f"Variable state: x={x}, y={y}, z={z}")
# Or use structlog for structured output
```

Then re-run with `DEBUG` level enabled.

---

## Phase 2: Pattern Analysis

**Find the pattern before fixing:**

### 1. Find Working Examples

- Locate similar working code in the same codebase
- What works that's similar to what's broken?

**Action:** Use `search_files` to find comparable patterns:

```python
search_files("similar_pattern", path="src/", file_glob="*.py")
```

### 2. Compare Against References

- If implementing a pattern, read the reference implementation COMPLETELY
- Don't skim — read every line
- Understand the pattern fully before applying

### 3. Identify Differences

- What's different between working and broken?
- List every difference, however small
- Don't assume "that can't matter"

### 4. Understand Dependencies

- What other components does this need?
- What settings, config, environment?
- What assumptions does it make?

---

## Phase 3: Hypothesis and Testing

**Scientific method:**

### 1. Form a Single Hypothesis

- State clearly: "I think X is the root cause because Y"
- Write it down
- Be specific, not vague

### 2. Test Minimally

- Make the SMALLEST possible change to test the hypothesis
- One variable at a time
- Don't fix multiple things at once

### 3. Verify Before Continuing

- Did it work? → Phase 4
- Didn't work? → Form NEW hypothesis
- DON'T add more fixes on top

### 4. When You Don't Know

- Say "I don't understand X"
- Don't pretend to know
- Ask the user for help
- Research more

---

## Phase 4: Implementation

**Fix the root cause, not the symptom:**

### 1. Create Failing Test Case

- Simplest possible reproduction
- Automated test if possible
- MUST have before fixing
- Use the `test-driven-development` skill

### 2. Implement Single Fix

- Address the root cause identified
- ONE change at a time
- No "while I'm here" improvements
- No bundled refactoring

### 3. Verify Fix

```bash
# Run the specific regression test
pytest tests/test_module.py::test_regression -v

# Run full suite — no regressions
pytest tests/ -q
```

### 4. If Fix Doesn't Work — The Rule of Three

- **STOP.**
- Count: How many fixes have you tried?
- If < 3: Return to Phase 1, re-analyze with new information
- **If ≥ 3: STOP and question the architecture (step 5 below)**
- DON'T attempt Fix #4 without architectural discussion

### 5. If 3+ Fixes Failed: Question Architecture

**Pattern indicating an architectural problem:**
- Each fix reveals new shared state/coupling in a different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals:**
- Is this pattern fundamentally sound?
- Are we "sticking with it through sheer inertia"?
- Should we refactor the architecture vs. continue fixing symptoms?

**Discuss with the user before attempting more fixes.**

This is NOT a failed hypothesis — this is a wrong architecture.

---

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals a new problem in a different place**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (Phase 4 step 5).

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern, don't fix again. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
| **4. Implementation** | Create regression test, fix root cause, verify | Bug resolved, all tests pass |

## Hermes Agent Integration

### Multi-Machine Setups

When Hermes runs on multiple machines (e.g., Mac Pro + Mac mini), the **error path tells you which machine's gateway is failing**. See `references/multi-machine-hermes-debugging.md` for the full diagnostic sequence, including how to restart a remote gateway when SSH is broken.

**Session accumulation in TUI Gateway:** Dashboard slow + many zombie slash_worker processes → see `references/tui-gateway-slash-worker-leak.md` (under `hermes-agent` skill). Root cause: `_sessions` dict in `tui_gateway/server.py` has no max size/eviction, and `atexit` only fires on clean exit. Example of Phase 1 multi-component evidence gathering (process inventory + log analysis).

### Investigation Tools

Use these Hermes tools during Phase 1:

- **`search_files`** — Find error strings, trace function calls, locate patterns
- **`read_file`** — Read source code with line numbers for precise analysis
- **`terminal`** — Run tests, check git history, reproduce bugs
- **`web_search`/`web_extract`** — Research error messages, library docs

### With delegate_task

For complex multi-component debugging, dispatch investigation subagents:

```python
delegate_task(
    goal="Investigate why [specific test/behavior] fails",
    context="""
    Follow systematic-debugging skill:
    1. Read the error message carefully
    2. Reproduce the issue
    3. Trace the data flow to find root cause
    4. Report findings — do NOT fix yet

    Error: [paste full error]
    File: [path to failing code]
    Test command: [exact command]
    """,
    toolsets=['terminal', 'file']
)
```

### With test-driven-development

When fixing bugs:
1. Write a test that reproduces the bug (RED)
2. Debug systematically to find root cause
3. Fix the root cause (GREEN)
4. The test proves the fix and prevents regression

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

**No shortcuts. No guessing. Systematic always wins.**

---

## Tool Disconnection Troubleshooting

### Symptoms

- Tool call returns error like "Connection refused", "Connection reset", "EOF"
- Tool hangs indefinitely with no response
- Tool returns partial result then times out
- Error: "MCP server crashed" or "stderr: ..."

### Diagnostic Sequence

#### 1. Identify Which Tool Is Affected

- One specific tool fails → problem with that tool
- ALL tools from a server fail → problem with the server
- Tools fail intermittently → resource contention or timeout issue

#### 2. Check Tool Server Status

```bash
# List running MCP servers (if hermes command available)
hermes tools list

# Check server health/ping
hermes tools ping <server-name>

# View server logs (if accessible)
cat ~/.hermes/logs/*.log
```

#### 3. Network/Connection Checks (for HTTP-based tools)

```bash
# Can we reach the service?
curl -v http://localhost:PORT/health

# Is something listening?
lsof -i :PORT

# Firewall or permission issue?
sudo lsof -i :PORT -P
```

#### 4. Process-Level Diagnosis

```bash
# Is the process running?
ps aux | grep <process-name>

# Has it crashed? Check exit code
# 0 = clean exit, 1-255 = error, -9 = SIGKILL (OOM killer or manual)

# Memory exhaustion?
top -pid <PID>
dmesg | grep -i "kill" | tail -5  # OOM killer evidence
```

#### 5. Restart the Tool/Server

```bash
# Restart the specific tool's server
kill -9 <PID> && <start-command> &

# Or restart the entire Hermes gateway
hermes restart
```

#### 6. Configuration Check

```bash
# Verify tool config in config.yaml
cat ~/.hermes/config.yaml | grep -A 10 "<tool-name>"

# Check env vars the tool depends on
env | grep -E "TOOL_|MCP_|API_"
```

### Common Root Causes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "Connection refused" | Service not running | Restart service |
| "EOF" after initial success | Server crashed (OOM) | Increase memory, check logs |
| Hangs indefinitely | Deadlock or infinite loop | Send SIGINT, attach debugger |
| Intermittent failures | Resource contention | Queue requests, add backpressure |
| "Permission denied" | Wrong user/group | `chmod`/`chown` or check sandbox |

### Recovery Verification

After restarting:
1. Run a simple tool call to confirm it works
2. Re-run the operation that failed
3. Check server logs for recurring errors

---

## Memory Store Corruption Repair

### Symptoms

- Agent loses context mid-session
- "Memory read failed" or "Corrupt index" errors
- Persistent data missing or garbled
- `skill_view` returns stale or wrong content
- Historical context reset unexpectedly

### Diagnostic Steps

#### 1. Identify Which Memory Store Is Affected

- **Skills** → `~/.hermes/skills/`
- **Memory/HPC** → `~/.hermes/memory/` or configured store path
- **Session state** → `~/.hermes/sessions/`
- **Config** → `~/.hermes/config.yaml`

#### 2. Check File Integrity

```bash
# List skill directories with timestamps
ls -la ~/.hermes/skills/

# Find recently modified files
find ~/.hermes -type f -mtime -1 | head -20

# Check for zero-length files (truncation)
find ~/.hermes -size 0 -ls

# Check for unusually large files
find ~/.hermes -type f -size +100M -ls
```

#### 3. Detect JSON/Markdown Corruption

```bash
# Validate JSON files
python3 -c "import json; json.load(open('file.json'))"

# Validate YAML
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Find non-UTF8 bytes
grep -P '[\x80-\xff]' ~/.hermes/skills/*/SKILL.md | head -5
```

#### 4. Check for Split/Partial Writes

```bash
# Look for duplicate frontmatter (indicates concatenated write)
grep -c "^---$" ~/.hermes/skills/*/SKILL.md
# Should be exactly 2 per file (frontmatter open + close)
# More than 2 = partial write concatenation
```

#### 5. Repair Strategies

**For corrupted skill files:**
```bash
# Restore from git if tracked
cd ~/.hermes/skills && git checkout -- <corrupted-skill>/

# Or re-create from known-good source
```

**For corrupted JSON memory store:**
```bash
# Backup corrupted file
cp corrupted.json corrupted.json.bak

# Try to parse and salvage what we can
python3 -c "
import json
with open('corrupted.json') as f:
    content = f.read()
idx = content.rfind('}')
if idx != -1:
    valid = content[:idx+1]
    data = json.loads(valid)
    with open('repaired.json', 'w') as f:
        json.dump(data, f, indent=2)
    print('Salvaged', len(data), 'entries')
"
```

**For corrupted SQLite-based memory (Hermes HPC):**
```bash
# Check SQLite integrity
sqlite3 memory.db "PRAGMA integrity_check;"

# If errors found, dump and rebuild
sqlite3 memory.db ".dump" > memory.sql
sqlite3 memory.db < memory.sql
```

#### 6. Prevention

- Always `kill` processes gracefully (no `kill -9` during writes)
- Keep memory stores on local filesystem (not network mounts)
- Use atomic writes: write to `.tmp`, then `mv .tmp target`
- Schedule periodic integrity checks in cron

---

## Debug Logging Standards

### Why Standards Matter

Undisciplined logging creates noise that hides real errors. Standards ensure logs are **searchable**, **parsable**, and **actionable**.

### Log Level Standards

| Level | When to Use | Example |
|-------|-------------|---------|
| `DEBUG` | Flow details, variable values, branch decisions | `DEBUG: Entering function foo(x={x})` |
| `INFO` | Normal operation milestones | `INFO: User authenticated, session=abc` |
| `WARN` | Unexpected but recoverable condition | `WARN: Retry attempt 2/3 for API call` |
| `ERROR` | Operation failed, needs attention | `ERROR: DB connection timeout after 30s` |
| `FATAL` | Process cannot continue | `FATAL: Out of memory, shutting down` |

**Rule:** In production, `DEBUG` should be off. `INFO` should be the minimum.

### Structured Log Format

Use machine-parseable format in production:

```
timestamp | level | component | message | context (key=value,...)
```

Example:
```
2026-05-17T14:23:01.003Z | ERROR | auth | Login failed | user=user@example.com, attempt=3, reason=invalid_password
```

### What to Log

**Always log:**
- Entry and exit of significant operations (with duration)
- External service calls (request/response summary, latency)
- Authentication/authorization decisions
- Data transformations (input → output summary)
- Error conditions (full stack trace)

**Never log:**
- Secrets, passwords, API keys, tokens
- Full PII (log ID instead)
- Large binary blobs
- DEBUG-level in production (performance impact)

### Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `print("got here")` | No context, no level | Use `logging.debug()` with state |
| `log.info("result=" + str(r))` | String concat slow | Use f-string or format params |
| `log.error(e)` with no message | No context | `log.error("Operation X failed", exc_info=True)` |
| Logging every loop iteration | Log flood | Log summary after loop |
| No timestamps | Can't correlate events | Always include ISO-8601 timestamp |

### Debug Logging Checklist

- [ ] All external calls are logged (endpoint, latency, result summary)
- [ ] Errors include `exc_info=True` (full stack trace)
- [ ] Timestamps are ISO-8601 and timezone-aware
- [ ] Sensitive data is NOT logged
- [ ] Logs are parseable (JSON or `|`-delimited in production)
- [ ] DEBUG logs are off in production
- [ ] Each log entry contains enough context without reading other entries
