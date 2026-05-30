# 系统深层检查清单 (2026-05-30 第二轮)

## 快速检查流程

```python
# 1. Skills冲突检查
skill_names = [d.name for d in Path.home() / ".hermes" / "skills" iterdir() if d.is_dir()]

# 2. Cron任务状态
subprocess.run(["hermes", "cron", "list"])

# 3. 关键进程
{"hermes_gateway": "pgrep -af 'hermes.*gateway'", 
 "screen_watcher": "pgrep -f 'screen_watcher.py'",
 "ollama": "pgrep -f 'ollama'",
 "chrome_cdp": "lsof -i :9333"}

# 4. 错误日志摘要
today_errors = [l for l in errors_log if l.startswith(date.today())]
types = Counter(e.split()[2] for e in today_errors[-100:])  # WARNING/ERROR分布

# 5. Hindsight容器
docker ps --filter "name=hindsight"
curl -s http://localhost:8899/v1/default/banks  # 验证API

# 6. 缺失Skill导致Cron失败
# pro-buyer, 1688-automation 等被cron引用但不存在的skill → 删除cron job
```

## 发现的真实问题

| 问题 | 风险 | 处理 |
|------|------|------|
| skills仓库ahead 17 commits | 中 | `git reset --hard origin/main` |
| pro-buyer skill缺失 | 高 | 删除引用它的cron job |
| 1688-automation skill缺失 | 高 | 删除引用它的cron job |
| N8N MCP zombie进程(PID 32510) | 高 | `kill -9` 终止 |
| screen_watcher残留bash wrapper | 中 | `kill -9` 清理 |
| 孤儿脚本27个 | 低 | 全部删除 |
| Gateway多实例残留 | 高 | `kill -9`最老PID |

## 判断标准

- **无限循环风险**：检查skill是否自调用cron、cron是否触发其他cron
- **鬼打墙**：5分钟内同一任务重复失败 → 查锁机制 + 冷却时间
- **多实例冲突**：Gateway报错"already running" → `kill -9` 残留PID
- **zombie进程**：进程存在但端口不监听 → kill重拉

## 快速深度检查命令

```bash
# 进程三连检查
pgrep -af "screen_watcher|hermes.*gateway"   # 确认进程数
lsof -i :9333                                # 检查CDP端口
ps -p <pid> -o pid,etime,command           # 进程详情

# Cron任务健康
hermes cron list                             # 7个任务正常？
grep "ERROR" ~/.hermes/logs/errors.log | tail -5

# Docker容器
docker ps --format "{{.Names}} {{.Status}}"  # hindsight OOM?

# 孤儿脚本清理
ls ~/.hermes/scripts/*.bak.*                 # 备份文件？
ls ~/.hermes/scripts/ | wc -l               # 脚本数量？

# Skills健康
ls ~/.hermes/skills/ | wc -l                # 64个？
```
