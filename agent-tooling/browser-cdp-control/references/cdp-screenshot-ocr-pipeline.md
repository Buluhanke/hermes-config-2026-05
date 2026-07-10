# CDP Screenshot → PNG → Tesseract OCR 完整管道（2026-07-11 验证）

## 问题背景

企业微信智能表格（doc.weixin.qq.com/sheet）canvas 渲染，无法用 DOM 读取。`vision_analyze` 不支持 `file://` URL，`browser_vision` 截图后分析也失败。最终用 CDP screenshot → Tesseract OCR 成功。

## 完整管道

### 步骤 1：CDP Page.captureScreenshot

```python
import json
# 通过 CDP WebSocket
ws.send(json.dumps({
    "id": 99,
    "method": "Page.captureScreenshot",
    "params": {"format": "png", "quality": 80}
}))
resp = json.loads(ws.recv())
b64 = resp["result"]["data"]
```

### 步骤 2：base64 解码为 PNG

```python
import base64, pathlib
img_data = base64.b64decode(b64)
png_path = pathlib.Path("/tmp/weixin_cdp.png")
png_path.write_bytes(img_data)
print(f"Saved {len(img_data)} bytes")
```

### 步骤 3：Tesseract OCR

```bash
tesseract /tmp/weixin_cdp.png stdout -l chi_sim+eng --psm 6
```

参数说明：
- `chi_sim+eng` — 中文简体 + 英文混合
- `--psm 6` — 假设单栏统一文字块（表格最优）

### Python 一行调用

```python
import subprocess, pathlib, base64, json

def ocr_png(png_path, lang="chi_sim+eng"):
    r = subprocess.run(
        ["tesseract", str(png_path), "stdout", "-l", lang, "--psm", "6"],
        capture_output=True, text=True, timeout=30
    )
    return r.stdout

# CDP screenshot JSON 文件 → OCR
def cdp_json_to_text(json_file, out_png):
    text = pathlib.Path(json_file).read_text()
    import re
    m = re.search(r'"data": "([A-Za-z0-9+/=]+)"', text)
    if not m:
        return ""
    img_data = base64.b64decode(m.group(1))
    out = pathlib.Path(out_png)
    out.write_bytes(img_data)
    return ocr_png(out)
```

## Tesseract 安装

```bash
brew install tesseract
# 验证语言包
tesseract --list-langs | grep chi
```

## 限制

- Tesseract 对表格线框识别差，列对齐依赖 OCR 文字位置
- 手写体、艺术字识别率低
- 表格合并单元格判断不准

## 替代方案优先级

1. `Runtime.evaluate` 读 DOM（企业微信公式栏）→ 最准
2. `browser_vision` 截图 → 简单场景
3. CDP screenshot → Tesseract OCR → canvas 表格最终降级
