# 深度进化发现（2026-05-30补充）

## macOS26/Agent (448★) — 重大发现

**URL**: https://github.com/macOS26/Agent
**Stars**: 448★（截至2026-05-30）
**描述**: Mac Agent for macOS 26: the agentic AI harness for your Mac Desktop. Computer use, automation, scripting, coding, and more. Powered by 18+ providers across local and cloud LLMs.

**对比Hermes的computer_use**:
| 能力 | macOS26/Agent | Hermes computer_use |
|------|--------------|---------------------|
| Mac专属优化 | ✅ 原生设计 | ✅ 可用但非Mac原生 |
| Provider数量 | 18+ | 取决于配置 |
| 自动化深度 | macOS原生API | cua-driver通用方案 |
| 集成Telegram | ❌ 未提及 | ✅ 内置 |

**评估**: 可作为Hermes Mac能力的补充参考，但不需要替换。Hermes的跨平台能力更重要。

## the-eyes (1★) — 视觉皮层

**URL**: https://github.com/nullvoider07/the-eyes
**Stars**: 1★
**描述**: The visual cortex for Computer Use Agents, bridging desktops and AI. Abstracts OS capture to deliver high-fidelity streams. Supports Windows, macOS, Linux.

**评估**: 架构思路有价值，但star太少，待观察。

## 2captcha/mcp-captcha-solver (4★)

**URL**: https://github.com/2captcha/mcp-captcha-solver
**Stars**: 4★
**描述**: MCP server for AI agents that handles captcha bypass workflows through dedicated tools. Includes reCAPTCHA v2 solving, Selenium workflows.

**评估**: MCP架构可参考，但需要付费API。Hermes已有ddddocr本地验证码方案，暂不需要。

## EvanTenenbaum/hermes-agent-self-evolution (0★)

**URL**: https://github.com/EvanTenenbaum/hermes-agent-self-evolution
**描述**: Fork of NousResearch/hermes-agent-self-evolution with patches for Hermes Agent skill evolution. Uses DSPy + GEPA.

**评估**: 与现有`proactive-self-evolution` skill思路一致，可作为备选实现参考。