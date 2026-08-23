# Verify the OpenClaw MCP bridge without `hermes mcp test`

`hermes mcp list` / `hermes mcp test` crash on stdio servers (they assume a `url` field
exists — KeyError at `hermes_cli/mcp_config.py:764`). Use this raw JSON-RPC handshake to
prove the bridge is actually live and tool-discovering.

```python
import subprocess, json, os, time
TOKEN = "<token-from-~/.openclaw/openclaw.json>"
p = subprocess.Popen(
    ["openclaw", "mcp", "serve", "--url", "ws://127.0.0.1:18789", "--token", TOKEN],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, env=dict(os.environ))
def rpc(id, method, params=None):
    p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": id,
                              "method": method, "params": params or {}}) + "\n")
    p.stdin.flush()
rpc(1, "initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                      "clientInfo": {"name": "probe", "version": "1"}})
time.sleep(2)
print("INIT:", p.stdout.readline()[:400])
rpc(2, "tools/list", {})
time.sleep(1)
print("TOOLS:", p.stdout.readline()[:600])
p.terminate()
```

Expected good result:
- `initialize` → `serverInfo.name == "openclaw"`, `serverInfo.version == "2026.7.x"`.
- `tools/list` → 9 tools: `conversations_list, conversation_get, messages_read,
  attachments_fetch, events_poll, events_wait, messages_send, permissions_list_open,
  permissions_respond`.

If `initialize` is never returned, the gateway token/url is wrong or the OpenClaw
gateway (LaunchAgent on :18789) is not running — start it with `openclaw daemon status`
/ `openclaw gateway run`.
