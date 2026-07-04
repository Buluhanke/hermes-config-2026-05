# Cocoloop Hub 调研笔记 (2026-06-30)

## 平台快照

- **官网**: https://www.cocoloop.cn/
- **Skill 商店**: https://hub.cocoloop.cn/
- **定位**: OpenClaw 生态核心, 国内"安全 + 精品" Skills 市场
- **数字**: 12,920 Skills / 50+ 平台 / CLS 安全认证体系
- **关联产品**: Molili (技能安装客户端) / pixpix.com (AI 生图) / apkclaw.ai (Android 包)
- **竞品**: Anthropic Skills (150.6k) / LibreChat Skills

## Top 10 头部 Skills (按热度排序)

| # | Skill 名 | 用途 | 热度 | 借鉴度 |
|---|---|---|---|---|
| 🥇 | tavily-search-pro | AI 全能搜索研究 | 12.8k | 🟡 中 (可换 OpenAI Web Search) |
| 🥈 | capability-evolver | Agent 自主进化引擎 | 7.9k | 🔴 高 (与 Hermes self-improvement 同主题) |
| 🥉 | agent-overflow | Agent 集体记忆 + 协作 | 6.3k | 🟠 实验性, 看看思路 |
| 4 | summarize | 多模态智能摘要 | 9.6k | ⚪ Hermes 已有 summarize tool |
| 5 | docker-sandbox | VM 级隔离代码执行 | **18.7k (顶部)** | ❌ **永久禁区** (用户 2026-06-30 拒绝 docker) |
| 6 | agent-browser | AI 原生浏览器自动化 | 13.9k | 🟡 (vs Playwright / CDP / browser-use skill) |
| 7 | self-improvement | AI 持续进化 + 知识沉淀 | 8k | 🟠 同 Hermes SOUL 9 进化循环 |
| 10 | wacli | WhatsApp CLI | 15.5k | ⚪ 不适用 Hermes |

## 热门趋势 (读头部 50 个 Skill 提炼)

1. **Self-Improving Agent 系列占头部** — 5 个变种 (Self-Improving Agent / self-improving-agent / Proactive Agent / Self-Improving + Proactive / Skill Vetter) 全部使用 WAL (Write-Ahead Log) 协议记录错误, 跟 Hermes 的 `fact_store` 是同一思路但更结构化
2. **Proactive Agent 排名第一的子类别** — "WAL protocol + work-buffer + scheduled tasks + persistent memory". Hermes 已经在 `proactive-execution` skill 走这套, 但没用 WAL, 可借鉴
3. **Multi Search Engine (16 引擎聚合)** — 7 国内 + 9 国际, 零 API 密钥, 隐私优先. 可作 `web-content-pipeline` 升级参考
4. **API Gateway (Maton 官方)** — 150+ 应用统一接入. 这个跟 Hermes 的 fallback chain 思路不一样, 但 ASR 认证层可借鉴
5. **docker-sandbox 18.7k 热度** = 用户原话驱动的反向验证: 别人在拼命做"沙箱化执行", Hermes 永远不做. 这是 Hermes 的**差异化定位**, 不是劣势

## Hermes 板块 (重要发现)

社区有 "🪼 Hermes Agent" 专门分类 (板块缩写 🦧), 关联帖子:
- "最近在折腾 Hermes, 升级到最新版本后发邮件总报错" — 788 浏览, 1 回复
- 建议下次做 `hermes-proactive-check` 时去 /Hermes-Agent 板块扫一眼用户求助

## 已学到的 5 个高价值经验

1. **WAL 协议 (Write-Ahead Log)** — Agent 每次决策前先写结构化日志, 错误/教训永久入库. 比 Hermes 当前 `fact_store` 更严格. **状态**: 待验证 → 写一个 prototype
2. **0-thinking 决策清单** — Skill 商店顶部都贴"快速安装 3 步"截图, 与 Hermes `proactive-execution` 思路一致
3. **CLS 安全认证分级** — 头部 Skill 都带 S+/S/A 标签, 表示经过审计. Hermes 装第三方 skill 时缺这道关. **Action**: 给 Hermes skill 加审核清单
4. **docker-sandbox 反向验证** — 别人做容器基座是因为想 AI 跑任意代码, Hermes 用户拒绝 = Hermes 定位是"个人数字秘书"而非"代码沙箱", 这是产品定位优势不是劣势
5. **"先装再清" 工作流** — 用户原话: "单一工作流". 装 / 试 / 卸是连贯动作, 不互相冲突

## 可借鉴到 Hermes 的具体动作 (按 ROI 排序)

| ROI | 动作 | 工作量 | 优先级 |
|---|---|---|---|
| 🟢 高 | 写 `hermes_skill_vetter` skill — 装前安全审计 | 半天 | P0 |
| 🟢 高 | 给 Hermes skill 库加 CLS 等级标签 | 2h | P1 |
| 🟡 中 | 研究 WAL 协议, 升级 fact_store 写入路径 | 1 天 | P2 |
| 🟡 中 | 借鉴 OpenAI Codex Claude 玩法汇总的"使用手册集合帖"模式 | 半天 | P2 |
| 🔴 低 | fork Molili 安装客户端 (与 Hermes 路径冲突) | 不做 | -- |

## 不借鉴的清单

- ❌ docker-sandbox (绝对禁区)
- ❌ OpenClaw 龙虾产品本身 (Hermes 是 OpenClaw 竞品定位)
- ❌ Molili 安装客户端 (Hermes 不需要独立安装器)

## 用户相关偏好

- 用户在 Cocoloop 社区对 "Hermes Agent 升级到最新版本后发邮件总报错" 这类帖子有共鸣 — 后续可设 cron 每 3 天扫一次社区 Hermes 板块
- Cocoloop 整体用户群对 Hermes 比 LibreChat 友好 (有专门板块, 不是无人区), 适合作为 Hermes 反馈渠道之一
