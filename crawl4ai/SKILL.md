---
name: crawl4ai
description: Crawl4AI — GitHub 73.6K⭐开源网页爬虫，网页→干净Markdown，专为大模型优化。触发：需要抓取网页并转为干净格式/RAG数据准备/结构化提取/大模型友好爬虫。
triggers:
  - 爬取网页转为markdown
  - RAG数据准备
  - 网页去噪清洗
  - 结构化数据提取
  - llm友好爬虫
  - crawl4ai
  - 网页转markdown
version: 1.1.0
---

## 安装状态

**已安装**（无需 pip install）。使用 Hermes venv 内置 playwright + markdownify + beautifulsoup4，调用系统缓存的 Chromium headless shell。

## 核心用法

### Python API（推荐）

```python
import subprocess, json

result = subprocess.run(
    ['python3', '/Users/aimac/.hermes/scripts/crawl4ai_shell.py', url, '--wait', '2000'],
    capture_output=True, text=True, timeout=60
)
markdown = result.stdout
```

### CLI

```bash
# 基础爬取
python3 ~/.hermes/scripts/crawl4ai_shell.py https://example.com

# JS页面等待渲染
python3 ~/.hermes/scripts/crawl4ai_shell.py <url> --wait 3000
```

## 与现有工具的关系

| 工具 | 适合场景 | vs Crawl4AI |
|------|----------|-------------|
| `web_extract` | 简单页面+PDF | 无JS渲染，快速 |
| `browser_navigate` | 需交互的页面 | 返回DOM树，非Markdown |
| **本脚本** | 干净Markdown+RAG | 去噪+JS渲染+大模型友好 |

## 技术细节

- **浏览器**：调用 `~/Library/Caches/ms-playwright/chromium_headless_shell-1217/` 缓存的 Chromium headless shell
- **渲染策略**：`domcontentloaded` + 2s 等待（可调 `--wait`）
- **正文提取**：BeautifulSoup 去噪（nav/header/footer/script/aside）→ markdownify 转 Markdown
- **超时**：30s

## 验证

```bash
python3 ~/.hermes/scripts/crawl4ai_shell.py https://example.com
```
