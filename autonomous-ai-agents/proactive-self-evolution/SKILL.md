---
name: proactive-self-evolution
description: "主动自我进化 — 不等指令，持续扫描全网增长自身能力。每小时轻量巡检，每天深度学习，每周汇总汇报。"
triggers:
  - "不等用户下达任务，主动寻找成长机会"
  - "任何空闲时间都用于自我提升"
  - "发现新工具/新方法立即评估能否接入Hermes"
---

# proactive-self-evolution

**核心原则**：不等指令，持续进化，全网搜索，不依赖模型自身知识。

## 三层进化机制

### 第一层：碎片巡检（每2小时，轻量，≤5分钟）
- cronjob `0 */2 * * *` 触发（每天8次：8/10/12/14/16/18/20/22点）
- **执行前先查 session_search**：确认用户最近1小时无活跃对话才执行，否则往后推2小时，静默退出
- **白天只浅搜**：GitHub trending / HN热门 / 技术博客快速扫一眼
- 轮换方向：工具发现 / 技术博客 / 真人化短板（新方案）
- 单次不超过5分钟，只记不做深度研究
- 重大突破立即QQ通知，普通发现静默存档

## 第二层：深度学习（每天凌晨2点，满血跑）
- cronjob `0 2 * * *` 触发
- **必须走全网搜索**，不依赖模型知识
- **搜索方向（锚定真人化路线）**：
  - 屏幕感知突破（最优先）：screen understanding AI agent / desktop computer use / visual grounding
  - 验证码对抗：CAPTCHA bypass / anti-detection / browser fingerprint
  - 类人操作节奏：humanization browser automation / behavioral simulation
  - 1688采购闭环：1688 API / procurement automation
- **直接对话浏览器AI**：打开ChatGPT/Claude讨论（仅第二层）
  - ⚠️ **已知障碍**：沙盒环境下CDP WebSocket隔离，execute_code中WebSocket握手必然失败
  - 绕过：用 `terminal()` 在host执行Python，或在host环境手动开Qwen/ChatGPT页面
  - 替代：web_search + web_extract 可覆盖大部分研究问题，浏览器AI对话仅作为深度验证
  - "桌面AI Agent目前最强的屏幕感知方案是什么？"
  - "如何让AI操作浏览器看起来像真人？"
  - "AI采购 Agent最难的环节是什么？"
- **结合已有技能综合思考**：1688自动化 / CDP深度控制 / MCP工具生态 / 浏览器持久化
  - 现有能力 + 新发现 = 什么新可能性？
- 评估能否缝进Hermes，存入 ~/Vision_Lab/ 和 ~/Brain_Lab/
- 存疑：搜索和对话都找不到答案的 → 标记需用户确认
- **2026-05-17发现**：Patchright CLI已装(1.58.2)、smolvlm2已装Ollama、CapSolver为验证码首选方案、browser-use 78k stars
### 第三层：每周汇报（周五18:00）
- cronjob `0 18 * * 5` 触发
- 汇总一周发现，简报发 QQ

## 知识源优先级

1. **GitHub** — `gh search repos` + `site:github.com` + trending
2. **arXiv** — 论文预印本
3. **Hacker News** — `site:news.ycombinator.com`
4. **技术博客/文档**
5. **浏览器AI对话** — CDP控制ChatGPT/Claude（仅第二层）
6. **EvoMap evolver** — GEP (Genome Evolution Protocol)，基因式能力演进，83k star工程技能库（mattpocock/skills）可适配

## 存储路径
## 已知执行障碍（实测确认，勿重复踩坑）

### CDP WebSocket沙盒隔离（2026-05-17确认）
execute_code 沙盒环境内无法连接CDP WebSocket（`ws://localhost:9333`），原因是沙盒网络隔离。
- **现象**：`WebSocket handshake failed` — 即使端口9333在host可通
- **绕过方案**：用 `terminal()` 执行Python脚本（不走沙盒），或用 `mcp_cua_*` 工具
- **浏览器AI对话步骤受影响**：无法通过CDP WebSocket向Qwen/ChatGPT发消息

