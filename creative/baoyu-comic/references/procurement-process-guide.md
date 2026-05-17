# Procurement Process Comic Script Template

Create knowledge comics that visualize B2B procurement workflows — from需求发起 to合同签署 to货物验收. Use this template to create educational, step-by-step procurement comics for training, onboarding, or process documentation.

## Content Type Profile

| Attribute | Value |
|-----------|-------|
| Triggers | 采购流程、采购培训、供应商管理、入职培训、企业采购、供应链管理、采购审批 |
| Art Style | minimalist (default), ligne-claire, manga |
| Tone | neutral (default), warm, professional |
| Layout | four-panel (default), standard, mixed, webtoon |
| Aspect | 4:3 (landscape) for process flows, 3:4 (portrait) for narrative |
| Page Count | 4-16 pages |

## When to Use This Template

Use this template when creating:
- Procurement process training materials
- Onboarding comics for new procurement staff
- Supplier cooperation storyboards
- Business negotiation scripts
- Step-by-step purchasing workflow guides

## Core Process Arc: The 6-Stage Procurement Cycle

```
Stage 1: 需求提出 (Need Identification)
         ↓
Stage 2: 供应商筛选 (Supplier Sourcing)
         ↓
Stage 3: 询价与比价 (RFQ & Comparison)
         ↓
Stage 4: 合同签订 (Contract Execution)
         ↓
Stage 5: 订单执行 (Order Fulfillment)
         ↓
Stage 6: 验收与付款 (Inspection & Payment)
         ↓
Stage 7 (loop): 供应商评估 (Supplier Evaluation) → back to Stage 2
```

## Storyboard Template

### YAML Front Matter

```yaml
---
title: "[Process Name] 采购流程"
process_type: "procurement workflow"
industry: "[行业: 制造业/电商/贸易/服务/IT]"
company_size: "[企业规模: 初创/中小企业/大型企业]"
audience: "采购新人/供应商/内部协作部门"
source_language: "zh"
aspect_ratio: "4:3"
page_count: 8
---
```

### Page Structure (Four-Panel Template)

For simple 4-page comics, use this structure:

```
## Page 1: 需求提出 (Need Identification)
Filename: 01-page-[slug].png
Core Message: Who needs what, and why it matters
Panel 1 (TOP LEFT): 需求发起人坐在工位，提交采购申请
Panel 2 (TOP RIGHT): 采购申请表单（示意图）
Panel 3 (BOTTOM LEFT): 需求审批流程（示意图）
Panel 4 (BOTTOM RIGHT): 需求确认，进入下一阶段

## Page 2: 供应商筛选 (Supplier Sourcing)
... (same structure for each stage)
```

### Extended Page Structure (8-16 pages)

For detailed process comics:

```
## Page 1: Opening — The Procurement Need
Filename: 01-page-[slug].png
Layout: cinematic
Core Message: Set the scene — who needs what
Panel 1 (Wide establishing): Office interior, morning meeting
Panel 2 (Close-up): Manager pointing at whiteboard with "紧急补货"
Panel 3 (Medium): Buyer receiving task assignment
Panel 4 (Close-up): Buyer checking existing supplier list

## Page 2-3: 供应商筛选 (Supplier Sourcing)
Filename: 0N-page-[slug].png
Core Message: How to find the right suppliers
Panel 1: 1688/阿里巴巴搜索界面
Panel 2: 供应商列表对比（价格/评分/MOQ）
Panel 3: 联系供应商，发送询价函
Panel 4: 供应商回复，收集资料

## Page 4-5: 询价与比价 (RFQ & Comparison)
Filename: 0N-page-[slug].png
Core Message: Getting the best value
Panel 1: 收到各家供应商报价
Panel 2: 比价表（价格/交期/质量对比）
Panel 3: 技术评估/样品评估
Panel 4: 综合评分，确定入围供应商

## Page 6-7: 合同签订 (Contract Execution)
Filename: 0N-page-[slug].png
Core Message: Formalizing the agreement
Panel 1: 合同条款确认
Panel 2: 法务审核
Panel 3: 双方签章
Panel 4: 合同存档，下达采购订单

## Page 8: 订单执行与跟踪 (Order Fulfillment & Tracking)
Filename: 0N-page-[slug].png
Core Message: Keeping the order on track
Panel 1: 下达采购订单给供应商
Panel 2: 生产进度跟踪（旺旺/邮件）
Panel 3: 品质检验（来料检验）
Panel 4: 出货通知，收货准备

## Page 9: 验收与入库 (Inspection & Warehousing)
Filename: 09-page-[slug].png
Core Message: Confirming what was ordered arrived
Panel 1: 货物到达，清点数量
Panel 2: 质量抽检
Panel 3: 不良品处理（退换货流程）
Panel 4: 合格品入库，系统录入

## Page 10: 付款结算 (Payment Settlement)
Filename: 10-page-[slug].png
Core Message: Closing the loop
Panel 1: 收到供应商发票
Panel 2: 财务核对发票与入库单
Panel 3: 付款审批流程
Panel 4: 完成付款，供应商评价

## Page 11: 供应商评估与归档 (Supplier Evaluation)
Filename: 11-page-[slug].png
Core Message: Learning for next time
Panel 1: 评估维度：质量/交期/价格/服务
Panel 2: 评估打分表
Panel 3: 评估结果归档
Panel 4: Future supplier selection informed by evaluation

## Page 12: Closing — The Complete Cycle
Filename: 12-page-[slug].png
Core Message: From need to delivery, complete
Panel 1: Summary visual of all 6 stages
Panel 2: Stakeholders satisfied
Panel 3: Next procurement cycle begins
Panel 4: 采购流程圆满完成
```

