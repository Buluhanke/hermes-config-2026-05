# pending_tasks 无持久化问题（2026-06-02）

## 问题描述

idle_learning cron job 在执行时，任务进度存在内存中（pending_tasks 队列）。Gateway 重启 → 内存清空 → 任务状态丢失。

Hermes 有 `resume_pending` 自动续连机制，但：
- 只在 1 小时内有效
- 针对**会话**而非 cron 任务

## 影响场景

cron job "夜间强化学习 night-001" 执行 idle_learning 时：
1. 读取目标列表（如 repo 更新检测）
2. 开始处理，遇到 gateway 重启（SIGTERM storm / launchd 服务消失）
3. 内存中 pending_tasks 清空
4. 下一轮 cron 触发时从头开始（重复工作）

## 解决方向（待实现）

需要给 idle_learning 增加持久化层：
1. **state file**：`~/.hermes/logs/idle_learning_state.json` 记录每轮检测的 repo + last_commit hash
2. **每轮结束时写入**：检测完成后更新 last_commit，下次轮次直接比对
3. **sleep 保护**：检测到 Gateway 不稳定时（多次 restart），idle_learning 主动 sleep 等待恢复

当前 workaround：新鲜度门控（30分钟跳过）在一定程度上缓解了重复工作，但不是根本解决。

## 验证命令

```bash
# 检查 pending_tasks 持久化状态
cat ~/.hermes/logs/idle_learning_state.json 2>/dev/null || echo "state file not found"

# 检查 gateway restart 频率
grep "gateway.restart\|initiating shutdown" ~/.hermes/logs/gateway.log | tail -20
```