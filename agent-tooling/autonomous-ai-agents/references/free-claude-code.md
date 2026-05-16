# free-claude-code — 部署与调试参考

## 概述

[free-claude-code](https://github.com/Alishahryar1/free-claude-code) 将 Claude Code 的 Anthropic API 请求路由到免费/廉价后端（NVIDIA NIM、Ollama、LM Studio 等），避免消耗 Anthropic API 额度。

## 快速部署

```bash
# 1. 安装 Claude Code（需要先装 npm）
npm install -g @anthropic-ai/claude-code

# 2. 安装 free-claude-code（Python 3.14）
uv tool install free-claude-code

# 3. 初始化配置（生成 ~/.config/free-claude-code/.env）
fcc-init

# 4. 启动代理服务（后台运行）
fcc-server &
```

**端口**: `:8082`，**Admin UI**: `http://127.0.0.1:8082/admin`

## NVIDIA NIM 配置

### 获取 API Key
访问 https://build.nvidia.com/settings/api-keys 获取免费 key。

### 通过 Admin UI 配置（推荐）
1. 打开 `http://127.0.0.1:8082/admin`
2. 在 `NVIDIA NIM API Key` 输入框填入 key
3. 点击 `Validate` → `Apply`

### 手动编辑配置文件
```bash
# 配置文件位置
~/.config/free-claude-code/.env

# 关键配置项
NVIDIA_NIM_API_KEY=NVIDAPI_REDACTED
MODEL=nvidia_nim/meta/llama-3.1-8b-instruct
ANTHROPIC_AUTH_TOKEN=freecc
```

## 模型选择

### ⚠️ GLM-4.7 已 EOL
之前推荐的 `nvidia_nim/z-ai/glm4.7` 已停止服务，不要使用。

### 可用模型（2025-05 实测）
| 模型 | 状态 | 说明 |
|------|------|------|
| `nvidia_nim/meta/llama-3.1-8b-instruct` | ✅ 可用 | 8B 规模，免费额度充足 |
| `meta/llama-3.1-8b-instruct` | ✅ 可用 | 同上，纯模型名 |
| `nvidia/llama-3.3-nemotron-70b-instruct` | ❌ 404 | 路径格式不对 |
| `deepseek-ai/deepseek-coder-6.7b-instruct` | ❌ 超时 | 可能需要代理 |
| `z-ai/glm5` | ❌ 超时 | 不可用 |

### 模型配置方法
在 Admin UI 的 `Default Model` 输入框填入完整 provider 前缀：
```
nvidia_nim/meta/llama-3.1-8b-instruct
```

## API 调试方法

### 直接调用 proxy（最可靠）
CLI（`fcc-claude`）对 pipe 交互不友好，调试时直接用 curl：

```bash
curl -s -X POST "http://127.0.0.1:8082/v1/messages" \
  -H "x-api-key: freecc" \
  -H "Content-Type: application/json" \
  -H "Anthropic-Version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-latest",
    "messages": [{"role": "user", "content": "Say hello in 3 words"}],
    "max_tokens": 50
  }' --max-time 30
```

**认证方式**: `x-api-key` header（不是 `Authorization: Bearer`）。

### 健康检查
```bash
curl -s http://127.0.0.1:8082/health
# 返回 {"detail":"Missing API key"} 表示服务正常运行（需要加 auth header）
```

### 验证 NVIDIA NIM 连通性
```bash
curl -s -X POST "https://integrate.api.nvidia.com/v1/chat/completions" \
  -H "Authorization: Bearer <NVAPI_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"model":"meta/llama-3.1-8b-instruct","messages":[{"role":"user","content":"Hi"}],"max_tokens":10}' \
  --max-time 15
```

## 架构说明

```
Claude Code CLI
    ↓ (ANTHROPIC_BASE_URL=http://127.0.0.1:8082)
fcc-server (local proxy :8082)
    ↓ (路由规则)
NVIDIA NIM / Ollama / LM Studio
```

- `fcc-claude` 是启动器：读取配置、设置环境变量、启动真正的 `claude` 命令
- `fcc-server` 是代理：接收 Claude Code 的 API 请求，路由到配置的 provider
- Admin UI 修改 `~/.config/free-claude-code/.env` 并支持热重载

## 常见问题

### fcc-claude 超时无响应
- 原因：Claude Code CLI 本身对 pipe 模式不友好，不是配置问题
- 解决：用 curl 直接调 proxy API 验证是否正常

### 模型请求返回 Provider API request failed
- 检查 NVIDIA NIM key 是否正确
- 用上面的 curl 命令直接测 NVIDIA NIM 是否可达
- 检查是否有代理干扰（FCC_NIM_PROXY 可设置代理）

### Admin UI 打不开
- 确认 `fcc-server` 在运行：`ps aux | grep fcc-server`
- 确认端口：`lsof -i :8082`

## 与 Claude Code 的关系

- free-claude-code **不包含** Claude Code，需要单独安装
- 它是一个 proxy 层，让 Claude Code 可以调用非 Anthropic 的模型
- Agent S 这类工具如果支持自定义 API endpoint，也可以用这个 proxy
