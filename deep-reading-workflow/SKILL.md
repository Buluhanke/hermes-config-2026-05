---
name: deep-reading-workflow
version: 0.1
description: "深度阅读 书论文长文消化 Adler结构Feynman输出知识网络。Use when 深度啃一本书一篇论文并内化"
triggers:
  - "深度阅读"
  - "消化论文"
  - "构建知识网络"
  - "卢曼笔记"
  - "深度消化"
  - "结构笔记"
trigger_type: knowledge_management
tags: [knowledge-management, note-taking, deep-learning, zettelkasten, luhmann]
created: 2026-07-25
来源: clawhub/deep-learning skill + Hermes 本地化
---

# Deep Reading Workflow — 深度阅读工作流

## 工作流概览

```
Phase 0: 执行计划（≥6 [TODO] + Context）
  ↓
Phase 1: 结构笔记（Mortimer Adler — 核心命题 + 逻辑链）
  ↓
Phase 2: 索引笔记（Niklas Luhmann — 关键词 + 多入口）
  ↓
Phase 2.5: 索引入网（挂载到已存在索引 + 移动到 03_索引/）
  ↓
Phase 3: 原子笔记递归生长（Luhmann + Feynman — 边创建边发现）
  ↓
Phase 4: 方法论整理（Pragmatist — SOP/模板/检查清单）
  ↓
Phase 5: 终极审查（Feynman — 去魅/比喻/逻辑/拓扑）
  ↓
Phase 6: 入网审查（Luhmann — 双向链接 + 索引接入）
  ↓
Phase 6.5: 流程执行审查（强制）
```

## 存储位置

```
~/.hermes/deep-reading/YYYY-MM-DD_[主题]/
├── 01_[主题]_执行计划.md
├── structure_note.md      # Phase 1
├── index_note.md          # Phase 2
├── atomic_*.md            # Phase 3（多文件）
├── method_*.md            # Phase 4
├── review.md              # Phase 5
├── network_review.md      # Phase 6
└── audit_report.md        # Phase 6.5
```

## 质量标准

- **案例保真**: 有原文必须保留具体数字/作者/时间线；无原文标注来源限制
- **无模糊词**: 禁止"优化"/"加强"/"适当"，必须具体动作或量化指标
- **元数据强制**: 所有笔记必须含 YAML frontmatter (type, tags, links)
- **双向链接**: 每张笔记 ≥2 条双向链接

## 验证命令

```bash
# 验证文件结构
find ~/.hermes/deep-reading/$(date +%Y-%m-%d)* -name "*.md" | wc -l
# 应 ≥ 4（结构+索引+原子+方法）
```
