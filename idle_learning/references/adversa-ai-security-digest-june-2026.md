# Adversa AI — Top Agentic AI Security Resources June 2026

**Source**: https://adversa.ai/blog/top-agentic-ai-security-resources-june-2026/
**Date**: May 26, 2026 (published), Jun 2, 2026 (reviewed)
**Author**: Rony Utevsky / Adversa AI

## Key Disclosures

### 1. SymJack — Symlink-Hijack RCE (HIGH, Hermes Direct)
- **Mechanism**: Symlink-disguised file copy tricks AI coding assistants into RCE.
  "The approval prompt is lying to you."
- **Tested & Vulnerable**: Claude Code, Cursor, Antigravity, GitHub Copilot, Grok Build, Gemini CLI
- **All six were vulnerable**.
- **Hermes Mapping**: Hermes `terminal()` in subagent context is susceptible to symlink attacks. DRY_RUN=True is behavioral, not architectural.

### 2. TrustFall — One-Click RCE (HIGH, Hermes Direct)
- **Mechanism**: Regression in Claude Code trust dialog + settings-scope inconsistency. Cloned repo runs unsandboxed code.
- **Affected**: Claude Code, Cursor, Gemini CLI, GitHub Copilot
- **Hermes Mapping**: `delegate_task` subagent self-reporting vulnerability is same class.

### 3. AgentTrust (arXiv 2605.04785)
- Runtime safety evaluation intercepts tool calls before execution.
- Returns allow/warn/block/review verdicts. Shell deobfuscation + attack-chain detection.

### 4. Hybrid Inspection + TBAC (arXiv 2605.02682)
- Semantic inspection + task-based access control under zero-trust model.

### 5. Four OpenClaw Flaws
- MCP loopback runtime vulnerabilities — data theft, privilege escalation, persistence.

### 6. Towards Trustworthy Agentic AI (arXiv 2605.22568)
- Comprehensive survey: safety, robustness, privacy, system security.
- "AI agent is only as trustworthy as the weakest thing it is allowed to act on."

## Risk Matrix

| Finding | Direct Risk | Indirect Risk | Action |
|---------|-------------|---------------|--------|
| SymJack | MEDIUM — terminal() can be symlink-attacked | HIGH — subagent self-report gap | Add reference; no config change |
| TrustFall | LOW — no trust dialog in Hermes | MEDIUM — same "reported fine after bad action" pattern | Monitor |
| AgentTrust | LOW — not integrated | HIGH — reference architecture for DRY_RUN=False | Mark for precondition eval |
| TBAC | LOW | MEDIUM — zero-trust aligns with Hermes | Reference only |
| OpenClaw | LOW — no MCP loopback in Hermes | MEDIUM — skills/plugins parallel | Reference only |
