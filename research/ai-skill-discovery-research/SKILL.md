---
name: ai-skill-discovery-research
description: "研究 / 借鉴 任意 AI / Agent / Skill 生态平台 (Cocoloop Hub, Anthropic Skills, GPTStore, Coze, Dify, MCP Servers, OpenAI GPTs, Anthropic Claude Plugins 等). 用户给 URL 或者说『研究这个 / 看看 X 平台 / 有什么借鉴价值』时加载. 覆盖『先了解再装』三阶段: 评估 (依赖/内存/许可证)、方案 A/B/C 呈现、装/跑/卸闭环. 与 `self-hosted-ai-service-install` 互补 (那个是『装起来跑』, 这个是『挑哪些值得装』)."
when_to_use: "用户说『研究 X / 帮我看看这个平台 / 有啥 Skills / 借鉴这个生态 / 给个 GitHub URL 让你分析 / 找类似 X 的工具』. 也用于『空闲巡检』(配合 `idle-learning-rounds` cron)"
---

# AI 技能 / Agent 生态平台调研 (Discovery & Adoption Research)

**核心原则**: Hermes 不能『先 clone 再装再装依赖最后发现不值得装』. 先调研 → 评估 → 报告 → 让用户拍板 → 才动手. 这与 `self-hosted-ai-service-install` 的『装了再说』互补 — 那个是评估完了动手, 这个是评估本身.

## 三阶段工作流（必走）

### 阶段 1: 信息获取 (5 分钟内)

**并行抓**:
```bash
# 1. 主页: 产品定位/核心功能/竞争差异
# 2. 文档/About 页: 技术栈/依赖/部署要求
# 3. GitHub repo: README/LICENSE/Dependencies
#    (有 GitHub URL 时)
```

**工具选择** (按顺序, 先快的):
- `web_search` → 平台名 + "what is / alternative / review 2026" 找综述
- `web_extract` (Trafilatura) → 主页 + 文档页 markdown
- `browser_navigate` → 只有 SPA 渲染或登录后内容才用

**必看清单 (5 项)**:
1. **产品定位**: 解决谁的问题? vs 现有方案有何区别?
2. **依赖清单**: 需要 MongoDB/Postgres/Redis? 需要 Docker? 需要 GPU?
3. **资源代价**: idle 多少内存? 跑满多少? (看他们 GitHub issue 或官方文档)
4. **许可证**: MIT/Apache/AGPL/SSPL? (用户原话可能要商用)
5. **技能/Skill 数量与质量**: 有没有 5k+ Skills 之类指标? 头部技能是什么?

### 阶段 2: 评估与方案 A/B/C (硬性要求)

**永远先输出**:
- 一句话定位 (用户能复用, 不啰嗦)
- 借鉴价值 1-3 条 (架构 / 前端 / 代码审计 三档分级)
- **方案 A / B / C 决策表** (用户原话: 『做了就回不去的选择要带方案』)
- 不要的事 (无依赖, 跳过; 浪费资源, 不装; 不适用, 不学)

**绝不**:
- ❌ 不列具体方案数让用户选 (除非用户原话明确让给选项)
- ❌ 不自动 clone / 装 (用户没说『立即执行』就停在这一步)
- ❌ 不直接列『装这个』, 必须先讲清价值/代价

### 阶段 3: 装/跑/卸闭环 (用户拍板后)

用户说『立即执行』后才进这一阶段, 走 `self-hosted-ai-service-install` skill. **本 skill 只到阶段 2**.

⚠️ **特殊检查清单** (Hermes 24GB 资源约束):
- 容器类 → **绝对拒绝** (用户 2026-06-30 明确禁令, 见 `hermes-runtime-fortress` 四·禁)
- 装新 Skill → 看是否需要装额外依赖 (`pip install` / `npm i`)
- 内存增量 > 500MB → 必须告诉用户再决定
- macOS 自家替代方案优先 (Apple Container over Docker)

## 报告模板 (用户拍板前用)

```markdown
## [平台名] 快速总结

**官网**: URL
**定位**: 一句话
**依赖**: MongoDB / Postgres / Redis / GPU / Docker / 零依赖
**许可证**: MIT / Apache / AGPL
**关键数字**: 13K+ Skills / 50+ 平台 / 头部技能 18.7k 热度

## 对 Hermes 直接相关的发现
1. ⭐ [最相关的 3-5 条]
2. [可有可无的借鉴点]

## 🎯 可执行选项
A. [选项 1: 最小代价, 高 ROI] (推荐 + 理由)
B. [选项 2: 中代价, 学习用]
C. [选项 3: 不装, 只读源码]
D. [不调研, 关闭任务]
```

## 触发词清单 (0 思考加载)

- "研究 X / 看看 X 平台 / 调研 X"
- "有啥 Skills 借鉴"
- "GitHub URL: [some URL] 看看"
- "Cocoloop / Anthropic Skills / Coze / Dify / GPTStore / MCP server 目录"
- "X MCP 接入很简单" 类一句话引入 (用户说『简单』= 0 思考进入研究模式)
- "这个有啥作用 / 借鉴价值" (用户已经研究完, 进入方案选择)

## 已研究案例 (作为 reference 积累)

- **Cocoloop (cocoloop.cn / hub.cocoloop.cn)** — 2026-06-30 — `references/cocoloop-hub-research-2026-06-30.md`
- **LibreChat (LibreChat/LibreChat)** — 2026-06-30 — 走 `self-hosted-ai-service-install` 已跑通
- **Claude Code (anthropics/skills, anthropics/claude-code)** — 2026-06-30 — 借鉴 Agent SDK 架构 + MCP 集成

## 关联 skill

- `self-hosted-ai-service-install` — 评估完后真的装走这个
- `hermes-runtime-fortress` — 24GB 资源约束 / 容器禁区
- `idle-learning-rounds` — cron 自动跑多方向调研
- `verification-before-reporting` — 调研结论也要带 link 证据

## Pitfall — 用户问『这有啥作用』时怎么答

**反例** (违规):
> "这是 OpenClaw 生态的技能商店"
> 说完不解释对 Hermes 的价值 → 用户得再问一轮

**正例**:
> "对 Hermes **当前核心能力没有直接提升**, 但有 3 个可借鉴价值: 1) 架构参考 (高) 2) 前端复用 (中) 3) 代码审计 (低). 然后给选项 A/B/C"

**铁律**: 用户给平台/URL 让研究, 0 思考不只产出『这是个什么』, 必带『对 Hermes 有啥用 / 借鉴啥 / 不借鉴啥』三段.

## Pitfall — 用户说『装一下试试』≠『一直用』

**用户工作流偏好** (2026-06-30): "先装再清" 是单一工作流, 不是两件事. 用户会说『装 X 试试』然后『不搞了, 清除掉』. 装之前必看:
- 装路径是否独立 (`/tmp/xxx` 而非 `/Users/aimac/Projects/`) — 卸载好卸
- 是否依赖系统包 (`brew install`) — 卸残留会多 2 步
- 是否注册 launchd / systemd 服务 — 自动启动会留 plist

→ 走 `self-hosted-ai-service-install` 的 clean uninstall checklist.

## Pitfall — 不要把『列表呈现』当『研究完毕』

**反例** (嘴炮): 抓 10 个 skill 名字 + 排名 + 链接 → 用户问『so what』

**正例**: 给用户**他自己能用的**结论 + 行动. Hermes 借鉴 LibreChat 不是为了部署 LibreChat, 是为了**先 clone 可看代码, 用到具体模块时再去 deep-dive**. 跑通后用户原话『那我跑通了怎么用』 → 答: "需要拆点啥直接说, 默认不动."
