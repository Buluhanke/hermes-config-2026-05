# MCP Server Setup for Python Agents (supply-agent Pattern)

## The Pattern

When a Python agent is distributed as a zip/package (not a REST API), the setup workflow is:

1. Extract the zip to a directory
2. Create a JSON-RPC stdio MCP wrapper that imports and calls the agent's `run_agent()` function
3. Register the wrapper in `~/.hermes/config.yaml` under `mcp_servers:`
4. Restart the gateway

## Step-by-Step

### 1. Extract the agent package

```bash
rm -rf ~/supply-agent && mkdir -p ~/supply-agent
unzip /path/to/agent.zip -d ~/supply-agent
```

### 2. Verify the agent works standalone first

```python
import sys
sys.path.insert(0, '/path/to/agent-dir')
from agent import run_agent
result = run_agent('spec', '10x10x10 cm')
print(result)
```

**Pitfall: formatter.py syntax errors** — Python packages with f-strings or multi-line strings containing emoji/newlines can have syntax errors when extracted. Test directly before wrapping.

### 3. Create the MCP wrapper

Write `/path/to/agent-dir/mcp_server.py`:

```python
#!/usr/bin/env python3
"""MCP server wrapping supply-agent."""

import sys, json

sys.path.insert(0, '/path/to/agent-dir')
from agent import run_agent

def handle_request(req):
    method = req.get("method", "")
    params = req.get("params", {})
    req_id = req.get("id")

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "supply_agent", "version": "1.0.0"}
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "run_supply_agent",
                        "description": "运行供应链智能体，搜索1688/拼多多/淘宝/义乌供应商",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "input_type": {"type": "string", "enum": ["spec", "image", "text"]},
                                "input_data": {"type": "string"}
                            },
                            "required": ["input_type", "input_data"]
                        }
                    }
                ]
            }
        elif method == "tools/call":
            tool = params.get("name")
            args = params.get("arguments", {})
            if tool == "run_supply_agent":
                output = run_agent(args.get("input_type"), args.get("input_data"))
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
        resp = handle_request(json.loads(line))
        print(json.dumps(resp), flush=True)

if __name__ == "__main__":
    main()
```

### 4. Register in config.yaml

```yaml
mcp_servers:
  supply_agent:
    command: python3
    args:
    - /path/to/agent-dir/mcp_server.py
```

### 5. Restart gateway

```bash
hermes gateway restart
```

## `fallback_providers` Must Be Set Explicitly

When configuring custom providers as fallbacks, `fallback_providers` in `config.yaml` **defaults to `[]`** — an empty list means no automatic fallback occurs even if `custom_providers` is correctly configured. The agent will fail with 401 instead of switching to the备用模型.

```yaml
model:
  default: MiniMax-M2.7-highspeed
  provider: aicodee

fallback_providers:
- gemini        # must be explicitly set — empty [] = no fallback

custom_providers:
- api_key: YOUR_API_KEY...
  name: aicodee
  base_url: https://v2.aicodee.com/v1
  default_model: MiniMax-M2.7-highspeed
- api_key: GOOGLE_AI_KEY_REDACTED...
  name: gemini
  base_url: https://generativelanguage.googleapis.com/v1beta
  default_model: gemini-2.0-flash
```

The `fallback_providers` list names must match the `name` field in `custom_providers`.

## WeCom Platform Configuration (企业微信机器人)

To add an enterprise WeChat bot:

```yaml
platforms:
  wecom:
    enabled: true
    extra:
      bot_id: "your-bot-id"
      secret: "your-secret"
      websocket_url: "wss://openws.work.weixin.qq.com"
      dm_policy: "open"        # open | allowlist | disabled | pairing
      group_policy: "open"     # open | allowlist | disabled
```

Then `hermes gateway restart`.

Note: `wecom` (企业微信) and `weixin` (个人微信/微信对话开放平台) are separate platforms in Hermes. Both can run simultaneously.
