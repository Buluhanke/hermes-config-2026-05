# Hermes Doctor 排障笔记

## 常见警告项解释

### browser-cdp 系统依赖未满足
**原因**：browser_cdp 工具需要 Chrome 开启 `--remote-debugging-port`，但当前 Playwright agent-browser 模式不暴露 CDP 端口。

**处理**：如需启用，在专属 Chrome（9333）上配置 `--remote-debugging-port=9333`。用户 Chrome（9222）已配置此端口。

**不影响**：普通浏览器操作（browser_navigate、browser_click 等）无需此工具。

### OAuth 未登录
**原因**：Codex、Gemini、MiniMax、xAI 等显示 "OAuth not logged in"。

**结论**：用 API Key 方式配置就不需要 OAuth。API Key 能用 = 正常，OAuth 可以忽略。

### 可选依赖缺失（Telegram/Discord 等）
**原因**：这些平台根本没配置，所以报缺失。

**结论**：通讯渠道正常就不需要管，不影响使用。

### hermes doctor --fix
**注意**：`--fix` 不能修复 browser-cdp 和 OAuth 问题。它只修复能自动修复的项（如安装缺失的 pip 包）。

## insights 命令局限性
`hermes insights` 只显示 **token 消耗量**，不显示各平台的额度/余额。查询额度需登录各平台官网：
- MiniMax：https://www.minimaxi.com/
- DeepSeek：https://platform.deepseek.com/
- OpenRouter：https://openrouter.ai/credits