## Character Design for Procurement Comics

### Two-Character Minimalist Structure

For simple four-panel process comics:

| Role | Archetype | Visual | Expression Range |
|------|-----------|--------|------------------|
| 采购员 | Procurement staff | Simple figure, clipboard/laptop | Neutral → Focused → Satisfied |
| 供应商 | Factory rep | Simple figure, factory background hint | Welcoming → Attentive → Professional |

### Multi-Character Structure

For detailed narrative comics:

| Role | Archetype | Visual Cues | Role in Process |
|------|-----------|-------------|-----------------|
| 采购员 (Buyer) | 公司采购专员 | Professional attire, organized desk, clipboard | Central character, drives process |
| 需求部门 (Requestor) | 需求发起人 | Department-specific attire (lab coat/warehouse vest/etc.) | Initiates need |
| 供应商 (Supplier) | 工厂销售/老板 | Factory setting, professional photo | Provides supply |
| 财务 (Finance) | 财务专员 | Calculator, receipt stacks, formal outfit | Payment approval |
| 仓管 (Warehouse) | 仓库管理员 | Warehouse setting, barcode scanner, practical wear | Goods receipt |
| 经理 (Manager) | 审批决策者 | Business attire, signature pen, decisive posture | Final approval |

## Visual Metaphors for Procurement Concepts

| Concept | Visual Metaphor |
|---------|-----------------|
| 需求提出 | Puzzle piece being placed on board |
| 供应商筛选 | Funnel filtering down to best options |
| 比价 | Scale balance with supplier logos on each side |
| 合同签订 | Two puzzle pieces clicking together |
| 订单执行 | Conveyor belt with packages moving forward |
| 质量检验 | Magnifying glass revealing quality stamp |
| 验收完成 | Green checkmark / door opening to next stage |
| 付款完成 | Handshake over completed transaction |
| 供应商评估 | Star rating filling in |

## 采购流程快查手册 (Quick Reference)

### 关键决策点

| Decision Point | Options | Considerations |
|----------------|---------|----------------|
| 选择供应商 | 现有合格供应商 vs 新开发 | 价格/交期/质量风险 |
| 采购方式 | 询价采购 vs 招标 vs 单一来源 | 金额大小/紧急程度 |
| 付款方式 | 款到发货 vs 货到付款 vs 账期 | 供应商关系/谈判能力 |
| 质量控制 | 来料检验 vs 过程监控 vs 出货检验 | 产品类别/风险等级 |

### 常见问题与解决方案

| Issue | Visual | Solution |
|-------|--------|----------|
| 供应商延期 | Clock visual, worried buyer | 备选供应商 + 合同条款 |
| 质量问题 | Red X mark, defective product | 退换货流程 + 质量协议 |
| 价格变动 | Price tag changing | 价格锁定条款 |
| MOQ不满足 | Small order vs container visual | 拼单 / 协商MOQ |

## Four-Panel Process Comic Template

For minimal, quick-to-generate process comics:

```
---
title: "[Process Name] — 采购四格漫画"
process_type: "procurement quick-guide"
aspect_ratio: "4:3"
page_count: 1
---

## Page 1: [Process Name] 四格流程
Filename: 01-page-[slug].png

Panel 1 - TOP LEFT (Stage 1: 需求发起):
- Visual: [需求发起人] + [需求物品/图标]
- Text: [Need description]

Panel 2 - TOP RIGHT (Stage 2: 供应商选择):
- Visual: [供应商筛选过程] + [筛选图标]
- Text: [Selection criteria]

Panel 3 - BOTTOM LEFT (Stage 3: 合同与订单):
- Visual: [合同签订] + [订单下达]
- Text: [Contract/order details]

Panel 4 - BOTTOM RIGHT (Stage 4: 验收付款):
- Visual: [货物验收] + [付款完成]
- Text: [Completion note]

Style: Minimalist line art, black outlines, [spot color] accent on key elements, clean white background.
Layout: 2×2 grid, equal panel sizes.
Asian business illustration style.
```

## Quality Markers

- [ ] Process flow is accurate and complete (no missing steps)
- [ ] Key decision points are highlighted
- [ ] Characters are simple but distinguishable
- [ ] Visual metaphors aid understanding without being distracting
- [ ] Chinese text uses full-width punctuation
- [ ] Final panel shows completion/milestone clearly
- [ ] Comic can stand alone as training material without additional explanation
- [ ] Process is appropriately detailed for target audience (novice vs experienced)