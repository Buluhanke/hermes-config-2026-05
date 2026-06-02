---
name: mcp-residue-cleanup
description: 清理 Hermes MCP 服务残留（进程/文件/日志/凭证），解决路径不存在错误
triggers:
  - MCP server 报 Cannot find module 错误
  - n8n 或其他 MCP 连接失败高频重试
  - 删除后残留进程/文件
---

# MCP 服务残留清理

## 触发条件
- MCP server 报 `Cannot find module 'xxx'` 或 `路径不存在` 错误
- MCP 服务频繁重试连接失败，刷大量 stderr 日志
- n8n / 其他 MCP 服务删除后进程/文件残留
- config.yaml 里没有但系统里有残留的 MCP 进程

## 清理步骤

### 1. 确认残留进程
```bash
ps aux | grep -iE "n8n-mcp|n8n\s" | grep -v grep
```

### 2. 确认残留文件
```bash
ls -d ~/.n8n ~/.n8n-mcp ~/.local/bin/n8n* 2>/dev/null
du -sh ~/.n8n ~/.npm/_npx/*/node_modules/n8n* 2>/dev/null
find ~/.npm/_npx -name "n8n*" -maxdepth 3 2>/dev/null
```

### 3. 找 n8n 日志文件大小
```bash
du -sh ~/.hermes/logs/n8n.*.log ~/.hermes/logs/n8n*.log 2>/dev/null
```

### 4. 删除进程
```bash
pkill -9 -f "n8n-mcp" 2>/dev/null && echo "进程已杀"
```

### 5. 删除残留文件
```bash
rm -rf ~/.n8n ~/.n8n-mcp ~/.local/bin/n8n* ~/.npm/_npx/*/node_modules/n8n* 2>/dev/null
rm -f ~/.hermes/logs/n8n.err.log ~/.hermes/logs/n8n.log 2>/dev/null
```

### 6. 从 .env 清除 MCP 相关凭证
```bash
grep -n "N8N_\|n8n" ~/.hermes/.env 2>/dev/null   # 先确认
sed -i '/^N8N_/d' ~/.hermes/.env                 # 删除 N8N_ 开头的行
```

### 7. 确认 config.yaml 没有残留
```bash
python3 -c "import yaml; print(list(yaml.safe_load(open('/Users/$(whoami)/.hermes/config.yaml')).get('mcp_servers',{}).keys()))"
```
应为 `['chrome', 'filesystem', 'github', 'memory', 'searxng']`，不含 n8n

### 8. 验证清理完成
```bash
ps aux | grep -iE "n8n" | grep -v grep   # 应无输出
du -sh ~/.n8n ~/.n8n-mcp 2>&1             # 应报 No such file
```

## 常见残留路径
| 路径 | 说明 | 典型大小 |
|---|---|---|
| `~/.n8n/` | n8n 本体数据目录 | ~50M |
| `~/.n8n-mcp/` | n8n-mcp 配置 | 4K |
| `~/.local/bin/n8n*` | n8n-wrapper 脚本/软链 | 4K |
| `~/.npm/_npx/<hash>/` | n8n-mcp npm 缓存 | ~170M |
| `~/.hermes/logs/n8n*.log` | stderr 噪音日志 | 0-3M |
| `~/.hermes/.env` | N8N_ENCRYPTION_KEY | — |

## 注意事项
- 只删除与问题服务相关的残留，不要碰其他 MCP（chrome、github 等）
- `.env` 凭证删除前确认用户同意
- 如果是 `hermes mcp install` 安装的，还需从 catalog manifest 考虑是否卸载：`hermes mcp uninstall n8n`（可选，manifest 文件保留不影响运行）