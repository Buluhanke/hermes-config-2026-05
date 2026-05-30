---
name: hermes-evolution-status
description: Hermes进化状态追踪 - 记录当前系统状态、已知问题和进化方向
trigger: 每天9点daily进化 或 每周一weekly进化 时更新
---

# Hermes Evolution Status Tracker

## 当前时间
2026-05-30 23:00 复盘更新

## 核心技能实际运行状态

### hermes-humanization-core ⚠️ 半残
- pyautogui: Homebrew ✅, venv ❌
- mss: 全部环境 ❌（截图依赖缺失）
- pynput: Homebrew ✅, venv ❌
- windmouse: 全部 ❌
- cloakbrowser: 全部 ❌
- VLM: qwen3-vl:2b (1.8GB) ✅ + qwen2.5:1.5b (940MB) ✅
- 技能文档丰富，实际依赖散落，无人调度

### hermes-vision-agent ✅ 感知正常
- Vision OCR 60ms ✅、PaddleOCR ✅、dddddocr ✅、pymupdf ✅、qwen3-vl:2b ✅
- 唯一完整可运行的 hermes-系核心技能

### hermes-voice-module ⚠️ 部分缺失
- Edge TTS: Framework Python 3.14 ✅, venv ✅, Homebrew ❌
- Faster-Whisper: Framework 3.14 ✅, venv ❌, Homebrew ❌

### hermes-memory-hpc ⚠️ 数据在但未激活
- ChromaDB 数据库存在（221KB）✅
- 采购流程从未主动调过 remember/recall

### hermes-evolution-context ❌ 框架文件全丢
- ltm.py ❌、evolve_context.py ❌、personality.md ❌
- current_context.json 唯一幸存

### hermes-evolution-status ✅ 文档存活

## 系统架构

### 核心进程
```
hermes gateway (PID 27863/27922)
├── mcp-chrome-stdio x2 (PID 27923, 27870)
├── n8n (Docker, PID 990, :5678)
└── Dashboard (PID 29352, :9119) ✅
```

### 浏览器
- Chrome with `--remote-debugging-port=9333`（chrome-debug profile）
- MCP Chrome Extension loaded
- CUA Driver v0.2.0 installed at /Applications/CuaDriver.app
- **Playwright CDP脚本** `~/.hermes/scripts/browser_cdp.py` 可用（MCP bridge掉线时的备用方案）

### 端口状态
- 5678: n8n ✓
- 8888: SearXNG本地Docker ✓（但当前切回公共searx.be了）
- 9333: Chrome CDP ✓
- 9119: Dashboard ✅ 已启动

### 磁盘/内存
- 磁盘: 241GB空闲 (7% used)
- 内存: ~203MB RSS，健康

## 已发现的问题

### 1. Config版本落后 (2026-05-27)
- 当前 v23，最新 v24
- `hermes config migrate` 返回空（无破坏性迁移步骤，仅提示性升级）
- 非阻塞，不影响实际功能

### 2. screen_watch hook失效 (2026-05-27)
- hook加载成功但跳过：`[screen_watch] 跳过（缺少humanization_core）`
- 根因：hook内部用`~`路径未展开，手动测试 `expanduser` 后导入成功
- 自定义hook，不影响官方核心功能
- 相关路径：`~/.hermes/hermes-humanization-core/humanization_core.py`

### 3. OAuth未登录 (2026-05-27)
- MiniMax OAuth、Google Gemini OAuth、xAI Codex OAuth均未登录
- doctor提示，不一定是故障（取决于是否使用这些渠道）

### 4. available_models警告 (持续，可忽略)
- `available_models` 被config加载器忽略
- 日志有WARNING，不影响功能
- 不要尝试删除——之前用sed导致YAML格式破坏

### 5. Python非venv运行 (2026-05-27)
- doctor建议使用venv
- 当前Python 3.14.4系统级运行
- 非阻塞，hermes功能正常

### 6. smolvlm2 幻觉问题 (2026-05-26确认，持续)
- 2B小模型，真实截图有幻觉
- 考虑换更强VLM或用AX tree代替

### 7. LTM框架未接入Hermes核心 (2026-05-26，持续)
- `evolution_core.py` 和 `personality.md` 已创建但启动时不自动加载

