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

### 第二层：深度学习（每天凌晨2点，满血跑）
- cronjob `0 2 * * *` 触发
- **必须走全网搜索**，不依赖模型知识
- **搜索方向（锚定真人化路线）**：
  - 屏幕感知突破（最优先）：screen understanding AI agent / desktop computer use / visual grounding
  - 验证码对抗：CAPTCHA bypass / anti-detection / browser fingerprint
  - 类人操作节奏：humanization browser automation / behavioral simulation
  - 1688采购闭环：1688 API / procurement automation
- **直接对话浏览器AI**：打开ChatGPT/Claude讨论（仅第二层）
  - "桌面AI Agent目前最强的屏幕感知方案是什么？"
  - "如何让AI操作浏览器看起来像真人？"
  - "AI采购 Agent最难的环节是什么？"
- **结合已有技能综合思考**：1688自动化 / CDP深度控制 / MCP工具生态 / 浏览器持久化
  - 现有能力 + 新发现 = 什么新可能性？
- 评估能否缝进Hermes，存入 ~/Vision_Lab/ 和 ~/Brain_Lab/
- 存疑：搜索和对话都找不到答案的 → 标记需用户确认

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

- ~/Vision_Lab/ — 工具/技能方向发现
- ~/Brain_Lab/ — 思路/方法论方向发现

## 判断标准：能否缝进Hermes（按真人化优先级）

1. 屏幕全域感知（95%差距）→ 最高优先
2. 验证码对抗（100%差距）
3. 类人操作节奏（80%差距）
4. 移动端操控（100%差距）
5. 多步骤业务闭环（50%差距）

## 已知局限

- 模型知识有天花板，必须全网搜索验证
- 国内网络需代理：Shadowrocket 127.0.0.1:1082
- 任务 prompt 要精简，避免超 context limit（MiniMax 8K tokens）。实测：prompt 超过约 19K tokens（~7000中文）会被 OpenRouter 拦截并报 402
- cron job prompt 需要定期检查精简，新发现不要直接追加，先问"这次发现值不值得增加 prompt 长度"
- Mac mini M4 无 NVIDIA GPU，无法运行需要 CUDA 的工具（如 Chandra OCR 2，需要 4GB+ 显存）

## 参考资料

- [Cron Jobs 配置](./references/cron-jobs-config.md) — job_id、schedule、编辑注意事项
- [Matt Pocock Skills + EvoMap 参考](./references/mattpocock-evomap.md) — 83k star工程技能库 + GEP演进协议详解
