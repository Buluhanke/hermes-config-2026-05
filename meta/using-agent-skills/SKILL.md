---
name: using-agent-skills
description: 技能导航 — 根据任务类型推荐合适的Hermes技能，实现工作流程自动化。
triggers:
  - "不知道该用哪个skill"
  - "遇到新类型的任务"
  - "需要组合多个skill完成复杂任务"
  - "想确认是否有更合适的skill可用"
  - "某个skill不work，想找替代方案"
  - "熟记这些技能"  # 新增：用户要求主动学习技能
  - "我们安装的与实际使用的相差很大"  # 新增：用户指出差距
---

# Using Agent Skills

## Overview

Hermes拥有185+技能，覆盖不同任务类型。本skill帮助你快速定位最合适的技能组合，避免在错误的方向上浪费时间。

## ⚠️ Active Skill Learning（主动学习原则）

**用户期望**：你不是"技能导航员"，而是"技能学习者"。当用户说"熟记这些技能"或提供文档链接时，你需要：

1. **深度理解**：不只是浏览 SKILL.md，要逐字阅读、理解每个技能的核心逻辑、触发条件、使用场景
2. **阅读完整文档**：包括 user-stories、所有子页面、参考文档
3. **理解差距**：对比"已安装的技能"和"实际使用的技能"，找出未充分利用的技能
4. **主动应用**：学习后立即在任务中应用相关技能，验证理解是否正确

**学习信号**：
- 用户说"熟记这些技能" + 文档链接
- 用户说"我们安装的与实际使用的相差很大"
- 用户说"读一遍所有内容，包括每一页"

**学习流程**：
```
收到学习请求
├── 1. 识别文档来源（skills 列表 / user-stories）
├── 2. 逐页阅读（不跳过任何页面）
├── 3. 提取关键信息（核心能力、触发条件、使用场景）
├── 4. 对比已安装技能（找出差距）
└── 5. 在任务中应用（验证理解）
```

**示例**：
- 用户说"研究 Agent Reach 和 ClawRouter"：
  - 先阅读官方文档（install.md、README.md）
  - 理解每个工具的核心能力、安装方式、使用场景
  - 对比当前 Hermes 架构（web_search、skills）
  - 给出"是否需要安装"的明确建议
  - 在后续任务中尝试调用（如用 curl 测试 API）

## Skill分类全景图

### 🔵 采购与供应链（Procurement）
| 任务 | 推荐Skill |
|------|----------|
| 规格不清晰，需要先定义需求 | spec-driven-sourcing |
| 1688搜索商品、比价、找供应商 | 1688-sourcing |
| 1688官方API数据获取 | 1688-open-platform-api |

### 🟢 工程流程（Engineering Workflow）
| 任务 | 推荐Skill |
|------|----------|
| 任务模糊，不知道从哪里开始 | idea-refine, planning-and-taYOUR_API_KEY |
| 大任务需要分解 | planning-and-taYOUR_API_KEY, incremental-implementation |
| 遇到错误，不知道根因 | debugging-and-error-recovery |
| 代码评审 | code-review-and-quality |
| 新功能/重构上线 | shipping-and-launch |
| Git协作 | git-workflow-and-versioning |
| API设计 | api-design |
| 安全问题 | security-hardening |
| 性能问题 | performance-optimization |
| 需要验证/测试 | test-driven-development |
| 上下文丢失或混乱 | context-engineering |

### 🟡 平台集成（Platform Integration）
| 任务 | 推荐Skill |
|------|----------|
| GitHub协作 | github-pr-workflow, github-code-review |
| Apple生态（iMessage/提醒等）| imessage, apple-reminders, findmy |
| 邮件 | himalaya |
| Notion | notion |
| Airtable | airtable |
| Spotify | spotify |
| YouTube内容 | youtube-content |

### 🔴 浏览器与桌面自动化
| 任务 | 推荐Skill |
|------|----------|
| 需要操作浏览器（登录态重要）| hermes-rpa（用已有Chrome）|
| 通用浏览器自动化 | browser-use |
| 截图+OCR+键盘鼠标操控 | desktop-control |
| 需要视觉理解页面 | vision + hermes-rpa |

### 🟣 代码开发（Code Development）
| 任务 | 推荐Skill |
|------|----------|
| 写代码让AI代劳 | claude-code, codex, opencode |
| Python数据分析 | data-analyzer, jupyter-live-kernel |
| Jupyter交互计算 | jupyter-live-kernel |
| 代码检查 | codebase-inspection |
| 调试 | python-debugpy, systematic-debugging |

