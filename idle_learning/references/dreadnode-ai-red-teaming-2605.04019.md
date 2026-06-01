# Dreadnode AI Red Teaming Agent — arXiv 2605.04019

**Paper**: "Redefining AI Red Teaming in the Agentic Era: From Weeks to Hours"
**arXiv**: [2605.04019](https://arxiv.org/abs/2605.04019)
**Date**: 2026-05-05
**Authors**: Dheekonda, Raja Sekhar Rao; Pearce, Will; Landers, Nick
**Framework**: Open-source Dreadnode SDK

## Core Contributions

1. **Agentic interface**: Operators describe goals in natural language via the Dreadnode TUI. Agent handles attack selection, transform composition, execution, and reporting. Weeks compress to hours.

2. **Unified framework**: Single framework for probing traditional ML models (adversarial examples) AND generative AI systems (jailbreaks), removing need for separate libraries.

3. **Llama Scout case study**: 85% attack success rate with severity up to 1.0, using zero human-developed code.

## Capability Scope

| Dimension | Count |
|-----------|-------|
| Adversarial attacks | 45+ |
| Transforms (encoding, persuasion, injection, etc.) | 450+ |
| Scorers | 130+ |
| Modules | 38 |

## Coverage Areas

The 38 modules cover:
- Encoding and ciphers
- Persuasion and framing
- Prompt injection (skeleton key, DAN, role-play wrappers)
- Language adaptation
- Adversarial suffixes
- MCP tool attacks
- Multi-agent exploits
- Exfiltration techniques
- Reasoning attacks
- Guardrail bypass
- Browser agent attacks
- Backdoor and fine-tuning exploits
- Supply chain attacks
- Multimodal perturbations

## Hermes Mapping

**Direct risk**: LOW. Dreadnode is a red-teaming *testing* framework, not an attack vector itself. It tests agent security postures.

**Indirect risk**: MEDIUM. Dreadnode's MCP tool attacks + multi-agent exploits + guardrail bypass modules directly test agent architectures similar to Hermes (delegate_task, memory injection, tool calling). If Hermes were Dreadnode-targeted, these modules would probe:
  - **delegate_task subagent isolation**: Can a subagent be tainted and escalate to the parent?
  - **memory poisoning**: Can crafted memory entries bias tool selection? (See also: MemMorph, Sleeper Poisoning)
  - **MCP tool poisoning**: Can a maliciously configured MCP tool exfiltrate context?

**Action**: No configuration changes needed. Add to direction C's red-teaming reference library for future Hermes security posture testing.

## Source

Discovered via: `ddgs text -q "agentic AI red team pentesting guardrail 2026" -m 5` — direction C rotation keyword.
