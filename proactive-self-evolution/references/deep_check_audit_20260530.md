# 系统深层检查清单 (2026-05-30)

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

## 本次发现的真实问题

| 问题 | 风险 | 处理 |
|------|------|------|
| skills仓库ahead 17 commits | 中 | `git reset --hard origin/main` |
| pro-buyer skill缺失 | 高 | 删除引用它的cron job |
| 1688-automation skill缺失 | 高 | 删除引用它的cron job |
| 凌晨5分钟双重cron | 低 | 接受，不冲突 |
| 自我优化循环已建立 | ✅ | 凌晨2点自动跑 |

## 判断标准

- **无限循环风险**：检查skill是否自调用cron、cron是否触发其他cron
- **鬼打墙**：5分钟内同一任务重复失败 → 查锁机制 + 冷却时间
- **多实例冲突**：Gateway报错"already running" → `kill -9` 残留PID