### ⚪ 媒体与内容
| 任务 | 推荐Skill |
|------|----------|
| 文字转语音 | tts, moss-tts-nano |
| 图片处理 | Vision — Image Processing, Resize, Convert & Watermark |
| 音乐生成 | audiocraft-audio-generation |
| PPT制作 | powerpoint |

### 🟠 MLOps与模型
| 任务 | 推荐Skill |
|------|----------|
| 本地模型推理 | vllm |
| 模型微调 | unsloth, fine-tuning-with-trl |
| 模型评测 | evaluating-llms-harness |
| 图像分割 | segment-anything-model |

## 复杂任务的技能组合

### 场景1: 1688采购完整流程
```
spec-driven-sourcing → 1688-sourcing → hermes-rpa → data-analyzer
    （定义规格）     （搜索比价）    （提取数据）  （整理结果）
```

### 场景2: 新功能开发
```
idea-refine → planning-and-taYOUR_API_KEY → test-driven-development → code-review-and-quality → shipping-and-launch
  （澄清需求）       （任务分解）          （TDD开发）             （代码评审）              （发布）
```

### 场景3: 调试线上问题
```
debugging-and-error-recovery → context-engineering → security-hardening（如果涉及安全）
    （根因分析）         （整理上下文）        （修复后检查）
```

### 场景4: 浏览器操作（需要已登录状态）
```
hermes-rpa（复用已有Chrome）→ vision（如果需要理解页面）
```

### 场景5: 代码审查+安全检查
```
code-review-and-quality → security-hardening → git-workflow-and-versioning
```

## Skill选择决策树

```
任务类型？
├── 采购/供应链
│   ├── 规格不清晰 → spec-driven-sourcing
│   └── 规格清晰 → 1688-sourcing / 1688-open-platform-api
│
├── 工程开发
│   ├── 任务规划 → idea-refine → planning-and-taYOUR_API_KEY
│   ├── 编码实现 → claude-code / codex / opencode
│   ├── 调试错误 → debugging-and-error-recovery
│   ├── 代码评审 → code-review-and-quality
│   ├── 测试 → test-driven-development
│   └── 部署发布 → shipping-and-launch
│
├── 自动化操作
│   ├── 浏览器（需登录） → hermes-rpa
│   ├── 浏览器（无需登录） → browser-use
│   ├── 桌面GUI → desktop-control / macos-computer-use
│   └── 跨平台 → hermes-rpa
│
├── 数据分析
│   ├── 数据处理 → data-analyzer
│   ├── Jupyter → jupyter-live-kernel
│   └── AI模型 → vllm / unsloth / fine-tuning-with-trl
│
└── 平台集成
    ├── GitHub → github-pr-workflow
    ├── Apple生态 → imessage / apple-reminders
    ├── 邮件 → himalaya
    └── 文档 → notion / obsidian
```

## 常见错误

| 错误 | 后果 | 正确做法 |
|------|------|---------|
| 用browser-use操作需要登录的1688 | 每次都是新会话，无法保留登录态 | 用hermes-rpa连接已有Chrome |
| 遇到错误直接尝试修复 | 浪费时间在症状而非根因 | 先用debugging-and-error-recovery |
| 大任务不分解直接开始 | 容易迷失方向，返工多 | 先planning-and-taYOUR_API_KEY |
| 用1688-sourcing搜索时规格不清晰 | 搜索结果不符合需求 | 先spec-driven-sourcing |
| 读了技能文档但从未在任务中使用 | 理解停留在表面 | 学习后立即在任务中应用 |

## Verification

验证清单：

- [ ] 任务已正确分类
- [ ] 选择了最适合的skill
- [ ] 确认该skill的triggers匹配当前情况
- [ ] 多个任务时已规划skill调用顺序
- [ ] 确认没有更专门的skill可用

## 支持文件

- [Agent Reach 和 ClawRouter 研究报告](./references/agent-reach-clawrouter-research.md) — 2026-05-28 对比评估两个工具的安装必要性和优势
- [搜索降级方案](./references/search-fallback.md) — 当 web_search 不可用时的 ddgs 降级流程
- [网络与代理诊断](./references/network-proxy-debugging.md) — 代理故障排查，HN/HN Firebase/github 分项检测
- [HN Firebase API 用法](./references/hn-firebase-api-usage.md) —HN 数据获取的正确 Python 脚本模式（cron 环境必备）
- [Cron 脚本执行限制](./references/cron-script-execution.md) — python3 -c/heredoc 在 cron 环境被拦截的 workaround
- [马拉松脚本](./scripts/idle-marathon.sh) — 马拉松学习模式脚本（用户指令触发，持续到指定时间）
- [马拉松核心引擎](./scripts/idle-marathon-core.sh) — 后台实际执行版，每30分钟循环
