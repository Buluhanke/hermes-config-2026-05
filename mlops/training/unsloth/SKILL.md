---
name: unsloth
description: "Unsloth: 2-5x faster LoRA/QLoRA fine-tuning, less VRAM."
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [unsloth, torch, transformers, trl, datasets, peft]
metadata:
  hermes:
    tags: [Fine-Tuning, Unsloth, Fast Training, LoRA, QLoRA, Memory-Efficient, Optimization, Llama, Mistral, Gemma, Qwen]

---

# Unsloth Skill

Comprehensive assistance with unsloth development, generated from official documentation.

## When to Use This Skill
This skill should be triggered when:
- Working with unsloth
- Asking about unsloth features or APIs
- Implementing unsloth solutions
- Debugging unsloth code
- Learning unsloth best practices
- Training/fine-tuning LLMs for domain-specific tasks (e.g., supply chain procurement agents)

## User Workflow Preferences ⚠️

**CRITICAL**: This user prefers direct execution over guidance.

- **NO step-by-step explanations** — user says "你给我装" (just install it) or "不用了" (no need) when guidance is provided
- **Short, direct responses** — avoid verbose explanations, get straight to the action
- **Execute immediately** — user wants the agent to take action, not ask permission for every step
- **Silent failures** — if a fallback model fails, silently switch without showing technical details
- **User corrections override** — if the user corrects an approach, stop and use the corrected method immediately

**When to apply**: Always start with direct action. Only provide explanations if the user explicitly asks "how" or "why". After completing a task, briefly confirm with one line like "Done" or "切换完成" — no lengthy summaries.

## Environment Constraints

**User's current setup**:
- **Hardware**: Intel Mac (i5-9600KF, 32GB RAM, no GPU)
- **Cannot run local fine-tuning** — no CUDA/MPS acceleration
- **Remote Mac mini**: 192.168.0.4 (user has SSH access but authentication issues)
- **Cloud GPU**: Must use cloud GPU providers (RunPod, Vast.ai) for local training

**Training recommendations**:
1. **Cloud GPU (preferred)**: Rent GPU instance (A100/H100) for 4-8 hours
2. **Mac mini (if Apple Silicon)**: Use MLX for lightweight fine-tuning
3. **API fine-tuning**: Use DeepSeek/OpenAI's online fine-tuning API

**Do NOT attempt local training on Intel Mac** — will be extremely slow and impractical.

## Domain-Specific Training Context

**User's primary domain**: Supply chain procurement (找品)

**Key requirements**:
- Target suppliers: 10+ minimum
- Origin preference: Jiang-Zhe-Hu (Jiangsu-Zhejiang-Shanghai) region
- Product categories: Packaging materials (纸箱), business supplies
- Data sources: 1688, PDD (拼多多), Taobao, YiwuGo
- Current blockers: 1688 anti-bot detection, mock data in supply-agent-v11

**Training goals** (from user): "让hermes变强" (make Hermes stronger)

**Potential training directions**:
1. **Supplier matching**: Train model to identify high-quality suppliers from scraped data
2. **Price comparison**: Train to extract and compare prices across platforms
3. **Quality assessment**: Train to evaluate factory certifications, production capacity
4. **Procurement workflow**: Train to automate the full procurement pipeline

**Relevant user projects**:
- `~/supply-agent-v11/` — Supply chain agent skeleton (mock data)
- `~/1688_bot/` — 1688 scraping with anti-detection attempts
- `~/dianchacha_v2.5.3/` — 电查查 (electricity consumption database for supplier verification)

**Reference data sources** (for training):
- 1688 scraped product listings (currently failing due to anti-bot)
- PDD/Taobao/YiwuGo product data
- Supplier profiles with quality metrics
- Price history data

## Quick Reference
### Common Patterns
*Quick reference patterns will be added as you use the skill.*

## Reference Files
This skill includes comprehensive documentation in `references/`:
- **llms-txt.md** - Llms-Txt documentation

Use `view` to read specific reference files when detailed information is needed.

## Working with This Skill
### For Beginners
Start with the getting_started or tutorials reference files for foundational concepts.

### For Specific Features
Use the appropriate category reference file (api, guides, etc.) for detailed information.

### For Code Examples
The quick reference section above contains common patterns extracted from common usage examples in the docs.

## Resources
### references/
Organized documentation extracted from official sources. These files contain:
- Detailed explanations
- Code examples with language annotations
- Links to original documentation
- Table of contents for quick navigation

### scripts/
Add helper scripts here for common automation tasks.

### assets/
Add templates, boilerplate, or example projects here.

## Notes
- This skill was automatically generated from official documentation
- Reference files preserve the structure and examples from source docs
- Code examples include language detection for better syntax highlighting
- Quick reference patterns are extracted from common usage examples in the docs

## Updating
To refresh this skill with updated documentation:
1. Re-run the scraper with the same configuration
2. The skill will be rebuilt with the latest information
