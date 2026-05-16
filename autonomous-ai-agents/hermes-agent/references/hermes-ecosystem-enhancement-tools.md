# Hermes Ecosystem Enhancement Tools (2026-05-12)

五套可以补充 Hermes Agent 能力的工具，覆盖代码上下文、Token 成本、Web UI、长期记忆、多Agent编排。

## 1. Repomix — 代码上下文打包

- **仓库**：`github.com/yamadashy/repomix`
- **用途**：把整个代码仓库打包成一个 AI 友好文件，方便 Hermes 一次性读取项目全貌
- **安装**：`npm install -g repomix` 或 `npx repomix .`
- **Hermes skill**：`hermes skills install https://raw.githubusercontent.com/yamadashy/repomix/main/.claude/skills/repomix-explorer/SKILL.md`
- **使用**：`repomix --style markdown` → 输出到 `repomix-output.md`，可直接传给 LLM
- **支持**：MCP Server 模式（`npx repomix --mcp`）
- **特点**：轻量，零配置，One-shot

## 2. TokScale — Token 成本可视化

- **仓库**：`github.com/junhoyeo/tokscale`
- **用途**：跟踪所有 AI 编码 Agent 的 Token 使用量和成本（支持 Hermes）
- **安装**：`npm install -g tokscale` 或 `npx tokscale@latest`
- **Hermes 数据来源**：原生读取 `$HERMES_HOME/state.db`（SQLite sessions 表）
- **使用**：`tokscale`（TUI模式）、`tokscale --light`（表格模式）
- **支持 20+ Agent**：OpenCode、Claude Code、Codex、Copilot CLI、Cursor 等
- **Rust 核心**：10x 加速文件解析，工业级性能
- **特点**：轻量，可视化优秀，有社交排行榜

## 3. Hermes Workspace — Web 工作台

- **仓库**：`github.com/outsourc-e/hermes-workspace`
- **用途**：给 Hermes Agent 一个 Web UI —— 聊天、文件、终端、记忆、Skill管理
- **安装方式**：

### 方式A：附加到现有 Hermes（推荐，已有 Hermes 环境）
```bash
git clone https://github.com/outsourc-e/hermes-workspace.git ~/hermes-workspace
cd ~/hermes-workspace
pnpm install
cp .env.example .env
echo 'HERMES_API_URL=http://127.0.0.1:8642' >> .env
echo 'HERMES_DASHBOARD_URL=http://127.0.0.1:9119' >> .env
pnpm dev  # → http://localhost:3000
```

### 方式B：Docker Compose
```bash
docker compose up  # 同时启动 Hermes Agent + Workspace
```

### 方式C：一键脚本
```bash
curl -fsSL https://raw.githubusercontent.com/outsourc-e/hermes-workspace/main/install.sh | bash
```

- **前置条件**：Hermes Gateway 运行中（`:8642`）、Dashboard 运行中（`:9119`）
- **验证**：
  ```bash
  curl http://127.0.0.1:8642/health       # → {"status":"ok"}
  curl http://127.0.0.1:9119/api/status   # → {"status":"ok", ...}
  ```
- **特点**：PWA 可安装成桌面/手机应用，Tailscale 远程访问

## 4. Hindsight — 智能长期记忆

- **官网**：`https://vectorize.io/hindsight` | 集成文档：`https://hindsight.vectorize.io/sdks/integrations/hermes`
- **用途**：替换 Hermes 内置记忆系统，实现跨会话智能召回
- **两种模式**：

### Cloud 模式（推荐，最简单）
1. 注册：`https://ui.hindsight.vectorize.io/connect` → 获取 API Key
2. 配置：
```bash
hermes memory setup  # 选 hindsight
```
或手动：
```bash
hermes config set memory.provider hindsight
echo "HINDSIGHT_API_KEY=你的key" >> ~/.hermes/.env
echo "HINDSIGHT_API_URL=https://api.hindsight.vectorize.io" >> ~/.hermes/.env
```

