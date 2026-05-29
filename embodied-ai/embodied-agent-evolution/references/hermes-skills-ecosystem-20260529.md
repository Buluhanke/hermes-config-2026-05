# Hermes Skills 生态全图（2026-05-29）

## 规模

| 来源 | 数量 | 状态 |
|------|------|------|
| Community Hub | 68,530 | 需联网安装 |
| Builtin（内置） | 46 | `~/.hermes/skills/` 已装 |
| Optional（可选） | 84 | 未安装，需手动 `hermes skills install official/...` |
| Hub安装 | 10 | 本系统已装（clawhub/official） |
| Local自定义 | 57 | 本系统本地创建 |

## 本系统已装Skills（113个enabled）

**来源分布**：10 hub + 46 builtin + 57 local

**核心builtin列表**：

### apple（5个）
- `apple-notes` — Apple Notes管理（memo CLI）
- `apple-reminders` — Apple Reminders（remindctl）
- `findmy` — 设备/AirTag追踪（FindMy.app）
- `imessage` — iMessage/SMS发送接收
- `macos-computer-use` — **核心**：后台驱动macOS桌面

### autonomous-ai-agents（5个）
- `claude-code` — 委托Claude Code CLI
- `codex` — 委托OpenAI Codex CLI
- `hermes-agent` — Hermes自身配置/扩展
- `kanban-codex-lane` — Kanban工作流中Codex隔离通道
- `opencode` — 委托OpenCode CLI

### github（5个）
- `codebase-inspection` — LOC统计
- `github-auth` — HTTPS token/SSH/gh CLI登录
- `github-code-review` — PR审查
- `github-issues` — Issue管理
- `github-pr-workflow` — PR生命周期

### media（5个）
- `gif-search` — Tenor GIF搜索
- `heartmula` — Suno音乐生成
- `songsee` — 音频特征提取
- `spotify` — Spotify控制
- `youtube-content` — YouTube摘要

### mlops（10个）
- `audiocraft-audio-generation` — MusicGen
- `dspy` — 声明式LM程序
- `evaluating-llms-harness` — LLM基准测试
- `huggingface-hub` — HF模型管理
- `llama-cpp` — GGUF本地推理
- `obliteratus` — 消除LLM refusal
- `segment-anything-model` — SAM图像分割
- `serving-llms-vllm` — vLLM服务
- `weights-and-biases` — W&B实验跟踪
- `fine-tuning-with-trl` / `unsloth` — 微调

### productivity（8个）
- `airtable` — Airtable REST API
- `google-workspace` — Gmail/Calendar/Drive/Docs/Sheets
- `linear` — Linear项目管理
- `maps` — OpenStreetMap地理编码
- `nano-pdf` — PDF编辑
- `ocr-and-documents` — PDF/扫描OCR
- `powerpoint` — PPTX创建编辑
- `teams-meeting-pipeline` — Teams会议摘要

### devops（3个）
- `kanban-orchestrator` — Kanban编排
- `kanban-worker` — Kanban工作worker
- `webhook-subscriptions` — Webhook事件驱动

### data-science（1个）
- `jupyter-live-kernel` — 交互式Jupyter

## Optional Skills重点推荐（未安装）

按真人化优先级排序：

| 技能 | 说明 | 安装命令 |
|------|------|---------|
| `macos-computer-use` | ✅ builtin已装，核心桌面控制 | — |
| `agentmail` | 独立AI邮箱，自主收件处理 | `hermes skills install official/email/agentmail` |
| `searxng-search` | 70+搜索引擎聚合，隐私搜索 | `hermes skills install official/research/research-searxng-search` |
| `openhands` | 通用AI coding agent | `hermes skills install official/autonomous-ai-agents/autonomous-ai-agents-openhands` |
| `whisper` | 语音识别 | `hermes skills install official/mlops/mlops-whisper` |
| `docker-management` | Docker容器管理 | `hermes skills install official/devops/devops-docker-management` |
| `huggingface-accelerate` | 分布式训练 | `hermes skills install official/mlops/mlops-accelerate` |
| `chroma` / `pinecone` / `qdrant` | 向量数据库（RAG用） | 各有安装命令 |
| `duckduckgo-search` | 免费搜索，无API Key | `hermes skills install official/research/research-duckduckgo-search` |

## 查找技能的命令

```bash
# 列出所有已安装
hermes skills list

# 搜索Hub技能
hermes skills search <keyword>

# 安装官方optional技能
hermes skills install official/<category>/<skill>

# 安装community技能
hermes skills install clawhub/<name>
```

## Skills Hub网页（需认证）

- 官方Hub：https://hermes-agent.nousresearch.com/docs/skills/
- 显示：68,530 community + 90 builtin + 84 optional + N categories
- 需登录才能浏览和安装community技能

## 关键结论（真人化角度）

1. **builtin已经很强**：46个builtin覆盖了电脑控制、编码/github、媒体、生产力、MLOps等核心领域
2. **optional是扩展方向**：84个optional技能按需安装，特别是`agentmail`/`searxng-search`/`openhands`
3. **community 6万+质量参差**：需要甄别，部分依赖OpenClaw环境变量不兼容Hermes
4. **当前短板**：执行层（`macos-computer-use`已装但需验证）、记忆层（Hindsight已部署）