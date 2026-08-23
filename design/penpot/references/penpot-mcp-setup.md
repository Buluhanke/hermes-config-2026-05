# PenPot MCP Server — Setup Reference

## Token 格式（关键）

PenPot MCP Key 是 **JWE 格式**（AES-256 Key Wrap 加密），不是普通 Bearer token。

结构：`eyJhbGciOiJBMjU2S1ciLCJlbmMiOiJBMjU2R0NNIn0.<segment1>.<segment2>.<segment3>.<segment4>`
- Header alg: `A256KW`（AES-256 Key Wrap）
- Enc: `A256GCM`（AES-256-GCM 加密）

**认证方式**：token 通过 HTTP query param 传入，不是 Authorization header：
```
http://localhost:4401/mcp?userToken=<JWE>
```

## 安装（npm 全局）

```bash
npm install -g @penpot/mcp
# 验证
npm list -g @penpot/mcp  # → 2.15.4
```

## 启动 MCP Server（本地方式，需跑两个服务）

```bash
cd $(npm root -g)/@penpot/mcp
npm run bootstrap
```

**注意**：本地需要同时运行 MCP server + plugin web server，比官方托管方式复杂。

## 本地安装与构建（需要跑两个服务）

如果选择本地 MCP 模式（需要同时跑 MCP server + PenPot plugin web server）：

```bash
# 路径
cd ~/.local/lib/node_modules/@penpot/mcp

# 1. 安装依赖（批准 esbuild 构建脚本）
pnpm install
pnpm approve-builds esbuild sharp

# 2. 构建 server
cd packages/server
pnpm run build
# 输出: dist/index.js (581.9kb, ESM)

# 3. 启动 MCP server
cd ~/.local/lib/node_modules/@penpot/mcp/packages/server
PENPOT_MCP_SERVER_PORT=4401 PENPOT_MCP_WEBSOCKET_PORT=4402 node dist/index.js &
# 日志输出:
#   Modern Streamable HTTP endpoint: http://localhost:4401/mcp
#   WebSocket server URL: ws://localhost:4402
#   REPL interface URL: http://localhost:4403
```

验证 server 启动成功：
```bash
lsof -i :4401 -i :4402 | grep LISTEN
```

## 推荐方式：官方托管（Remote MCP）

只需一个 URL + key，无需本地运行服务。

### 获取 MCP 凭证

1. 打开 https://design.penpot.app 并登录
2. 右上角头像 → **Integrations** → **MCP Server**
3. 开启 MCP 开关
4. 复制 **Server URL** 和 **MCP Key**

### 配置到 Hermes

在 `~/.hermes/config.yaml` 的 `mcp_servers:` 下添加：

```yaml
penpot:
  url: "<Server URL 从 Integrations 页面获取>"
  headers:
    Authorization: "Bearer <MCP Key>"
```

重启 gateway 生效。

## MCP Tools（设计相关）

- `execute_code` — 在 Penpot 环境执行代码
- `high_level_overview` — 设计文件概览
- `penpot_api_info` — API 信息
- `export_shape` — 导出设计元素
- `import_image` — 导入图片（本地 MCP 模式可用）

## 本地 MCP vs Remote MCP

| | 本地 | 远程（官方托管）|
|---|---|---|
| 需要本地 Node.js | ✅ | ❌ |
| 需要跑两个服务 | ✅ | ❌ |
| import_image | ✅ | ❌ |
| export_shape | 完整 | 有限制 |
| 只需账号+key | ❌ | ✅ |
| 数据走 Penpot 服务器 | ❌ | ✅ |

## 已知限制

- Remote MCP 模式下 `import_image` 不可用（无法从本地文件导入）
- Chromium 142+ 浏览器有 Private Network Access 限制，`localhost` 连接需在浏览器弹窗中授权
- MCP 一次只在一个浏览器 tab 活跃（当前聚焦的页面）
