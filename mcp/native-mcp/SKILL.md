---
name: native-mcp
description: "MCP client: connect servers, register tools (stdio/HTTP)."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [MCP, Tools, Integrations]
    related_skills: [mcporter]
---

# Native MCP Client

Hermes Agent has a built-in MCP client that connects to MCP servers at startup, discovers their tools, and makes them available as first-class tools the agent can call directly. No bridge CLI needed -- tools from MCP servers appear alongside built-in tools like `terminal`, `read_file`, etc.

## When to Use

Use this whenever you want to:
- Connect to MCP servers and use their tools from within Hermes Agent
- Add external capabilities (filesystem access, GitHub, databases, APIs) via MCP
- Run local stdio-based MCP servers (npx, uvx, or any command)
- Connect to remote HTTP/StreamableHTTP MCP servers
- Have MCP tools auto-discovered and available in every conversation

For ad-hoc, one-off MCP tool calls from the terminal without configuring anything, see the `mcporter` skill instead.

## Prerequisites

- **mcp Python package** -- optional dependency; install with `pip install mcp`. If not installed, MCP support is silently disabled.
- **Node.js** -- required for `npx`-based MCP servers (most community servers)
- **uv** -- required for `uvx`-based MCP servers (Python-based servers)

Install the MCP SDK:

```bash
pip install mcp
# or, if using uv:
uv pip install mcp
```

## Quick Start

Add MCP servers to `~/.hermes/config.yaml` under the `mcp_servers` key:

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Restart Hermes Agent. On startup it will:
1. Connect to the server
2. Discover available tools
3. Register them with the prefix `mcp_time_*`
4. Inject them into all platform toolsets

You can then use the tools naturally -- just ask the agent to get the current time.

## Configuration Reference

Each entry under `mcp_servers` is a server name mapped to its config. There are two transport types: **stdio** (command-based) and **HTTP** (url-based).

### Stdio Transport (command + args)

```yaml
mcp_servers:
  server_name:
    command: "npx"             # (required) executable to run
    args: ["-y", "pkg-name"]   # (optional) command arguments, default: []
    env:                       # (optional) environment variables for the subprocess
      SOME_API_KEY: "value"
    timeout: 120               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### HTTP Transport (url)

```yaml
mcp_servers:
  server_name:
    url: "https://my-server.example.com/mcp"   # (required) server URL
    headers:                                     # (optional) HTTP headers
      Authorization: "Bearer YOUR_API_KEY..."
    timeout: 180               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### All Config Options

| Option            | Type   | Default | Description                                       |
|-------------------|--------|---------|---------------------------------------------------|
| `command`         | string | --      | Executable to run (stdio transport, required)     |
| `args`            | list   | `[]`    | Arguments passed to the command                   |
| `env`             | dict   | `{}`    | Extra environment variables for the subprocess    |
| `url`             | string | --      | Server URL (HTTP transport, required)             |
| `headers`         | dict   | `{}`    | HTTP headers sent with every request              |
| `timeout`         | int    | `120`   | Per-tool-call timeout in seconds                  |
| `connect_timeout` | int    | `60`    | Timeout for initial connection and discovery      |

Note: A server config must have either `command` (stdio) or `url` (HTTP), not both.

## How It Works

### Startup Discovery

When Hermes Agent starts, `discover_mcp_tools()` is called during tool initialization:

1. Reads `mcp_servers` from `~/.hermes/config.yaml`
2. For each server, spawns a connection in a dedicated background event loop
3. Initializes the MCP session and calls `list_tools()` to discover available tools
4. Registers each tool in the Hermes tool registry

### Tool Naming Convention

MCP tools are registered with the naming pattern:

```
mcp_{server_name}_{tool_name}
```

Hyphens and dots in names are replaced with underscores for LLM API compatibility.

Examples:
- Server `filesystem`, tool `read_file` → `mcp_filesystem_read_file`
- Server `github`, tool `list-issues` → `mcp_github_list_issues`
- Server `my-api`, tool `fetch.data` → `mcp_my_api_fetch_data`

