# Wrapping a REST API as an MCP Server for Hermes

When you have a REST API service and want to expose it as MCP tools to Hermes (so any messaging platform can call it), write a Python stdio MCP server that wraps the REST calls.

## Pattern

```python
#!/usr/bin/env python3
"""MCP server wrapping your REST API."""

import sys
import json
import urllib.request

BASE_URL = "http://localhost:3001"  # your REST API base URL

def api_get(endpoint):
    with urllib.request.urlopen(f"{BASE_URL}{endpoint}") as resp:
        return json.loads(resp.read())

def api_post(endpoint, data):
    payload = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def handle_request(req):
    method = req.get("method", "")
    params = req.get("params", {})
    req_id = req.get("id")

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "your_agent_name", "version": "1.0.0"}
            }

        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "your_tool_name",
                        "description": "What the tool does",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "arg1": {"type": "string", "description": "Description"},
                            },
                            "required": ["arg1"]
                        }
                    }
                ]
            }

        elif method == "tools/call":
            tool = params.get("name")
            args = params.get("arguments", {})

            if tool == "your_tool_name":
                output = api_get("/api/endpoint")  # or api_post()
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

## Installing and Wiring to Hermes

1. **Write the MCP server** to `/path/to/your_agent/mcp_server.py`

2. **Test it manually:**
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"your_tool_name","arguments":{"arg1":"value"}}}' \
  | python3 /path/to/your_agent/mcp_server.py
```

3. **Add to Hermes config.yaml:**
```yaml
mcp_servers:
  your_agent:
    command: python3
    args:
      - /path/to/your_agent/mcp_server.py
```

4. **Restart Hermes:**
```bash
hermes gateway restart
```

5. **Verify tools loaded:**
Look for `MCP servers have been reloaded. Added servers: your_agent. N MCP tool(s) now available.`

## Tool Naming

MCP tools are registered as `mcp_{server_name}_{tool_name}`. If server name is `supply_agent` and tool name is `run_supply_agent`, the full tool name is `mcp_supply_agent_run_supply_agent`.

## REST API Must Be Running

The MCP wrapper calls `http://localhost:PORT` — the REST API service must be running before Hermes starts. If the REST API dies, the MCP tool calls will fail with connection errors.

Keep both running:
- REST API: `node server.js` (or equivalent)
- MCP wrapper: started automatically by Hermes at gateway startup

## Example: supply-agent-v11

Used in this session for a supply-chain procurement agent:
- REST API at `localhost:3001`
- MCP wrapper at `/Users/mac/supply-agent-v11/mcp_server.py`
- Tools exposed: `run_supply_agent` (input_type: spec|image|text + input_data)
