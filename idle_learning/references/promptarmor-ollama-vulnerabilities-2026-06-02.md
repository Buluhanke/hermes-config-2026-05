---
name: promptarmor-ollama-vulnerabilities-2026-06-02
created: 2026-06-02
source: PromptArmor Threat Intelligence
---

# Unpatched Ollama Vulnerabilities: Phishing Overlays and Data Exfiltration

**Source**: https://www.promptarmor.com/resources/unpatched-ollama-vulnerabilities-phishing-overlays-and-data-exfiltration

**Reported**: December 18, 2025 to Ollama team. No response after 4 follow-ups.

## Attack Chain

1. User asks Ollama to read an external website or document
2. Site contains hidden prompt injection (1pt font, white-on-white)
3. Model outputs malicious HTML that overlays the entire Ollama desktop UI
4. Attacker captures credentials entered into the phishing overlay

## Three Zero-Click Data Exfiltration Paths

- All exploitable via indirect prompt injection
- No human approval step required
- Attack vector: model is manipulated to fetch malicious URLs

## Relevance to Hermes

- **Direct risk: LOW** — Hermes uses Ollama API (localhost:11434), not the desktop UI
- **Indirect risk: MEDIUM** — Handler pipeline feeds screenshots via /api/chat, but scene classification prompt is fixed and not user-controllable
- **Action**: No immediate change. Monitor Ollama patches.