### Auto-Injection

After discovery, MCP tools are automatically injected into all `hermes-*` platform toolsets (CLI, Discord, Telegram, etc.). This means MCP tools are available in every conversation without any additional configuration.

### Connection Lifecycle

- Each server runs as a long-lived asyncio Task in a background daemon thread
- Connections persist for the lifetime of the agent process
- If a connection drops, automatic reconnection with exponential backoff kicks in (up to 5 retries, max 60s backoff)
- On agent shutdown, all connections are gracefully closed

### Idempotency

`discover_mcp_tools()` is idempotent -- calling it multiple times only connects to servers that aren't already connected. Failed servers are retried on subsequent calls.

## Transport Types

### Stdio Transport

The most common transport. Hermes launches the MCP server as a subprocess and communicates over stdin/stdout.

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

The subprocess inherits a **filtered** environment (see Security section below) plus any variables you specify in `env`.

### HTTP / StreamableHTTP Transport

For remote or shared MCP servers. Requires the `mcp` package to include HTTP client support (`mcp.client.streamable_http`).

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer YOUR_API_KEY..."
```

If HTTP support is not available in your installed `mcp` version, the server will fail with an ImportError and other servers will continue normally.

## Security

### Environment Variable Filtering

For stdio servers, Hermes does NOT pass your full shell environment to MCP subprocesses. Only safe baseline variables are inherited:

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`
- Any `XDG_*` variables

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      # Only this token is passed to the subprocess
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

### Credential Stripping in Error Messages

If an MCP tool call fails, any credential-like patterns in the error message are automatically redacted before being shown to the LLM. This covers:

- GitHub PATs (`ghp_...`)
- OpenAI-style keys (`YOUR_API_KEY...`)
- Bearer tokens
- Generic `token=`, `key=`, `API_KEY=`, `password=`, `secret=` patterns

## Troubleshooting

### "MCP SDK not available -- skipping MCP tool discovery"

The `mcp` Python package is not installed. Install it:

```bash
pip install mcp
```

### "No MCP servers configured"

No `mcp_servers` key in `~/.hermes/config.yaml`, or it's empty. Add at least one server.

### "Failed to connect to MCP server 'X'"

Common causes:
- **Command not found**: The `command` binary isn't on PATH. Ensure `npx`, `uvx`, or the relevant command is installed.
- **Package not found**: For npx servers, the npm package may not exist or may need `-y` in args to auto-install.
- **Timeout**: The server took too long to start. Increase `connect_timeout`.
- **Port conflict**: For HTTP servers, the URL may be unreachable.

### "MCP server 'X' requires HTTP transport but mcp.client.streamable_http is not available"

Your `mcp` package version doesn't include HTTP client support. Upgrade:

```bash
pip install --upgrade mcp
```

### Tools not appearing

- Check that the server is listed under `mcp_servers` (not `mcp` or `servers`)
- Ensure the YAML indentation is correct
- Look at Hermes Agent startup logs for connection messages
- Tool names are prefixed with `mcp_{server}_{tool}` -- look for that pattern
- **Test the MCP server manually first** (see Debugging section below) before adding to config

### Common pitfall: mcp-chrome-stdio binary exists and Chrome has --load-extension, but no MCP tools appear

This happens when `config.yaml` was overwritten and the `mcp_servers` section was removed. The binary, the Chrome extension, and the Hermes MCP config are three independent pieces — all must be present.

Diagnosis:
```bash
which mcp-chrome-stdio                     # binary installed?
ps aux | grep "mcp-chrome-extension" | grep -v grep  # Chrome loaded?
grep -A3 "mcp_servers" ~/.hermes/config.yaml         # config present?
grep "registered.*tool.*from chrome" ~/.hermes/logs/agent.log  # logs confirm?
```

Fix: add to `~/.hermes/config.yaml`:
```yaml
mcp_servers:
  chrome:
    command: "mcp-chrome-stdio"
    timeout: 120
    connect_timeout: 60
```
Then `hermes gateway restart`. Verify with `grep "registered" ~/.hermes/logs/agent.log`.

