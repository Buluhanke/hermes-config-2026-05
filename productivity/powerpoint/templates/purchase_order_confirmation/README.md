# 采购订单确认PPT模板

## 快速开始

```bash
cat > data.json << 'EOF'
{
  "title": "采购订单确认书",
  "order_no": "PO-2025-00123",
  "date": "2025-01-15",
  "buyer": "我司（深圳XXX贸易有限公司）",
  "seller": "杭州XXX服饰有限公司",
  "contact": "王经理",
  "phone": "0755-12345678",
  "delivery_date": "2025-02-15",
  "delivery_address": "深圳市南山区科技园路1号",
  "payment_terms": "T/T 30% 定金，余款发货前付清",
  "items": [
    { "name": "女士纯棉T恤 M码 白色", "sku": "TS-W-M-WH", "qty": "500", "price": "¥28.00", "subtotal": "¥14,000.00" },
    { "name": "女士纯棉T恤 M码 黑色", "sku": "TS-W-M-BK", "qty": "300", "price": "¥28.00", "subtotal": "¥8,400.00" },
    { "name": "运动卫衣 L码 灰色", "sku": "HOOD-L-GR", "qty": "200", "price": "¥65.00", "subtotal": "¥13,000.00" }
  ],
  "subtotal": "¥35,400.00",
  "tax_rate": "13%",
  "tax_amount": "¥4,602.00",
  "total_amount": "¥40,002.00",
  "notes": "请按期交货，质量问题需在收货7日内书面提出。"
}
EOF

node render.js data.json purchase_order.pptx
```

## 幻灯片结构

| 序号 | 幻灯片 | 内容 |
|------|--------|------|
| 1 | 封面 | 标题、订单号、甲乙方、日期 |
| 2 | 订单信息 | 订单编号、日期、交货信息、付款方式 |
| 3 | 采购明细 | 产品表格（序号、名称、SKU、数量、单价、小计）及汇总 |
| 4 | 条款与备注 | 标准条款 + 自定义备注 |
| 5 | 签章确认 | 甲乙双方签章区域 |

## spec.json 必填字段

| 字段 | 说明 |
|------|------|
| order_no | 采购订单编号 |
| buyer | 采购方公司名称 |
| seller | 供应商名称 |
| items | 产品明细数组（见下） |
| total_amount | 合同总金额 |

## items 数组项

```json
{
  "name": "产品名称（含规格）",
  "sku": "SKU编号",
  "qty": "数量",
  "price": "单价",
  "subtotal": "小计"
}
```
