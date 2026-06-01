# Adversa AI June 2026 Security Digest — 新发现（2026-06-02）

来源: https://adversa.ai/blog/top-agentic-ai-security-resources-june-2026/
发布: June 1, 2026
28 resources total, 8 篇未被之前方向C扫描覆盖

## ⭐ ASPI (Ambiguity Seeking → Prompt Injection) — Hermes 中等风险

**关键洞察**: Agent 询问澄清的行为本身成为新的注入通道。用户问"您想要A还是B"时，攻击者可以通过误导性上下文劫持Agent的决策。

**Hermes 映射**: delegate_task subagent 的 clarify 能力可能被利用。应考虑在 subagent 中禁用 clarify 或添加白名单。

## ⭐ Sleeper Memory Poisoning (Hidden in Memory)

**关键洞察**: 休眠记忆跨 session 触发。攻击者植入虚假记忆后，Agent 在后续 session 中触发受控行为，延迟难以追溯。

**Hermes 映射**: memory 系统持久存储跨会话 — 理论上有注入风险。memory 写入应有独立验证回读。

## ⭐ Copirate 365 (CVE-2026-24299)

**关键洞察**: DEF CON 2026 议题。间接提示注入 + 渲染层数据窃取 + 延迟工具调用 + 内存中毒 → 持久化 Copilot 后门。

**Hermes 映射**: 间接注入链路的教科书案例。Hermes screen_trigger handler 冷却时间 60s 起到类似防护作用。

## MemMorph — 内存中毒劫持 tool selection

不触及工具元数据，通过少量伪装记录偏移 Agent 工具选择。难以检测。

## SafeHarbor — 免训练层级记忆 guardrail

层级记忆架构 + 熵基自进化。不重新训练基础模型即可拒绝有害请求同时保留效用。

## ARGUS — 上下文感知注入防护

provenance-aware influence graph 审计每个 agent 决策，捕获适配上下文环境的注入。

## AgentShield — 蜜罐/欺骗检测

在工具系统中植入 honeytoken 和诱饵工具，被攻陷的 Agent 会暴露自己。

## Towards Trustworthy Agentic AI — 综合综述

全面映射 Agentic AI 风险：safety/robustness/privacy/system security。方向 C 通用参考。
