# Browser Agent & MCP 动态速报 (2026-08-07)

## Browser Agent SOTA

### cotomi Act (2026)
- WebArena 80.4%，**首超人类基线78.2%**
- 核心：从用户日常浏览行为中学习隐性组织知识（任务看板+wiki），持久化 + 人-Agent双向编辑
- TOCTOU漏洞：规划与执行之间页面可被恶意修改，10款主流browser agent全部中招；pre-execution validation（MutationObserver+ResizeObserver）可完全防御，额外开销<0.05s

### Webwright (Microsoft)
- Terminal-based harness：Agent写Playwright代码控制浏览器，非逐个动作预测
- 3个模块：Runner(150行) + Model接口(550行) + Environment(300行)
- Online-Mind2Web 86.67%；Odysseys 60.1%（最佳开源方案）
- GPT-5.4 平均$2.37/任务；Claude Opus 4.7 $6.09

### SuperBrowser
- Vision-first OCR bounding-box + 三角色脑(Orchestrator/Planner/Worker) + 六相上下文驱逐
- Mind2Web Hard 89.47%（第三名，超越所有开源方案）
- **成本差距**：US workers平均31次tool calls，Chinese workers平均41次（贵33%）

### ColorBrowserAgent
- WebArena 71.2% SOTA；知识适应（Human-in-the-loop）+ 渐进式记忆压缩

### Agent JIT Compilation
- JIT-Planner（多代码计划+验证+最低成本选择）+ JIT-Scheduler（Monte Carlo延迟估计+并行策略）
- vs Browser Use：**10.4×加速+28%准确率**；vs OpenAI CUA：**2.4×加速+9%准确率**

## MCP 生态

### MCP 2026-07-28 规范
- **stateless core**：initialize/initialized废止，explicit handle替代session
- MRTR替代server发起的elicitation/sampling/roots请求
- AWS/Anthropic/Cloudflare联合背书
- Tier-1 SDK（TypeScript/Python/Go/C#）全部支持

### computer-use-mcp 崛起
- Rust NAPI跨平台：Mac+Win+Linux，46工具，**120MB内存**
- vs Python方案（180-200MB）
- 支持Skills teach/replay模式，verified outcomes
- 已确认支持Hermes Agent

## 模型动态

### 中国模型工具效率差距（重要）
- Claude Opus 4.8：27次tool calls完成任务
- Kimi-K2.6：53次tool calls完成**同等任务**（近2倍）
- 即使答案正确率相当，工具调用效率差异显著
- US workers平均31 calls；Chinese workers平均41 calls（+33%）

## GitHub Trending (2026-08-07)
- microsoft/fara — Fara1.5 frontier computer use agent models
- TurixAI/TuriX-CUA — Computer Use Agent
- OpenGVLab/ScaleCUA — ICLR 2026 Oral，跨平台(Win/Mac/Linux/Android)
- xlang-ai/OpenCUA — NeurIPS 2025 Spotlight
- meituan/EvoCUA — 演进式Computer Use Agent
- showlab/ShowUI-Aloha — 真人教学Computer-use Agent
