# Agent Reach 安装与调试

## 概述
Agent Reach v1.4.0 — 多平台社交媒体 AI Agent CLI，支持 Twitter/小红书/Reddit/微博/B站/微信公众号等渠道的搜索和内容获取。

- 安装：`uv tool install agent-reach` 或 `pip install agent-reach`
- 主命令：`agent-reach <subcommand>`
- 诊断：`agent-reach doctor`

## 目录结构
```
~/.agent-reach/          # 主目录
~/.agent-reach/tools/    # 上游工具目录（pipx安装后为空，用全局 CLI）
~/.local/bin/            # pipx 全局安装路径（bili/rdt/xhs/twitter 等）
```

## 渠道状态（2026-05-27 实测）

| 渠道 | 状态 | 备注 |
|------|------|------|
| 网页搜索 | ✅ | 基础渠道 |
| YouTube | ✅ | 基础渠道 |
| GitHub | ✅ | 基础渠道 |
| RSS | ✅ | 基础渠道 |
| V2EX | ✅ | 基础渠道 |
| B站（bili） | ✅ | 直连可用 |
| 微信公众号 | ⚠️ | 无账号，用 Exa MCP 替代搜索 |
| Exa（全网语义搜索） | ✅ | 通过 mcporter 配置 |
| 微博 | ✅ | MCP server 已修复（10工具） |
| GitNexus | ✅ | MCP server 正常（13工具） |
| Twitter/X | ❌ | 超时，需代理或 Cookie |
| Reddit（rdt） | ❌ | 超时，需代理 |
| 小红书（xhs） | ❌ | 超时，需代理 |
| 抖音 | ❌ | 需 Cookie |
| LinkedIn | ❌ | 需 Cookie |

## 常见故障

### 1. mcporter 报错 ENOTDIR
**症状**：`mcporter config add` 报错 `ENOTDIR ~/config`

**原因**：`~/config` 是个空文件而非目录（可能被其他工具覆盖）

**修复**：
```bash
mv ~/config ~/config.bak && mkdir -p ~/config
# 重试 mcporter config add ...
```

### 2. weibo MCP server offline
**症状**：`mcporter servers` 显示 weibo offline

**原因**：mcp-server-weibo 不在 PATH

**修复**：使用完整路径
```bash
mcporter config remove weibo
mcporter config add weibo /Users/aimac/.local/pipx/venvs/agent-reach/bin/mcp-server-weibo
```

### 3. CLI 工具（rdt/twitter/xhs）网络超时
**症状**：命令执行超时，curl 直连代理端口正常

**原因**：CLI 工具未自动使用系统代理环境变量

**诊断**：
```bash
curl -x http://127.0.0.1:7897 https://example.com  # 验证代理可达
HTTPS_PROXY=http://127.0.0.1:7897 rdt search "test"  # 测试代理环境变量
```

**说明**：部分工具（如 `bili`）国内直连可用，Twitter/Reddit/小红书 需要代理

### 4. MCP 工具名未知
**症状**：不知道 MCP server 提供哪些工具，猜测名称失败

**正确做法**：
```bash
mcporter tools <server-name>   # 列出可用工具
mcporter call <server> --tool <name> --help  # 查看工具用法
```

不要猜测工具名，用 `mcporter tools` 查出来再用。

## API Key 配置
```bash
agent-reach config set groq_api_key <key>      # 小宇宙播客转文字用
agent-reach config set openai_api_key <key>    # 通用
agent-reach config set xiaoyuzhou_groq_api_key <key>  # 播客转录
```

## 平台登录要求
- Twitter/Reddit/小红书/微博：需要浏览器授权 Cookie 才能完全使用
- 抖音/LinkedIn：需要 Cookie，无 Cookie 完全不可用
- 微信公众号：无账号可用 Exa MCP 替代搜索

登录后 Cookie 通过浏览器开发者工具获取。

## 参考命令
```bash
agent-reach install --env=auto        # 基础渠道
agent-reach install --channels=all    # 全部可选渠道
agent-reach doctor                    # 诊断
mcporter servers                      # 查看 MCP 服务器状态
mcporter tools <server>              # 列出工具
mcporter call <server> --tool <tool> --<param> <value>  # 调用工具
```
