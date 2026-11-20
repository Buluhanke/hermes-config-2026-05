---
name: wps-office-mac-automation
description: "WPS Mac自动化。Use when natural language WPS on Mac"
category: productivity
version: 1.0.0
author: user
license: MIT
metadata:
  hermes:
    tags: [wps, office, mac, automation, mcp]
    related_skills: []
---

# WPS Office Mac Automation (MCP + Skills)

## When to Use
- User wants to automate WPS Office (Word/Excel/PPT) on macOS using natural language
- User asks to create, edit, or convert WPS documents programmatically
- User needs WPS formulas, formatting, or batch operations

## Trigger
User wants to automate WPS Office on macOS using natural language (create docs, edit spreadsheets, generate PPTs, convert formats).

## Core Problem
- Mac 版 WPS **不支持 VBA/COM**（Windows 专属，macOS 沙盒限制）
- Mac 版 WPS 仅支持 JSA 宏（JavaScript API），功能受限
- 需要通过 MCP + Skills 双层架构实现自动化

## Solution: wps-skills (dividduang/wps-skills)

### 架构
```
Hermes/Claude → MCP Server (HTTP:58891) → WPS 加载项 (轮询客户端) → WPS Office
```
- macOS: 逆向轮询模式（WPS 加载项每 500ms 轮询 MCP Server）
- Windows: COM 桥接模式（PowerShell → WPS COM 对象）
- macOS 功能完整（196 工具），Windows 仅基础功能（~25 工具）

### 安装

1. 下载：`curl -sL https://codeload.github.com/dividduang/wps-skills/tar.gz/refs/heads/main -o /tmp/wps-skills.tar.gz`
2. 解压：`tar -xzf /tmp/wps-skills.tar.gz && mv wps-skills-main wps-skills`
3. 运行安装：`cd wps-skills && bash scripts/auto-install-mac.sh`
4. 注册 MCP：`hermes config set mcp_servers.wps_office.command node` + args + enabled
5. 重启 WPS Office + Hermes gateway

### 验证
- `ls ~/.claude/skills/` → 应有 wps-excel/word/ppt/office
- `ls ~/Library/Containers/com.kingsoft.wpsoffice.mac/Data/.kingsoft/wps/jsaddons/claude-assistant_` → 加载项已装
- 打开 WPS → 「Claude助手」选项卡 → 状态「轮询中」

### 使用方式
自然语言控制 WPS：
- "帮我写个 VLOOKUP 公式查价格"
- "把这份 Excel 导出为 PDF"
- "在 PPT 第 3 页插入柱状图"

### 4 Skills
| Skill | 覆盖 | 工具数 |
|---|---|---|
| wps-excel | 单元格读写、公式、排序、筛选、条件格式 | ~60 |
| wps-word | 段落、标题、表格、图片、页眉页脚 | ~50 |
| wps-ppt | 幻灯片、形状、文本框、动画 | ~40 |
| wps-office | 跨应用协调、文件 I/O、格式转换 | ~46 |

### Pitfalls
- **Mac 版 WPS 无法用 VBA/COM**：macOS 沙盒限制，COM 是 Windows 专属。Mac 上只能用 JSA 宏或 MCP+Skills。
- **WPS 加载项必须在 WPS 客户端内运行**：加载项是内嵌网页 + JS 桥接，不能在浏览器里直接运行。
- **WPS 加载项目录名必须以 `_` 结尾**：`claude-assistant_`，否则 WPS 不识别为开发模式加载项。
- **MCP Server 端口 58891**：macOS 用逆向轮询（加载项轮询 MCP），不是 MCP 主动连接 WPS。
- **安装脚本找不到 `claude` 命令**：Hermes 环境下 `claude` CLI 可能不在 PATH，需手动 `hermes config set`。
- **WPS 必须重启**：加载项安装后，WPS 不重启不会加载新加载项。
- **Gateway 必须重启**：MCP config 修改后，Hermes gateway 需 HUP 重载才能识别新 server.
- **Dev 模式加载项可能不自动加载**：publish.xml 设置 `enable="enable_dev"`，WPS 可能需要手动启用。若打开 WPS 后菜单栏无「Claude助手」选项卡，进入 WPS → 工具 → 加载项 → 启用「Claude助手」。MCP poll 端点返回空 = add-in 未连接。

### Alternative: Python 直接读写（不启动 WPS）
```python
from openpyxl import load_workbook
from docx import Document
wb = load_workbook("data.xlsx")
ws = wb.worksheets[0]
ws["A1"] = "Hello"
wb.save("data.xlsx")
```
适用：批量数据处理、不需 WPS 渲染的场景。不支持公式计算、图表联动。