# 1688 Procurement Infographic Content Template

Template for structuring 1688 (Alibaba.cn) procurement data into infographic-ready content.

## Purpose

Transform 1688 platform procurement data into structured content for infographic generation. Preserves all data verbatim, organizes for visual communication.

## 1688-Specific Content Sections

### Section 1: Procurement Overview

**Key Concept**: High-level summary of procurement performance for the period.

**Content**:
- Total spend (¥)
- Number of orders placed
- Number of active suppliers
- Average lead time (days)
- Order completion rate (%)

**Visual Element**:
- Type: KPI cards row
- Subject: 4-6 key metrics with trend arrows
- Treatment: Big numbers, color-coded trends (green up, red down)

**Text Labels**:
- Headline: "1688采购概览"
- Subhead: "[Month/Quarter] 采购数据"
- Labels: "总支出", "订单数", "供应商数", "平均交期", "完成率"

---

### Section 2: Supplier Performance Comparison

**Key Concept**: Comparative evaluation of active suppliers across key criteria.

**Content** (per supplier, verbatim):
| 供应商 | 综合评分 | 价格评分 | 质量评分 | 交期评分 | 服务评分 | 月订单量 | 合作时长 |
|--------|----------|----------|----------|----------|----------|----------|----------|
| [Supplier A] | [X/5] | [X/5] | [X/5] | [X/5] | [X/5] | [XXX] | [X个月] |
| [Supplier B] | [X/5] | [X/5] | [X/5] | [X/5] | [X/5] | [XXX] | [X个月] |

**Visual Element**:
- Type: comparison matrix with supplier cards
- Subject: side-by-side supplier evaluation
- Treatment: color-coded score bars, radar chart overlay

**Text Labels**:
- Headline: "供应商对比"
- Subhead: "价格 / 质量 / 交期 / 服务"
- Labels: supplier names, criteria names, score values

---

### Section 3: Price Trend Analysis

**Key Concept**: Historical pricing trends for top purchased SKUs.

**Content** (per SKU, verbatim):
| 产品 | 近30天最低价 | 近30天最高价 | 当前价格 | 均价 | 价格趋势 |
|------|-------------|-------------|----------|------|----------|
| [SKU A] | ¥[XXX] | ¥[XXX] | ¥[XXX] | ¥[XXX] | ↑/↓/→ |

**Visual Element**:
- Type: line chart with area fill
- Subject: price over time for top 3 SKUs
- Treatment: annotation callouts for price changes, promotions

**Text Labels**:
- Headline: "价格趋势"
- Y-axis: "价格 (¥)"
- X-axis: "日期"
- Legend: SKU names with current price
- Stats box: 最低价, 最高价, 均价, 当前价

---

### Section 4: Category Breakdown

**Key Concept**: Spend distribution across product categories.

**Content** (verbatim):
| 品类 | 采购额 (¥) | 占比 | 订单数 | 环比变化 |
|------|-----------|------|--------|----------|
| [Category A] | [XXX,XXX] | [XX%] | [XXX] | [+/-XX%] |
| [Category B] | [XXX,XXX] | [XX%] | [XXX] | [+/-XX%] |

**Visual Element**:
- Type: horizontal bar chart or treemap
- Subject: category spend breakdown
- Treatment: sorted by spend descending, percentage labels

**Text Labels**:
- Headline: "品类采购分布"
- Subhead: "采购额占比"
- Labels: category names, values, percentages

---

### Section 5: Alert & Action Items

**Key Concept**: Key risks and recommended actions based on data.

**Content** (verbatim):
- 供应商A: 交期延迟率上升 [+X%], 建议: 沟通确认
- 价格波动提醒: [SKU B] 近7天价格上涨 [X%], 建议: 适量囤货
- 质量风险: [供应商C] 近期退货率 [X%], 建议: 跟进处理

**Visual Element**:
- Type: alert cards with icons
- Subject: risk indicators and action items
- Treatment: severity color coding (red/yellow/green), checkmark icons

**Text Labels**:
- Headline: "风险提醒与行动项"
- Alert type: "交期风险", "价格风险", "质量风险", "库存预警"
- Action: "建议: [action text]"

---

## 1688 Data Fields Reference

### KPI Metrics
| Field | Format | Example |
|-------|--------|---------|
| 总支出 | ¥XXX,XXX | ¥1,234,567 |
| 订单数 | X,XXX 单 | 456 单 |
| 供应商数 | X 家 | 23 家 |
| 平均交期 | X 天 | 7-15 天 |
| 完成率 | XX% | 98.5% |

### Supplier Evaluation
| Field | Format | Example |
|-------|--------|---------|
| 综合评分 | X.X/5 | 4.5/5 |
| 价格评分 | X.X/5 | 4.2/5 |
| 质量评分 | X.X/5 | 4.8/5 |
| 交期评分 | X.X/5 | 4.0/5 |
| 服务评分 | X.X/5 | 4.3/5 |
| 月订单量 | XXX 单 | 128 单 |
| 合作时长 | X 个月 | 18 个月 |

### Price Data
| Field | Format | Example |
|-------|--------|---------|
| 价格 | ¥XXX.XX | ¥89.00 |
| 均价 | ¥XXX.XX | ¥82.50 |
| 价格趋势 | ↑/↓/→ | ↑ +5.2% |
| 日期范围 | YYYY-MM-DD | 2024-01-01 |

### Category Data
| Field | Format | Example |
|-------|--------|---------|
| 品类名称 | 中文 | 服装辅料 |
| 采购额 | ¥XXX,XXX | ¥234,567 |
| 占比 | XX% | 18.5% |
| 环比变化 | +/-XX% | +12.3% |

## Design Instructions for 1688 Content

### Style Preferences
- Primary color: Alibaba Orange (#FF5000) for accents
- Data colors: Professional blues, greens, reds for status
- Clean, professional look suitable for B2B context

### Layout Preferences
- Dashboard layout for full procurement report
- Bento-grid for mixed metrics and comparisons
- Binary-comparison for supplier A vs B

### Chart Preferences
- Bar charts for category breakdowns
- Line charts for price trends
- Tables for supplier comparisons
- KPI cards for headline numbers
