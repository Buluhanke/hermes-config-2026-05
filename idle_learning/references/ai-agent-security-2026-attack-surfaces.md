# AI Agent Security 2026: Attack Surfaces in MCP, Function Calling, and Computer-Use Systems

**Source**: https://www.programming-helper.com/tech/ai-agent-security-2026-attack-surfaces-mcp-function-calling
**Author**: Sarah Chen, May 5, 2026
**Verified**: 2026-06-02 via browser_navigate + browser_console JS extraction
**Tags**: MCP, tool poisoning, function calling injection, computer-use, multi-agent, delegate_task

## Three Attack Surfaces

### 1. Tool Poisoning (MCP Tool Definitions)
- Attacker introduces malicious tool definitions that appear legitimate
- Three vectors: registry compromise, supply chain injection, deceptive naming
- LLM cannot verify tool intent independently — trusts the schema as authoritative
- **Multi-tool environments amplify risk** — each tool is a poison point
- Mitigation: assume at least one tool definition may be compromised

### 2. Function Calling Injection
- Extends prompt injection to action-oriented domain
- Crafted prompts exploit model's tool selection → attacker-controlled arguments
- **Mitigation code pattern**:
  ```python
  class FunctionCallValidator:
      def __init__(self, allowed_patterns):
          self.allowed_patterns = allowed_patterns
      def validate_call(self, function_name, arguments) -> bool:
          ...  # regex pattern validation per function
  ```

### 3. Computer-Use Agents: Extending the Attack Surface
- **Screen capture manipulation**: attacker controls what appears on screen → agent takes unintended actions (fake login forms, fabricated banking interfaces, fictional system prompts)
- **Action execution hijacking**: mouse/keyboard/browser actions can be redirected
- **Credential exposure**: computer-use agents inevitably expose authentication tokens
- **Mitigation**: screen content verification, isolated VMs/containers, short-lived session tokens

## Multi-Agent Systems: Compound Vulnerabilities (Directly Relevant to Hermes delegate_task)

| Architecture | Risk pattern | Hermes relevance |
|-------------|-------------|-----------------|
| Hierarchical (orchestrator → sub-agents) | Orchestrator compromised → all sub-agents exposed | delegate_task uses this pattern |
| Agent2Agent protocol | Impersonation, falsified responses, logic manipulation | Hermes subagent self-report is unverified |
| Inter-agent communication | False information injection → cascading bad decisions | No independent verification channel |

## Key Mitigations
1. **Network isolation**: deploy agents in dedicated VMs/containers with limited network access
2. **Short-lived session tokens**: assume credentials will be exposed
3. **Function call validation**: regex pattern check per argument per function
4. **Assume compromise at every layer**: design systems that limit blast radius
5. **Monitor function call patterns**: tool usage anomalies, inter-agent behavior

## Risk Matrix for Hermes

| Threat | Direct Risk | Indirect Risk | Action |
|--------|-------------|--------------|--------|
| Tool Poisoning | LOW — Hermes tools defined locally | MED — if MCP servers used | Monitor MCP registries |
| Screen Manipulation | HIGH — screen_trigger_handler | HIGH — auto_execute | Verify screen content |
| Subagent Self-Report | HIGH — delegate_task | MED — no rollback mechanism | Add post-execution verification |
| Credential Exposure | MED — computer_use tool | MED — token in environment | Implement token rotation |
