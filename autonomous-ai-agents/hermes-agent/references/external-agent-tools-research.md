# 外部 Agent 工具研究笔记

## gstack (85K ⭐)
- **地址**: https://github.com/garrytan/gstack
- **定位**: AI 工程工作流 — 23个专家角色（CEO评审/eng manager/QA/安全审计等）
- **依赖**: Claude Code CLI（桌面 Electron 环境）
- **安装**: `git clone --single-branch --depth=1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup`
- **状态**: ❌ 此 Mac 无头环境，Electron helper 缺失，Claude Code CLI 无法运行
- **结论**: 需要桌面级 Claude Code 环境

## gbrain (11K ⭐)
- **地址**: https://github.com/garrytan/gbrain
- **定位**: AI 记忆大脑 — 知识图谱 + 混合搜索，P@5 49.1%
- **依赖**: Bun
- **安装**:
  ```bash
  git clone --depth=1 https://github.com/garrytan/gbrain.git ~/gbrain
  cd ~/gbrain && bun install && bun link
  # 手动创建 CLI 入口
  ln -sf ~/gbrain/src/cli.ts ~/.local/bin/gbrain
  chmod +x ~/.local/bin/gbrain
  ~/.local/bin/gbrain init
  ```
- **版本**: 0.27.0（实测）
- **状态**: ✅ 已安装

## awesome-hermes-agent (4.6K ⭐)
- **地址**: https://github.com/0xNyk/awesome-hermes-agent
- **定位**: Hermes 生态导航库 — skills/tools/集成/资源汇总
- **状态**: 导航页，非可安装工具，收藏即可

## hermes-agent-self-evolution (2.4K ⭐)
- **地址**: https://github.com/NousResearch/hermes-agent-self-evolution
- **定位**: 自进化优化 — DSPy + GEPA 自动进化 skill/prompt
- **依赖**: pip
- **安装**: `pip install -e ~/hermes-agent-self-evolution`
- **成本**: $2-10/次优化运行
- **状态**: ✅ 已安装（dspy 3.2.1, gepa 0.0.27）

## OpenHarness (HKUDS)
- **地址**: https://github.com/HKUDS/OpenHarness
- **定位**: 轻量级 Agent 框架（tool-use/skills/memory/多Agent协调）
- **与 Hermes 关系**: 功能重叠，定位比 Hermes 更底层/通用
- **安装**: `curl -fsSL https://raw.githubusercontent.com/HKUDS/OpenHarness/main/scripts/install.sh | bash` 或 `pip install openharness-ai`
- **ohmo**: 基于 OpenHarness 的个人 Agent，支持飞书/Slack/Telegram/Discord
- **状态**: 未安装（与 Hermes 功能重叠）

## free-claude-code (24K ⭐)
- **地址**: https://github.com/Alishahryar1/free-claude-code
- **定位**: Claude Code 免费路由代理 — 把 Claude Code 的 Anthropic API 流量路由到 NVIDIA NIM/Kimi/Wafer/OpenRouter/DeepSeek 等免费端点
- **支持客户端**: Claude Code CLI / VSCode 扩展 / Discord bot / Telegram bot
- **状态**: ✅ 已在 aimac 部署（2026-05-14）
- **安装**:
  ```bash
  npm install -g @anthropic-ai/claude-code           # Claude Code CLI
  uv tool install --force git+https://github.com/Alishahryar1/free-claude-code.git
  ```
- **启动**: `fcc-server` → http://127.0.0.1:8082/admin 配置 API key
- **调用**: `fcc-claude "<指令>"`（自动设置环境变量 + 启动 claude 命令）
- **Hermes 调用**: `terminal` 执行 `fcc-claude "<指令>"` 即可

## Agent S (11K ⭐)
- **地址**: https://github.com/simular-ai/Agent-S
- **定位**: 开源 GUI Agent 框架 — S3 版本 OSWorld 72.6%（超越人类 72%）
- **架构**: 主模型（GPT-5等）推理 + 接地模型（UI-TARS）屏幕坐标定位 + 本地代码执行
- **支持平台**: Linux / macOS / Windows
- **状态**: ✅ 已在 aimac 部署（2026-05-14）
- **安装**:
  ```bash
  # 需要 Python ≤3.12，单独建 venv
  uv python install 3.12
  cd ~/Agent-S && uv venv .venv --python 3.12 && source .venv/bin/activate
  pip install -e .
  brew install tesseract  # OCR 依赖（已安装）
  ```
- **运行**:
  ```bash
  agent_s --provider openai --model gpt-5-2025-08-07 \
    --ground_provider huggingface --ground_url http://localhost:8080 \
    --ground_model ui-tars-1.5-7b --grounding_width 1920 --grounding_height 1080
  ```
- **依赖**: 主模型 API（OpenAI/Anthropic）+ 接地模型服务（UI-TARS-1.5-7B，需额外部署）
- **Hermes 调用**: `terminal` 执行上述命令即可，或 Python SDK 导入 `from gui_agents.s3.agents.agent_s import AgentS3`

## 推荐安装优先级

| 工具 | 对 Hermès 用户价值 | 安装难度 | 状态 |
|------|-------------------|----------|------|
| free-claude-code | 🔥 免费白嫖 Claude Code CLI | ⭐ 简单 | ✅ 已装 |
| Agent S | 🔥 顶级开源 GUI Agent，可与 Hermes 互补 | ⭐ 中等（需部署接地模型） | ✅ 已装 |
| gbrain | 🔥 显著提升任何 Agent 记忆能力 | ⭐ 简单 | ✅ 已装 |
| hermes-agent-self-evolution | 让 Hermès 自我进化 | ⭐ 简单 | ✅ 已装 |
| gstack | 桌面 Claude Code 用户用 | ⚠️ 需桌面环境 | ❌ |
| OpenHarness | 低优先级（与 Hermès 重叠） | — | 未装 |
| awesome-hermes-agent | 导航页 | — | 收藏 |

## Bun 安装要点（Intel Mac）

```bash
# 1. 先查架构
uname -m  # x86_64 = Intel，arm64 = Apple Silicon

# 2. 获取最新版 URL
curl -fsSL https://api.github.com/repos/oven-sh/bun/releases/latest | python3 -c "import sys,json; r=json.load(sys.stdin); print(r['tag_name']); [print(a['name'], a['browser_download_url']) for a in r['assets'] if 'darwin' in a['name'].lower()]"

# 3. 下载 x64 版本（Intel Mac）
curl -fsSL -o /tmp/bun.zip "https://github.com/oven-sh/bun/releases/download/bun-v1.3.13/bun-darwin-x64.zip"

# 4. 解压安装
unzip -o /tmp/bun.zip -d ~/bun-tmp
cp ~/bun-tmp/bun-darwin-x64/bun ~/local/bin/bun
chmod +x ~/local/bin/bun
~/local/bin/bun --version
```

**常见错误**: `Bad CPU type in executable` → 下载了 ARM64 版本在 Intel Mac 上运行，必须换 x64 版本。