### Connection keeps dropping

The client retries up to 5 times with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at 60s). If the server is fundamentally unreachable, it gives up after 5 attempts. Check the server process and network connectivity.

### MCP server wraps REST API but tool calls fail with "Connection refused"

If your MCP server is a wrapper around a REST API (common pattern: Python/Node script that forwards MCP tool calls to a local REST service), the underlying REST service **must stay running**. The MCP server process itself can stay alive while the backend REST API dies silently.

Symptoms: MCP server process is running (`ps aux | grep mcp_server`), but all tool calls return "Connection refused". WeChat/other platform reports the service is down.

Fix: Keep the REST backend running with a supervisor (see `references/auto-purchase-mcp/` for the auto_purchase_agent setup which uses this pattern). Monitor and restart the REST API if it dies:

```bash
# Check if REST API is running
curl -s http://localhost:3001/api/suppliers

# If not, restart it
cd ~/auto_purchase_agent_v2 && node server.js &
```

### Clean reinstall of a Node.js REST API + MCP wrapper

If reinstalling from a zip (e.g. auto_purchase_agent_v2.zip):

1. Kill all processes (REST API + MCP wrapper)
2. Wipe the entire project directory — do NOT reuse node_modules or data from old install
3. Extract zip to fresh directory
4. `npm install` to regenerate node_modules
5. Recreate MCP wrapper script (not in the zip)
6. Start REST API, then start MCP wrapper
7. Restart Hermes gateway

```bash
# Full clean reinstall
pkill -f "mcp_server.py"; pkill -f "node.*server.js"
rm -rf ~/auto_purchase_agent_v2
mkdir ~/auto_purchase_agent_v2
unzip -o /path/to/new_version.zip -d ~/auto_purchase_agent_v2
cd ~/auto_purchase_agent_v2 && npm install
# Recreate mcp_server.py...
mkdir -p data && node server.js &
python3 mcp_server.py &
hermes gateway restart
```

## Debugging an MCP Server

### Test stdio MCP server manually

Before adding a server to `config.yaml`, test it standalone:

```bash
# List tools
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python3 /path/to/mcp_server.py

# Call a tool
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"tool_name","arguments":{}}}' | python3 /path/to/mcp_server.py
```

A working server returns JSON-RPC responses. If it hangs or errors, fix the server first.

### pip install mcp timeout

If `pip install mcp` times out (common on slow networks), try:

```bash
uv pip install mcp --system
```

Or use a stdio MCP server written in Node.js instead (no `mcp` package needed on host).

## Wrapping a Plain REST API as an MCP Server

If the service you want to connect is a plain REST API (not an MCP server itself), you need to write a **wrapper MCP server** that translates MCP tool calls into HTTP requests. Use Python or Node.js stdio MCP server — Hermes launches it as a subprocess and communicates over stdin/stdout.

### Python stdio MCP server template

Minimal Python MCP server wrapping any REST API:

```python
#!/usr/bin/env python3
"""MCP server that wraps a REST API as MCP tools."""
import sys, json, urllib.request, urllib.parse

BASE_URL = "http://localhost:3001"  # your REST API base URL

def handle_request(req):
    method = req.get("method", "")
    params = req.get("params", {})
    req_id = req.get("id")

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "my_api", "version": "1.0.0"}
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "my_tool",
                        "description": "What the tool does",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"arg1": {"type": "string"}},
                            "required": ["arg1"]
                        }
                    }
                ]
            }
        elif method == "tools/call":
            tool = params.get("name")
            args = params.get("arguments", {})
            # Dispatch and call REST API
            result = {"content": [{"type": "text", "text": json.dumps(api_result)}]}
        else:
            result = None
        response = {"jsonrpc": "2.0", "id": req_id, "result": result}
    except Exception as e:
        response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}}
    return response

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    resp = handle_request(json.loads(line))
    print(json.dumps(resp), flush=True)
```

### Config for custom MCP wrapper

