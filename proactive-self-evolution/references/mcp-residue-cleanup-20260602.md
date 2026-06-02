# MCP Server 残留清理实战（2026-06-02）

## 问题现象
- `Cannot find module '/Users/aimac/.local/bin/n8n'` 大量刷 stderr
- `n8n-mcp` 进程残留（4个）持续运行
- `n8n.err.log` 膨胀到 3M
- Hermes agent.log 报错 `MCP server 'n8n' initial connection failed`

## 根因分析

Hermes 有两套 MCP 加载机制：

**1. config.yaml mcp_servers**（显式配置）
```yaml
mcp_servers:
  chrome:
    command: mcp-chrome-stdio
  filesystem:
    command: npx
    args: ['-y', '@modelcontextprotocol/server-filesystem', ...]
```
这是用户可见的，在 `~/.hermes/config.yaml` 里。

**2. optional-mcps/ manifest**（隐藏目录）
```
~/.hermes/hermes-agent/optional-mcps/n8n/manifest.yaml
```
这个目录里的 manifest 会让 Hermes 自动发现并启动 n8n-mcp（即使不在 config.yaml）。

问题在于：
- manifest 指定 `command: ${INSTALL_DIR}/.venv/bin/python` + `args: [${INSTALL_DIR}/server.py]`
- 但 n8n-mcp 内部会尝试 require `/Users/aimac/.local/bin/n8n`（一个根本不存在的路径）
- n8n-wrapper 指向 `/Users/aimac/.local/bin/n8n`（死链接）
- 结果：MCP 连接成功（9工具注册），但 n8n 内部报错刷屏

## 清理操作（已执行）

```bash
# 进程
pkill -9 -f "n8n-mcp"

# 文件
rm -rf ~/.n8n ~/.n8n-mcp ~/.local/bin/n8n* ~/.npm/_npx/b6a381d62ce0fe56/
rm -f ~/.hermes/logs/n8n.err.log ~/.hermes/logs/n8n.log

# .env 凭证
sed -i '/^N8N_/d' ~/.hermes/.env
```

## 关键路径汇总

| 路径 | 大小 | 说明 |
|------|------|------|
| `~/.n8n/` | ~56M | n8n 本体数据 |
| `~/.n8n-mcp/` | 4K | n8n-mcp 配置 |
| `~/.local/bin/n8n*` | 4K | wrapper + 死链接 |
| `~/.npm/_npx/<hash>/` | ~170M | n8n-mcp npm 缓存 |
| `~/.hermes/logs/n8n.err.log` | ~3M | stderr 噪音 |

总计释放：**~230M**

## 验证命令

```bash
ps aux | grep -iE "n8n" | grep -v grep  # 应无输出
ls -d ~/.n8n ~/.n8n-mcp 2>&1            # 应报 No such file
grep "N8N" ~/.hermes/.env                 # 应无输出
python3 -c "import yaml; print(list(yaml.safe_load(open('/Users/aimac/.hermes/config.yaml')).get('mcp_servers',{}).keys()))"
# 应为 ['chrome', 'filesystem', 'github', 'memory', 'searxng']
```

## 教训

1. **optional-mcps/ 是隐藏的自动加载路径**——不在 config.yaml 也会跑
2. **n8n-mcp 有内部依赖**——CLI n8n 不存在时内部会报错（但工具仍注册成功）
3. **npm 缓存残留大**——`_npx/<hash>` 常 ~170M，删除后释放明显
4. **stderr 日志会膨胀**——及时清理 `n8n.err.log`