# Penpot MCP Integration Reference

## Architecture

```
LLM (Hermes) → MCP Server → WebSocket → Penpot Plugin → Penpot
```

Penpot MCP has two components:
1. **MCP Server** (Node.js) — exposes design tools to the LLM
2. **Penpot Plugin** — browser-side plugin that connects to the MCP server via WebSocket

## Two Ways to Connect

### Option A: Official Hosted (no self-host)
1. Run: `npx -y @penpot/mcp@latest`
   - MCP server starts, outputs local URL + API Key (e.g. `http://localhost:18789`)
2. Open Penpot → Settings → Integrations → MCP Server
3. Enter the server URL and key from step 1
4. Hermes connects as MCP client to `http://localhost:18789`

**Problem**: `npx` network access required. If npx fails (common in some environments), use Option B.

### Option B: Clone + Build from Source
```bash
git clone https://github.com/penpot/penpot.git --branch mcp-prod-2.14.1 --depth 1
cd penpot/mcp
pnpm install
pnpm run build
pnpm run start
```

## Hermes MCP Client Config

Hermes acts as MCP client. Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  penpot:
    url: "http://localhost:18789"
    headers:
      Authorization: "Bearer <api-key-from-server-output>"
    timeout: 180
```

Hermes must be restarted after config change.

## Key Files (installed package)

- Source: `~/.local/lib/node_modules/@penpot/mcp/`
- README: `packages/server/README.md`
- Architecture diagram: `resources/architecture.png`

## Known Issues

- `npx @penpot/mcp@latest` times out in network-restricted environments → use source clone
- MCP server requires Node.js v22.x
- Penpot must be open in browser AND the MCP Plugin must be connected for tools to work
