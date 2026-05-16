# auto_purchase_agent MCP Wrapper

REST API + Python stdio MCP wrapper running on this system.

## Service Layout

| Component | Command | Port |
|-----------|---------|------|
| REST API (Node.js) | `node server.js` | 3001 |
| MCP wrapper (Python) | `python3 mcp_server.py` | stdin/stdout |

## Config in `~/.hermes/config.yaml`

```yaml
mcp_servers:
  auto_purchase:
    command: "python3"
    args: ["/Users/mac/auto_purchase_agent_v2/mcp_server.py"]
```

## Files

- `/Users/mac/auto_purchase_agent_v2/server.js` — REST API (auto_purchase_agent v2)
- `/Users/mac/auto_purchase_agent_v2/mcp_server.py` — MCP wrapper
- `/Users/mac/auto_purchase_agent_v2/data/suppliers.db` — SQLite database

## Known Issues

- REST API (server.js) can die silently while mcp_server.py keeps running → all tool calls fail with "Connection refused". Always check REST API first: `curl -s http://localhost:3001/api/suppliers`
- SQLite DB stored relative to working directory — start server from `~/auto_purchase_agent_v2` so `data/suppliers.db` is found correctly
