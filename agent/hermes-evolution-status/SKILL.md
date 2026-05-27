---
name: hermes-evolution-status
description: Hermes进化状态追踪 - 记录当前系统状态、已知问题和进化方向
trigger: 每天9点daily进化 或 每周一weekly进化 时更新
---

# Hermes Evolution Status Tracker

## 当前时间
2026-05-27

## 系统架构

### 核心进程
```
hermes gateway (PID 27863/27922)
├── mcp-chrome-stdio x2 (PID 27923, 27870)
├── n8n (Docker, PID 990, :5678)
└── Dashboard (PID 29352, :9119) ✅
```

### 浏览器
- Chrome with `--remote-debugging-port=9333`
- MCP Chrome Extension loaded
- CUA Driver v0.2.0 installed at /Applications/CuaDriver.app

### 端口状态
- 5678: n8n ✓
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

### 8. CodeGraph MCP 失败 (持续，可忽略)
- `codegraph` 可执行文件不存在
- 不影响核心功能

## 当前Cron Jobs状态
无（用户不需要定时任务）

## Hermes版本
- 本地: 27d1e1c（2026-05-26最新）
- 远程: 27d1e1c ✅ 已是最新

## 进化方向

### 短期 (1-2周)
1. ✅ Dashboard已随进程启动自动运行（2026-05-27）
2. screen_watch hook的humanization_core路径问题 → 修复hook内`~`路径展开
3. smolvlm2 幻觉问题 → 考虑换用更强的 VLM 或用 AX tree 代替
4. Config v23→v24 正式迁移（可选，当前无破坏性差异）

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