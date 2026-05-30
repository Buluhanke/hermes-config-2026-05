# n8n MCP + Gateway 生命周期管理（2026-05-30 实测）

## MCP 服务器进程模型

Gateway 启动时通过 `mcp_servers` 配置启动两个 stdio 子进程：

```
gateway (pid 31207)
  ├─ mcp-chrome-stdio (pid 31210) → Chrome CDP
  └─ hermes-n8n-mcp/server.py (pid 31211) → n8n REST API bridge
```

Gateway 重启时（旧进程 kill + `--replace` 新启动）：
1. 旧 gateway (pid 31207) 被 SIGTERM → 退出
2. 旧 MCP 子进程 (31210, 31211) 变成孤儿（orphan），但仍保持连接
3. 新 gateway 启动时会尝试连接已存在的 MCP stdio → 成功复用
4. 新 MCP 子进程同时被 spawn（32154, 32155）→ 产生"重复连接"现象

**结论**：MCP 子进程不需要重启。Gateway 崩溃重启后 MCP 自动恢复。

## 验证 MCP 连接状态的正确方式

```bash
# 查看 MCP 服务器状态（推荐）
hermes mcp list

# 测试单个 MCP 连通性
hermes mcp test n8n
hermes mcp test chrome
```

**错误方式**：
- `curl http://localhost:8642/v1/gateway/status` → 404（此端点不存在）
- gateway 端口 8642 没有有意义的 HTTP API（返回纯 404）

## Gateway 端口说明

| 端口 | 进程 | 说明 |
|------|------|------|
| 8642 | gateway (python) | aiohttp HTTP 服务器，但无公开 REST API |
| 9119 | 未知第三方 | 非 Hermes 相关 |

Gateway 实际通过通讯渠道（Feishu/Weixin/QQ/Telegram）接收消息，不通过 HTTP 端口。

## n8n 当前状态（2026-05-30）

- **容器**：hermes-ai-n8n-1，运行正常
- **healthz**：`curl http://localhost:5678/healthz` → `{"status":"ok"}`
- **workflow 数量**：0（数据库 `workflow_entity` 表为空）
- **API Key**：已配置（`n8n_pbv54VyhlZMpTUWhM0nnPFHH-p2kiW6f`），存在 `user_api_keys` 表
- **API 认证**：`curl -H "X-N8N-API-KEY: <key>" http://localhost:5678/api/v1/workflows` → `{"data":[]}`
- **MCP 工具数**：11个（health, list_workflows, get_workflow, find_workflows, list_executions, get_execution, recent_failures, export_workflow, activate_workflow, deactivate_workflow, container_logs）

## n8n API Key 直接从 SQLite 提取

当 n8n UI 无法复制完整 Key（显示被截断/遮蔽）时，可直接从数据库读：

```bash
sqlite3 ~/n8n_data/database.sqlite "SELECT label, apiKey, createdAt FROM user_api_keys LIMIT 10;"
```

输出格式：
```
Hermes Agent|n8n_pbv54VyhlZMpTUWhM0nnPFHH-p2kiW6f|2026-05-30 08:54:58.250411
```

## MCP Reload 系统通知

Gateway 日志中的 `[IMPORTANT: MCP servers have been reloaded]` 是正常系统消息，不代表报错。

含义：MCP 服务器列表被重新加载（通常发生在 gateway 配置变更时）。不影响已有连接。

## Gateway 重启标准流程

```bash
# 找到 gateway pid
pgrep -fl "hermes.*gateway\|gateway.*run"

# 重启（--replace 防止端口冲突）
kill <pid> && sleep 2 && cd ~/.hermes/hermes-agent && venv/bin/hermes gateway run --replace &
```

验证：
```bash
sleep 5 && tail -10 ~/.hermes/logs/gateway.log
hermes mcp list  # 确认 MCP 在线
```

## 当前运行的进程（2026-05-30）

```
gateway (pid 32505) on port 8642
├── chrome MCP (pid 32154) → 27 tools
└── n8n MCP (pid 32155) → 11 tools

Docker containers:
├── hermes-ai-n8n-1 (port 5678)
├── hermes-ai-chromadb-1 (port 8000)
├── open-webui (port 3000)
├── searxng
```