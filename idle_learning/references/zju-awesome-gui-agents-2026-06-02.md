# ZJU-REAL/Awesome-GUI-Agents Scanner Report — 2026-06-02

**Source**: https://github.com/ZJU-REAL/Awesome-GUI-Agents
**Last repo commit**: ~10 hours before scan (Jun 2, 2026)
**Scan method**: `curl raw.githubusercontent.com` → grep new entries

## New Papers Found (not in existing references)

### UltraCUA
- **Title**: UltraCUA: A Foundation Model for Computer Use Agents with Hybrid Action
- **Category**: Technical Report
- **Status**: ❓ NEW — needs investigation in Direction B session
- **Tags**: computer-use, foundation model, hybrid action

### OmegaUse
- **Title**: OmegaUse: Building a General-Purpose GUI Agent for Autonomous Task Execution (BaiDu)
- **Category**: Technical Report
- **Status**: ❓ NEW — needs investigation
- **Tags**: GUI agent, general-purpose, Baidu

### Surfer 2
- **Title**: Surfer 2: The Next Generation of Cross-Platform Computer-Use Agents
- **Category**: Technical Report
- **Status**: ❓ NEW — needs investigation
- **Tags**: cross-platform, computer-use, next-gen

### AgentS3
- **Title**: AgentS3: The Unreasonable Effectiveness of Scaling Agents for Computer Use
- **Category**: Technical Report
- **Status**: ❓ NEW — needs investigation
- **Tags**: scaling, computer-use, open-source

### SCALECUA
- **Title**: SCALECUA: Scaling Open-Source Computer Use Agents with Cross-Platform Data
- **Category**: Technical Report
- **Status**: ❓ NEW — needs investigation
- **Tags**: scaling, open-source, cross-platform, CU

### CODA
- **Title**: CODA: Coordinating the Cerebrum and Cerebellum for a Dual-Brain Computer Use Agent with Decoupled Reinforcement Learning
- **Category**: Technical Report
- **Status**: ❓ NEW — needs investigation
- **Tags**: dual-brain, RL, decoupled, computer-use

### UItron
- **Title**: UItron: Foundational GUI Agent with Advanced Perception and Planning
- **Category**: Technical Report
- **Status**: ❓ NEW — needs investigation
- **Tags**: GUI agent, perception, planning, foundation

## Already Known Papers (present in this repo but covered elsewhere)

- LiteGUI (arXiv 2605.07505) — already in learning_log ✅
- Fara-7B — already in learning_log ✅
- OS-Themis — already covered ✅
- Mano Technical Report — already covered ✅
- UI-TARS-2 — already covered ✅
- Holo1.5 — already covered ✅

## Scan Command Reference

```bash
# Full README scan
curl -sf --max-time 10 "https://raw.githubusercontent.com/ZJU-REAL/Awesome-GUI-Agents/main/README.md" \
  | grep -B1 "Technical Report\|Computer-use Agents\|Open.*Source Data\|Distill\|Reward Model" \
  | grep -v "^--$"

# Check if paper is already logged
grep -i "UltraCUA\|OmegaUse\|Surfer 2\|AgentS3\|SCALECUA\|CODA\|UItron" ~/.hermes/memory/idle_learning_log.md
```
