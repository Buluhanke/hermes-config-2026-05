# Agentic AI Security in 2026 (Zylos Research, 2026-05-16)

**Source**: zylos.ai/research/2026-05-16-agentic-ai-security-prompt-injection-defense-stack/
**Retrieved**: 2026-06-02 (browser_navigate, CDP full-text extraction)

## Key Stats (2025-2026)
- **73%** of production AI deployments had prompt injection (2025)
- **32% increase** in malicious payloads in web content (Nov 2025-Feb 2026)
- **91,403** attack sessions targeting exposed LLM endpoints (GreyNoise, Oct 2025-Jan 2026)
- **60%** of attack traffic shifted to **MCP endpoint reconnaissance** by Jan 2026
- **$5.72M** average AI breach cost without access controls (IBM)
- Only **29%** of orgs deploying agentic AI are prepared to secure them

## 6 Attack Categories

| Category | Description | Hermes relevance |
|----------|-------------|-----------------|
| Direct Prompt Injection | Instructions in user input | devin AI defenseless |
| Indirect Prompt Injection (IPI) | Instructions in external content (web, docs, code) | Cursor CVE-2025-59944, Anthropic Git MCP 3 CVEs |
| **Tool Poisoning** ⭐ | MCP tool metadata weaponized | skills metadata = Hermes equivalent |
| **Memory Poisoning** ⭐⭐ | Vector stores / episodic buffers corrupted | memory tool = direct attack surface |
| **Agent Impersonation** ⭐⭐ | Multi-agent orchestrator spoofed | delegate_task without auth |
| Supply Chain | Plugin/marketplace poisoning | skill_manage ecosystem |

## OWASP Agentic Top 10 (Dec 2025)

| # | Risk | Hermes |
|---|------|--------|
| 1 | Uncontrolled Autonomy | DRY_RUN guards |
| 2 | **Delegated Identity Abuse** ⭐ | delegate_task: subagents inherit full permissions |
| 3 | Cross-Agent Prompt Injection | Subagent self-report vulnerability |
| 4 | Excessive Tool Permissions | Skills/plugin access model |
| 5 | **Persistent Memory Tampering** ⭐⭐ | memory tool = attack surface |
| 6 | Supply Chain Compromises | skill_manage ecosystem |
| 7 | Audit Trail Gaps | Subagent execution not parent-logged |
| 8 | Trust Boundary Violations | Web content treated as data |
| 9 | **Orchestration Hijacking** ⭐ | delegate_task single point of failure |
| 10 | Privilege Escalation via Reasoning | CoT-based unauthorized actions |

## 7-Layer Defense Stack
1. Input Sanitization → 2. Sandboxed Execution → 3. Least Privilege → 4. HITL → 5. Supply Chain Security → 6. Memory Store Integrity → 7. Audit Logging

## Hermes Relevance: HIGHEST
- 4/6 attack categories directly applicable
- OWASP #2 = known delegate_task vulnerability
- OWASP #5 = memory tool durable cross-session state
- OWASP #9 = orchestrator single point of failure
- Defense Layer 4 = Hermes DRY_RUN model
- Defense Layer 6 = Hermes lacks provenance tracking on memory writes
