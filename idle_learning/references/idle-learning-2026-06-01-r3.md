# Idle Learning 2026-06-01 Session (Direction D: Execution Layer)

**Cron 触发**：scheduled job, 01:15
**方向**：D — Execution Layer Architecture

## 系统状态 (session start)

| 组件 | 状态 | 详情 |
|------|------|------|
| screen_watcher | ✅ Running | PID 3339, 自 00:46, 625 dry-run 记录 |
| current.png | ✅ Fresh | 3.37MB, 00:56（触发时前 19 min） |
| Ollama | ✅ Running | qwen3-vl:2b runner + serve |
| Handler | ✅ Normal | 冷却 60s, 否定词检测已验证 [silent] |
| github | blocked | 预期行为 |
| HN | blocked | 预期行为 |
| Firebase API | ✅ 200 | hn.firebaseio.com 可用 |
| raw.githubusercontent.com | ✅ ok | 可用 |

## HN Top 10 (2026-06-01 01:15)

1. [763pts] Domain expertise has always been the real moat — 已收录于此前学习
2. [352pts] The Website Specification — specification.website, Agent Readiness 18 项
3. [288pts] Dav2d — video codec, 不直接相关
4. [223pts] The solution might be cancelling my AI subscription — "Friction=Focus" 再确认
5. [188pts] Cloudflare Turnstile WebGL fingerprinting — 已收录于 2026-05-31 session
6. [72pts] 1-Bit Bonsai Image 4B Image Generation for Local Devices — 边缘相关
7. [54pts] Restartable Sequences (rseq) — kernel, 不直接相关
8. [23pts] Odysseus – self-hosted AI workspace — 全新项目，1.8k stars
9. [17pts] Chibil: C compiler → .NET IL — 低相关度
10. [7pts] The Speed of Prototyping in the Age of AI — 低相关度

## 核心发现摘要

### 1. Fara1.5 (Microsoft Research, 2026-05-21)
- Qwen3.5 基座 CUA 模型, 4B/9B/27B
- Observe-Think-Act loop, 3 帧截图输入
- Online-Mind2Web 63% (9B), 72% (27B)
- Context management meta-actions

### 2. Three Generations Framework (Mininglamp/Mano-P, dev.to)
- Gen 1: Selector-Action (RPA, brittle)
- Gen 2: Vision+LLM (Hermes current, open-loop)
- Gen 3: VLA Unified Model (closed-loop, target)
- Mano-P: GSPruning 2-3x, Cider SDK 1.4-2.2x, Apache 2.0

### 3. Odysseus (pewdiepie-archdaemon)
- Self-hosted AI workspace, opencode + MCP agent
- Cookbook hardware scanner → model recommender
- Docker + ChromaDB + SearXNG + ntfy

## 搜索链
HN Firebase API (top 15) → browser_navigate to Fara1.5 MSR article → browser_console extraction → ddgs "computer use agent vision grounding action execution architecture" → "Microsoft computer use agentic SLM 2026" → "GUI agents vs RPA VLA architecture Mininglamp 2026" → browser_navigate to dev.to article

## 在本次 session 中更新的 skill
- **vision-agent-loop**: 更新主模型（smolvlm2→qwen3-vl:2b），新增 Fara1.5 + 三代架构参考文件，替换所有过期代码示例
