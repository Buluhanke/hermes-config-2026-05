# Vision 工具降级链（2026-07-10 实测）

## 已知失效模式

| 工具 | 失效原因 | 降级方案 |
|------|---------|---------|
| `vision_analyze(file_url)` | 不支持 `file://` URL，报 "unsafe or private URL" | 换 HTTP URL 或用 Tesseract |
| `vision_analyze(http_url)` | 有时也失败（原因不明） | 换 Tesseract |
| `browser_vision` | 有独立截图路径，但分析常返回"看不到图片" | Tesseract 兜底 |

## 降级链（按顺序试）

```
vision_analyze(http://...)     → 失败 1 次即降级
         ↓
Tesseract (terminal)
         ↓
CDP Page.captureScreenshot → base64 解码 → tesseract OCR
```

## Tesseract OCR 读取截图（已验证 2026-07-10）

```bash
# 截图（不能用 screencapture 做 browser_vision 的替代，browser_vision 有独立内部路径）
screencapture -x /tmp/page.png

# OCR 提取中文+英文
tesseract /tmp/page.png stdout -l chi_sim+eng --psm 6 2>/dev/null | head -100
```

参数说明：
- `--psm 6` — 假设均匀布局，最适合表格类截图
- `-l chi_sim+eng` — 中文简体+英文混排
- 输出到 stdout 可以 pipe 给后续处理

## CDP Screenshot → Tesseract 完整流程

```python
# 1. CDP screenshot（通过 hermes result 文件）
import base64, re, subprocess

# 从 hermes result 文件提取 base64
with open('/path/to/hermes-result.txt') as f:
    content = f.read()
match = re.search(r'"data": "([A-Za-z0-9+/=]+)"', content)
b64 = match.group(1)
img_data = base64.b64decode(b64)
with open('/tmp/ocr_input.png', 'wb') as f:
    f.write(img_data)

# 2. Tesseract OCR
result = subprocess.run(
    ['tesseract', '/tmp/ocr_input.png', 'stdout',
     '-l', 'chi_sim+eng', '--psm', '6'],
    capture_output=True, text=True, timeout=30
)
print(result.stdout)
```

## 企业微信表格 OCR 实测（2026-07-10）

企业微信智能表格（canvas 渲染，DOM 无法读）：
- 列标题：A=持店+1688日期, B=品名, C=数量, D=销售金额, E=支出金额...
- 可见数据行：5/20~5/25 的采购销售记录
- OCR 成功率：✅ 成功读出所有列名和行数据

## 铁律

- `vision_analyze` 失败 1 次即降 Tesseract，不要重试 2-3 次
- `browser_vision` 和 `vision_analyze` 是两个独立工具，失败后都要各自降级
- Tesseract 对表格类截图（`--psm 6`）远比对自然语言截图更可靠
