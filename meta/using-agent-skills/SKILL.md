---
name: using-agent-skills
description: 技能导航 — 根据任务类型推荐合适的Hermes技能，实现工作流程自动化。
triggers:
  - "不知道该用哪个skill"
  - "遇到新类型的任务"
  - "需要组合多个skill完成复杂任务"
  - "想确认是否有更合适的skill可用"
  - "某个skill不work，想找替代方案"
version: 1.0.0
---

# Using Agent Skills

## Overview

Hermes拥有74+技能，覆盖不同任务类型。本skill帮助你快速定位最合适的技能组合，避免在错误的方向上浪费时间。

## Skill分类全景图

### 🔵 采购与供应链（Procurement）
| 任务 | 推荐Skill |
|------|----------|
| 规格不清晰，需要先定义需求 | spec-driven-sourcing |
| 1688搜索商品、比价、找供应商 | pro-buyer |
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
| 通用浏览器自动化 | browser-use（独立skill）|
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
| 图片处理 | vision-image-processing |
| 音乐生成 | audiocraft-audio-generation |
| PPT制作 | powerpoint |

### 🟠 MLOps与模型
| 任务 | 推荐Skill |
|------|----------|
| 本地模型推理 | vllm |
| 模型微调 | unsloth, trl-fine-tuning |
| 模型评测 | lm-evaluation-harness |
| 图像分割 | segment-anything |

## 复杂任务的技能组合

### 场景1: 1688采购完整流程
```
spec-driven-sourcing → pro-buyer → hermes-rpa → data-analyzer
    （定义规格）   （搜索比价）  （提取数据）  （整理结果）
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
│   └── 规格清晰 → pro-buyer / 1688-open-platform-api
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
│   ├── 浏览器（无需登录） → browser-use（独立skill）|
│   ├── 桌面GUI → desktop-control / macos-computer-use
│   └── 跨平台 → hermes-rpa
│
├── 数据分析
│   ├── 数据处理 → data-analyzer
│   ├── Jupyter → jupyter-live-kernel
│   └── AI模型 → vllm / unsloth / trl-fine-tuning
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
| 用pro-buyer搜索时规格不清晰 | 搜索结果不符合需求 | 先spec-driven-sourcing |

## Verification

验证清单：

- [ ] 任务已正确分类
- [ ] 选择了最适合的skill
- [ ] 确认该skill的triggers匹配当前情况
- [ ] 多个任务时已规划skill调用顺序
- [ ] 确认没有更专门的skill可用
