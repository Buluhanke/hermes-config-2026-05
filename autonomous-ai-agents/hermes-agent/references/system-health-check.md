# 系统健康检查清单（2026-05-18）

## 快速诊断顺序

```bash
# 1. Gateway 是否活着
ps aux | grep hermes | grep -v grep

# 2. Chrome + CDP (端口 9333)
curl -s http://localhost:9333/json/version

# 3. Ollama
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin).get('models',[])]"

# 4. n8n (可选)
lsof -i :5678

# 5. MCP servers 进程
ps aux | grep -E "mcp-chrome-stdio|cua-driver" | grep -v grep
```

## config.yaml 核心检查点

### ✅ toolsets 与 mcp_servers 必须对齐

**最常见配置断层**：在 `mcp_servers:` 里开了 chrome/cua，但 `toolsets:` 里没有对应的 browser/computer_use。

现象：Chrome 在跑、CDP 9333 在监听、MCP server 进程在运行——但 Hermes 无法使用任何浏览器工具。

正确配置：
```yaml
mcp_servers:
  chrome:
    command: mcp-chrome-stdio
  cua:
    command: cua-driver
    args: [mcp]

toolsets:
  - hermes-cli
  - terminal
  - browser        # ← 必须和 mcp_servers.chrome 对齐
  - computer_use   # ← 必须和 mcp_servers.cua 对齐
```

### ✅ 检查当前生效的 toolsets

```bash
python3 -c "
import yaml
with open('/Users/aimac/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
print('ENABLED toolsets:', cfg.get('toolsets', []))
print('MCP servers:', list(cfg.get('mcp_servers', {}).keys()))
"
```

### ✅ n8n 自动化平台

n8n 挂了两条诊断命令：
```bash
ps aux | grep n8n | grep -v grep
lsof -i :5678
```

无输出 = n8n 未运行。重启：
```bash
cd ~/n8n && docker-compose up -d  # 或你的启动方式
```

## 日志快速扫错

```bash
# agent 日志最新错误
tail -100 ~/.hermes/logs/agent.log | grep -E "ERROR|WARN|error" | tail -20

# gateway 日志
tail -50 ~/.hermes/logs/gateway.log 2>/dev/null
```

## 完整系统状态对照表

| 模块 | 检查命令 | 正常表现 |
|------|---------|---------|
| Hermes Gateway | `ps aux \| grep hermes` | 有 python 进程 |
| Chrome + CDP | `curl localhost:9333/json/version` | 返回 JSON |
| mcp-chrome-stdio | `ps aux \| grep mcp-chrome` | 有进程 |
| cua-driver | `ps aux \| grep cua-driver` | 有进程 |
| Ollama | `curl localhost:11434/api/tags` | 返回模型列表 |
| n8n | `lsof -i :5678` | 有 LISTEN |
| Telegram | `tail logs/agent.log \| grep telegram` | 有收发记录 |
