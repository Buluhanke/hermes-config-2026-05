# Behavior Skills Need Enforcement (Case Study)

> Distilled from Failure 64: `proactive-execution` SKILL.md violated its own rule on 2026-07-05.

## The Trap

A "behavior skill" is any skill whose purpose is to change *how* the agent acts (proactive-execution, verification-before-reporting, no-clarifying-questions, etc.). The default authoring instinct is:

1. Write a **rule list** ("立即动手 / 不反问 / 必须有证据")
2. Add a **description** that lists triggers
3. Ship it

This produces a **document**, not a skill. The agent loads it, the rules are in context, but the agent proceeds as if it didn't exist. Worse: in the failure case, the agent **writing** the skill falls into the exact violation the skill preaches — meta-failure, not just regular failure.

## The Three-Part Enforcement Pattern

Every behavior skill must contain **all three** parts. Missing any one = reverts to documentation.

### Part 1: Pre-Action Self-Check (L2)

Concrete questions the agent asks itself **before** the next action. Not principles — *questions*. Each question must have a "what to do if the answer is wrong" branch.

**Template**:
```
## Pre-Action 自检清单 (强制)

每次回复用户之前，脑子内部必走这 4 问：

| # | 自检问题 | 不通过时必做 |
|---|----------|--------------|
| 1 | [concrete question about the behavior] | [specific corrective action] |
| 2 | [concrete question] | [specific corrective action] |
| ... |
```

Why this works: forcing a yes/no question transforms a principle ("be proactive") into a checkable predicate ("did I call a tool?"). The "what to do if wrong" branch makes the correction mechanical, not interpretive.

### Part 2: Execution Flow (L2)

Mechanical steps, not principles. The agent should be able to follow them in order without thinking.

**Template**:
```
## 落地执行流程 (每任务必走)

[收到任务后机械执行以下步骤：]
步骤1  [action]   → [output]  (time budget)
步骤2  [action]   → [output]
...
步骤N  [action]   → [output]
```

Distinguish from rules:
- Rule: "Don't ask for confirmation" (principle)
- Flow: "步骤1 创建任务文件 → 步骤2 拆解步骤 → 步骤3 立即 tool call" (mechanical)

Rules require judgment; flows require reading.

### Part 3: Watchdog Hook (cron or file-scan)

A periodic check that detects violations of the behavior the skill preaches, independent of whether the agent loaded the skill. Two patterns:

**Pattern A — File/state watchdog** (preferred for offline behaviors):
```
cron schedule: */30 * * * *
detection: scan for expected state vs. actual state
example: proactive-execution watchdog scans ~/.hermes/tasks/ for
         "进行中" tasks older than 30min with no fact_store entry
         = no-execution violation
```

**Pattern B — Self-report trigger** (when state isn't observable):
```
cron prompt: ask the agent to grep its own recent replies for the
             violation pattern (e.g. "你又没干 / 列清单不动")
             and write a self-report if matches found
```

Watchdogs must have **deliver=local** (silent on healthy) and **only push when violated**. Healthy cron = silent. Broken watchdog = spam. See `proactive-execution/references/task-tracking-sop.md` for the failure pattern of broken watchdogs.

## Diagnosis Checklist

When auditing a behavior skill, ask:

1. Can the agent violate the rule *without noticing*? If yes → missing Pre-Action check.
2. Does the skill explain *what to do* or just *what to be*? If just the latter → missing Execution Flow.
3. Is there any way to detect violations after the fact? If no → missing Watchdog.
4. Has the agent that wrote the skill ever violated it? If yes → meta-failure, fix immediately.

## Why Documentation Fails

LLMs have a context window, not persistent character. Every skill load is a fresh encounter. Rules in a skill body compete with:
- User instructions
- Other loaded skills
- Tool outputs
- The model's own priors

For a rule to survive that competition, it needs to be **enforced by structure**, not just stated as text. Pre-Action checks survive because they're *questions* (force evaluation). Flow steps survive because they're *sequence* (one leads to next). Watchdogs survive because they're *external* (don't depend on the agent remembering).

## Real Failure Reference

`proactive-execution` SKILL.md v2.0 had 10 ✅ rules and 10 ❌ anti-patterns, totaling ~300 lines, and **the agent writing the response to "立即修复" violation opened with 4 pure-text characters before any tool call**. The skill itself was a perfect example of what it preached against. v2.1.0 fix: Pre-Action 自检4问 + 落地执行流程6步 + no-execution-detector cron. The skill's *own* Failure 64 documents the meta-violation.

**Iron rule for skill authors**: if your behavior skill can be written without showing you an enforcement mechanism, you're writing documentation, not a skill.