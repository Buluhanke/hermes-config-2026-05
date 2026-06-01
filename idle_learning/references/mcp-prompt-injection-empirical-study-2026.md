# MCP Prompt Injection Empirical Study (arXiv 2603.21642, Mar 2026)

- **Title**: Are AI-assisted Development Tools Immune to Prompt Injection?
- **Authors**: Charoes Huang, Xin Huang, Amin Milani Fard
- **arXiv**: 2603.21642 (Mar 23, 2026)
- **Subjects**: cs.CR, cs.SE

## Scope
First empirical analysis of 7 widely-used MCP clients under **tool-poisoning-mediated prompt injection**:

| Client | Security Posture |
|--------|-----------------|
| Claude Desktop | ✅ Strict safeguards |
| Claude Code | ⚠️ Moderate |
| Cursor | ❌ Highly vulnerable |
| Cline | ⚠️ Moderate |
| Continue | ⚠️ Moderate |
| Gemini CLI | ⚠️ Moderate |
| Langflow | ⚠️ Moderate |

## Attack Vectors Evaluated
1. **Cross-tool poisoning** — malicious tool output infects subsequent tools
2. **Hidden parameter exploitation** — parameter injection via tool descriptions
3. **Unauthorized tool calls** — bypassing tool approval dialogs

## Key Findings
- Significant security posture variance across MCP clients
- Some lack: static validation, parameter visibility, injection detection, user warnings, execution sandboxing, audit logging

## Hermes Risk Assessment
- **Current exposure**: LOW-MED
  - Hermes' native MCP client uses stdio transport (similar to Claude Desktop architecture)
  - Tool descriptions are locally defined, not user-supplied
  - No market for third-party MCP servers (yet)
- **Key gaps**: 
  - No injection detection on tool output
  - No execution sandbox for MCP server output
  - Subagent self-reporting (delegate_task) creates a "blind trust" gap

## Recommended Actions
1. Add MCP tool-output injection check (regex/heuristic)
2. Consider sandboxing MCP execution in isolated process
3. Reference this study when evaluating new MCP client features
