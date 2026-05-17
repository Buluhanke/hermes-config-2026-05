# MCP 协议深度理解

## 1. MCP 是什么

### 1.1 定义

MCP（Model Context Protocol）是 Anthropic 提出的标准化协议，用于在 LLM 与外部工具/数据源之间建立双向通信。相比传统的 Function Calling，MCP 是协议层统一封装，支持工具发现、握手协商、增量结果流式返回。

```
传统架构:
LLM → Function Calling → 各自封装的 REST/SDK (碎片化)

MCP架构:
LLM → MCP Client → MCP Server (stdio/HTTP/CDP) → 统一协议 → 各类资源
```

### 1.2 MCP vs Function Calling

| 维度 | Function Calling | MCP |
|------|-----------------|-----|
| 标准化程度 | 模型厂商各自定义 | 统一协议 |
| 工具发现 | 手工注册 schema | 运行时 `list_tools` |
| 传输方式 | HTTP/JSON | stdio / HTTP SSE / CDP |
| 状态管理 | 无状态 | 有状态会话 |
| 资源访问 | 仅工具 | 工具 + 资源 + Prompt |
| 生态扩展 | 依赖模型厂商 | 独立于模型 |

---

## 2. Hermes 中的 MCP 实现

Hermes 支持三种 MCP 连接模式，适用于不同场景。

### 2.1 stdio 模式

通过标准输入/输出与本地进程通信，适合本地 MCP 服务。

```json
{
  "mcpServers": {
    "chrome-stdio": {
      "command": "node",
      "args": ["/path/to/mcp-chrome-server/dist/index.js"],
      "env": {},
      "enabled": true
    }
  }
}
```

- **优点**: 低延迟，适合本地工具
- **缺点**: 仅限本地进程，无法跨机器

### 2.2 HTTP 模式

通过 HTTP + SSE（Server-Sent Events）与远程 MCP 服务通信。

```json
{
  "mcpServers": {
    "n8n": {
      "url": "https://your-n8n-instance.com/mcp/sse",
      "headers": {
        "Authorization": "Bearer your-token"
      },
      "enabled": true
    }
  }
}
```

- **优点**: 可远程访问，支持 HTTPS
- **缺点**: 需要网络延迟考虑

### 2.3 CDP 模式（Chrome DevTools Protocol）

针对浏览器自动化的专用模式，通过 CDP 与 Chrome 直接通信。

```json
{
  "mcpServers": {
    "chrome-cdp": {
      "cdpEndpoint": "ws://localhost:9222",
      "browserType": "chrome"
    }
  }
}
```

- **优点**: 完整浏览器控制能力
- **缺点**: 依赖 Chrome 开启调试端口

---

## 3. 已接入的 MCP 服务

### 3.1 chrome-stdio

浏览器自动化 MCP 服务，通过 stdio 通信。

**可用工具**:
- `chrome_navigate` — 导航到 URL / 后退前进
- `chrome_read_page` — 读取页面可访问性树
- `chrome_click_element` — 点击页面元素
- `chrome_fill_or_select` — 填充表单
- `chrome_screenshot` — 截图
- `chrome_console` — 获取控制台输出
- `chrome_network_request` — 发送网络请求
- `chrome_bookmark_*` — 书签管理

**配置示例**:
```json
{
  "mcpServers": {
    "chrome-stdio": {
      "command": "node",
      "args": ["/usr/local/lib/mcp-chrome-stdio/index.js"],
      "enabled": true
    }
  }
}
```

### 3.2 cua-driver

macOS 系统级自动化 MCP 服务，基于 Accessibility 和 ScreenRecording 权限。

**可用工具**:
- `cua_launch_app` — 后台启动应用
- `cua_get_window_state` — 获取窗口状态和 UI 树
- `cua_click` / `cua_double_click` / `cua_right_click` — 鼠标点击
- `cua_drag` — 拖拽操作
- `cua_type_text` — 文本输入
- `cua_press_key` / `cua_hotkey` — 键盘操作
- `cua_scroll` — 滚动
- `cua_screenshot` — 截图
- `cua_set_value` — 设置 UI 元素值
- `cua_list_apps` / `cua_list_windows` — 枚举应用和窗口

**权限要求**:
- Accessibility（辅助功能）
- Screen Recording（屏幕录制）

### 3.3 n8n

工作流自动化 MCP 服务，通过 HTTP SSE 连接 n8n 实例。

**可用工具**:
由 n8n 工作流定义，通常包含:
- 自定义 API 调用
- 数据库操作
- 消息通知
- 第三方集成（Slack, GitHub, Notion 等）

