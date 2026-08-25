---
name: skill-router
version: 1.0.0
description: "技能路由 总索引 找能力先查这里再动手。MUST USE when 任务可能已有对应skill但不确定名字——禁止凭'没有这能力'直接回答"
triggers:
  - 有没有技能/skill能做X
  - 怎么做X（任何任务开始前）
  - 我记得有个技能…
---

# Skill Router — 免记忆调用层

## 铁律

1. **回答"做不到/没有这功能"之前，必须先查这张表或跑 `skills_list()`。**
2. 找到候选 → `skill_view(name='<name>')` 加载全文再执行。
3. 表里没有 → `hermes skills search <关键词>` 搜 Hub，仍无才允许说"需要新方案"。
4. 用户也可随时 `/skill-name` 直调；连打多个如 `/pdf /xlsx 提取表格到Excel`。

## 路由表（领域 → 技能名）

| 领域 | 关键词线索 | 技能 |
|---|---|---|
| 文档办公 | Word Excel PPT PDF | docx · xlsx · powerpoint · pdf · minimax-docx/pdf/xlsx · nano-pdf |
| 邮件日历 | Gmail 收发件 日历 | himalaya · email-inbox-triage · google-workspace · apple-reminders · apple-notes |
| GitHub 全流程 | PR issue review CI | github-pr-workflow · github-issues · github-code-review · github-issue-to-pr · github-auth · github-repo-management |
| 编码委派 | 让别的AI写码 | claude-code · codex · opencode · merge-reconciler · simplify-code |
| 调试排障 | bug 报错 根因 | systematic-debugging · debugging-and-error-recovery · error-patterns · python-debugpy · node-inspect-debugger |
| 浏览器自动化 | 抓网页 登录态 反爬 | chrome-cdp-control · browser-cdp-control · osascript-chrome-js · scrapling · camofox · browser-read-funnel · zero-shot-web-read · hermes-browser-local-login |
| 桌面控制(GUI) | 点界面 操作app 截图 | computer-use · pi-computer-use · perception-decision-engine · action-validator · resilience-engine · cua-browser-control |
| 安卓手机 | 投屏 scrcpy root | android-control · android-lamda · android-root · desktop/android-remote-control |
| 1688/电商 | 找货 比价 价格监控 | 1688-sourcing · 1688-search-cn-gb-region-skill · 1688-price-extraction · 1688-cdp-product-fetch · 1688-matrix-dimension-sourcing · product-price-monitor |
| 记忆系统 | 记不住 检索 瘦身 | memory-cn · mempalace · memory-housekeeping · honcho · qmd |
| 自学进化 | 自动学习 fact_store | idle-learning-b-engine · idle-learning-deep-dive · idle-learning-deepening · community-learning · self-learning-methodology · abcd-learner |
| Hermes 运维 | gateway 模型 provider 配置 | hermes-agent(总入口) · gateway-restart-technique · hermes-desktop-restart · hermes-model-health · hermes-model-switching · hermes-provider-debugging/routing · hermes-config-tricks · hermes-observability · cron-job-reliability · self-maintenance |
| 技能库本身 | 装/升/写技能 | hermes-skills-management · writing-skills · writing-great-skills · skill-creator · skill-portable-packaging |
| 多智能体 | 并行 分工 子代理 | delegate_task工具 · dispatching-parallel-agents · subagent-driven-development · pacore-delegate-pattern |
| ML/本地模型 | 训练 微调 推理服务 | axolotl · keras/deep-learning · serving-llms-vllm · llama-cpp · huggingface-hub · ollama · weights-and-biases · memray-memory-profiler |
| 媒体生成 | 出图 出视频 音乐 | comfyui · audiocraft-audio-generation · heartmula · manim-video · ascii-video · songwriting-and-ai-music · baoyu-infographic |
| 设计/前端 | 落地页 UI 图表 | claude-design · popular-web-designs · sketch · p5js · excalidraw · architecture-diagram · design-md · pretext |
| 研究搜索 | 调研 论文 监控新闻 | deep-research · web-search-default/enhanced · anysearch · agent-reach · arxiv · litreview · dossier · pulse · competitor-news-monitor · blogwatcher · youtube-content |
| 数据库 | SQL 连接 导出 | database-client · chroma(RAG向量) |
| 笔记知识库 | Obsidian 思源 Notion | obsidian · siyuan · notion · llm-wiki · box · airtable |
| Apple 生态 | 备忘录 提醒 iMessage 定位 | apple-notes · apple-reminders · imessage · findmy · macos-file-sharing · macos-network-sharing |
| 密码安全 | 密码 API key 注入 | bitwarden-cli · 1password(-cli-agents) · secrets-management |
| 社交通道 | 推特 Telegram 群组 | xurl · social-media/xurl · yuanbao · gif-search |
| 金融建模 | 估值 三表 预测市场 | dcf-model · 3-statement-model · polymarket |
| 方法论 | 计划 重构 TDD 架构 | plan · planning-and-task-breakdown · spec-driven-development · test-driven-development · refactoring-patterns · improve-codebase-architecture · using-git-worktrees · weekly-review-planning · executing-plans |
| 输出规范 | 回答风格 去AI味 | i-have-adhd · output-style · humanizer · avoid-ai-writing · anti-counter-question · evidence-loop · handoff · progress-sync |
| 网络/系统 | 局域网 Docker 监控 | network-discovery · docker-management · prometheus-monitoring · mac-maintenance · terminal-backend-guide |

## 快速通道

```bash
skills_list()                        # 全量 name+description
skill_view(name='xxx')               # 载入全文执行
hermes skills search <关键词>        # Hub 上找新的
```
