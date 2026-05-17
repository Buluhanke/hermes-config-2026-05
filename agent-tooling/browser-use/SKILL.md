---
name: browser-use
description: >
  browser-use — 免费开源的 AI 浏览器自动化框架（GitHub 91K Stars）。
  通过自然语言指令让 AI 控制真实 Chrome 浏览器，完成点击、填表、爬取、导航等操作。
  无需 API Key，本地即可运行。支持 Ollama 本地模型。
triggers:
  - browser-use 安装 / 配置 / 使用
  - AI 控制浏览器 / 浏览器自动化
  - 用 AI 操作网页 / 自然语言浏览器控制
  - browser-use vs playwright vs puppeteer
  - 1688 自动化方案对比
  - 本地浏览器自动化 无需 API key
tags: [browser, automation, ai, python, open-source, local-llm, ollama]
version: 1.0.0
author: Hermes Agent
created: 2026-05-17
---

# browser-use 集成技能

## 概述

**browser-use** 是免费开源的 AI 浏览器自动化框架（MIT License，GitHub 91K Stars）。
让 AI Agent 通过自然语言指令控制真实 Chrome 浏览器，无需云服务，本地即可运行。

- **官网**: https://github.com/browser-use/browser-use
- **文档**: https://docs.browser-use.com
- **Python**: >= 3.11
- **License**: MIT

---

## 1. browser-use 核心能力

### 1.1 工作原理

```
AI Agent（自然语言指令）
    ↓
browser-use Controller（解析任务）
    ↓
Browser Agent（规划操作步骤）
    ↓
Playwright/Chromium（执行浏览器操作）
    ↓
网页反馈 → 循环直到任务完成
```

### 1.2 核心功能

| 功能 | 说明 |
|------|------|
| 自然语言控制 | "点击登录按钮"、"搜索 iPhone" |
| 多种模型支持 | OpenAI / Anthropic / Google GenAI / Groq / **Ollama（本地）** |
| 多标签页管理 | 自动打开/切换/关闭标签页 |
| 内容提取 | 从页面提取结构化数据（文本、表格、链接） |
| 视觉理解 | 集成 Qwen2.5-VL 等 VLM 理解页面截图 |
| 零成本本地 | 无需任何 API Key（用 Ollama） |

### 1.3 支持的模型

```
OpenAI        → GPT-4o, GPT-4o-mini
Anthropic     → Claude 3.5 Sonnet, Claude 3 Opus
Google        → Gemini 2.0 Flash, Gemini 2.5 Pro
Groq          → Llama 3.1, Mixtral 8x7B（免费高速）
Ollama        → qwen2.5, llama3, mistral（本地免费）
```

---

## 2. 与 CDP / Puppeteer / Playwright 对比

### 2.1 横向对比表

| 维度 | **browser-use** | **Playwright** | **Puppeteer** | **CDP (MCP)** |
|------|----------------|----------------|---------------|---------------|
| **定位** | AI Agent 控制浏览器 | 跨浏览器测试框架 | Chrome 专用 | 浏览器调试协议 |
| **控制方式** | 自然语言指令 | 代码级 API | 代码级 API | 工具调用 |
| **AI 集成** | ✅ 原生 | ❌ 需自己封装 | ❌ 需自己封装 | ✅ 通过 MCP |
| **本地运行** | ✅ 免费 | ✅ 免费 | ✅ 免费 | ✅ 免费 |
| **登录态** | ⚠️ 每次新会话 | ⚠️ 需配置 | ⚠️ 需配置 | ✅ 复用已有 Chrome |
| **学习成本** | 低（自然语言） | 高（API） | 中（Node.js） | 中（协议） |
| **反爬绕过** | ⚠️ 一般（和 Playwright 类似） | ⚠️ 一般 | ⚠️ 一般 | ✅ 最佳（复用真 Chrome） |
| **多步自动化** | ✅ Agent 循环自主完成 | ❌ 需自己写循环 | ❌ 需自己写循环 | ⚠️ 需自己编排 |
| **适用场景** | AI Agent 网页任务 | Web 测试/爬虫 | Chrome 自动化 | Hermes 已有 Chrome |

### 2.2 各工具适用场景

