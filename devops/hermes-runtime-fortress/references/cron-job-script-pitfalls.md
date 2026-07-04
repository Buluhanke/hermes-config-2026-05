# cron job 静默失败 + script 字段 4 陷阱

## 背景

2026-06-30 实战: 用户引用历史快照, 说"`perception_autoheal` last_run_at: null, 从未跑过", 但 `hermes cron list` 现场查 28 个 active job 状态完全不同:

| 引用说 | 实际 |
|---|---|
| 26 个任务 | **28 个 active** |
| perception_autoheal 从未跑过 | 24h 前跑过, 状态 ok |
| (没提别的) | `v31-sync-watchdog` + `task-watchdog` 报 `Script not found` 24h+ |

根因: 大换血/手工清理时 `~/.hermes/scripts/` 下的 .sh 脚本被搬走, cron job 还在 schedule, 每 tick 报 error, 但 `last_status: error` 在 `hermes cron list` 默认输出里要 `grep error:` 才能看到.

## 体检模板 (5 步, 0 思考照抄)

```bash
# 1. 拉权威清单
hermes cron list > /tmp/cron_list.txt

# 2. 算分布
echo "active: $(grep -c '\[active\]' /tmp/cron_list.txt)"
echo "ok:     $(grep -c 'Last run:.*ok' /tmp/cron_list.txt)"
echo "error:  $(grep -c 'Last run:.*error' /tmp/cron_list.txt)"
echo "null:   $(grep -c 'Last run:  *null' /tmp/cron_list.txt)"

# 3. 抓所有 error 行
grep -B1 -A2 "Last run:.*error" /tmp/cron_list.txt

# 4. 修每个 job
# 4a. 找回或重写缺失脚本
cp -L <original> ~/.hermes/scripts/<name>.sh  # 必须 -L 解开软链
chmod +x ~/.hermes/scripts/<name>.sh
~/.hermes/scripts/<name>.sh  # 本地跑一发 exit 0 验证

# 4b. 改 cron job 指向
hermes cron update --job-id <id> --script <name>.sh

# 5. 等下一 tick (15分钟/小时) 验证
hermes cron list | grep -A4 <id>
# 期望: last_run_at 新时间戳 + last_status: ok
```

## cron `script` 字段 4 陷阱

### 陷阱 1: 绝对路径被拒

```bash
hermes cron update --job-id cede6601b1e3 --script /Users/aimac/.hermes/scripts/v31_sync_watchdog.sh
# ❌ 报错: "Script path must be relative to ~/.hermes/scripts/. Got absolute or home-relative path"
# ✅ 修法: 只传 basename
hermes cron update --job-id cede6601b1e3 --script v31_sync_watchdog.sh
```

### 陷阱 2: Symlink 被拒

```bash
# 先尝试创建软链
ln -sf /Users/aimac/.hermes/skills/meta/cross-channel-sop-sync/scripts/v31_sync_watchdog.sh \
       ~/.hermes/scripts/v31_sync_watchdog.sh
hermes cron update --job-id cede6601b1e3 --script v31_sync_watchdog.sh
# ❌ 报错: "Script path escapes the scripts directory via traversal: 'v31_sync_watchdog.sh'"
# ✅ 修法: cp -L 解开软链
cp -L /Users/aimac/.hermes/skills/meta/cross-channel-sop-sync/scripts/v31_sync_watchdog.sh \
      ~/.hermes/scripts/v31_sync_watchdog.sh
```

### 陷阱 3: 同 inode cp 跳过

```bash
# 软链还在, 想覆盖复制真实内容
cp /Users/aimac/.hermes/skills/meta/cross-channel-sop-sync/scripts/v31_sync_watchdog.sh \
   ~/.hermes/scripts/v31_sync_watchdog.sh
# ❌ 报错: "are identical (not copied)" (因软链指向源文件, inode 相同)
# ✅ 修法 A: cp -L 解开
cp -L <src> <dst>
# ✅ 修法 B: 先删再复制
rm ~/.hermes/scripts/v31_sync_watchdog.sh
cp <src> ~/.hermes/scripts/v31_sync_watchdog.sh
```

### 陷阱 4: 缺脚本 silent error

job 还在 schedule, 每 tick 报 `Script not found`, `last_status: error` 持续累积, 但:
- job 不会自动 disable
- 不会推 Telegram (除非配置了 alert 钩子)
- `hermes cron list` 默认不显示 status 错误细节, 需 `grep error`
- 5-30 天没人看 cron list 就一直 silent

**修法**: 每月/每次大清理后, 必跑 `hermes cron list | grep -c "error"` 看 error 数. 0 个 = 干净, >0 必查.

## 反面案例

差点把 `perception_autoheal` 当 "需要修" 处理, 实际排查发现:
- `perception_autoheal` 24h 前跑过, 状态 ok (用户引用的快照是错的)
- `v31-sync-watchdog` + `task-watchdog` 真的失败, 缺脚本

浪费 1 整轮 + 给用户错误印象. **教训**: 任何"X 个任务 / 任务列表 / 哪些失败"类引用 → 0 思考 `hermes cron list` 拉权威清单, 不信任何历史快照/截图/转述.

## 关联

- `verification-before-reporting` Failure 55 (新增, 同一 session 实战)
- `hermes-task-watchdog` skill "cron self-dedup missing" pitfall (类似模式: 工具缺失但 job 还在跑)
- `hermes-runtime-fortress` SKILL.md 第八节 (本文件指针)
- `proactive-execution` Failure 49 (memory tool 不可用 fallback — 同样 silent-failure 模式)