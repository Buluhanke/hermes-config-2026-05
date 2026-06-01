# OCR引擎对比与陷阱（2026-06-02实测）

## 实测结论

| 引擎 | 调用方式 | 中文 | 速度 | 稳定性 |
|------|---------|------|------|--------|
| Apple Vision | `/opt/homebrew/bin/python3` + PyObjC | ✅ | 60-240ms | ⚠️ Swift API语法易错 |
| PaddleOCR | hermes venv | ✅ | ~1s | ❌ 参数版本问题 |
| pytesseract | Homebrew Python | ⚠️ | 慢 | ❌ 对阿里云盘页面返回空 |
| ddddocr | Homebrew Python | ✅ | 快 | ⚠️ 仅限验证码 |

## PaddleOCR 陷阱

**症状：** `ValueError: Unknown argument: show_log`

**原因：** `show_log` 参数在新版本中被移除。

**正确初始化：**
```python
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='ch', use_textline_orientation=True)
```

注意：`use_angle_cls` 也已废弃，改用 `use_textline_orientation`。

## Apple Vision OCR 直接调用陷阱

直接用 PyObjC 调用 Vision API 语法复杂，易错。

**推荐用命令行方式：**
```bash
# 截图后用 Vision 读取文字
screencapture -x /tmp/page.png
```

**如果必须用 Python：** 使用 `vision` pip 包封装，或直接用 hermes-vision-agent 技能里的 `hermes_ocr` 工具。

## 阿里云盘快传页面识别

**问题：** 阿里云盘快传链接（alipan.com/t/xxx）需要登录才能查看内容。

**browser工具的Chrome（chrome-debug profile）不含阿里云盘登录状态**，无法直接读取。

**解法：**
1. 在 browser 工具的 Chrome 中先登录阿里云盘（扫码一次，cookie保存）
2. 或者让用户直接告诉文件内容
3. 或者用 MCP Chrome 工具（如果已登录）

**判断方式：**
- 页面标题是"阿里云盘快传"但内容只有"下载桌面端" → 未登录
- 页面显示具体文件列表 → 已登录

## MCP Chrome Bridge 故障应急

症状：`Failed to connect to MCP server`

**检查：**
```bash
# 检查mcp-chrome-stdio进程
ps aux | grep mcp-chrome

# 检查CDP端口
lsof -i :9333
```

**Playwright CDP 应急方案：**
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://localhost:9333')
```

注意：端口9333是chrome-debug profile的调试端口，不是标准Chrome端口。