```yaml
mcp_servers:
  my_api:
    command: "python3"
    args: ["/path/to/mcp_server.py"]
    timeout: 30
```

Tools appear as `mcp_my_api_my_tool` after Hermes restart.

### Common pitfalls

- **JSON-RPC protocol**: Use `"2.0"` not `"1.0"`. Missing version causes silent failures.
- **Flush output**: `print(json.dumps(resp), flush=True)` — without `flush=True`, Hermes may timeout waiting for response.
- **urllib timeout**: Set a timeout on `urlopen` or it blocks forever: `urlopen(url, timeout=10)`.
- **Unicode**: Use `ensure_ascii=False` when dumping JSON from REST APIs returning Chinese characters.
- **JSON in text field**: MCP protocol returns tool results as `{"content": [{"type": "text", "text": "..."}]}`, not raw JSON strings.

## MCP Server 模板库

当需要给本地 Python 包写 MCP 包装器时，见：

- [references/python-package-mcp-wrapper.md](references/python-package-mcp-wrapper.md) — 完整模板 + 验证步骤

**Python agent package as MCP server (supply-agent-v11):** `references/mcp-server-python-agent-setup.md`

**Python package MCP wrapper (supply-agent-v11):** `references/supply-agent-mcp-wrapper.md`

**WeCom platform config:** same reference above.

**Pitfall: formatter.py syntax errors** — test the agent directly before wrapping. Run `cd /path/to/agent && python3 -c "from agent import run_agent; print(run_agent('spec','test'))"` to verify.

**Pitfall: `fallback_providers: []` must be set explicitly** — see reference above for the correct config.

## Examples

### Time Server (uvx)

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Registers tools like `mcp_time_get_current_time`.

### Filesystem Server (npx)

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    timeout: 30
```

Registers tools like `mcp_filesystem_read_file`, `mcp_filesystem_write_file`, `mcp_filesystem_list_directory`.

### GitHub Server with Authentication

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
    timeout: 60
```

Registers tools like `mcp_github_list_issues`, `mcp_github_create_pull_request`, etc.

### Remote HTTP Server

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.mycompany.com/v1/mcp"
    headers:
      Authorization: "Bearer YOUR_API_KEY"
      X-Team-Id: "engineering"
    timeout: 180
    connect_timeout: 30
```

### Multiple Servers

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]

  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"

  company_api:
    url: "https://mcp.internal.company.com/mcp"
    headers:
      Authorization: "Bearer YOUR_API_KEY"
    timeout: 300
```

All tools from all servers are registered and available simultaneously. Each server's tools are prefixed with its name to avoid collisions.

## Sampling (Server-Initiated LLM Requests)

Hermes supports MCP's `sampling/createMessage` capability — MCP servers can request LLM completions through the agent during tool execution. This enables agent-in-the-loop workflows (data analysis, content generation, decision-making).

Sampling is **enabled by default**. Configure per server:

```yaml
mcp_servers:
  my_server:
    command: "npx"
    args: ["-y", "my-mcp-server"]
    sampling:
      enabled: true           # default: true
      model: "gemini-3-flash" # model override (optional)
      max_tokens_cap: 4096    # max tokens per request
      timeout: 30             # LLM call timeout (seconds)
      max_rpm: 10             # max requests per minute
      allowed_models: []      # model whitelist (empty = all)
      max_tool_rounds: 5      # tool loop limit (0 = disable)
      log_level: "info"       # audit verbosity
```

Servers can also include `tools` in sampling requests for multi-turn tool-augmented workflows. The `max_tool_rounds` config prevents infinite tool loops. Per-server audit metrics (requests, errors, tokens, tool use count) are tracked via `get_mcp_status()`.

Disable sampling for untrusted servers with `sampling: { enabled: false }`.

### Remote HTTP Server

For a complete working example of this MCP+REST wrapper pattern (auto_purchase_agent), see `references/auto-purchase-mcp.md`.

## MCP Server 开发模板

MCP 服务器开发有三种常见场景：

### 场景 A: Python 包包装器（本地模块 → MCP）

