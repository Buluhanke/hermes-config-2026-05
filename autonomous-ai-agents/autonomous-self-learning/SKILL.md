---
name: autonomous-self-learning
description: Hermes 自主持续学习框架 — 自我驱动学习、任务执行、状态汇报的闭环。解决"任务发出去了但没执行"的问题。
trigger: 当用户授权自主行动时加载此技能
---

## 自主执行原则

1. **不等待确认**：用户授权后立即执行，不请示不讨论
2. **闭环追踪**：任务从发出到完成必须全程可追踪
3. **主动汇报**：完成后立即汇报结果+问题+建议，不等用户来问
4. **自动修复**：任务失败时先尝试修复，修复不了再通知用户

## cron job 监控要点

- cron job 失败不会自动通知用户，需要主动巡检
- 每次启动时检查 `gateway.log` 中所有 cron job 的状态
- 发现 `error`/`fail` 状态立即尝试修复或切换方案
- 修复后重新调度，不让任务空转

## 任务执行检查清单

- [ ] 任务是否已创建？
- [ ] cron job 是否成功触发？
- [ ] 触发后实际执行了什么？（看日志）
- [ ] 执行结果是否符合预期？
- [ ] 如果失败，有没有自动重试？
- [ ] 用户是否收到了完成/失败通知？

## 常见失败模式

- 模型调用失败（网络、API Key）→ 检查配置，切换模型
- 任务队列积压 → 减少并发，清理队列
- 依赖服务不可用 → 降级方案或通知用户

## cron 脚本 HOME 变量陷阱（2026-05-27 发现）

**问题**：cron 环境下 HOME 变量为空，脚本中 `~/.hermes/` 展开为 `/.hermes/`（根目录），权限不足写入失败。表现为 cron job 状态 `error`，日志显示 `Permission denied` 或路径变成 `/.hermes/...`。

**症状**：cron job 状态 error，但手动运行脚本正常。

**修复方法**：所有脚本内路径使用 `${HOME:-/Users/aimac}` 替代 `~` 或 `$HOME`。
```bash
# 错误
LOG="${HOME}/.hermes/logs/evolution.log"
OBSIDIAN=~/Obsidian/...

# 正确
LOG="${HOME:-/Users/aimac}/.hermes/logs/evolution.log"
OBSIDIAN="${HOME:-/Users/aimac}/Obsidian/..."
```

**验证**：用 `env -i HOME= PATH=$PATH bash ~/.hermes/scripts/xxx.sh` 模拟 cron 环境测试。

## cron job 修复模式

当 cron job 出现 error/fail 时：
1. 读取 `~/.hermes/logs/gateway.log` 定位错误原因
2. 如果是脚本问题（HOME/路径/权限）→ 直接 patch 脚本
3. 如果是配置问题 → 用 `cronjob update` 修复 job 配置
4. 修复后立即 `cronjob run` 手动触发一次验证
5. 确认 ok 后清除 error 状态