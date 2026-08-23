---
name: ollama
description: 本地 LLM 推理引擎 — 安装、启动、模型管理、REST API 调用、与 Hermes 集成。触发：ollama、本地模型、local LLM、离线推理、本地跑模型。
triggers:
  - ollama
  - 本地模型
  - local LLM
  - 离线推理
  - 本地跑模型
  - ollama serve
  - ollama run
version: "1.0"
author: Hermes Agent
tags:
  - llm
  - local-ai
  - inference
  - ollama
---

# Ollama Skill

本地 LLM 推理引擎，通过单一命令运行开源大语言模型（Llama 3.2、Phi 3、Qwen 2.5 等），无需云端 API Key，完全离线可用。

---

## 目录

1. [安装](#1-安装)
2. [启动服务](#2-启动服务)
3. [模型管理](#3-模型管理)
4. [查询/对话](#4-查询对话)
5. [REST API](#5-rest-api)
6. [与 Hermes 集成](#6-与-hermes-集成)
7. [坑点](#7-坑点)
8. [验证](#8-验证)

---

## 1. 安装

### 方式一：Homebrew（推荐，macOS）

```bash
brew install ollama
```

> Homebrew 会自动配置 launchd 开机自启服务（`brew services run ollama`）。

### 方式二：Install Script（Linux/macOS 通用）

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 方式三：下载二进制（手动）

```bash
# 下载最新版 macOS arm64 压缩包
curl -LO https://github.com/ollama/ollama/releases/latest/download/ollama-darwin-arm64.zip
unzip ollama-darwin-arm64.zip
mv Ollama-darwin-arm64 /usr/local/bin/ollama   # 或 ~/local/bin/ollama
chmod +x /usr/local/bin/ollama
```

### 验证安装

```bash
ollama version
```

---

## 2. 启动服务

### 2.1 前台启动（调试用）

```bash
ollama serve
```

输出类似：
```
🚀 Ollama is running on http://127.0.0.1:11434
```

### 2.2 后台运行（推荐持久化）

**macOS via launchd（Homebrew 安装默认方式）：**

```bash
brew services start ollama   # 开机自启
brew services stop ollama    # 停止
brew services restart ollama # 重启
```

**Linux via systemd：**

```bash
# 安装时脚本会自动创建 systemd 服务，无需手动配置
systemctl --user enable ollama
systemctl --user start ollama
systemctl --user status ollama
```

**nohup 方式（无 launchd/systemd 时）：**

```bash
nohup ollama serve > ~/.ollama/ollama.log 2>&1 &
echo $! > ~/.ollama/ollama.pid
```

### 2.3 端口说明

- 默认监听 `http://127.0.0.1:11434`
- **仅本地回环接口**，不暴露到局域网（安全）
- 如需远程访问，参见 [坑点](#7-坑点) 章节

### 2.4 环境变量（可选）

```bash
export OLLAMA_HOST=0.0.0.0:11434        # 监听所有接口（谨慎）
export OLLAMA_MODELS=/path/to/models    # 自定义模型存储路径
export OLLAMA_KEEP_ALIVE=5m             # 模型在内存中保持时间
export OLLAMA_NUM_PARALLEL=4            # 并行推理数量
ollama serve
```

---

## 3. 模型管理

### 3.1 拉取模型

```bash
# 标准格式：ollama pull <model-name>
ollama pull llama3.2                         # Llama 3.2 3B（默认 latest tag，约 2GB）
ollama pull llama3.2:3b
ollama pull llama3.2:1b                      # 量化版，更小更快
ollama pull phi3                             # Microsoft Phi-3 Mini
ollama pull phi3:latest
ollama pull qwen2.5                          # Qwen 2.5 系列
ollama pull qwen2.5:7b
ollama pull qwen2.5:14b                      # 较大模型，需要更多内存
ollama pull mistral                          # Mistral 7B
ollama pull mixtral
ollama pull deepseek-r1:7b                   # DeepSeek R1
ollama pull deepseek-r1:14b
ollama pull gemma2                           # Google Gemma 2
ollama pull gemma2:9b
ollama pull nomic-embed-text                 # 嵌入模型（用于 RAG）
```

### 3.2 查看已下载模型

```bash
ollama list
```

示例输出：
```
NAME                ID           SIZE      MODIFIED
llama3.2:3b         a6d0b2c3...  1.9GB     2 hours ago
phi3:latest         b7c1d4e5...  2.3GB     3 days ago
qwen2.5:7b          c8e2f3a4...  4.1GB     1 week ago
```

### 3.3 删除模型

```bash
ollama rm llama3.2:3b
ollama rm phi3
```

### 3.4 模型文件位置

```bash
# 默认存放路径
ls ~/.ollama/models/

# 自定义路径
echo $OLLAMA_MODELS
```

### 3.5 从 GGUF 文件导入自定义模型

如果已有 GGUF 格式模型文件，可通过 Modelfile 导入：

```bash
# 1. 创建 Modelfile
cat > ~/Modelfile << 'EOF'
FROM ./my-model.gguf
PARAMETER temperature 0.7
PARAMETER top_p 0.9
TEMPLATE """{{ .System }}
User: {{ .Prompt }}
Assistant:"""
EOF

# 2. 创建模型
ollama create my-custom-model -f ~/Modelfile

# 3. 使用
ollama run my-custom-model
```

---

## 4. 查询/对话

### 4.1 交互式对话（REPL）

```bash
ollama run llama3.2
```

进入交互式界面，直接输入问题，Ctrl+D 退出。

### 4.2 单次查询（非交互式）

```bash
# 通过 stdin 传入
echo "What is the capital of France?" | ollama run llama3.2

# 通过 -p 参数
ollama run llama3.2 "Explain quantum entanglement in simple terms"

# 多轮对话（multiline 支持）
ollama run llama3.2 << 'EOF'
User: What is photosynthesis?
Assistant: Photosynthesis is the process...
User: What about respiration?
EOF
```

### 4.3 参数控制

```bash
ollama run llama3.2 \
  --verbose \
  --temperature 0.7 \
  --top_p 0.9 \
  --top_k 40 \
  --num_predict 512 \
  --stop "User:"

# 参数说明：
# --verbose        显示完整响应（含 timing 信息）
# --temperature    随机性（0=确定输出，2=高随机），默认 0.7
# --top_p          核采样阈值，默认 0.9
# --top_k          top-k 采样，默认 40
# --num_predict    最大 token 数（-1 为无限制）
# --stop           遇到指定字符串时停止生成
```

### 4.4 多模态模型（视觉）

```bash
# LLaVA 等视觉语言模型支持图片输入
ollama run llava "描述这张图片的内容" --image /path/to/image.png
```

---

## 5. REST API

Ollama 提供完整的 REST API，Base URL：`http://127.0.0.1:11434`

### 5.1 生成文本（/api/generate）

**请求：**

```bash
curl -X POST http://127.0.0.1:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "prompt": "What is the meaning of life?",
    "stream": false,
    "options": {
      "temperature": 0.7,
      "num_predict": 256
    }
  }'
```

**响应（stream=false）：**

```json
{
  "model": "llama3.2",
  "created_at": "2025-01-01T00:00:00.000000Z",
  "response": "The meaning of life is...",
  "done": true,
  "context": [1, 2, 3, ...],
  "total_duration": 5123000000,
  "load_duration": 1200000000,
  "prompt_eval_count": 12,
  "eval_count": 128,
  "eval_duration": 4000000000
}
```

### 5.2 对话（/api/chat）

```bash
curl -X POST http://127.0.0.1:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ],
    "stream": false
  }'
```

### 5.3 流式输出

```bash
curl -X POST http://127.0.0.1:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "prompt": "Write a haiku about coding.",
    "stream": true
  }'
# 响应为 Server-Sent Events，每行一个 JSON 对象
```

### 5.4 嵌入（/api/embeddings）

```bash
curl -X POST http://127.0.0.1:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nomic-embed-text",
    "prompt": "The quick brown fox jumps over the lazy dog"
  }'
```

### 5.5 模型列表

```bash
curl http://127.0.0.1:11434/api/tags
```

### 5.6 获取模型信息

```bash
curl http://127.0.0.1:11434/api/show?info=true \
  -d '{"name": "llama3.2"}'
```

### 5.7 创建/删除模型

```bash
# 创建（从 Modelfile）
curl -X POST http://127.0.0.1:11434/api/create \
  -H "Content-Type: application/json" \
  -d '{"name": "my-model", "path": "/path/to/Modelfile"}'

# 删除
curl -X DELETE http://127.0.0.1:11434/api/delete \
  -d '{"name": "my-model"}'
```

---

## 6. 与 Hermes 集成

> 注意：截至当前版本，Hermes 尚未内置 ollama provider 插件。以下是两种可行集成方式，推荐方式一。

### 6.1 方式一：通过 OpenAI 兼容 API 接入（推荐）

Ollama 提供与 OpenAI API 兼容的端点，可直接配置为 Hermes 的 custom provider。

**步骤：**

1. 确保 ollama serve 运行中
2. 配置 Hermes custom provider（config.yaml）：

```yaml
custom_providers:
  ollama_local:
    api_base: http://127.0.0.1:11434/v1
    api_key: "ollama"   # Ollama 不需要真实 key，但字段必填
    model: llama3.2
    name: Ollama Local
    provider: openai    # Ollama v0.1.20+ 支持 OpenAI 兼容格式
```

3. 重启 Hermes Gateway 后，使用 `/model ollama_local` 切换

### 6.2 方式二：通过 MCP Server 接入

如果需要更紧密的集成，可使用社区 MCP 工具连接 Hermes：

```bash
# 安装 ollama-mcp 或类似工具（需自行调研社区项目）
# 此方式依赖第三方项目，稳定性不一
```

> ⚠️ MCP 集成方式取决于社区插件可用性，建议优先使用方式一。

### 6.3 在 Hermes Skill 中调用 Ollama

作为工作流的一部分，可在 skill 中调用 ollama REST API：

```bash
# 示例：在 skill 脚本中调用 ollama
RESULT=$(curl -s -X POST http://127.0.0.1:11434/api/generate \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"llama3.2\",\"prompt\":\"$USER_PROMPT\",\"stream\":false}"))
echo "$RESULT" | jq -r '.response'
```

### 6.4 嵌入模型集成（RAG 场景）

```bash
# 使用 nomic-embed-text 获取文本向量
EMBEDDING=$(curl -s -X POST http://127.0.0.1:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"nomic-embed-text\",\"prompt\":\"$TEXT\"}")
```

---

## 7. 坑点

### 坑点 1：ollama serve 后台运行与开机自启

**问题：** `ollama serve` 在终端关闭后终止，需要持久化运行。

**解决方案：**
- macOS：使用 Homebrew 服务管理 `brew services start ollama`
- Linux：使用 systemd `systemctl --user enable ollama`
- 确认服务状态：`brew services list` 或 `systemctl --user status ollama`

### 坑点 2：模型文件体积巨大

**问题：** 7B 模型约 4GB，14B 模型约 8GB，磁盘和内存消耗大。

**解决方案：**
- 拉取前检查磁盘空间：`df -h ~/.ollama/models`
- 选择量化版本：`ollama pull llama3.2:1b`（1B 约 700MB）
- 使用 `ollama rm` 删除不再需要的模型
- Mac M 系列芯片运行更高效（统一内存）

### 坑点 3：端口 11434 默认仅本地监听

**问题：** 远程机器无法访问本机 ollama 服务。

**解决方案（谨慎使用）：**
```bash
# 仅在内网可信环境下暴露
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```
- 公网暴露存在安全风险，Ollama 没有内置认证
- 推荐配合 VPN 或 SSH 隧道使用

### 坑点 4：模型拉取中断后无法续传

**问题：** `ollama pull` 中断后重新拉取需要从头开始。

**解决方案：**
- 确保网络稳定
- 拉取前留足磁盘空间
- 使用 `ollama pull --resume`（部分版本支持）

### 坑点 5：GPU 内存不足（Mac GPU 调度）

**问题：** Mac 上多个应用并发使用 GPU 时，Ollama 推理失败或被 OOM Killer 终止。

**解决方案：**
- 关闭其他 GPU 密集型应用（Xcode、Chrome、视频编辑软件）
- 使用更小的量化模型
- 查看 GPU 使用情况：`sudo powermetrics --samplers gpu_power -i 1000`

### 坑点 6：Model not found 错误

**问题：** `ollama run xxx` 提示模型不存在。

**解决方案：**
```bash
# 确认模型已拉取
ollama list

# 完整指定 tag（部分模型需要精确版本）
ollama pull llama3.2:3b
ollama run llama3.2:3b   # 使用完整名称
```

### 坑点 7：curl 请求返回 404 或空响应

**问题：** API 路径错误或服务未启动。

**解决方案：**
```bash
# 确认服务运行
curl http://127.0.0.1:11434/api/tags

# 检查 ollama 进程
ps aux | grep ollama

# 重启服务
brew services restart ollama
```

### 坑点 8：Mac ARM64 上运行 x86 架构镜像

**问题：** 通过 Docker 等方式运行时可能出现架构不匹配。

**解决方案：**
- macOS 直接安装版（brew）已针对 ARM64 优化，优先使用原生安装

---

## 8. 验证

### 8.1 基础验证清单

```bash
# 1. 检查 ollama 可执行
ollama version

# 2. 检查服务是否运行（进程）
ps aux | grep ollama | grep -v grep
# 期望：看到 ollama serve 进程

# 3. 检查服务是否监听端口
lsof -i :11434
# 期望：本地回环地址，ollama 进程

# 4. 检查模型列表（非空）
ollama list
# 期望：至少一个模型

# 5. 简单推理测试（非交互式）
echo "2+2等于几？" | ollama run llama3.2
# 期望：返回结果 "4"
```

### 8.2 API 验证

```bash
# 健康检查
curl -s http://127.0.0.1:11434/api/tags | jq '.models | length'
# 期望：>= 1（已有模型数量）

# 生成接口测试
RESPONSE=$(curl -s -X POST http://127.0.0.1:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2","prompt":"Say exactly: hello","stream":false}')
echo "$RESPONSE" | jq -r '.response'
# 期望：包含 "hello"
```

### 8.3 完整流程验证脚本

```bash
#!/bin/bash
set -e

echo "=== Ollama 验证脚本 ==="

echo "[1/6] 检查 ollama 版本..."
ollama version

echo "[2/6] 检查服务进程..."
if pgrep -x ollama > /dev/null; then
  echo "✓ Ollama 进程运行中"
else
  echo "✗ Ollama 进程未运行，请运行: brew services start ollama"
  exit 1
fi

echo "[3/6] 检查端口 11434..."
if lsof -i :11434 | grep -q LISTEN; then
  echo "✓ 端口 11434 正在监听"
else
  echo "✗ 端口 11434 未监听"
  exit 1
fi

echo "[4/6] 检查模型列表..."
MODEL_COUNT=$(ollama list | tail -n +2 | wc -l | tr -d ' ')
if [ "$MODEL_COUNT" -ge 1 ]; then
  echo "✓ 已安装 $MODEL_COUNT 个模型"
else
  echo "! 尚未安装任何模型，建议: ollama pull llama3.2"
fi

echo "[5/6] 测试生成 API..."
RESULT=$(curl -s -X POST http://127.0.0.1:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2","prompt":"Reply with exactly the word: ok","stream":false}')
if echo "$RESULT" | jq -r '.response' | grep -qi "ok"; then
  echo "✓ API 生成正常"
else
  echo "✗ API 生成异常: $(echo $RESULT | jq -r '.response')"
  exit 1
fi

echo "[6/6] 测试对话 API..."
CHAT_RESULT=$(curl -s -X POST http://127.0.0.1:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2","messages":[{"role":"user","content":"Reply with exactly: done"}],"stream":false}')
if echo "$CHAT_RESULT" | jq -r '.message.content' | grep -qi "done"; then
  echo "✓ 对话 API 正常"
else
  echo "✗ 对话 API 异常"
  exit 1
fi

echo ""
echo "=== 验证完成，所有检查通过 ==="
```

---

## 附录：常用模型推荐

| 模型 | 参数量 | 适用场景 | 最低内存 |
|------|--------|----------|----------|
| llama3.2:1b | 1B | 资源极度受限环境 | 4GB |
| llama3.2:3b | 3B | 日常对话、轻量任务 | 6GB |
| phi3:3.8b | 3.8B | 指令跟随、代码 | 8GB |
| qwen2.5:7b | 7B | 通用对话、中文 | 8GB |
| llama3.2:7b | 7B | 高质量对话 | 8GB |
| qwen2.5:14b | 14B | 复杂推理 | 16GB |
| mixtral:8x7b | 8x7B MoE | 高质量生成 | 12GB |
| deepseek-r1:7b | 7B | 推理/数学 | 8GB |

> Mac M 系列芯片推荐优先使用 llama3.2:3b 或 qwen2.5:7b，推理速度可接受且内存压力较小。