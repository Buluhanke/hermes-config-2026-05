# Hermes Skills 快速索引（2026-07-16 最终版）

> 所有 72 个技能均在 `~/.hermes/skills/<name>/SKILL.md`，depth=1，一眼可检索。

## 一、核心工作流（高频使用）

| Skill | 触发词 | 功能 |
|--------|--------|------|
| `abcd-learner` | 知识落地/升华/idle-learning E阶段 | fact→skill升华 |
| `anysearch` | 垂直搜索/金融/学术/安全情报/批量 | 23个垂直领域+通用搜索 |
| `agent-reach` | 调研/全网搜索/各平台内容 | 13平台内容获取 |
| `deep-research` | 深度调研/战略研究 | 多引擎9阶段研究闭环 |
| `product-research` | 产品调研/比价/推荐 | 价格验证+平替规则 |

## 二、浏览器/桌面自动化

| Skill | 触发词 | 功能 |
|--------|--------|------|
| `browser-cdp-control` | 浏览器CDP/DOM/截图/表单 | Chrome DevTools Protocol |
| `browser-use` | 浏览器自动化/表单/数据提取 | browser-use CLI |
| `computer-use` | 桌面控制/点击/输入/scroll | cua-driver后台操作 |
| `agent-rdp` | 远程控制Windows/RDP | IronRDP远程控制 |

## 三、文档生成

| Skill | 触发词 | 功能 |
|--------|--------|------|
| `officecli` | Word/Excel/PPT编辑 | Office文档CLI |
| `minimax-docx` | 生成Word文档 | 专业DOCX |
| `minimax-xlsx` | 生成Excel/数据分析 | Excel读写 |
| `minimax-pdf` | 生成PDF/专业排版 | 视觉质量+品牌 |
| `ppt-generation` | 生成PPT演示文稿 | 专业PPT |

## 四、Hermes系统

| Skill | 触发词 | 功能 |
|--------|--------|------|
| `self-maintenance` | Gateway保活/内存守护/健康检查 | 自动巡逻+失败自愈 |
| `hermes-observability` | LLM可观测性/token/延迟/错误率 | SQLite traces追踪 |
| `hermes-skills-management` | 安装skill/技能管理/诊断 | Hermes Hub十大类技能 |
| `hermes-agent` | Hermes配置/扩展/开发 | 51608字节完整手册 |
| `hermes-agent-skill-authoring` | 写SKILL.md/技能创作 | 技能文件规范 |
| `skill-creator` | 创建新skill/迭代优化 | 技能开发TDD方法 |
| `skill-curation` | 审计skill库/恢复孤儿 | curator健康检查 |
| `cron-job-reliability` | cron可靠性/定时任务诊断 | 任务健康检查 |

## 五、代码质量/架构

| Skill | 触发词 | 功能 |
|--------|--------|------|
| `systematic-debugging` | 调试/根因分析/bug | 4阶段调试法 |
| `test-driven-development` | TDD/测试先行 | 红绿重构循环 |
| `clean-code` | 整洁代码/重构 | 代码可读性 |
| `refactoring-patterns` | 重构模式 | 遗留代码改造 |
| `software-design-philosophy` | 软件设计哲学 | 架构决策原则 |
| `clean-architecture` | 整洁架构 | 分层架构 |
| `system-design` | 系统设计/架构 | 分布式系统 |
| `working-with-legacy-code` | 遗留代码 | 遗留系统处理 |
| `team-topologies` | 团队拓扑/组织架构 | 团队协作模式 |

## 六、DevOps/基础设施

| Skill | 触发词 | 功能 |
|--------|--------|------|
| `github-repo-management` | GitHub仓库管理/PR | gh CLI封装 |
| `verification-before-completion` | 验证后才算完成 | 证据>声明 |
| `dispatching-parallel-agents` | 并行任务分发 | 多独立任务并行 |
| `using-git-worktrees` | git worktree隔离 | 隔离工作区 |
| `prometheus-monitoring` | Prometheus监控 | 指标采集 |
| `secrets-management` | 密钥管理/CI/CD | Vault/AWS Secrets |
| `subagent-driven-development` | 子代理驱动开发 | 计划执行 |

