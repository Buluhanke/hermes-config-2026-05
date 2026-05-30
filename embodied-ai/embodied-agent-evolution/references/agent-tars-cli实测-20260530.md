# Agent TARS CLI 实测记录（2026-05-30）

## 安装状态
- 安装位置：`/Users/aimac/.local/bin/agent-tars`
- 版本：v0.3.0（Node.js，requires Node >= 22.15.0，当前v24.14.1 ✅）
- 安装方式：`npm install -g @agent-tars/cli`

## 核心命令
```bash
agent-tars run --headless --input "指令"        # headless执行
agent-tars serve --port 8888 --open             # 启动web服务
agent-tars request --help                        # 直接API调用
```

## 模型配置（实测）
```bash
# ✅ 本地Ollama（最稳定）
agent-tars run --headless \
  --model.provider ollama \
  --model.id qwen2.5:1.5b \
  --model.baseURL "http://localhost:11434/v1" \
  --input "say hello"

# ✅ 云端MiniMax（兼容OpenAI格式）
agent-tars run --headless \
  --model.provider openai \
  --model.id MiniMax-M2.7 \
  --model.apiKey "$MINIMAX_KEY" \
  --model.baseURL "https://api.minimaxi.com/v1" \
  --input "say hello"

# ⚠️ 端口占用：默认8899被Hindsight占用，启动前需停掉容器
docker stop hermes-hindsight
```

## ⚠️ 已知问题

### 1. 端口8899被Hindsight占用
- agent-tars默认端口8899，与Hindsight Docker容器冲突
- 解决：启动前 `docker stop hermes-hindsight`，完成后 `docker start hermes-hindsight`
- 临时方案：`--port 18765`（随机高端口）

### 2. MiniMax额度限制
- MiniMax M2.7免费额度已耗尽（429 usage limit exceeded）
- 解决：等额度刷新，或用本地ollama模型
- 本地模型测试正常：qwen2.5:1.5b响应正常，qwen3-vl:2b超时

### 3. smolvlm2-agentic-gui响应极慢
- 约46秒+，建议用qwen2.5:1.5b纯文本模型做快速测试
- vision模型成本高，screen分析用smolvlm2，文本任务用qwen2.5

## 与UI-TARS Desktop的关系
| 属性 | Agent TARS CLI | UI-TARS Desktop |
|------|--------------|----------------|
| 安装状态 | ✅ 已安装可用 | ❌ brew损坏+GitHub超时 |
| 架构 | vision→action→verify循环 | 相同 |
| 对外API | 有（serve模式） | 无 |
| 费用 | 本地免费 | 免费 |
| M4适配 | ✅ 完全兼容 | ⚠️ 无.dmg包 |

## 实际测试结果（2026-05-30）
```
$ agent-tars run --headless --model.provider ollama --model.id qwen2.5:1.5b ...
Hello! How can I assist you today?
```

## 适用场景
- 快速CLI测试（prompt验证、屏幕截图描述）
- MCP server模式：作为MCP工具被其他Agent调用
- 自动化流程节点（headless，无UI）