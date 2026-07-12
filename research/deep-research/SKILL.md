---
name: deep-research
description: 多引擎深度研究skill，走完Search→Extract→Verify→Report完整闭环
trigger: 深度研究|详细调研|多引擎搜索|深入分析
---

# Deep Research Skill

## 触发词
「深度研究」「详细调研」「多引擎搜索」「深入分析」

## 执行流程

### 步骤 1：分解任务 + 识别决策类型
把查询分解为 3 个维度：
- 官方/一手信息（官网、官方博客）
- 行业分析（评测、对比文章）
- 社区讨论（Reddit、Twitter、GitHub）

**消费类产品研究的特殊流程（2026-07-11 新增）：**
- 「性价比最高」「最推荐」「最好用」类问题 → 必须分场景回答，不能只给单一答案
- 先验证「唯一解」是否成立 → 搜索「替代品/同价位对比/平替」
- 先确认用户需求（宽带大小、是否需要2.5G、预算敏感度）再推荐，避免「最XX」陷阱
- 消费类产品的「最佳」结论依赖用户场景，泛化结论往往有误导性

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
- **过早下「性价比最高」结论**：消费类产品第一轮搜索≠最终结论，必须再搜1-2轮验证「唯一解」是否成立（R68S案例：第二轮搜索发现R2S和R66S都是有效替代方案）
- **搜索结果不完整时不能反问用户去验证**：搜到的价格数据缺斤少两，应该继续搜下一轮，而不是告诉用户"你自己去对比"。如果一轮搜索没覆盖到用户提到的具体配置，继续搜；确实搜不到才明确说"这个价位我没找到数据"。
- **消费类产品必须分场景回答，不能只给单一答案**：消费类产品（笔电/手机/相机）价格区间很大，「最佳」结论依赖用户需求和预算，泛化结论有误导性。先按配置/性能/价格三维度对比，再给出场景化建议。

## 研究成果存档
- [远程控制技能调研（remote-control-skills-research）](references/remote-control-skills-research.md) — 2026-07-11：vnc-computer-use、agent-rdp、QuickDesk 等方案的对比与选型
- [软路由硬件选购案例（R68S/R2S/R66S对比）](references/soft-router-research-case.md) — 2026-07-11：300元内软路由性价比研究，R68S非唯一解，场景细分后各有机场景
