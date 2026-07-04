# 2026-06-30 — Cron job 健康体检实战复盘

## 背景
用户消息: "拿到所有 26 个任务. 1:00-7:00 区间共 9 个任务... 感知系统自动修复
(perception_autoheal) last_run_at: null, **从来没成功跑过**"

第一反应(错): 立刻去诊断 perception_autoheal, 写 todo, 准备动手修.

正确反应(对): 0 思考先 `hermes cron list` 拉权威清单, 确认状态.

## 真实数据 (2026-06-30 02:01+08:00)

`hermes cron list` 现场跑出 **28 个 active jobs** (不是用户引用的 26):

| Job ID | Name | Schedule | last_run | last_status |
|---|---|---|---|---|
| b2ad855429b2 | hermes-queue-drain | */5 * * * * | 02:00:45 | ok |
| 2f527c06f06d | idle-killer | */15 * * * * | 02:00:44 | ok |
| ... (25 个全 ok) ... | | | | |
| cede6601b1e3 | v31-sync-watchdog | 0 9 * * 1 | 2026-06-29 09:00 | **error: Script not found** |
| 5620c7e8011e | task-watchdog | */15 * * * * | 02:00:43 | **error: Script not found** |
| 495eb9bfbddc | 感知系统自动修复 (perception_autoheal) | 0 3 * * * | 2026-06-29 23:17 | ok |

**关键差异**:
- `perception_autoheal` **不是 null**, 上次跑过 24h 前, 状态 ok ✅
- 用户截图/历史快照里说的"26 个任务"也是错的 (实际 28 个)
- **真正有问题的**: `v31-sync-watchdog` + `task-watchdog` 两个, 缺脚本

## 用户引用错的根因 (推测)

可能的来源:
1. 上一次对话某个 agent 跑了 `cron list` 时正好看到 perception_autoheal 还
   没到 03:00 触发时间, 就报"null/从未跑过"
2. 用户/agent 看到的可能是早期更早的快照
3. "感知系统自动修复" 这名字含 "修复" 字眼, 容易脑补"它从没成功过"

## 修复路径 (实战跑通, 0 思考照抄)

### Step 1: 查真错误清单
```bash
hermes cron list > /tmp/cron_list.txt
grep -B1 -A2 "Last run:.*error" /tmp/cron_list.txt
# 输出:
#   cede6601b1e3 [active]
#     Name:      v31-sync-watchdog
#     Schedule:  0 9 * * 1
#     Last run:  2026-06-29T09:00:18.258495+08:00  error: Script not found: ...
#   5620c7e8011e [active]
#     Name:      task-watchdog
#     Schedule:  */15 * * * *
#     Last run:  2026-06-30T02:00:43.577678+08:00  error: Script not found: ...
```

### Step 2: 找缺哪个脚本
```bash
ls ~/.hermes/scripts/task-watchdog.sh
# No such file or directory
ls ~/.hermes/scripts/cross-channel-sop-sync/scripts/v31_sync_watchdog.sh
# No such file or directory
```

### Step 3a: 重写 `task-watchdog.sh` (本来就该在 `~/.hermes/scripts/` 下)
```bash
cat > ~/.hermes/scripts/task-watchdog.sh <<'EOF'
#!/bin/bash
# task-watchdog.sh — 每 15 分钟扫描 ~/.hermes/tasks/ 找停滞任务
set -e
TASKS_DIR="$HOME/.hermes/tasks"
STUCK_MINUTES=120
if [ ! -d "$TASKS_DIR" ]; then echo "No tasks dir"; exit 0; fi
NOW=$(date +%s)
STUCK_FOUND=0
for f in "$TASKS_DIR"/*.md; do
  [ -f "$f" ] || continue
  AGE=$((NOW - $(stat -f %m "$f" 2>/dev/null || echo $NOW)))
  if [ $AGE -gt $((STUCK_MINUTES * 60)) ]; then
    if grep -q "状态：进行中" "$f" 2>/dev/null; then
      echo "STUCK: $(basename "$f" .md) (${AGE}s old)"
      STUCK_FOUND=$((STUCK_FOUND + 1))
    fi
  fi
done
[ $STUCK_FOUND -eq 0 ] && echo "OK: no stuck tasks"
EOF
chmod +x ~/.hermes/scripts/task-watchdog.sh
~/.hermes/scripts/task-watchdog.sh  # 本地验证 exit 0
# 期望: "OK: no stuck tasks"
```

### Step 3b: 修 `v31_sync_watchdog.sh` (原本在 skill 目录, 需复制到 scripts/)
```bash
# 找到原位置
find ~/.hermes -name "v31_sync_watchdog.sh"
# 命中: /Users/aimac/.hermes/skills/meta/cross-channel-sop-sync/scripts/v31_sync_watchdog.sh

# cron update 拒绝 symlink (cp 不复制同 inode), 必须 -L 解开
cp -L /Users/aimac/.hermes/skills/meta/cross-channel-sop-sync/scripts/v31_sync_watchdog.sh \
      ~/.hermes/scripts/v31_sync_watchdog.sh
chmod +x ~/.hermes/scripts/v31_sync_watchdog.sh
```

### Step 4: 改 cron job 指向新脚本 (script 字段不接受绝对路径)
```bash
hermes cron update --job-id 5620c7e8011e --script task-watchdog.sh
hermes cron update --job-id cede6601b1e3 --script v31_sync_watchdog.sh
# 期望: 返回 success=true, script 字段更新为短名
```

### Step 5: 验证
```bash
hermes cron list | grep -A5 "v31-sync\|task-watchdog"
# 期望: last_run_at 时间戳更新 + last_status: ok
```

## 工具陷阱清单 (Step 4 踩的 4 个坑)

| 陷阱 | 现象 | 修法 |
|---|---|---|
| 绝对路径被拒 | `Script path must be relative to ~/.hermes/scripts/` | 只传 basename, 如 `task-watchdog.sh` |
| Symlink 被拒 | `Script path escapes the scripts directory via traversal` | `cp -L` 解开软链, 或真实复制 |
| 缺脚本 silent error | last_status 持续 `error: Script not found`, job 还在 schedule | 必跑 `chmod +x` + 本地 exec 验证 exit 0 |
| 同 inode cp 跳过 | `cp src dst` 报 `are identical (not copied)` (因 symlink 没解开) | `cp -L src dst` |

## 关联

- `verification-before-reporting` Failure 55 (cron job 健康体检铁律)
- `verification-before-reporting` Failure 30 ("全部修复"类汇总要逐项验)
- `verification-before-reporting` Failure 29 (凌晨报告的事实要现场复测)
- `proactive-execution` Failure 49 (memory tool 不可用 fallback — 同样"工具缺失但
  job 还在跑"模式)
- `hermes-task-watchdog` 自身 skill 的 "cron self-dedup missing" pitfall