# PaddleOCR v3.6.0 — 本地 OCR 替代方案

## 背景

百度 OCR 有每月 1000 次的免费额度限制。当额度耗尽或需离线使用时，PaddleOCR v3.6.0 是成熟的本地替代方案。

## 安装状态

**已安装于**：`/Users/aimac/.hermes/hermes-agent/venv/bin/python`

首次初始化时会自动下载模型（约 300MB+），存放在 `~/.paddlex/official_models/`。

## 快速验证

```bash
/Users/aimac/.hermes/hermes-agent/venv/bin/python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(lang='ch'); print('✓ PaddleOCR OK')"
```

## 中文识别示例

```python
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='ch')
result = ocr.ocr('/path/to/image.png')
for line in result[0]:
    print(line[1][0])  # (坐标, (文字, 置信度))
```

## 若未安装（venv 内安装步骤）

```bash
cd /Users/aimac/.hermes/hermes-agent
./venv/bin/pip install paddlepaddle paddlex paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 依赖链

```
paddlepaddle     # 底层引擎
paddlex[ocr]     # 中间件
paddleocr        # 上层接口
```

## 与百度 OCR 的对比

| | 百度 OCR | PaddleOCR |
|---|---|---|
| API 额度 | 每月 1000 次 | 无限制 |
| 离线 | ❌ | ✅ |
| 首次安装大小 | 微小 | ~300MB（模型） |
| 中文识别精度 | 高 | 高（PP-OCRv5） |
| 安装复杂度 | 低（pip） | 中（依赖链长） |

## 已知问题

- Python 3.14 不兼容（Mac arm64 无 wheel），需用 Python 3.11
- 首次初始化慢（下载模型）
- `show_log` 参数在 v3.6.0 中已移除，使用时去掉该参数