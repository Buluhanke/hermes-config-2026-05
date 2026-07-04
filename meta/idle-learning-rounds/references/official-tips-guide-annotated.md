# Hermes 官方 Tips 页面注释版

**来源**: https://hermes-agent.nousresearch.com/docs/guides/tips/
**抓取日期**: 2026-07-01
**状态**: 已验证 (cron idle 学习实际用过)

## 技巧全列表（含用法笔记）

### 1. AGENTS.md 文件 — 重复指令不再手动输入

**官方原文**: "If you find yourself repeating the same instructions ('use tabs not spaces', 'we use pytest', 'the API is at /api/v2'), put them in an AGENTS.md file. The agent reads it automatically every session — zero effort after setup."

**本机用法**: 该文件应放在项目根目录或用户 home 目录。Agent 每个会话自动读取，不需手动加载。无需记忆文件格式——纯 markdown 即可。

### 2. 具体描述问题

"Vague prompts produce vague results. Instead of 'fix the code,' say 'fix the TypeError in `api/handlers.py` on line 47 — the `process_request()` function receives `None` from `parse_body()`.'"

**本机用法**: 用户写任务时适用；agent 执行任务回 report 也适用。

### 3. 上游提供上下文

"Front-load your request with the relevant details: file paths, error messages, expected behavior."

**本机用法**: 这也就是 SOUL.md 说的「任务拆解后写入文件」。

### 4. 让 Agent 用它的工具

"Don't try to hand-hold every step. Say 'find and fix the failing test' rather than 'open `tests/test_foo.py`, look at line 42, then...'"

### 5. 用 Skills 处理复杂工作流

"Before writing a long prompt explaining how to do something, check if there's already a skill for it. Type `/skills` to browse available skills, or just invoke one directly like `/axolotl` or `/github-pr-workflow`."

**本机用法**: 这是真正的 productivity hack——不是从零写 prompt，而是 `/skills` 看已有的。

### 6. CLI 多行输入

"Press **Alt+Enter**, **Ctrl+J**, or **Shift+Enter** to insert a newline without sending."

**终端兼容性**: Shift+Enter 只在 Kitty/foot/WezTerm/Ghostty 默认工作；iTerm2/Alacritty/VS Code 需要开 Kitty 键盘协议。Alt+Enter 和 Ctrl+J 通用。

### 7. 粘贴检测

"The CLI auto-detects multi-line pastes. Just paste a code block or error traceback directly — it won't send each line as a separate message."

### 8. Ctrl+C 中断和重定向

"Press **Ctrl+C** once to interrupt the agent mid-response. You can then type a new message to redirect it. Double-press Ctrl+C within 2 seconds to force exit."

**现场用法**: 用户说"别做 X 了做 Y"时触发。

### 9. `hermes -c` 恢复会话

"Forgot something from your last session? Run `hermes -c` to resume exactly where you left off, with full conversation history restored. You can also resume by title: `hermes -r "my research project"`."

### 10. Ctrl+V 贴图给视觉分析

"Press **Ctrl+V** to paste an image from your clipboard directly into the chat. The agent uses vision to analyze screenshots, diagrams, error popups, or UI mockups — no need to save to a file first."

### 11. `/` + Tab 自动补全 slash 命令

"Type `/` and press **Tab** to see all available commands."

### 12. 若不清楚选哪个模型

"Run `hermes setup --portal` — you get 300+ models including Claude, GPT-5, and Gemini under one subscription."

## 价值评级（for future idle learning）

| 技巧 | 实用度 | 说明 |
|---|---|---|
| AGENTS.md | ⭐⭐⭐⭐⭐ | 省掉「每次都要说」的重复，最高杠杆 |
| `hermes -c` 恢复会话 | ⭐⭐⭐⭐ | 中断后恢复，避免从头说 |
| Ctrl+C 中断 | ⭐⭐⭐⭐ | 不比在 terminal 等 5 分钟 |
| `/skills` 查已有 skill | ⭐⭐⭐⭐ | 避免重复发明轮子 |
| Ctrl+V 贴图 | ⭐⭐⭐ | 省去 save/to/path 步骤 |
| 多行输入 Alt+Enter | ⭐⭐⭐ | terminal 日常按键 |
