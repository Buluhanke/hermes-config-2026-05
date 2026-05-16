# Python 模块 MCP 包装器模板

## 背景

有时你要接入 Hermes 的不是 REST API（用 HTTP URL 配置），也不是 npx/uvx 的社区 MCP 服务器（用 command+args 配置），而是一个**本地 Python 包**。

解决方案：写一个 Python stdio MCP 服务器作为中间层，Hermes 通过 `command: python3` + `args: [mcp_server.py]` 启动它。

## 模板结构

```
your-package/
├── agent.py              # 原始包入口
├── mcp_server.py          # MCP 包装器（新增）
└── ...
```

## mcp_server.py 模板

```python
#!/usr/bin/env python3
"""MCP server wrapping <package-name>."""

import sys
import json

sys.path.insert(0, '/absolute/path/to/your/package')
from agent import run_agent   # 你的包入口

def handle_request(req):
    method = req.get("method", "")
    params = req.get("params", {})
    req_id = req.get("id")

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "your_package", "version": "1.0.0"}
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "your_tool_name",
                        "description": "工具描述",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "param1": {"type": "string", "description": "参数1"},
                            },
                            "required": ["param1"]
                        }
                    }
                ]
            }
        elif method == "tools/call":
            tool = params.get("name")
            args = params.get("arguments", {})

            if tool == "your_tool_name":
                output = run_agent(args.get("param1", ""))
                result = {"content": [{"type": "text", "text": json.dumps(output, ensure_ascii=False)}]}
            else:
                result = {"content": [{"type": "text", "text": f"Unknown tool: {tool}"}]}
        else:
            result = None

        response = {"jsonrpc": "2.0", "id": req_id, "result": result} if result else \
                   {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}
    except Exception as e:
        response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}}

    return response

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        resp = handle_request(req)
        print(json.dumps(resp), flush=True)

if __name__ == "__main__":
    main()
```

## Hermes 配置

在 `~/.hermes/config.yaml` 添加：

```yaml
mcp_servers:
  your_server_name:
    command: python3
    args:
    - /absolute/path/to/your/package/mcp_server.py
```

## 验证步骤

```bash
# 1. 手动测试 MCP 服务器（模拟 Hermes 发 JSON-RPC）
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"your_tool_name","arguments":{"param1":"test"}}}' \
  | python3 /path/to/mcp_server.py

# 2. 重启 Hermes
hermes gateway restart

# 3. 检查 MCP 是否加载（看日志）
hermes logs --level info --lines 30 | grep -i mcp
```

## 已知问题 & 解决

| 问题 | 原因 | 解决 |
|------|------|------|
| SyntaxError（string literal） | 多行字符串没转义 | 用 `\\n` 或 `"""` 包裹 |
| ModuleNotFoundError | sys.path 没加对 | 确保 `/absolute/path` 正确 |
| Hermes 找不到工具 | MCP server 没重启 | `hermes gateway restart` |
| Connection refused | REST API 没启动 | 确保后端服务先跑起来 |

## 本会话案例

- **supply-agent-v11** (`~/supply-agent-v11/`): Python 包，入口 `run_agent(input_type, input_data)`
- 包装后工具名：`mcp_supply_agent_run_supply_agent`
- 当前返回 mock 数据（格式化示例），真实平台（1688/拼多多/淘宝/义乌）待接入