### 9. browser-use + Gemini 不兼容 (2026-05-30确认)
- browser-use 0.12.8 使用自定义消息类型（`browser_use.llm.messages.SystemMessage`）
- Gemini（通过 `langchain-google-genai` 的 `ChatGoogleGenerativeAI`）不识别这些自定义消息
- 第1步导航可以（通过初始action实现），但第2步开始模型调用失败
- 需升级browser-use或改用OpenAI/Anthropic驱动
- 已打6处patch（`llm.provider`/`model_name` AttributeError），系统Python (3.14) 版本

### 10. OCR引擎丢失后需修复 (2026-05-30)
- PaddleOCR和pymupdf装在hermes-agent venv里，venv清理后会丢失
- 已添加恢复命令到hermes-ocr skill
- Vision OCR：仅Homebrew Python可用（`/opt/homebrew/bin/python3`需有pyobjc）

### 11. Git备份被GitHub Push Protection拦截 (2026-05-30)
- 脚本 `git add -A` 包含了 `.env` 和 `config.yaml` 中的API Key
- GitHub检测到密钥后阻止推送，31个commit积压本地
- 解决方向：.gitignore加入.env，或清理历史中的密钥commit

### 12. SearXNG双实例 (2026-05-30)
- 本地Docker `127.0.0.1:8888` — 运行中，之前切回公共 searx.be
- 切换方法：改config.yaml中 `SEARXNG_URL`

### 13. LTM框架文件丢失 (2026-05-30 复盘发现)
- ltm.py / evolve_context.py / personality.md 全部不存在
- SKILL.md 描写的内容与文件系统不一致

### 14. 语音模块依赖跨Python环境散落 (2026-05-30 复盘发现)
- Edge TTS: Framework 3.14 + venv ✅ 但 Homebrew ❌
- Faster-Whisper: Framework 3.14 ✅ 但 venv ❌ Homebrew ❌
- 没有统一的调度入口

### 15. humanization-core 强依赖缺失 (2026-05-30 复盘发现)
- mss（截图）、windmouse（贝塞尔曲线）、cloakbrowser（反检测）全部缺失
- pyautogui/pynput 仅 Homebrew Python 有，venv 无
- gateway 环境依赖不同步

### 16. Memory限额调整 (2026-05-30)
- memory_char_limit: 200000 → 40000
- user_char_limit: 10000 → 20000

## 当前Cron Jobs状态

| 任务 | 频率 | 状态 |
|------|------|------|
| Hermes配置备份 | 每60分钟 | OK（但推送被GitHub拦截） |
| Skills同步 | 每60分钟 | 已修复 |
| 语音缓存清理 | 每天3:00 | OK |
| n8n工作流备份 | 每天4:00 | OK |
| 健康守护-自我修复 | 每5分钟 | OK |
| 夜间强化学习 | 23:00-07:00 | OK |
| Hermes自我优化循环 | 每天2:00 | 待首次执行 |

## Hermes版本
- 本地: 27d1e1c（2026-05-26最新）
- 远程: 27d1e1c ✅ 已是最新

## 进化方向

### 短期 (1-2周)
1. ✅ Dashboard已随进程启动自动运行（2026-05-27）
2. ✅ OCR引擎全部恢复（PaddleOCR + pymupdf 已重装，2026-05-30）
3. screen_watch hook修复 → 修复hook内`~`路径展开（pending）
4. Git备份推送修复 → 清理历史密钥commit + 加.gitignore（pending）
5. browser-use + Gemini → 考虑升级到0.12.9或换API驱动（pending）

### 中期 (1个月)
1. 屏幕感知闭环真实化 - screen_watcher → handler → 主动推送
2. 百度 OCR API 配置 (未配置 BAIDU_OCR_KEY)
3. 1688 采购流程半自动化

### 长期 (数字生命体2.0)
1. 感知闭环：屏幕变化 → 语义理解 → 主动Telegram推送
2. 语音对话：真实双向语音交互
3. 自主学习：不再等指令，主动找事做

## Skills创建记录
- vision/screen-watcher-vision (2026-05-26) - smolvlm2幻觉缓解策略