# 库存预警系统 (Inventory Early Warning)

## 1. 库存预警的意义

库存预警是采购管理的核心风控机制，目标在于：

- **避免断货**：当库存低于安全线时及时补货，防止销售中断
- **防止积压**：当库存高于上限时停止采购，避免资金占用和损耗
- **合理采购**：基于真实消耗速度制定采购计划，避免拍脑袋决策

| 场景 | 后果 |
|------|------|
| 断货 | 订单流失、客户流失、搜索排名下降 |
| 积压 | 资金占用、仓储成本、临期损耗 |
| 采购过早/过量 | 现金流压力、库存周转率下降 |

---

## 2. 预警指标设计

### 2.1 安全库存公式

```
安全库存 (Safety Stock) = (最大日消耗量 × 最大供货周期) - (平均日消耗量 × 平均供货周期)
```

简化版（常用）：

```
安全库存 = 日均消耗量 × 供货周期 × 安全系数
```

| 参数 | 说明 | 典型值 |
|------|------|--------|
| 日均消耗量 | 过去N天总消耗 / N | 历史数据计算 |
| 供货周期 | 从下单到入库的天数 | 供应商SLA |
| 安全系数 | 1.2 ~ 1.6 | 波动越大越高 |

**再订货点 (ROP)**：

```
再订货点 = 日均消耗量 × 供货周期 + 安全库存
```

**最大库存**：

```
最大库存 = 再订货点 + 经济订货量 (EOQ)
```

### 2.2 预警等级四色

| 等级 | 颜色 | 库存状态 | 动作 |
|------|------|----------|------|
| 红色 | 🔴 紧急 | 库存 ≤ 安全库存 × 0.5 | 立即询价，优先采购 |
| 橙色 | 🟠 警告 | 库存 ≤ 安全库存 | 24小时内询价 |
| 黄色 | 🟡 观察 | 安全库存 < 库存 ≤ 再订货点 | 3天内关注 |
| 绿色 | 🟢 正常 | 库存 > 再订货点 | 常规监控 |

---

## 3. 数据采集方式

### 3.1 手动录入

适用于小批量、非标准化采购。

```markdown
字段：SKU | 当前库存 | 最后更新时间 | 备注
```

### 3.2 1688订单同步

通过1688开放平台API拉取订单状态：

```
订单状态 → 货源在途 → 入库数量自动增加
```

关键节点：
- **已下单**：采购已发出，计入在途
- **已发货**：物流运输中
- **已签收**：库存实际增加

### 3.3 物流签收同步

物流轨迹 webhook 或定时拉取：

```
快递到达 → 驿站/仓库签收 → 自动更新库存
```

常用快递轨迹 API：
- 菜鸟电子面单
- 快递鸟
- 自身ERP系统

---

## 4. 预警通知流程

```
检测 → 通知 → 建议 → 确认 → 询价
```

### 4.1 检测

- **定时检测**：每日早9点 / 下午3点自动跑批
- **触发式检测**：库存变化时实时计算
- **手动检测**：运营人员随时可触发

### 4.2 通知

| 通知方式 | 场景 |
|----------|------|
| 企业微信/钉钉机器人 | 红色预警立即推送 |
| 邮件 | 每日汇总报告 |
| 看板卡片 | 橙色及以上写入看板 |

通知内容：
```
🔴 [紧急补货] SKU-A1234
当前库存：50 件（安全库存 100 件）
预计断货时间：3 天
建议采购量：500 件
👉 https://procurement.example.com/sku/A1234
```

### 4.3 建议

系统给出采购建议（见第5节），包含：
- 推荐供应商
- 参考单价
- 建议订购量
- 预计到货时间

### 4.4 确认

采购负责人确认执行或调整：
- **确认执行**：进入询价流程
- **暂缓**：记录原因，等待下次预警重新触发
- **取消**：标记SKU，永久关闭预警

### 4.5 询价

确认后跳转至1688/供应商系统发起询价或直接下单。

---

## 5. 采购建议计算 Python 函数