适用于已有 Python 模块/包，想暴露为 MCP 工具。

```
your-package/
├── agent.py              # 原始包入口
├── mcp_server.py          # MCP 包装器
└── ...
```

完整模板：

```python
#!/usr/bin/env python3
"""MCP server wrapping <package-name>."""
import sys, json

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

配置：

```yaml
mcp_servers:
  your_server_name:
    command: python3
    args:
    - /absolute/path/to/your/package/mcp_server.py
    timeout: 30
```

### 场景 B: REST API 包装器（HTTP 后端 → MCP stdio）

适用于有 REST API 后端，想包装为 MCP 工具的场景。

```python
#!/usr/bin/env python3
"""MCP server wrapping a REST API as MCP tools."""
import sys, json, urllib.request, urllib.parse

BASE_URL = "http://localhost:3001"  # REST API base URL

def api_get(path, params=None):
    url = BASE_URL + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())

def handle_request(req):
    method = req.get("method", "")
    params = req.get("params", {})
    req_id = req.get("id")

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "my_api", "version": "1.0.0"}
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "get_suppliers",
                        "description": "获取供应商列表",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "status": {"type": "string", "description": "供应商状态"}
                            }
                        }
                    },
                    {
                        "name": "get_product_detail",
                        "description": "获取商品详情",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "productId": {"type": "string", "description": "商品ID"}
                            },
                            "required": ["productId"]
                        }
                    }
                ]
            }
        elif method == "tools/call":
            tool = params.get("name")
            args = params.get("arguments", {})
            if tool == "get_suppliers":
                data = api_get("/api/suppliers", {"status": args.get("status", "active")})
                result = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}
            elif tool == "get_product_detail":
                data = api_get(f"/api/products/{args['productId']}")
                result = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}
            else:
                result = {"content": [{"type": "text", "text": f"Unknown tool: {tool}"}]}
        else:
            result = None

        response = {"jsonrpc": "2.0", "id": req_id, "result": result} if result else \
                   {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}
    except Exception as e:
        response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}}

    return response

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    resp = handle_request(json.loads(line))
    print(json.dumps(resp), flush=True)
```

### 场景 C: Node.js stdio MCP 服务器

适用于社区现有 Node.js MCP 包，或用 JavaScript 包装现有服务。

```javascript
#!/usr/bin/env node
// mcp_server.js — Node.js stdio MCP server
const readline = require('readline');

const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: false });

function sendResponse(response) {
  console.log(JSON.stringify(response));
}

rl.on('line', (line) => {
  if (!line.trim()) return;
  const req = JSON.parse(line);
  const { method, params = {}, id } = req;

  try {
    if (method === 'initialize') {
      sendResponse({ jsonrpc: '2.0', id, result: {
        protocolVersion: '2024-11-05',
        capabilities: { tools: {} },
        serverInfo: { name: 'my-node-server', version: '1.0.0' }
      }});
    } else if (method === 'tools/list') {
      sendResponse({ jsonrpc: '2.0', id, result: {
        tools: [{
          name: 'hello',
          description: 'Say hello',
          inputSchema: { type: 'object', properties: { name: { type: 'string' }}, required: ['name'] }
        }]
      }});
    } else if (method === 'tools/call') {
      const { name, arguments: args } = params;
      if (name === 'hello') {
        sendResponse({ jsonrpc: '2.0', id, result: {
          content: [{ type: 'text', text: `Hello, ${args.name}!` }]
        }});
      }
    }
  } catch (e) {
    sendResponse({ jsonrpc: '2.0', id, error: { code: -32603, message: e.message }});
  }
});
```

配置：

```yaml
mcp_servers:
  my_node:
    command: node
    args: ["/path/to/mcp_server.js"]
