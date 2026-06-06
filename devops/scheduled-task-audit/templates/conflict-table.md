# Scheduled-Task 冲突审计结果模板

执行 `bash audit_scheduled_tasks.sh` 后，把输出填入下表。

## 时间表

| 任务 | 调度 | 实际行为 | 状态 |
|---|---|---|---|
| `ai.hermes.self-evolution` | `StartInterval=1800` | | ✅ / ⚠️ / 🔴 |
| `ai.hermes.self-evolution-daily` | `Hour=9 Minute=0` | | ✅ / ⚠️ / 🔴 |
| `ai.hermes.self-evolution-weekly` | `Weekday=1 Hour=9 Minute=0` | | ✅ / ⚠️ / 🔴 |
| `<other_plist>` | | | |
| `<orphan_script>` | 无（注释失效） | | ⚠️ / 🔴 |
| `<crontab_entry>` | `<cron_expr>` | | ✅ / ⚠️ / 🔴 |

## 冲突矩阵

| 冲突类型 | 涉及任务 | 时间 | 风险等级 |
|---|---|---|---|
| 同秒并发 | | | |
| 窗口内并发 | | | |
| 同脚本多 mode | | | |
| 端口不一致 | | | |
| 共享资源争抢 | | | |

## 风险扫描

- [ ] `pkill -9 -f Chrome` — 高风险，会误杀用户浏览器
- [ ] `killall <service>` — 中风险
- [ ] `rm -rf` 路径非特定 — 中风险
- [ ] `launchctl unload/bootout` — 中风险
- [ ] `defaults delete` — 低-中风险

## 处置建议

1. **保留**：<list>
2. **修改调度**：<list with proposed schedule>
3. **删除**（需用户授权）：<list with reason>
4. **重构**（去掉破坏性副作用）：<list with plan>

## 验证清单

- [ ] `crontab -l` 与脚本中注释的 cron 表达式一致
- [ ] `lsof -nP -iTCP -sTCP:LISTEN | grep -i chrome` 与脚本中端口一致
- [ ] 删孤儿脚本后没有依赖方（`grep -rln <script_name> ~/.hermes/`）
- [ ] launchd plist 修改后 `launchctl print <label>` 检查