```
browser-use  ✅  适合:
  - AI Agent 需要自主操作网页
  - 快速原型验证（无需写代码）
  - 无需登录的公开页面操作
  - 配合 Ollama 本地免费使用

Playwright  ✅  适合:
  - 需要精确控制浏览器行为
  - 跨浏览器测试（Chrome/Firefox/Safari）
  - 复杂交互流程自动化
  - 已有完整代码体系

Puppeteer   ✅  适合:
  - Node.js 项目
  - Chrome 特定功能（PDF生成等）
  - 轻量级 Chrome 自动化

CDP/MCP     ✅  适合:
  - Hermes Agent 已有的 Chrome 会话
  - 需要复用用户登录态
  - 配合 hermes-rpa 使用
```

### 2.3 关键区别：browser-use vs hermes-rpa

| | browser-use | hermes-rpa |
|---|---|---|
| **浏览器** | 启动独立浏览器实例 | 复用用户已登录的 Chrome |
| **登录态** | ❌ 每次新会话，无法保留 | ✅ 通过 CDP 复用已有 cookies |
| **控制方式** | Playwright API | AXUI + 截图 + OCR + cliclick |
| **视觉理解** | 可选集成 VLM | Baidu OCR + Qwen2.5VL |
| **适用场景** | 公开页面快速自动化 | 已登录页面（1688/微信等） |

> **结论**：1688 等需要登录的网站，用 hermes-rpa；公开页面快速任务，用 browser-use。

---

## 3. 在 Hermes 中的集成方案

### 3.1 已有的 MCP 集成

browser-use 已作为 MCP server 注册到 Hermes，工具前缀 `mcp_browser_use_`：

| 工具 | 用途 |
|------|------|
| `browser_navigate` | 打开 URL |
| `browser_get_state` | 获取页面状态 + 元素列表 |
| `browser_screenshot` | 截图（返回 bytes，不写文件） |
| `browser_click` / `browser_type` | 交互操作 |
| `browser_scroll` | 滚动页面 |
| `browser_extract_content` | 内容提取（当前版本不稳定） |
| `browser_go_back` | 后退 |
| `browser_list_tabs` / `browser_switch_tab` | 多标签页管理 |

### 3.2 验证 MCP 连接状态

```bash
hermes mcp list                    # 确认 browser_use 已注册
hermes tools list | grep browser   # 确认 tools 已启用
```

### 3.3 推荐使用场景

```
场景选择：
├── 公开页面快速操作（无需登录）
│   └── → browser-use（MCP 工具）
│
├── 需要登录态的复杂页面（1688/微信/ChatGPT）
│   └── → hermes-rpa（复用已有 Chrome + CDP）
│
├── AI Agent 自主多步任务（通用）
│   └── → browser-use + Python API（本地运行）
│
└── 需要精确控制的测试/爬虫
    └── → Playwright（代码级 API）
```

### 3.4 本地 Python 集成（推荐用于复杂任务）

对于需要 AI 自主决策的多步任务，推荐直接调用 browser-use Python API：

```python
# 安装
uv init && uv add browser-use

# 安装浏览器驱动
uvx browser-use install
```

---

## 4. 安装与配置

### 4.1 前置要求

- Python >= 3.11
- uv 包管理器（比 pip 快）
- Chromium 浏览器

### 4.2 安装步骤

```bash
# 1. 安装 uv（如已安装跳过）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 创建项目并安装 browser-use
uv init my-browser-agent
cd my-browser-agent
uv add browser-use

# 3. 安装 Chromium 浏览器
uvx browser-use install
```

### 4.3 配置 Ollama 本地模型（零成本）

```python
import os
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

# 模型会自动使用 Ollama 中已下载的模型
# 推荐: qwen2.5:latest（支持视觉）
```

---

## 5. 示例代码

### 5.1 基础示例：让 AI 自主完成网页任务

```python
from browser_use import Controller
from langchain_ollama import ChatOllama

# 初始化本地模型
llm = ChatOllama(model="qwen2.5:latest")

# 初始化 Controller
controller = Controller()

# 定义任务
task = "在 Google 上搜索 'browser-use github'，找到结果后告诉我星标数量"

# 执行
result = controller.run(task, llm=llm)
print(result)
```

### 5.2 进阶示例：带视觉理解