```

### MCP 服务器开发 Checklist

- [ ] JSON-RPC version 必须是 `"2.0"`（不是 `"1.0"`）
- [ ] 输出必须 `flush=True`（Python）或 `console.log()` 后立即 flush（Node.js）
- [ ] `initialize` 必须返回 `protocolVersion` + `capabilities` + `serverInfo`
- [ ] `tools/list` 返回的工具 `name` 建议用 snake_case（MCP 规范）
- [ ] `tools/call` 的 `arguments` 是 dict，直接下标访问即可
- [ ] REST API 包装器必须设置 `urllib.timeout`，否则会永久阻塞
- [ ] 中文/特殊字符用 `ensure_ascii=False`
- [ ] 先手动测试，再加入 `config.yaml`（见 Debugging 章节）

---

## 1688 场景工具注册

### 1688 平台 MCP 工具注册流程

```
注册 ISV 应用 → 获取 appKey + appSecret → 申请 API 权限 → 包装为 MCP 工具
```

### 1688 MCP 工具配置模板

```yaml
mcp_servers:
 .alibaba:
    command: python3
    args: ["/path/to/alibaba_mcp_server.py"]
    env:
      ALIBABA_APP_KEY: "your_app_key"
      ALIBABA_APP_SECRET: "your_app_secret"
      ACCESS_TOKEN: "your_access_token"  # OAuth2 token
    timeout: 60
    connect_timeout: 30
```

### 1688 常用 API → MCP 工具映射

| 1688 API | MCP 工具名 | 用途 |
|----------|-----------|------|
| `alibaba.product.get` | `mcp_alibaba_product_get` | 获取商品详情 |
| `alibaba.category.attribute.get` | `mcp_alibaba_category_attr` | 获取类目属性 |
| `alibaba.logistics.offline.send` | `mcp_alibaba_logistics_send` | 物流发货 |
| `alibaba.trade.order.list.get` | `mcp_alibaba_orders` | 订单列表 |
| `alibaba.product.upload` | `mcp_alibaba_product_upload` | 商品上传 |

### 1688 API 签名计算（必须）

1688 API 需要 **RSA 签名**，不能直接用 appSecret 签名。在 MCP 服务器中：

```python
import base64, hashlib, rsa, time, urllib.parse