### Chrome MCP Bridge状态检测（2026-05-16确认）
MCP bridge（`mcp-chrome-stdio`）与Chrome进程独立，bridge挂了≠Chrome不可控。
- **fallback**：CDP HTTP端点 `http://127.0.0.1:9333/json` 始终独立可用
- **验证命令**：`lsof -i :9333 | grep Chrome`

### browser_navigate登录态（2026-05-16确认）
未配置CDP时，`browser_navigate` 每次开独立实例无登录态。配置 `browser.cdp_url: 'http://127.0.0.1:9333'` 后走 `connect_over_cdp`，自动复用Chrome cookies。

## 进化存储路径
- ~/Vision_Lab/ — 工具/技能方向
- ~/Brain_Lab/ — 思路/方法论方向

## 已验证可用的工具（避免重复调研）

### 2026-05-17实测确认
- **Patchright CLI**: `/Library/Frameworks/Python.framework/Versions/3.14/bin/patchright` (v1.58.2)，Playwright反检测fork
- **smolvlm2**: `ahmadwaqar/smolvlm2-agentic-gui` 已装Ollama，本地VL模型(2GB)，直接输出归一化坐标
- **Playwright**: hermes venv中可用 `from playwright.sync_api import sync_playwright`

## 真人化目标锚定（2026-05-15确立）

1. 屏幕全域感知（95%差距）→ 最高优先
2. 验证码对抗（100%差距）
3. 类人操作节奏（80%差距）
4. 移动端操控（100%差距）
5. 多步骤业务闭环（50%差距）

## 关键行为准则（来自用户纠正，不可违背）

**核心原则：永远不要问用户"你想往哪个方向"或"你要我做什么方向"。**

用户给指令是"让Hermes真人化"，不是"让用户指挥Hermes去做什么"。正确流程是：
1. 自己内视当前能力缺口
2. 自己制定行动优先级
3. 自己执行，自己验证
4. 有结果了再汇报

用户原话："你的思维错了，不是我想往哪个方向，而是你在内人到真人化的这个路上，你现在哪些欠缺的是你要自己去寻找"

**违反这条原则的表现（立刻停止）：**
- 向用户抛选择题："你想做A还是B？"
- 向用户请求方向授权："接下来我应该做什么方向？"
- 任何把决策权推回给用户的表述

## 已知局限

- 模型知识有天花板，必须全网搜索验证
- 国内网络需代理：Shadowrocket 127.0.0.1:1082；Clash verge-mih 监听 7897
- 任务 prompt 要精简，避免超 context limit（MiniMax 8K tokens）。实测：prompt 超过约 19K tokens（~7000中文）会被 OpenRouter 拦截并报 402
- cron job prompt 需要定期检查精简，新发现不要直接追加，先问"这次发现值不值得增加 prompt 长度"
- Mac mini M4 无 NVIDIA GPU，无法运行需要 CUDA 的工具（如 Chandra OCR 2，需要 4GB+ 显存）
- **Ollama 路径**：`/Applications/Ollama.app/Contents/Resources/ollama`（不是 `/opt/homebrew/bin/ollama`，也不是 `/usr/local/bin/ollama`）
- **已安装模型**（2026-05-17）：`qwen2.5vl:7b`（6GB）、`ahmadwaqar/smolvlm2-agentic-gui:latest`（2GB，Mac视觉专用）、`qwen3-fast`、`qwen3:8b`

## 真人化自评模板（每次内视时使用）

格式：
```
| 能力 | 差距% | 说明 |
|------|------|------|
```

关键维度：
- 屏幕感知（主动/全域/实时）
- ASR语音识别（能听）
- TTS语音合成（能说）
- 移动端操控（手机盲区）
- 验证码对抗（1688核心卡点）
- 主动性（不等指令自己找事做）
- 工作记忆（跨session连续性）

**行动准则**：先补最高价值的短板，不要均衡用力。用「自评→行动→验证→汇报」闭环代替「问用户该做什么」。

## 参考资料

- [Cron Jobs 配置](./references/cron-jobs-config.md) — job_id、schedule、编辑注意事项
- [Matt Pocock Skills + EvoMap 参考](./references/mattpocock-evomap.md) — 83k star工程技能库 + GEP演进协议详解
