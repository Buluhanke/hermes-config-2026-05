# Python stdio MCP Wrapper for auto_purchase_agent

Tested and working wrapper that translates MCP tool calls into REST API requests.

## Source

`/Users/mac/auto_purchase_agent_v2/mcp_server.py`

## Key Implementation Details

### JSON-RPC Version
Must use `"2.0"`, not `"1.0"`:
```python
response = {"jsonrpc": "2.0", "id": req_id, "result": result}
```

### Output Flushing
Without `flush=True`, Hermes times out waiting for response:
```python
print(json.dumps(resp), flush=True)
```

### HTTP Timeout
`urlopen` blocks forever without timeout — always set it:
```python
with urllib.request.urlopen(url, timeout=10) as resp:
```

### Unicode Chinese Characters
REST API returns Chinese characters, must use `ensure_ascii=False`:
```python
json.dumps(data, ensure_ascii=False)
```

### MCP Result Format
Tool results MUST be wrapped as:
```python
{"content": [{"type": "text", "text": json.dumps(api_result, ensure_ascii=False)}]}
```
NOT raw JSON strings.

### Required MCP Methods
The wrapper must handle:
- `initialize` — return protocol version + capabilities
- `tools/list` — return tool definitions with inputSchema
- `tools/call` — dispatch to REST API

### Test Commands
```bash
# List tools
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python3 ~/auto_purchase_agent_v2/mcp_server.py

# Call get_suppliers
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_suppliers","arguments":{}}}' | python3 ~/auto_purchase_agent_v2/mcp_server.py

# Call purchase_plan
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"purchase_plan","arguments":{"product":"纸箱","spec":"50x50cm","topK":3}}}' | python3 ~/auto_purchase_agent_v2/mcp_server.py
```
