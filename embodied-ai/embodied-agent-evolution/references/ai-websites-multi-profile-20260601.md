# AI平台多账号登录问题（2026-06-01）

## 问题现象

browser工具操作chrome-debug profile访问AI网站时，显示未登录。但用户在日常Chrome中已登录。

## 根本原因

Chrome使用双profile隔离：

| Profile | 路径 | 用途 |
|---------|------|------|
| chrome-debug | `~/.hermes/chrome-debug/` | Hermes browser工具专用 |
| Default | `~/Library/Application Support/Google/Chrome/Default/` | 用户日常Chrome |

**Cookie和登录状态不共享**。

## 各平台实测状态（2026-06-01凌晨）

| 平台 | 状态 | 说明 |
|------|------|------|
| ✅ 豆包 | 可用，已登录 | 直接对话 |
| ❌ 智谱GLM | 滑动验证 | 需要真人滑动 |
| ❌ DeepSeek | 手机验证码 | 需要手机号 |
| ❌ ChatGPT | cookies未保存 | 需要重新登录 |
| ⚠️ Grok | 未登录 | 需要注册账号 |

## 解决方案

在chrome-debug中打开目标网站，用户手动登录一次，cookies保存后即可正常使用browser工具。

## Chrome双实例架构澄清（2026-06-01修正）

之前错误结论："所有Chrome进程都是chrome-debug"。正确理解：

- `ps aux | grep Chrome` 显示的进程确实是chrome-debug
- 但用户日常Chrome（Default profile）的cookies存在另一个目录
- 两者是独立的，不是"所有Chrome都是chrome-debug"

## 验证命令

```bash
# 查看chrome-debug的cookies
ls ~/.hermes/chrome-debug/Default/Cookies

# 查看用户日常Chrome的cookies
ls ~/Library/Application\ Support/Google/Chrome/Default/Cookies
```

## 相关脚本

- `~/.hermes/scripts/hermes_reflection.py` — Reflection机制
- `~/.hermes/scripts/hermes_execution.py` — DynamicWait+HumanTrajectory
- `~/.hermes/scripts/hermes_agent_loop.py` — 完整Agent Loop
