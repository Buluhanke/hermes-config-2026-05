---
name: mcp-server-build
description: FastMCP自建MCP Server指南
version: 1.0.0
---

# MCP Server自建 — FastMCP框架

## When to Use
- 需要扩展AI工具能力
- 连接私有API到AI助手
- 自定义工具/资源/提示

## Core Features
- **tools**：可调用函数，带参数定义
- **resources**：静态数据/文件访问
- **prompts**：预定义提示模板
- **stdio调试**：通过标准输入输出通信

## Quick Start
```python
# server.py
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def search_code(query: str) -> str:
    """搜索代码库"""
    return f"找到: {query}"

@mcp.resource("file://README")
def readme() -> str:
    return open("README.md").read()

@mcp.prompt()
def review_code(file: str) -> str:
    return f"审查这个文件: {file}"

# 运行
mcp.run()
```

```json
// 客户端配置 (cursor_settings.json)
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["server.py"]
    }
  }
}
```

## Pitfalls
- stdio通信调试困难
- 工具参数类型需要严格定义
- 安全沙盒配置复杂
- 多语言SDK一致性
- 版本升级API变化