```python
from browser_use import Agent
from langchain_ollama import ChatOllama

llm = ChatOllama(model="qwen2.5:latest")

agent = Agent(
    task="打开 1688 搜索 LED 灯带，找到第一个商品并提取价格",
    llm=llm,
    use_vision=True,  # 启用视觉理解
)

result = agent.run()
print(result)
```

### 5.3 多步自动化：提取商品信息

```python
from browser_use import Controller
from langchain_ollama import ChatOllama
import asyncio

llm = ChatOllama(model="qwen2.5:latest")
controller = Controller()

async def scrape_1688_products(keyword: str, max_items: int = 5):
    """提取 1688 商品信息"""
    task = f"""
    1. 打开 https://s.1688.com/youzhan/market/...
    2. 搜索 '{keyword}'
    3. 按销量排序
    4. 提取前 {max_items} 个商品的信息：
       - 商品名称
       - 价格
       - 销量
       - 公司名称
    5. 将结果以 JSON 格式输出
    """
    
    result = await controller.run(task, llm=llm)
    return result

# 运行
products = asyncio.run(scrape_1688_products("LED 灯带"))
print(products)
```

### 5.4 登录态处理（配合 hermes-rpa）

```python
# browser-use 无法保留登录态，用于公开页面
# 对于需要登录的 1688 操作，使用 hermes-rpa

from browser_use import Controller
from langchain_ollama import ChatOllama

llm = ChatOllama(model="qwen2.5:latest")
controller = Controller()

# 公开页面直接用 browser-use
task = "在 Google 搜索天气，告诉我北京今天的温度"

result = controller.run(task, llm=llm)
print(result)
```

### 5.5 Hermes MCP 工具调用

```python
# 通过 Hermes 的 MCP 工具调用 browser-use
# 无需安装，直接使用已注册的 MCP 工具

# 1. 打开页面
browser_navigate(url="https://example.com")

# 2. 获取页面状态
state = browser_get_state(include_screenshot=True)

# 3. 交互操作
browser_click(ref="@e1")  # 点击元素
browser_type(text="搜索内容")  # 输入文本

# 4. 获取截图供 vision 分析
screenshot_data = browser_screenshot()
```

---

## 6. 注意事项与坑点

### 6.1 反爬警告

> ⚠️ **1688 反爬**：browser-use 的 Chrome CDP 自动化和 Playwright 一样返回虚假 HTML，仍被 1688 检测到。
> 如需操作已登录的 1688，使用 hermes-rpa（复用已有 Chrome）。

### 6.2 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 页面返回虚假 HTML | 1688 反爬检测 | 换 hermes-rpa 或 Selenium |
| 内容提取返回空 | 页面加载未完成 | 增加等待时间或重试 |
| Ollama 连接超时 | 模型未启动 | `ollama serve` 确认运行 |
| 浏览器未安装 | driver 未安装 | `uvx browser-use install` |

### 6.3 截图获取方式

MCP 工具 `browser_screenshot` 返回 JSON（含 `size_bytes`、`viewport`），**不写文件**。

若需截图用于 vision 分析：
```python
# 调用 browser_get_state(include_screenshot=true) 获取 base64 截图
state = browser_get_state(include_screenshot=True)
# 截图数据直接在返回结果中
```

---

## 7. 相关 Skill 关联

| Skill | 关系 |
|-------|------|
| `hermes-rpa` | 已登录页面的浏览器自动化（复用 Chrome） |
| `autonomous-ai-agents` | AI Agent 框架总览（含 browser-use 参考文档） |
| `using-agent-skills` | 技能导航（browser-use 在其中标注为"通用浏览器自动化"） |
| `1688-automation` | 1688 采购完整流程（底层用 hermes-rpa） |

## Verification

验证清单：

- [ ] 理解 browser-use 与 Playwright/Puppeteer 的定位差异
- [ ] 确认使用场景：公开页面用 browser-use，已登录页面用 hermes-rpa
- [ ] 知道如何安装：`uv add browser-use` + `uvx browser-use install`
- [ ] 了解 Ollama 集成：设置 `OLLAMA_BASE_URL` 环境变量
- [ ] 清楚 1688 反爬限制，不在 browser-use 上浪费精力
