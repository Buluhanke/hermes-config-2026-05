# 错误模式速查 (auto-generated, 2026-07-08)

来源: `auto_skill_from_failure.py` 每日扫描 `~/.hermes/logs/agent.log` 生成。

## 活跃模式 (2026-07-08 扫描)

| 模式 | 次数/天 | 严重度 | 根因 |
|---|---|---|---|
| TimeoutError | 2014 | 🟡 2 | QQBot WS 空闲超时 / API 慢查询 |
| ConnectionError | 214 | 🟡 3 | NVIDIA/GLM API endpoint 不达 |
| JSON parse error | 13 | 🟢 1 | API 超时返回非 JSON |
| Import error | 9 | 🟡 2 | launchd cwd=/ 导致模块加载失败 |
| Permission denied | 5 | 🟡 3 | 同上，相对路径权限问题 |
| CDP attach failed | 4 | 🔴 4 | page-level WS 未就绪或 target 已关闭 |

## 更新机制

- cron job `auto-skill-from-failure-scan` 每 2 小时运行
- 输出: `~/.hermes/skills/auto-generated/error-patterns-YYYYMMDD.md`
- skill 固化: 每月整理一次写入 `browser-cdp-control` 主 SKILL.md Pitfalls 区
