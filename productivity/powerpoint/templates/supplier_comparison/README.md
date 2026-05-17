# 供应商比价PPT模板

## 文件结构

```
supplier_comparison/
├── README.md          # 本文件
└── render.js         # pptxgenjs 渲染脚本
```

## 快速开始

```bash
# 准备数据文件 data.json
cat > data.json << 'EOF'
{
  "title": "供应商比价分析报告",
  "subtitle": "2025年第一季度供应商评估",
  "date": "2025-01-15",
  "company": "深圳XXX贸易有限公司",
  "products": [
    {
      "name": "女士纯棉T恤",
      "spec": "M码/白色"
    }
  ],
  "suppliers": [
    {
      "name": "杭州XXX服饰有限公司",
      "contact": "李经理",
      "phone": "138-0000-1234",
      "price": "¥28.00",
      "moq": "500件",
      "lead_time": "15天",
      "rating": "★★★★☆",
      "certifications": ["ISO9001", "OEKO-TEX"],
      "payment_terms": "T/T 30%",
      "notes": "价格最优，交期稳定"
    },
    {
      "name": "广州YYY制衣厂",
      "contact": "王经理",
      "phone": "139-0000-5678",
      "price": "¥30.00",
      "moq": "300件",
      "lead_time": "12天",
      "rating": "★★★★★",
      "certifications": ["ISO9001", "CE", "GOTS"],
      "payment_terms": "T/T 30%",
      "notes": "质量最好，认证齐全"
    },
    {
      "name": "上海ZZZ服装公司",
      "contact": "张经理",
      "phone": "136-0000-9012",
      "price": "¥26.00",
      "moq": "800件",
      "lead_time": "20天",
      "rating": "★★★☆☆",
      "certifications": ["ISO9001"],
      "payment_terms": "T/T 40%",
      "notes": "价格最低，但MOQ高"
    }
  ],
  "recommendation": "综合考虑价格、质量、交期，推荐杭州XXX服饰有限公司为首选供应商。"
}
EOF

# 生成PPT
node render.js data.json output.pptx
```

## 幻灯片结构

| 序号 | 幻灯片 | 内容 |
|------|--------|------|
| 1 | 封面 | 标题、副标题、日期、公司名称 |
| 2 | 比价概览 | 参与比价的供应商数量、产品范围、评估维度说明 |
| 3 | 供应商对比表 | 各供应商价格、MOQ、交期、评分、资质等横向对比 |
| 4 | 综合排名 | 供应商综合评分排名（价格分+质量分+交期分） |
| 5 | 推荐结论 | 推荐供应商及理由 |

## spec.json 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| title | 否 | 演示文稿标题，默认"供应商比价分析报告" |
| subtitle | 否 | 副标题 |
| date | 否 | 日期字符串，默认今天 |
| company | 否 | 我方公司名称（封面右上角） |
| products | 否 | 比价产品数组，见下 |
| suppliers | 是 | 供应商数组，见下 |
| recommendation | 否 | 推荐结论文字 |

### products 数组项

```json
{
  "name": "产品名称",
  "spec": "规格/型号"
}
```

### suppliers 数组项

```json
{
  "name": "供应商名称",
  "contact": "联系人",
  "phone": "联系电话",
  "price": "单价",
  "moq": "最小订货量",
  "lead_time": "交期",
  "rating": "综合评分（星级）",
  "certifications": ["资质认证列表"],
  "payment_terms": "付款方式",
  "notes": "备注/亮点"
}
```