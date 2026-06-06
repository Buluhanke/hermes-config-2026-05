# Cron 脚本的 2 个高频坑（2026-06-05 实测落地）

> 配套 `safe-cron-script-edit-protocol-20260605.md`（5 步安全协议）
> 和 `safe-cron-do-segment-v1-1-20260605.md`（Do 段 v1.1 实战）
> 本文档聚焦两个**协议之外的"输出形态"坑**：日志双倍打印 + dry-run 缺位

---

## 坑 1：`tee -a` 在 launchd 下双倍写入（必踩）

### 现象

launchd 拉起的脚本 stdout 默认被 redirect 到 `StandardOutPath` 指向的 log 文件。
脚本内部用 `tee -a` 写日志时：

```bash
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [tag] $1" | tee -a "$LOG"
}
```

- `tee -a $LOG` 写一次到文件
- `tee` 把 stdout 也吐出来 → launchd 抓到 stdout → 再写一次到同一 log

**结果**：每行 log 在文件里出现 **2 次**。

### 实测（2026-06-05）

| 脚本 | 修前 stdout 行数 | 修后 stdout 行数 |
|---|---|---|
| `mem_patrol.sh` | 11 行（标题×2 + Top5×1） | 8 行（标题×1 + Top5×1） |
| `self_evolution.sh` | 10 行（每条×2） | 5 行（每条×1） |

注意：cron 跑的时候在文件里也是双倍，**不只 stdout**。`grep -c` 出来的统计是真实的 2 倍。

### 修法（必加 5 行）

把 `tee -a` 改成 **显式写文件 + 显式 echo**（不重定向）：

```bash
log() {
    # 写到 LOG + stdout (launchd 抓 stdout 也落同一 log, 不 tee -a 避免双倍)
    msg="$(date '+%Y-%m-%d %H:%M:%S') [tag] $1"
    echo "$msg" >> "$LOG"
    echo "$msg"
}
```

### 验证（4 步）

```bash
# 1. 手动跑一次, 记行数
bash ~/.hermes/scripts/<script>.sh <mode> 2>&1 | wc -l   # 应该是 N

# 2. 等 launchd 跑完一次（约 30min / 24h / 7d）
# 3. 看 log 文件最新 N 行
tail -N <N 倍行数> ~/.hermes/logs/<script>.log
# 4. 期望: 每条 log 出现 1 次, 不是 2 次
```

### 触发条件速查

| 调度方式 | 是否双写 | 原因 |
|---|---|---|
| launchd + `StandardOutPath` 指向同一 LOG | **✅ 双写** | tee stdout + launchd stdout 同落 LOG |
| launchd + `StandardOutPath=/dev/null` | ✅ 不双写 | 但 launchd 日志全丢（不推荐） |
| 直接 `bash script.sh`（不在 launchd 下） | ✅ 不双写 | launchd 不在中间 |
| launchd + `StandardOutPath=A.log` + tee 写 B.log | ✅ 不双写 | 两个文件分开 |

---

## 坑 2：`--dry-run` 模式 + `do_run()` 模板

### 为什么需要

cron 脚本加 Do 段（kill / pkill / rm / nohup launch）后，**唯一安全的验证方式**是 dry-run：

- `bash -n` 只查语法，**抓不到逻辑 bug**
- 静态 grep 路径标记，**抓不到变量未赋值 / 命令拼错**
- 直接 live-test，**会真杀进程**（违反协议 step 1）

### 模板（直接复制）

脚本顶部加：

```bash
# === dry-run 模式开关 ===
# 用法: bash script.sh <mode> --dry-run
# 效果: 所有"动手"操作 (kill/pkill/rm/nohup launch) 改为打印日志不执行
#       其他逻辑（grep/match/写 fact）照常跑
DRY_RUN=false
[ "${2:-}" = "--dry-run" ] && DRY_RUN=true

# 包装函数: 假就只打印, 真就真执行
do_run() {
    if [ "$DRY_RUN" = "true" ]; then
        log "🧪 [DRY-RUN] 将执行: $*"
        return 0
    fi
    "$@"
}
```

把所有"动手"点用 `do_run` 包起来：

```bash
# ❌ 错误: 直接执行
kill -TERM "$GW_PID" 2>/dev/null
nohup hermes gateway run &

# ✅ 正确: 走 do_run
do_run kill -TERM "$GW_PID" 2>/dev/null
do_run nohup hermes gateway run &
```

