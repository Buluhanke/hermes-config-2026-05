# Hermes Skills 生态速查（2026-05-29）

## 本系统已装：113个skills

| 来源 | 数量 | 说明 |
|------|------|------|
| builtin | 46 | 随 Hermes 安装，不可删 |
| local | 57 | 自定义技能 |
| hub | 10 | clawhub/official 安装 |

**查看命令**：`hermes skills list`

## 核心builtin清单（按类别）

### apple（5个，全已装）
`apple-notes` `apple-reminders` `findmy` `imessage` `macos-computer-use`

### autonomous-ai-agents（5个，全已装）
`claude-code` `codex` `hermes-agent` `kanban-codex-lane` `opencode`

### github（5个，全已装）
`codebase-inspection` `github-auth` `github-code-review` `github-issues` `github-pr-workflow`

### devops（3个，全已装）
`kanban-orchestrator` `kanban-worker` `webhook-subscriptions`

### mlops（10个，部分local）
builtin: `audiocraft` `dspy` `evaluating-llms-harness` `huggingface-hub` `llama-cpp` `obliteratus` `segment-anything` `serving-llms-vllm` `weights-and-biases`
local: `fine-tuning-with-trl` `unsloth`

### media（5个，全已装）
`gif-search` `heartmula` `songsee` `spotify` `youtube-content`

### productivity（8个，全已装）
`airtable` `google-workspace` `linear` `maps` `nano-pdf` `ocr-and-documents` `powerpoint` `teams-meeting-pipeline`

### data-science（1个）
`jupyter-live-kernel`

### 其他builtin
`dogfood` `yuanbao` `godmode` `openhue` `xurl` `systematic-debugging` `himalaya` `minecraft-modpack-server` `pokemon-player`

## Optional Skills（84个，未安装）

按真人化优先级推荐：

| 技能 | 安装命令 | 说明 |
|------|---------|------|
| `agentmail` | `hermes skills install official/email/agentmail` | AI独立邮箱，自主收件处理 |
| `searxng-search` | `hermes skills install official/research/research-searxng-search` | 70+搜索引擎聚合 |
| `openhands` | `hermes skills install official/autonomous-ai-agents/autonomous-ai-agents-openhands` | 通用AI coding agent |
| `docker-management` | `hermes skills install official/devops/devops-docker-management` | Docker容器管理 |
| `duckduckgo-search` | `hermes skills install official/research/research-duckduckgo-search` | 免费搜索，无需API Key |
| `whisper` | `hermes skills install official/mlops/mlops-whisper` | 语音识别 |

**已装optional**：`agentmail`

## Community Skills（68,530个）

网页：https://hermes-agent.nousresearch.com/docs/skills/
- 需要登录才能浏览和安装
- 质量参差，部分依赖OpenClaw环境变量（不兼容Hermes）
- 安装前检查SKILL.md是否引用`OPENCLAW_*`环境变量

## 真人化优先级结论

✅ **已装核心**：macos-computer-use / jupyter-live-kernel / systematic-debugging / obsidian
⬜ **建议安装**：agentmail / searxng-search / openhands / docker-management
❌ **暂不需要**：大部分mlops/fine-tuning类（无本地训练需求）