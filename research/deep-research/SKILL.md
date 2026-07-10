---
name: deep-research
description: 多引擎深度研究skill，走完Search→Extract→Verify→Report完整闭环
trigger: 深度研究|详细调研|多引擎搜索|深入分析
---

# Deep Research Skill

## 触发词
「深度研究」「详细调研」「多引擎搜索」「深入分析」

## 执行流程

### 步骤 1：分解任务
把查询分解为 3 个维度：
- 官方/一手信息（官网、官方博客）
- 行业分析（评测、对比文章）
- 社区讨论（Reddit、Twitter、GitHub）

### 步骤 2：多引擎并行搜索
```bash
web_search_plus query="关键词1" provider=serper
web_search_plus query="关键词2" provider=tavily  
web_search_plus query="关键词3" provider=exa
```

### 步骤 3：提取关键页面内容
```bash
web_extract_plus urls=["url1","url2","url3"] provider=firecrawl
```

### 步骤 4：AI 引擎交叉验证
- DeepSeek → browser_navigate + 对话验证
- Kimi → browser_navigate + 对话验证
- 同一问题多引擎回答，对比差异

### 步骤 5：输出结构化报告
```
## 研究主题
## 核心发现（3条）
## 各引擎观点对比
## 可信度评估
## 下一步行动建议
```

## 已验证的工具
- `web_search_plus` — 多引擎聚合搜索 ✅
- `web_extract_plus` — 页面内容提取 ✅
- Tesseract OCR — 企业微信表格/无法抓取的页面 ✅
- Chrome CDP → browser_navigate → browser_snapshot — AI 网站对话验证 ✅

## 坑点记录
- 企业微信表格：canvas渲染，AX树读不到 → 用 Tesseract OCR
- vision_analyze 不支持 file:// URL → 用 browser_vision 或 Tesseract
- API key 脚本直调会失败 → 走 Hermes agent 层而不是直接 curl

## 研究成果存档
- [远程控制技能调研（remote-control-skills-research）](references/remote-control-skills-research.md) — 2026-07-11：vnc-computer-use、agent-rdp、QuickDesk 等方案的对比与选型
