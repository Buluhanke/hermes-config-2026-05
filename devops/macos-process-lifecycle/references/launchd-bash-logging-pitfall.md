# launchd Bash 脚本日志双写坑（mem_patrol v1.0/v1.1 复现 → v1.2 修复）

## 现象
launchd 跑的 bash 脚本，**日志文件里每行打印两次**（每个 echo 出现 2 次）。手跑正常，只有 launchd 调度时复现。

## 根因
两个写入路径同时打到同一个文件：

```bash
log() {
    echo "$(date ...) $1" | tee -a "$LOG"   # 路径 1: tee 显式追加
}
# launchd plist 把脚本 stdout 重定向到 $LOG
# → 路径 2: tee 写一次 + stdout 再被 launchd 写一次 = 同一行两份
```

`tee -a` 同时做两件事：写文件 + 把同一行复制到 stdout。launchd 抓 stdout 再落盘，第二份就出现了。

## 修复（v1.2 实施，2026-06-05 验证）

```bash
log() {
    msg="$(date '+%Y-%m-%d %H:%M:%S') [mem-patrol] $1"
    echo "$msg" >> "$LOG"   # 路径 1: 显式追加，不走 stdout
    echo "$msg"            # 路径 2: stdout 让 launchd 抓
}
# 显式 echo >> file + echo 到 stdout = 每行 1 份
```

**关键原则**：要么 `tee -a` + plist 里 `StandardOutPath` 指向**另一个文件**，要么 `echo >> file` + `echo` 给 stdout，**不要两者同时往同一文件写**。

## 验证命令

```bash
# 手动跑：输出 8 行（统计 + Top5 标题 + 5 行数据 + 完成）
bash ~/.hermes/scripts/mem_patrol.sh 2>&1 | wc -l
# 修前：11 行（标题 6 + 数据 5）
# 修后：8 行（标题 3 + 数据 5）
```

## 适用所有 launchd + bash 组合

任何 `~/Library/LaunchAgents/ai.hermes.*.plist` 跑的 bash 脚本都应该检查这个模式：
- `cleanup_hermes_logs.sh` ✅ 已用 `echo >> LOG` 模式
- `mem_patrol.sh` ✅ v1.2 修复
- `self_evolution.sh` — 用的是 `print` python，无此坑
- **新写 launchd bash 脚本前先按这个模式写**

## 顺手记：plist 里 log 重定向的正确姿势

```xml
<key>StandardOutPath</key>
<string>/Users/aimac/.hermes/logs/<name>.log</string>
<key>StandardErrorPath</key>
<string>/Users/aimac/.hermes/logs/<name>_err.log</string>
```

如果脚本内部已经 `echo >> "$LOG"`，stdout 重定向到 `$LOG` 同一文件 = 双写。两种解法二选一：
1. 脚本里只 `echo`（不写文件），让 launchd 写文件
2. 脚本里 `echo >> $LOG` + `echo` 到 stdout（推荐，能手跑也能 launchd 跑都正常）
