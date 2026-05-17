# 采购成本分析 Skill

## 概述
本 skill 用于系统性分析采购成本，评估供应商报价，优化采购决策。

---

## 1. 成本构成分析

### 1.1 六大成本维度

| 成本项 | 说明 | 典型占比 | 计算方式 |
|--------|------|----------|----------|
| **货值** | 采购商品/原料的基价 | 60-85% | 数量 × 单价 |
| **运费** | 运输、快递、物流费用 | 3-10% | 距离 × 重量 × 费率 |
| **损耗** | 运输/仓储途中的破损、变质 | 0.5-3% | 货值 × 损耗率 |
| **人工** | 采购、验收、管理的相关人力成本 | 2-5% | 耗时 × 时薪 × 人数 |
| **仓储** | 库存持有、仓储租金、管理费用 | 1-5% | 单位仓储费 × 库存量 × 时间 |
| **资金占用** | 资金沉淀在库存中的机会成本 | 2-8% | 货值 × 资金占用率 × 时间 |

### 1.2 总成本公式

```
总采购成本 = 货值 + 运费 + 损耗 + 人工 + 仓储 + 资金占用
```

### 1.3 单位成本计算

```
单位成本 = 总采购成本 / 采购数量
```

---

## 2. 成本分析模板

### 2.1 Excel 数据结构

**工作表 1: 采购明细 (Purchase Details)**
```
| 供应商 | SKU | 品名 | 数量 | 单价 | 货值 | 运费 | 损耗率 | 损耗金额 | 人工 | 仓储 | 资金占用 | 总成本 | 单位成本 |
|--------|-----|------|------|------|------|------|--------|----------|------|------|----------|--------|----------|
```

**工作表 2: 供应商对比 (Supplier Comparison)**
```
| 供应商 | 报价 | 运费 | 交货周期 | 损耗率 | 综合单价 | 排名 |
|--------|------|------|----------|--------|----------|------|
```

**工作表 3: 成本趋势 (Cost Trend)**
```
| 月份 | 供应商 | 货值 | 综合成本 | 环比 | 同比 |
|------|--------|------|----------|------|------|
```

### 2.2 Excel 联动公式示例

```excel
// 总成本计算
=SUM(B2:G2)

// 综合单价 (含所有成本)
=(货值+运费+损耗+人工+仓储+资金占用)/数量

// 供应商评分
=权重1*价格分 + 权重2*质量分 + 权重3*交期分 + 权重4*服务分
```

---

## 3. 供应商比价方法

### 3.1 基础比价法

| 方法 | 适用场景 | 公式 |
|------|----------|------|
| 最低价法 | 标准品、竞争充分 | 选择报价最低者 |
| 平均价法 | 防止极端报价 | 与平均价接近者加分 |
| 目标价法 | 有预算约束 | 与目标价对比 |

### 3.2 TCO 总成本比价法

```python
def tco_comparison(suppliers: list[dict]) -> dict:
    """
    计算各供应商总拥有成本 (Total Cost of Ownership)
    suppliers: [{'name': str, 'unit_price': float, 'freight': float,
                 'lead_time': int, 'defect_rate': float, 'payment_days': int}]
    """
    results = []
    for s in suppliers:
        # 货值成本
        goods_cost = s['unit_price']
        
        # 运费分摊 (每批次固定+单位运费)
        freight_cost = s.get('freight', 0)
        
        # 损耗成本
        loss_cost = goods_cost * s.get('defect_rate', 0)
        
        # 资金占用成本 (年化利率 5%)
        capital_cost = goods_cost * 0.05 * (s.get('payment_days', 30) / 365)
        
        # 交期成本 (库存持有成本)
        # 假设安全库存 = lead_time / 30 个月
        holding_months = s.get('lead_time', 30) / 30
        holding_cost = goods_cost * 0.05 * holding_months
        
        tco = goods_cost + freight_cost + loss_cost + capital_cost + holding_cost
        results.append({'name': s['name'], 'tco': tco})
    
    return min(results, key=lambda x: x['tco'])
```

### 3.3 供应商评估矩阵

```
权重分配建议:
- 价格: 40%
- 质量: 25%
- 交期: 20%
- 服务: 10%
- 合规: 5%

评分标准:
- 价格: 最低价=10分, 每高1%扣0.5分
- 质量: 合格率100%=10分, 每降1%扣1分
- 交期: 准时=10分, 每延迟1天扣1分
- 服务: 满意度评分
```

---

## 4. 议价目标计算

### 4.1 目标价计算方法

