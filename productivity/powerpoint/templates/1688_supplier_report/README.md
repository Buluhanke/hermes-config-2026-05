# 1688供应商汇报PPT模板

## 文件结构

```
1688_supplier_report/
├── README.md          # 本文件
└── render.js         # pptxgenjs 渲染脚本
```

## 快速开始

```bash
# 准备数据文件 data.json
cat > data.json << 'EOF'
{
  "title": "1688供应商合作汇报",
  "subtitle": "杭州XXX服饰有限公司",
  "date": "2025-01-15",
  "supplier_name": "杭州XXX服饰有限公司",
  "contact": "李经理",
  "phone": "138-0000-1234",
  "email": "limanager@example.com",
  "company": "我司采购部",
  "summary": "公司成立于2010年，专注服装OEM/ODM，拥有完整生产线...",
  "main_business": "服装制造/OEM代工",
  "cooperation_years": "3年",
  "products": [
    {
      "name": "女士纯棉T恤",
      "category": "服装",
      "moq": "500件",
      "price_range": "¥25-45",
      "lead_time": "15天"
    },
    {
      "name": "运动卫衣",
      "category": "服装",
      "moq": "300件",
      "price_range": "¥55-88",
      "lead_time": "20天"
    }
  ],
  "payment_terms": "T/T 30% 定金",
  "moq_policy": "500件起订",
  "price_validity": "30天",
  "delivery_terms": "FOB 上海港",
  "annual_capacity": "100,000件/年",
  "inspection": "出厂全检",
  "certifications": ["ISO9001", "OEKO-TEX", "GOTS"],
  "quality_measures": ["ISO质量管理体系", "来料检验(IQC)", "过程检验(IPQC)", "成品检验(FQC)"]
}
EOF

# 生成PPT
node render.js data.json output.pptx
```

## 幻灯片结构

| 序号 | 幻灯片 | 内容 |
|------|--------|------|
| 1 | 封面 | 标题、副标题、供应商名称、日期 |
| 2 | 企业概况 | 公司基本信息、联系人、企业简介 |
| 3 | 主营产品 | 产品卡片列表（2列） |
| 4 | 价格与合作条款 | 付款方式、MOQ、交期等 |
| 5 | 质量保障 | 资质认证、质量管控措施 |
| 6 | 联系方式 | 供应商联系信息 |

## spec.json 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| title | 否 | 演示文稿标题，默认"1688供应商汇报" |
| subtitle | 否 | 副标题，默认用 supplier_name |
| supplier_name | 是 | 供应商企业名称 |
| contact | 是 | 联系人姓名 |
| phone | 是 | 联系电话 |
| email | 否 | 邮箱 |
| company | 否 | 采购方公司名称（封面右上角） |
| date | 否 | 日期字符串，默认今天 |
| summary | 否 | 企业简介正文 |
| main_business | 否 | 主营业务 |
| cooperation_years | 否 | 合作时长 |
| products | 否 | 产品数组，见下 |
| payment_terms | 否 | 付款方式 |
| moq_policy | 否 | MOQ政策 |
| price_validity | 否 | 报价有效期 |
| delivery_terms | 否 | 交货方式 |
| annual_capacity | 否 | 年供货能力 |
| inspection | 否 | 质检方式 |
| certifications | 否 | 资质认证列表 |
| quality_measures | 否 | 质量管控措施列表 |

### products 数组项

```json
{
  "name": "产品名称",
  "category": "类别",
  "moq": "最小订货量",
  "price_range": "价格区间",
  "lead_time": "交期"
}
```