**配置示例**:
```json
{
  "mcpServers": {
    "n8n": {
      "url": "https://n8n.example.com/mcp/sse",
      "headers": {
        "Authorization": "Bearer ${N8N_API_TOKEN}"
      },
      "enabled": true
    }
  }
}
```

### 3.4 文件系统（内置）

Hermes 内置的文件系统 MCP 服务。

**可用工具**:
- `read_file` — 读取文件（支持 offset/limit 分页）
- `write_file` — 写入文件（完全覆盖）
- `search_files` — 搜索文件内容或按名称查找
- `terminal` — 执行 shell 命令

---

## 4. 如何扩展 MCP 工具

### 4.1 MCP Server 配置格式

在 `~/.hermes/config.json` 中添加 `mcpServers` 条目：

```json
{
  "mcpServers": {
    "my-custom-server": {
      "command": "node",
      "args": ["/path/to/my-mcp-server/dist/index.js"],
      "env": {
        "MY_API_KEY": "${MY_API_KEY}"
      },
      "enabled": true
    }
  }
}
```

**字段说明**:
- `command`: 启动命令（node/python/其他可执行文件）
- `args`: 命令行参数数组
- `env`: 环境变量（支持 `${VAR}` 语法引用外部变量）
- `enabled`: 是否启用

### 4.2 开发自己的 MCP Server

#### 基础模板（Node.js）

```javascript
const { Server } = require('@modelcontextprotocol/sdk/server');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types');

const server = new Server(
  { name: 'my-mcp-server', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

// 注册工具列表
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'my_tool',
        description: '执行自定义操作的工具',
        inputSchema: {
          type: 'object',
          properties: {
            param1: { type: 'string', description: '参数1' },
            param2: { type: 'number', description: '参数2' }
          },
          required: ['param1']
        }
      }
    ]
  };
});

// 处理工具调用
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'my_tool':
        // 业务逻辑
        const result = await myToolLogic(args.param1, args.param2);
        return { content: [{ type: 'text', text: JSON.stringify(result) }] };

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [{ type: 'text', text: `Error: ${error.message}` }],
      isError: true
    };
  }
});

// 启动
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);
```

#### package.json 依赖

```json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0"
  }
}
```

#### 安装与配置

```bash
# 安装依赖
npm install

# 在 config.json 中注册
# "my-mcp-server": {
#   "command": "node",
#   "args": ["/path/to/dist/index.js"]
# }
```

---

## 5. 最佳实践

### 5.1 单一职责原则

每个 MCP 工具应只做一件事：

```
✅ 好的设计:
- chrome_navigate (仅导航)
- chrome_click_element (仅点击)
- chrome_read_page (仅读取)

❌ 避免:
- chrome_navigate_and_click (导航+点击混合)
- batch_operation (什么都做)
```

### 5.2 超时控制

所有外部调用必须设置合理的超时：

```javascript
// HTTP 请求超时
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), 30000);

try {
  const result = await fetch(url, {
    signal: controller.signal
  });
} finally {
  clearTimeout(timeout);
}

// MCP 工具调用超时（由 Hermes 控制）
// 建议工具本身执行时间 < 10s
```

### 5.3 重试机制

对临时性失败进行重试：

```javascript
async function withRetry(fn, maxAttempts = 3, delayMs = 1000) {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxAttempts) throw error;

      // 仅对临时性错误重试
      if (!isRetryableError(error)) throw error;

      console.warn(`Attempt ${attempt} failed, retrying in ${delayMs}ms...`);
      await sleep(delayMs);
      delayMs *= 2; // 指数退避
    }
  }
}

function isRetryableError(error) {
  const retryableCodes = ['ETIMEDOUT', 'ECONNRESET', 'ECONNREFUSED', 429, 503];
  return retryableCodes.some(code =>
    error.message?.includes(code) || error.code === code || error.status === code
  );
}
```

### 5.4 日志记录

保持可观测性：

```javascript
// 结构化日志
console.log(JSON.stringify({
  level: 'info',
  tool: 'my_tool',
  params: { param1: 'value1' },
  duration_ms: Date.now() - start,
  success: true
}));

// 错误日志
console.error(JSON.stringify({
  level: 'error',
  tool: 'my_tool',
  error: error.message,
  stack: error.stack,
  timestamp: new Date().toISOString()
}));
```

### 5.5 其他建议

| 实践 | 说明 |
|------|------|
| 参数校验 | 在工具入口校验必填参数和类型 |
| 优雅降级 | 依赖不可用时返回友好错误而非崩溃 |
| 资源清理 | 使用 try/finally 确保资源释放 |
| 安全敏感信息 | 使用环境变量而非硬编码，定期轮换 |
| 版本管理 | MCP Server 应声明版本，便于问题追溯 |
| 健康检查 | 长时间运行的 Server 应实现健康检查端点 |