```python
def calculate_target_price(
    market_price: float,      # 市场参考价
    volume_discount: float,    # 批量折扣率 (如 0.05 = 5%)
    target_margin: float,      # 期望毛利率 (如 0.15 = 15%)
    competitor_prices: list[float] = None
) -> dict:
    """计算议价目标区间"""
    
    # 基于市场行情的目标价
    base_target = market_price * (1 - volume_discount)
    
    # 考虑竞争对手价格
    if competitor_prices:
        avg_competitor = sum(competitor_prices) / len(competitor_prices)
        market_target = min(competitor_prices) * 0.98  # 低于最低价2%
    else:
        market_target = base_target
    
    # 保底价 (覆盖成本+目标利润)
    floor_price = market_price * (1 - target_margin)
    
    # 议价区间
    target_price = (base_target + market_target) / 2
    bargaining_range = (floor_price, target_price)
    
    return {
        'target_price': target_price,
        'floor_price': floor_price,
        'upper_limit': market_price,
        'bargaining_range': bargaining_range,
        'potential_saving': market_price - target_price
    }
```

### 4.2 议价策略建议

| 谈判杠杆 | 操作方法 | 效果 |
|----------|----------|------|
| 批量折扣 | 承诺季度/年度采购量 | 争取 3-8% 降价 |
| 付款条件 | 缩短账期或预付 | 争取 1-3% 折扣 |
| 竞争报价 | 引入备选供应商 | 争取 5-15% 降价 |
| 长期协议 | 签 1-3 年合约 | 争取 3-10% 降价 |
| 联合采购 | 与同行拼单 | 争取 5-12% 降价 |

---

## 5. 成本优化建议

### 5.1 成本优化矩阵

| 优化方向 | 具体措施 | 预期降幅 | 实施难度 |
|----------|----------|----------|----------|
| **采购集中化** | 整合需求, 集中采购 | 5-15% | 中 |
| **供应商整合** | 减少供应商数量, 培养战略供应商 | 3-10% | 中 |
| **减少损耗** | 改进包装, 优化物流 | 2-5% | 低 |
| **VMI 模式** | 供应商管理库存 | 3-8% | 高 |
| **谈判优化** | 批量、长期协议、竞争引入 | 5-12% | 低 |
| **替代方案** | 寻找性价比更高的替代物料 | 5-20% | 高 |

### 5.2 库存优化策略

```python
def optimize_order_quantity(
    annual_demand: float,      # 年需求量
    unit_cost: float,          # 单位成本
    ordering_cost: float,      # 每次订货成本
    holding_rate: float,       # 持有成本率 (如 0.25 = 25%)
) -> dict:
    """经济订货量 (EOQ) 模型"""
    import math
    eoq = math.sqrt(2 * annual_demand * ordering_cost / (unit_cost * holding_rate))
    
    # 年总成本
    ordering_total = (annual_demand / eoq) * ordering_cost
    holding_total = (eoq / 2) * unit_cost * holding_rate
    purchase_total = annual_demand * unit_cost
    total_cost = ordering_total + holding_total + purchase_total
    
    return {
        'eoq': eoq,                    # 经济订货量
        'orders_per_year': annual_demand / eoq,  # 年订货次数
        'total_cost': total_cost,
        'ordering_cost': ordering_total,
        'holding_cost': holding_total
    }
```

### 5.3 关键绩效指标 (KPI)

| KPI | 计算方式 | 目标值 |
|-----|----------|--------|
| 采购成本率 | 采购总成本 / 采购总额 | < 95% |
| 议价节省率 | 节省金额 / 预算金额 | > 5% |
| 供应商集中度 | 前3供应商采购额占比 | < 60% |
| 交期准确率 | 准时交货次数 / 总交货次数 | > 95% |
| 损耗率 | 损耗金额 / 货值 | < 1% |
| 库存周转率 | 年销售成本 / 平均库存 | > 8次 |

---

## 使用指南

1. **数据收集**: 收集各供应商报价单、物流费用、质量数据
2. **成本计算**: 按六大维度分解并计算总成本
3. **供应商比价**: 使用 TCO 方法进行综合比较
4. **议价准备**: 计算目标价和议价区间
5. **决策优化**: 结合成本与供应风险做出最优决策
6. **监控复盘**: 定期复盘成本变化，持续优化

---

## 模板文件

建议同时创建以下辅助文件:
- `procurement_cost_template.xlsx` - Excel 成本分析模板
- `supplier_evaluation_matrix.xlsx` - 供应商评估矩阵
- `cost_tracking_dashboard.xlsx` - 成本跟踪仪表板