```python
from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class SKUConfig:
    """SKU 配置参数"""
    sku_id: str
    name: str
    avg_daily_consumption: float      # 日均消耗量（件/天）
    max_daily_consumption: float       # 最大日消耗量
    lead_time_days: float              # 供货周期（天）
    max_lead_time_days: float          # 最大供货周期
    safety_factor: float = 1.4         # 安全系数


@dataclass
class InventoryStatus:
    """库存状态"""
    sku_id: str
    current_stock: float               # 当前库存
    on_the_way: float = 0              # 在途数量


@dataclass
class ProcurementRecommendation:
    """采购建议"""
    sku_id: str
    recommended_qty: int               # 建议采购量
    safety_stock: float                # 安全库存
    reorder_point: float               # 再订货点
    max_stock: float                   # 最大库存
    urgency: str                       # red/orange/yellow/green
    days_until_stockout: Optional[float]  # 预计断货天数
    action: str                        # 建议动作


def calculate_procurement(
    config: SKUConfig,
    status: InventoryStatus
) -> ProcurementRecommendation:
    """
    计算采购建议

    公式：
      安全库存 = (最大日消耗 × 最大供货周期) - (日均消耗 × 供货周期)
      再订货点 = 日均消耗 × 供货周期 + 安全库存
      最大库存 = 再订货点 + 经济订货量
      经济订货量 (EOQ) = sqrt(2 × 年消耗量 × 订货成本 / 单价持有成本)
    """
    # 安全库存
    safety_stock = (config.max_daily_consumption * config.max_lead_time_days) \
                   - (config.avg_daily_consumption * config.lead_time_days)
    safety_stock = max(safety_stock, config.avg_daily_consumption * config.lead_time_days * (config.safety_factor - 1))

    # 再订货点
    reorder_point = config.avg_daily_consumption * config.lead_time_days + safety_stock

    # 经济订货量（简化版：覆盖 N 天消耗）
    # EOQ = sqrt(2 * D * S / H)，此处用覆盖 N 天方式简化
    eoq = config.avg_daily_consumption * 14  # 目标覆盖14天消耗

    # 最大库存
    max_stock = reorder_point + eoq

    # 可用库存（含在途）
    available = status.current_stock + status.on_the_way

    # 断货天数计算
    if config.avg_daily_consumption > 0 and available > 0:
        days_until_stockout = available / config.avg_daily_consumption
    else:
        days_until_stockout = 0.0

    # 推荐采购量
    if available < reorder_point:
        recommended_qty = math.ceil(max_stock - available)
    else:
        recommended_qty = 0

    # 预警等级
    if available <= safety_stock * 0.5:
        urgency = "red"
        action = "立即询价，优先采购"
    elif available <= safety_stock:
        urgency = "orange"
        action = "24小时内询价"
    elif available <= reorder_point:
        urgency = "yellow"
        action = "3天内关注"
    else:
        urgency = "green"
        action = "常规监控"

    return ProcurementRecommendation(
        sku_id=config.sku_id,
        recommended_qty=recommended_qty,
        safety_stock=round(safety_stock, 2),
        reorder_point=round(reorder_point, 2),
        max_stock=round(max_stock, 2),
        urgency=urgency,
        days_until_stockout=round(days_until_stockout, 1) if days_until_stockout else None,
        action=action
    )


# ------------------------------
# 使用示例
# ------------------------------
if __name__ == "__main__":
    config = SKUConfig(
        sku_id="SKU-A1234",
        name="蓝牙耳机",
        avg_daily_consumption=20,      # 日均20件
        max_daily_consumption=35,       # 最多35件/天
        lead_time_days=5,               # 供货周期5天
        max_lead_time_days=8,           # 最长8天
        safety_factor=1.4
    )

    status = InventoryStatus(
        sku_id="SKU-A1234",
        current_stock=80,
        on_the_way=0
    )

    result = calculate_procurement(config, status)

    print(f"=== 采购建议：{result.sku_id} ===")
    print(f"安全库存：{result.safety_stock} 件")
    print(f"再订货点：{result.reorder_point} 件")
    print(f"最大库存：{result.max_stock} 件")
    print(f"当前可用：{status.current_stock + status.on_the_way} 件")
    print(f"预计断货：{result.days_until_stockout} 天")
    print(f"预警等级：{result.urgency}")
    print(f"建议采购：{result.recommended_qty} 件")
    print(f"执行动作：{result.action}")
```

---

## 6. 与看板集成

### 6.1 库存预警泳道（Swimlane）

在看板系统中设置独立的 **库存预警泳道**：

```
┌─────────────────────────────────────────────┐
│  🔴 红色预警（立即处理）                      │
│  ┌──────────┐ ┌──────────┐                 │
│  │ SKU-A1234 │ │ SKU-B5678 │  → 立即询价    │
│  │ 断货倒计时│ │ 断货倒计时│                 │
│  │ 2.5天    │ │ 0.8天    │                 │
│  └──────────┘ └──────────┘                 │
├─────────────────────────────────────────────┤
│  🟠 橙色预警（24h内处理）                     │
│  ┌──────────┐                               │
│  │ SKU-C9012 │  → 确认采购量               │
│  └──────────┘                               │
├─────────────────────────────────────────────┤
│  🟡 黄色预警（观察中）                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ SKU-D3456 │ │ SKU-E7890 │ │ SKU-F1111 │   │
│  └──────────┘ └──────────┘ └──────────┘    │
├─────────────────────────────────────────────┤
│  🟢 绿色（正常）                             │
│  （常规泳道，不单独列出）                     │
└─────────────────────────────────────────────┘
```

### 6.2 红卡标记（Red Card）

红色预警自动生成 **红卡**，贴在对应商品卡上：

**红卡内容模板**：

```
┌─────────────────────────────┐
│  🔴 紧急补货                │
│  ─────────────────────────  │
│  SKU：SKU-A1234             │
│  品名：蓝牙耳机             │
│  ─────────────────────────  │
│  当前库存：80 件            │
│  安全库存：142 件           │
│  预计断货：2.5 天           │
│  ─────────────────────────  │
│  建议采购量：500 件         │
│  ─────────────────────────  │
│  负责人：@张三             │
│  [确认执行] [暂缓] [取消]   │
└─────────────────────────────┘
```

### 6.3 看板卡片字段映射

| 看板字段 | 数据来源 | 说明 |
|----------|----------|------|
| 颜色标签 | `urgency` | 红/橙/黄/绿 |
| 断货倒计时 | `days_until_stockout` | 动态天数 |
| 采购建议量 | `recommended_qty` | 系统计算 |
| 负责人 | SKU 配置 | 归属采购员 |

---

## 附录：文件结构

```
procurement/
└── inventory-early-warning/
    ├── SKILL.md              # 本文件
    ├── calculate_procurement.py  # 采购建议计算模块
    └── config/
        └── sku_config.json   # SKU 配置示例
```