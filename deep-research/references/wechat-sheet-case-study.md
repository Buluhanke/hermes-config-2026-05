# 2026-07-11 企业微信表格深度研究案例

## 企业微信智能表格 doc.weixin.qq.com/sheet 读取结果

### 工作表结构
- 抖音、5月（当前）、采购单、报价表、转换、对账单、报销单

### 「5月」工作表列标题
A: 持店+1688日期 | B: 品名 | C: 数量 | D: 销售金额 | E: 支出金额 | F: 账户结余 | G: 应收款 | H: ORR | I: 账户实时现金 | J: 抖音账户 | K: 1688=抖音 | L: 1688未到账 | M: 抖音欠款 | N: 账面总金额 | O-V: 各月分红

### 「26年6月报销」XLS 文件（本地）
- 读取工具：`pip install xlrd` + `pandas.read_excel(..., engine='xlrd')`
- Sheet2：11条报销记录，合计 -5758，经办人"罗"
- Sheet3：空

## 关键坑点

1. **canvas 渲染**：公式栏只能读当前激活 cell，表格内容用 Tesseract OCR
2. **vision_analyze 不支持 file://**：CDP screenshot → base64 → tesseract
3. **活跃标签页判断**：CDP 9222 可能是 mirror Chrome 不是用户 Chrome，需 ps aux 鉴别
4. **写入真实表格 = 不可逆**：先确认测试环境还是真实数据

## 调研工具链
- `web_search_plus` 多引擎搜索 → 提取关键页面 → AI 网站对话验证
- `browser_navigate` + `browser_vision` → 直接在 AI 网站获取一手信息
- Tesseract OCR → 表格(canvas)内容读取
