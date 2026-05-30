# MCP Chrome 架构排障笔记
**日期**: 2026-05-30
**结论**: MCP chrome 工具调用失败 → Chrome扩展未装进chrome-debug

---

## 架构图

```
Hermes Agent
  ├─ dom_tools (dom_snapshot/click/fill/tabs)
  │   └─ CDP WebSocket → ws://127.0.0.1:9333
  │       ✓ 直接连 chrome-debug 实例，完全正常工作
  │
  └─ mcp_chrome_* (27个工具)
      ├─ stdio 通道 (initialize + tools/list)
      │   └─ mcp-chrome-stdio 进程 ← → Chrome扩展 [端口12306]
      │       ✓ list_tools 成功
      │       ✗ call_tool 失败 (extension HTTP server 没运行)
      │
      └─ HTTP 通道 (tool calls)
          └─ ws://127.0.0.1:12306/mcp
              ✗ Chrome扩展的嵌入式HTTP服务器未启动
```

---

## 为什么 12306 端口没有响应

Chrome扩展在点击 popup 的 "Connect" 按钮之前，不会启动内置的HTTP服务器（端口12306）。

**扩展安装位置错位**:
- MCP Chrome Extension (Web Store版 ID: `mnchdcikbochaacmcfohjibjkhdbaahe`) 被装进了**普通Chrome** profile
- 但 `mcp-chrome-stdio` 控制的 Chrome 实例是 `chrome-debug` profile (9333端口)
- 两个profile完全不共享扩展

**mcp-chrome-bridger register 做了什么**:
```
mcp-chrome-bridger register --detect
✓ Manifest → ~/Library/Application Support/Google/Chrome/NativeMessagingHosts/
✓ 注册了 com.mcpchromeserver.nativehost.json 和 com.chromemcp.nativehost.json
```
这只注册了 native messaging host 路径，让Chrome能调用 `mcp-chrome-stdio`；
但它**不会**自动把扩展装进 chrome-debug profile。

---

## 症状 vs 根因

| 症状 | 根因 |
|------|------|
| `tools/list` 成功返回27个工具 | stdio通信正常，扩展不需要运行 |
| `call_tool` 返回 "Failed to connect to MCP server" | port 12306连接失败 → 扩展HTTP服务器没启动 |
| port 12306 `curl` 返回 "Failed to connect to host" | 扩展没有启动内置服务器 |
| `mcp-chrome-stdio` 进程在运行 | 进程活着但等待扩展连接 |
| Chrome扩展popup显示 "Connect" 按钮 | 扩展已装但未激活 → 点击后才会启动12306端口 |

---

## 为什么不修 MCP 而是用 dom_tools

1. **MCP Chrome 需要用户手动操作**: 要把扩展装进chrome-debug profile，需要用户手动在 `chrome://extensions` 开启开发者模式，然后"加载已解压的扩展程序"——且扩展文件在Web Store安装后位于普通Chrome数据目录，不在 `~/.hermes/mcp-chrome-extension/`（该目录为空）

2. **dom_tools 已经完整**: dom_snapshot + dom_click + dom_fill + dom_tabs 覆盖了27个MCP工具的绝大部功能（除了 gif_recorder、performance_trace 这两个非核心功能）

3. **架构更简单**: dom_tools 用 CDP WebSocket 直连 9333，不依赖扩展，不依赖 native messaging，不依赖端口12306

---

## 相关文件

- `~/.hermes/hermes-agent/tools/dom_tools.py` — dom_tools 生产工具（已注册）
- `~/.hermes/hermes-agent/tools/browser_cdp_tool.py` — 架构参考
- `/Users/aimac/.local/bin/mcp-chrome-stdio` — MCP stdio 服务器
- `~/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.chromemcp.nativehost.json` — native messaging 配置
- `~/.hermes/chrome-debug/` — chrome-debug profile（port 9333）
- `/Users/aimac/.local/lib/node_modules/mcp-chrome-bridge/` — MCP chrome bridge npm包

## 恢复 MCP chrome 工具的方法

如果将来要把MCP chrome工具用起来：

1. 下载 MCP Chrome Extension 到本地（Web Store CRX 下载工具）
2. 用 Chrome 开发者模式加载扩展到 `~/.hermes/mcp-chrome-extension/`
3. 重启 chrome-debug Chrome (让它加载扩展)
4. 在 Chrome 窗口右上角点击扩展图标 → 点 "Connect"
5. 端口12306应该开始监听
6. tool calls 应该开始工作

**更简单方案**: 用 dom_tools，它不需要任何扩展。