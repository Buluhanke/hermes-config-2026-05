# Qwen3.7-Plus — Alibaba Cloud Multimodal Agent (June 2, 2026)

**Release date**: June 2, 2026 (Alibaba Qwen team)
**Platform**: Alibaba Cloud Bailian / Model Studio (international API access)
**Ollama status**: ❌ NOT available on Ollama (only qwen3 text + qwen3-coder-next as of June 3, 2026)
**Type**: Cloud-only MLLM (not downloadable/quantized for local use)

## Key Capabilities

Multimodal MLLM — image + video understanding (not generation). Five agentic capabilities:
1. **Deep reasoning**
2. **Self-programming** — writes/modifies own code
3. **Tool calling** — invokes external functions/APIs
4. **Verification & testing** — runs outputs and checks correctness
5. **Autonomous iteration** — loops until task completion

## Benchmark Performance

- **Vision Arena Preview**: Rank 16 overall, 5th globally in vision capability
- **Max (text-only)**: Scored 56.6 on AII (Artificial Intelligence Index) — highest among Chinese releases

## Hermes Relevance

- **No local impact** — cloud-only, does not affect local qwen3-vl:2b production line
- **Agentic loop architecture** — mirrors the 5-stage ReAct pattern already in Hermes
- **Platform observation**: Bailian RL mechanism + built-in safety guardrails for autonomous tool use
  - This is the same pattern Hermes is building toward (dry-run → approval-gated → autonomous)
- **Security angle**: Built-in guardrails for autonomous tool execution on cloud platform — relevant as Direction C reference for Hermes's guardrail roadmap

## Sources

- MarkTechPost: https://www.marktechpost.com/2026/06/02/alibabas-qwen-team-launches-qwen3-7-plus-adding-vision-deep-reasoning-tool-invocation-and-autonomous-iteration-on-the-bailian-platform/
- Qwen Blog: https://qwen.ai/blog?id=qwen3.7-plus
- Ollama Library search: qwen3.7-plus returns 404 (not available)