## 七、研究/调研

| Skill | 触发词 | 功能 |
|--------|--------|------|
| `dossier` | 尽职调查/背景调查/人/公司 | 决策级实体报告 |
| `pulse` | 近期趋势/社区讨论/Reddit/HN | 30天情报窗口 |
| `litreview` | 文献综述/PubMed/arXiv | 学术论文调研 |
| `grants` | NIH grant/科研经费 | 临床研究grant |
| `scrapling` | 网页爬取/Cloudflare绕过 | 高级爬虫 |
| `qmd` | 本地知识库搜索/RAG | 混合检索引擎 |
| `defuddle` | 干净网页内容提取 | 去广告/导航 |

## 八、写作/文案

| Skill | 触发词 | 功能 |
|--------|--------|------|
| `avoid-ai-writing` | 去AI味/去除写作痕迹 | 49模式检测+重写 |
| `write-product-spec` | PRD/产品规格文档 | PRODUCT.md规范 |
| `writing-skills` | 写skill文档 | TDD写技能方法 |

## 九、专业工具

| Skill | 触发词 | 功能 |
|--------|--------|------|
| `minimax-docx` | Word文档 | OpenXML专业生成 |
| `minimax-pdf` | PDF | 专业排版设计 |
| `minimax-xlsx` | Excel | 数据分析+公式 |
| `3-statement-model` | 财务模型(IS/BS/CF) | 三表联动 |
| `dcf-model` | DCF估值模型 | 内在价值分析 |
| `context-compression` | 上下文压缩 | 长会话优化 |
| `memory-cn` | Hermes中文记忆系统 | fact_store+Mnemosyne |
| `memray-memory-profiler` | Python内存分析 | Bloomberg Memray |

## 十、Specialty Skills

| Skill | 触发词 | 功能 |
|--------|--------|------|
| `dogfood` | QA测试/探索性测试 | web应用bug发现 |
| `obsidian` | Obsidian笔记库 | 本地笔记API |
| `siyuan` | 思源笔记API | 自托管知识库 |
| `courier-notification-skills` | 跨渠道通知 | Email/SMS/Push/Slack |
| `1password-cli-agents` | 1Password密钥管理 | agent安全密钥 |
| `executable-plans` | 执行计划 | 计划执行工作流 |
| `perception-decision-engine` | 4层感知决策漏斗 | VLM何时调/何时不调 |
| `improve-codebase-architecture` | 架构深化 | 架构改进诊断 |
| `open-source-skill-harvesting` | 开源skill采集 | GitHub→Hermes |
| `mac-maintenance` | Mac维护 | brew/Trash清理 |
| `anti-counter-question` | 反问技巧 | 避免回答陷阱 |

## 十一、错误模式（auto-generated每日生成）

| Skill | 说明 |
|--------|------|
| `error-patterns` | 错误根因分析+修复方案 |
| `auto-generated` | 每日错误模式存档，最新：error-patterns-20260716.md |

## 十二、检索优先级

```
1. 报错？ → error-patterns
2. 调研/研究？ → deep-research / dossier / pulse / anysearch
3. 文档生成？ → officecli / minimax-docx / ppt-generation
4. 浏览器自动化？ → browser-use / browser-cdp-control
5. Hermes自身？ → self-maintenance / hermes-observability / hermes-agent
6. 代码/架构？ → systematic-debugging / clean-code / system-design
7. 写作去AI味？ → avoid-ai-writing
8. 桌面控制？ → computer-use
```

## 十三、2026-07-16 整理记录

- 从.archive恢复26个有价值孤儿skill
- 删除10个空壳category目录
- 删除9个"小时工具错误聚集"重复存档
- 删除fact_store里16条重复error_pattern
- 最终：72个活跃skill，全部depth=1，全部有SKILL.md
- .archive保留116个（已归档，含占位符/旧版本/未审查）