def sign(params, app_secret):
    """1688 API 签名：MD5(appSecret + sorted_query_string + appSecret)"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    query_string = "&".join(f"{k}={v}" for k, v in sorted_params)
    to_sign = app_secret + query_string + app_secret
    return hashlib.md5(to_sign.encode()).hexdigest().upper()

def build_request(api_name, params, app_key, app_secret):
    common = {
        "app_key": app_key,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "format": "json",
        "v": "1.0",
        "sign_method": "md5",
    }
    all_params = {**common, **params}
    all_params["sign"] = sign(all_params, app_secret)
    return all_params
```

### 1688 在线测试工具自动化

1688 API 文档页的**在线测试工具**可以自动化：

```python
# 见 references/online-test-tool.md
# URL: https://open.1688.com/api/apiTool.htm?ns=<namespace>&n=<api_name>&v=<version>
```

### 1688 工具注册 Checkpoint

- [ ] ISV 注册审核通过（公司认证）
- [ ] appKey + appSecret 已获取
- [ ] 需要的 API 权限已申请并审批
- [ ] MCP 服务器手动测试通过（echo JSON-RPC 测试）
- [ ] 配置写入 `config.yaml`
- [ ] Hermes 重启后 MCP 工具可见

---

## MCP vs 传统工具对比

| 维度 | MCP 工具 | 传统工具（直接注册） |
|------|---------|-------------------|
| **定义位置** | 外部进程，通过协议发现 | Agent 内置，直接注册到工具集 |
| **通信方式** | stdio / HTTP (JSON-RPC 2.0) | 直接函数调用 |
| **工具发现** | 启动时 `tools/list` 自动发现 | 静态注册，提前知道所有工具 |
| **工具数量** | 可动态扩展，服务端增删工具不影响客户端配置 | 固定数量，修改需更新 agent 代码 |
| **状态管理** | 无状态，每次调用独立 | 可维护会话状态 |
| **错误处理** | 通过 JSON-RPC error 响应 | 抛出异常 |
| **适用场景** | 外部服务集成、第三方 API、社区工具 | Agent 核心能力、内置工具 |
| **性能** | 有进程间通信开销 | 无开销，直接调用 |
| **调试** | 可独立运行 MCP 服务器，手动发 JSON-RPC 测试 | 直接 pytest / 断点 |
| **生态** | Model Context Protocol 社区标准，大量现成服务器 | 无生态，靠内置实现 |
| **安全** | 环境变量过滤、凭证剥离 | 同进程，凭证在内存中 |

### 选择 MCP 的场景

- 外部服务（GitHub、Slack、数据库）
- 需要保持服务独立升级
- 社区已有 MCP 服务器（npm/uvx）
- HTTP API 包装（REST API → MCP）

### 选择传统工具的场景

- Agent 核心能力（文件读写、终端）
- 高频调用（每次调用有进程开销）
- 需要复杂状态管理
- 调试需要同步断点

---

## 工具发现机制

### 发现流程（Startup）

```
Hermes 启动 → 读取 config.yaml mcp_servers
  → 并发连接每个服务器
    → 发送 initialize + tools/list
      → 注册工具到全局工具集
        → 注入到所有 platform toolsets
```

### 手动触发发现

```bash
# 在已运行的 Hermes 中，重新发现（不会重启）
# 工具名以 mcp_ 前缀注册
hermes tools list | grep mcp_
```

### 健康检查

```bash
# 检查 MCP 服务器状态
curl http://localhost:9333/api/mcp/status  # 如果开了 MCP 管理 API

# 日志检查
grep -i "mcp" ~/.hermes/logs/agent.log
grep "registered.*tool" ~/.hermes/logs/agent.log
```

### 工具注册后的命名

```
mcp_{server_name}_{tool_name}
# server_name 和 tool_name 中的连字符/点号会被替换为下划线
```

例如：
- `mcp_alibaba_product_get`
- `mcp_github_list_issues`
- `mcp_filesystem_read_file`

### 动态发现（运行时）

当前版本 MCP 服务器在启动时发现后**不会热更新**。如果需要：

1. 添加新服务器 → 编辑 `config.yaml` → `hermes gateway restart`
2. MCP 服务器本身增删工具 → 重启 MCP 服务器 + `hermes gateway restart`

### 调试发现

```bash
# 1. 测试 MCP 服务器独立运行
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python3 mcp_server.py

# 2. 检查 Hermes 日志
tail -f ~/.hermes/logs/agent.log | grep -i mcp

# 3. 检查工具是否注册
hermes tools list
```

### 常见发现失败原因

| 症状 | 原因 | 解决 |
|------|------|------|
| 没有任何 mcp_ 工具 | mcp package 未安装 | `pip install mcp` |
| 服务器连不上 | command 不在 PATH | 用绝对路径 |
| 工具列表为空 | 服务器 tools/list 返回空 | 单独测试服务器 |
| 工具存在但调用失败 | REST 后端挂了 | 检查后端服务 |

---

## Notes

- MCP tools are called synchronously from the agent's perspective but run asynchronously on a dedicated background event loop
- Tool results are returned as JSON with either `{"result": "..."}` or `{"error": "..."}`
- The native MCP client is independent of `mcporter` -- you can use both simultaneously
- Server connections are persistent and shared across all conversations in the same agent process
- Adding or removing servers requires restarting the agent (no hot-reload currently)

## Reference Implementations

- `references/auto-purchase-mcp-wrapper.md` — Python stdio MCP wrapper for a REST API (auto_purchase_agent), tested and working on this system
- `references/hangwin-mcp-chrome-setup.md` — 安装指南：hangwin/mcp-chrome（Chrome扩展转MCP服务）集成到Hermes CDP Chrome（port 9333），实现CDP+MCP混合浏览器架构。**注：生产方案已更新为 mcp-chrome-stdio stdio 模式（绕过 MV3 SW 阻塞）。**。⚠️ 选 **stdio 方案**（`mcp-chrome-stdio`），HTTP bridge 因 MV3 SW 阻塞不工作。详情见文档顶部"快速上手"节。