**注意**：`do_run` 只包"动手"操作（kill / pkill / rm / nohup launch / chmod 改权限等），**不要包 read-only 探测**（grep / lsof / ps / df / curl）——那些本来就该真跑。

### 验证流程

```bash
# 1. 语法 + dry-run 解析
bash -n ~/.hermes/scripts/<script>.sh && echo "语法 OK"

# 2. dry-run 跑一次
bash ~/.hermes/scripts/<script>.sh <mode> --dry-run 2>&1 | head -30
# 期望看到: 多个 🧪 [DRY-RUN] 将执行: ... 行

# 3. 关键进程没被杀 (gateway 还在)
pgrep -f "hermes_cli.main" | head -3   # 应该还有 PID
```

### 实测（2026-06-05 self_evolution.sh）

| 检查项 | 期望 | 实际 |
|---|---|---|
| 语法 OK | ✅ | ✅ |
| dry-run 输出含 🧪 标记 | ✅ | ✅（5 个 do_run 点全触发）|
| gateway PID 33447/33454 仍在 | ✅ | ✅（未被 kill）|
| 工具错误模式被识别 | ✅ | ✅（22 次/小时 → ⚠️） |

---

## 坑 3：patch 工具"改变原意"反例

patch 工具按字符串匹配，**不读上下文**。改前必须把**整个目标段**读出来确认结构。

### 反例 1（2026-06-05 真事故）

原代码段：

```bash
pkill -f "chrome.*9333" 2>/dev/null
sleep 1
open -a "Google Chrome" --args \
    --remote-debugging-port=9333 \
    --user-data-dir="$HERMES_HOME/chrome-debug" \
    ...
```

用 patch 把 `pkill` 改 `do_run pkill` 时，**old_string 写错**，新代码变成：

```bash
do_run pkill -f "chrome.*9333" 2>/dev/null
sleep 1
do_run nohup "$HERMES_HOME/chrome-debug-launcher.sh" \   # ← 误改!
    --remote-debugging-port=9333 \
    ...
```

**原意是 `open -a Google Chrome`**，被改成 `nohup chrome-debug-launcher.sh`。两个完全不同的命令。第二次 patch 才回滚。

### 反例 2：write_file 路径手抖

```bash
# 写 plist 时, 把 /Users/aimac/ 打成 /Users/aimmes/ (多打一个 s)
# 后果: launchd 加载时找不到日志目录, 静默失败
```

### 防御 3 条

1. **patch 前 read_file 完整段**（不要只读一行 + 猜上下文）
2. **patch 后立即 `grep` 整段确认结构对**（不只是确认新行存在）
3. **结构性修改优先 write_file**（整段重写）而不是 patch 字符串（局部替换容易改坏）

### 自检清单

```
patch 前:
□ read_file 看了完整段（不是只读目标行）
□ old_string 是文件中唯一匹配（grep 验证）
□ new_string 在原结构里替换正确位置

patch 后:
□ grep 整个修改段确认没改坏相邻行
□ bash -n 语法 OK
□ dry-run 跑一次看输出
```

---

## 配套工具建议

把所有 cron 脚本的 log + dry-run 模板**统一进 `~/.hermes/scripts/lib/cron_helpers.sh`**：

```bash
# lib/cron_helpers.sh - 所有 cron 脚本 source 这一个文件
log() {
    msg="$(date '+%Y-%m-%d %H:%M:%S') [${SCRIPT_NAME:-cron}] $1"
    echo "$msg" >> "${LOG:-/tmp/cron.log}"
    echo "$msg"
}

DRY_RUN=false
[ "${2:-}" = "--dry-run" ] && DRY_RUN=true

do_run() {
    if [ "$DRY_RUN" = "true" ]; then
        log "🧪 [DRY-RUN] 将执行: $*"
        return 0
    fi
    "$@"
}
```

cron 脚本顶部加：

```bash
source ~/.hermes/scripts/lib/cron_helpers.sh
```

避免每个脚本重复实现一遍 log() / do_run()。

---

## 经验总结

> **tee -a + launchd = 双倍** 是 macOS launchd 的固有行为，不是 bug。
> **do_run() 是 cron 脚本的标配**，不是可选。
> **patch 改代码前必须 read_file 完整段**，不要相信自己的"我记得是这样"。

## 相关参考

- `safe-cron-script-edit-protocol-20260605.md` — 5 步安全协议
- `safe-cron-do-segment-v1-1-20260605.md` — Do 段 v1.1 实战（5 步 + 3 个新增项）
- `proactive-execution` 规则 6（不原地踏步） + 规则 21（有 bug 默认修）
