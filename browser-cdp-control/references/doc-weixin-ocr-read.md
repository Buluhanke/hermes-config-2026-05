# 企业微信表格 OCR 读取 — Tesseract 降级方案

## 何时用此方法

canvas 渲染的表格，`Page.captureScreenshot` → `vision_analyze` 全部失效时，用 Tesseract OCR。

## 完整工作流

### Step 1: CDP screenshot
```python
# browser_cdp CDP 截图（target_id 从 Target.getTargets 获取）
browser_cdp(method="Page.captureScreenshot", params={"format": "png", "quality": 80}, target_id="<page_target_id>")
# 返回 base64 PNG，写入文件
```

### Step 2: Tesseract OCR
```bash
tesseract /tmp/weixin_cdp.png stdout -l chi_sim+eng --psm 6 2>/dev/null | head -100
```

**参数说明**：
- `--psm 6` = 假设单 block 均匀行（适合表格）
- `-l chi_sim+eng` = 中文简体 + 英文混排
- 重度噪声：`--psm 4`（单 column）或 `11`（稀疏文字）

### Step 3: 解析 OCR 输出
OCR 输出格式示例（来自 `5月` 工作表）：
```
角 "26年5有月 ow wv              Se9coB=ER HF
开始 插入 数据 公式 视图

@ -  默认字体  0 » Ae Cle EB Reet  Fr Yr BT   BA  7  了-图冻结"  CRM He  Oo:  @   av
a4  插入  BTUS AT全 图条件格式"  =zER=      %  0   eR RL HR RUE 保护  页面设置"打印

AF  B         C         D    E      F      G     H     i       J     K     L     M    N    fo}    P    Q    R    Ss    T     u      V
1 持店+1688 日期;         品名         :数量;销售金额; 支出金额 ;账户结余;应收款; ORR ;账户实时现金#拌音账户| 1688 = 拌音 | 1688未到账| 择音欠款| 账面总金额| 9月分红| 10月分红| 1月分红| 12月分红| o1月分红
3    1011.68 =: 5818!      多功能分层架      1 360    3960      -3600      360 | 9960 |       :
4 7390078 SHIR) 过回原信库的撮人0 0 -2 gata                                                               —
...
```

**识别规律**：
- 列标题在 row 1
- 数据行以 `;` 分隔字段
- 数字列 OCR 精度较低（如 `3960` 读成 `3 60`），需后处理

### Step 4: 提取关键字段
```python
import re
ocr_text = open('/tmp/weixin_ocr.txt').read()

# 提取列标题（row 1 通常有大写字母序列）
headers = re.findall(r'[A-Z]{1,3}\s+', ocr_text)

# 提取数据行（以日期开头）
date_rows = re.findall(r';?(\d{1,2}月\d{1,2}日[^;\n]+)', ocr_text)
```

## 已知限制

| 问题 | 原因 | 缓解 |
|------|------|------|
| 数字 OCR 精度低（3960→3 60） | 表格线干扰 | 用正则清理空格 |
| 列标题识别成单字母 | 表格边框线干扰 | 人工确认关键列 |
| 混排时中文漏字 | 字体小/压缩 | `--psm 4` 尝试 |

## Tesseract 安装状态（2026-07-10）

```
tesseract 5.5.2
leptonica-1.87.0
已安装路径: /opt/homebrew/bin/tesseract
```

如需安装：`brew install tesseract tesseract-lang`
