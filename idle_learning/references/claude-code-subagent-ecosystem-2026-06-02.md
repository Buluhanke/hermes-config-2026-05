# Claude Code Subagent Ecosystem — Security Analysis

**Date**: 2026-06-02
**Source**: VoltAgent/awesome-claude-code-subagents (HN Firebase API discovery)
**Size**: 154+ subagents across 10 categories

## Overview

The VoltAgent repository is the definitive collection of Claude Code subagents — specialized AI assistants designed for specific development tasks. Installed via `claude plugin marketplace add` or direct `git clone` + `install-agents.sh`.

## Categories (10 total)

| # | Category | Plugin Name | Relevance |
|---|----------|-------------|-----------|
| 01 | Core Development | voltagent-core-dev | Low |
| 02 | Language Specialists | voltagent-lang | Low |
| 03 | Infrastructure & DevOps | voltagent-infra | Medium |
| 04 | **Quality & Security** | voltagent-quality-security | **HIGH** |
| 05 | Data & AI | voltagent-data-ai | Medium |
| 06 | Developer Experience | voltagent-devex | Low |
| 07 | Specialized Domains | voltagent-domains | Low |
| 08 | Business & Product | voltagent-business | Low |
| 09 | **Meta & Orchestration** | voltagent-meta | **HIGH** |
| 10 | Research & Analysis | voltagent-research | Medium |

## Subagents of Interest

### Meta-Orchestration (Cat 09) — Hermes Architectural Mirror
- **agent-organizer**: Multi-agent coordinator — task decomposition, agent selection, result synthesis
- **context-manager**: Context optimization, memory management
- **codebase-orchestrator**: Safe refactor governance w/ approval loops
- **multi-agent-coordinator**: Parallel processing, dependency management
- **task-distributor**: Load balancing, capability matching, priority scheduling

These mirror Hermes' `delegate_task` + orchestrator/worker architecture. The same security concerns apply:
- Subagent self-report verification (Snowflake Cortex sandbox escape pattern)
- Context loss between parent and child agents
- Unverified command execution in child contexts

### Quality-Security (Cat 04) — Security Subagents
- **security-reviewer**: Code security audit
- **compliance-auditor**: GDPR, HIPAA, SOC2
- **debugger**: Root cause analysis
- **chaos-engineer**: Resilience testing

## Installation Attack Surface

Three installation methods, all with supply chain risk:
1. **Plugin marketplace**: `claude plugin marketplace add VoltAgent/awesome-claude-code-subagents`
2. **Manual install**: `git clone` → copy to `~/.claude/agents/`
3. **Script install**: `curl -sO` → `install-agents.sh` — downloads agents directly from GitHub

Same attack surface as Claude Code plugin hijacking vulnerability.

## Hermes Risk Assessment

| Risk | Level | Details |
|------|-------|---------|
| Direct adoption risk | LOW | Hermes uses local skills, not marketplace plugins |
| Architectural relevance | HIGH | delegate_task mirrors meta-orchestration pattern |
| Security pattern relevance | HIGH | subagent self-report verification gap is identical |
| Future risk | MEDIUM | If Hermes adopts plugin marketplace, same attack surface applies |

## References
- VoltAgent repo: https://github.com/VoltAgent/awesome-claude-code-subagents
- Snowflake Cortex sandbox escape: `../snowflake-cortex-sandbox-escape-2026-06-02.md`
- Claude Code plugin hijacking: `../claude-code-marketplace-plugin-hijacking-2026-06-02.md`
