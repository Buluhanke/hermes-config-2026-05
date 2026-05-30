# OCR Engine Recovery Log

## 2026-05-30 — PaddleOCR + pymupdf 重装

### 背景
之前清理 Hermes 冗余 venv 时删除了 `.venv`（Python 3.13），连同 browser-use 和 PaddleOCR 一起丢失。hermes-agent 的 `venv`（Python 3.11）保留下来了，但 paddleocr 和 pymupdf 不在其中。

### 重装过程

**pymupdf（系统Python）：**
```bash
uv pip install pymupdf --system
```
→ 装到 `/Library/Frameworks/Python.framework/Versions/3.14` 下（35秒）

**PaddleOCR（hermes-agent venv）：**
```bash
uv pip install paddleocr --python ~/.hermes/hermes-agent/venv/bin/python3
```
→ 66个依赖包，含 opencv-contrib-python、paddlex、paddleocr 等（约2分钟）
→ 注意：首次运行会自动下载OCR模型（~300MB）

**pymupdf（hermes-agent venv，备用）：**
```bash
uv pip install pymupdf --python ~/.hermes/hermes-agent/venv/bin/python3
```

### 验证结果
- Vision OCR: ✅ Homebrew Python
- PaddleOCR: ✅ hermes-agent venv
- ddddocr: ✅ Homebrew Python
- pymupdf: ✅ 两个环境都有
- Baidu OCR: ✅ .env已配

### Lessons Learned
1. 系统Python 3.14的 `python3` 其实是 venv 的软链（`which python3` → `~/.hermes/hermes-agent/venv/bin/python3`）
2. 真实框架Python在 `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3`
3. 系统 Python（/usr/bin/python3）受 PEP 668 保护，不能直接 pip install
4. Vision OCR 只能通过 `/opt/homebrew/bin/python3`（Homebrew，含pyobjc）使用
5. uv 的 `--python` 参数可以指定任意 Python 路径安装包