### Local 模式（嵌入式 PostgreSQL + LLM）
- 需要额外 LLM API key（用于记忆提取和合成）
- 自动在后台启动 Hindsight daemon（端口 9077）
- 首次启动需等待 ~1 分钟（PostgreSQL 初始化）
- 日志：`~/.hermes/logs/hindsight-embed.log`

- **特性**：
  - 自动召回（每次 LLM 调用前查询相关记忆）
  - 自动保留（每次响应后存储对话）
  - `hindsight_retain` / `hindsight_recall` / `hindsight_reflect` 三个显式工具
  - 三种模式：hybrid（自动+工具）、context（仅自动）、tools（仅工具）
- **注意**：建议禁用 Hermes 内置 memory 避免冲突：`hermes tools disable memory`
- **需要**：Hermes Agent PR #2823 或更新版本（支持 lifecycle hooks）

## 5. Mission Control — 多 Agent 指挥中心

- **仓库**：`github.com/builderz-labs/mission-control`
- **用途**：任务看板、成本追踪、Skill 管理、安全审计——多 Agent 编排
- **安装**：
```bash
git clone https://github.com/builderz-labs/mission-control.git
cd mission-control
bash install.sh --local  # Node 22+ + pnpm 自动处理
# open http://localhost:3000/setup
```
或 Docker：
```bash
docker compose up
```

- **特性**（32 个面板）：
  - 任务看板（6列 Kanban）
  - 多 Gateway 连接（OpenClaw、CrewAI、LangGraph、AutoGen）
  - 安全审计（风险评分、密钥检测、MCP 审计）
  - Claude Code 桥接（只读集成）
  - 自然语言定时任务
  - 无外部依赖（SQLite + pnpm start）
- **适用场景**：多 Agent 协同、生产环境运维
- **⚠️ 较重**：Next.js 16 + React 19 + TypeScript 5.7，适合有多 Agent 需求的场景

## 安装优先级建议

| 层级 | 工具 | 难度 | 价值 |
|------|------|------|------|
| 1. 轻量即用 | Repomix + TokScale | ★☆☆ | ★★★ |
| 2. 记忆/大脑 | GBrain | ★★☆ | ★★★ |
| 3. 后续扩展 | Hermes Workspace / Hindsight / Mission Control | ★★☆ | ★★★ |

## 6. GBrain — 记忆力与图谱引擎  
- **仓库**：`https://github.com/garrytan/gbrain`  
- **用途**：替代 Hermes 内置 memory，提供实体图谱 + 向量搜索的永久记忆系统。自带 42 个 skills（笔记归档、股价追踪、Reddit 验证等）。  
- **安装**（已验证，macOS 26.4.1 arm64，Bun 1.3.13）：  
  ```bash
  git clone --depth=1 https://github.com/garrytan/gbrain.git ~/gbrain
  cd ~/gbrain && bun install && bun link
  export PATH="$HOME/.bun/bin:$PATH"   # bun link 创建 symlink 在此
  export GOOGLE_GENERATIVE_AI_API_KEY="你的key"
  gbrain init --non-interactive --pglite
  ```
- **配置嵌入引擎**（切换到 Google Gemini，避免 OpenAI key 依赖）：  
  ```bash
  gbrain config set embedding_provider google
  gbrain config set embedding_model google:gemini-embedding-001
  gbrain doctor --json   # 验证 → health_score 80（新装正常）
  ```
- **验证**：  
  ```bash
  gbrain --version          # v0.33.0
  gbrain providers list     # Google ✓ ready
  gbrain embed --stale      # 首次生成嵌入
  ```
- **Hermes 集成**：通过 MCP Server 对接（见 hermes-agent skill 中 gbrain 安装章节）
- **注意**：`~/.bun/bin/` 可能不在 PATH 中，需手动 export 或加到 `.zshrc`

## 注意事项

- **Hermes Workspace** 和 **Mission Control** 都跑在 3000 端口 —— 不能同时默认启动
- **Hindsight Cloud** 需要注册拿 key，但比 Local 模式简单得多
- **TokScale** 已经原生支持 Hermes，不需要额外配置
- **Repomix** 的 Hermes skill 可以直接安装使用
