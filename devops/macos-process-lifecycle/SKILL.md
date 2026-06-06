---
name: macos-process-lifecycle
description: macOS 进程生命周期管理 — 内存大户识别、空闲自动清理、状态保留、on-demand 启停。覆盖 Mac mini 24GB 等小内存机器的资源调度。当用户抱怨内存不够、要杀进程、要"按需启动/不用就关"时使用。
---

# macOS Process Lifecycle

对长时间运行的资源密集型进程（Chrome debug、Ollama、Electron App、大 renderer 进程）进行**按需启动 + 空闲清理**的资源管理框架。

## 触发条件

- 用户说"半小时不用就杀掉" / "调用时启动" / "太占内存" / "能不能关闭"
- Mac mini 24GB 等小内存机器空闲 < 4GB
- 单个进程 RSS > 200MB 且非核心
- 需要保留登录态 / 用户数据

## 核心原则

1. **状态保留 > 进程存活** — Chrome user-data-dir、cookies、`Library/Application Support/` 下的应用数据优先保留
2. **空闲阈值默认 30 分钟**（用户已确认，见 USER 偏好 — "半小时不用就可以杀掉了"）
3. **kill 前必须检查**：前台窗口、etime、父进程、是否系统服务
4. **SIGTERM → 3s 等待 → SIGKILL**（避免数据损坏）
5. **记录回滚信息**：PID + 时间戳写到 `/tmp/hermes_kills/<name>_<ts>.log` 备查
6. **kill 后必须验证**：vm_stat 重新读取，确认内存确实释放
7. **不**能动：Hermes 自家进程、用户当前正在用的 App（Claude 等）、系统服务（launchd PID 1）、登录态 tab 所在的 Chrome
8. **launchd 跑的 bash 脚本**：用 `echo >> $LOG` + `echo` 到 stdout，**不要**用 `tee -a $LOG`（会被 launchd stdout 重定向二次写到同一文件，每行出现两次）。完整复现/修复见 `references/launchd-bash-logging-pitfall.md`。

## 决策流程

### Step 1: 识别候选进程

```bash
ps -A -o pid,rss,command | sort -k2 -rn | head -10
```

输出格式建议：PID + MB + 进程名（裁剪路径）。

### Step 2: 评估可清理性

| 信号 | 含义 | 行动 |
|------|------|------|
| `osascript` 检测 `visible=true` | 进程在前台 | 询问用户 |
| `etime` < 30m | 刚启动 | 不杀 |
| `STAT` = Z | 僵尸进程 | 让父进程回收，**不杀** |
| 父进程 = launchd (PID 1) | 系统服务 | 不杀 |
| RSS > 200MB | 内存大户 | 优先评估 |
| 名字含 "Renderer" | Chrome 渲染子进程 | 检查父 Chrome 是否要保留 |
| `--user-data-dir=` 存在 | Chrome 登录态独立 | 杀后下次启动自动恢复 |

### Step 3: 状态保留检查

| 进程类型 | 状态文件 | 杀后影响 |
|---------|---------|---------|
| Chrome debug | `--user-data-dir=~/.hermes/chrome-debug/` | 登录态保留，下次启动恢复 |
| Electron App | `~/Library/Application Support/<App>/` | 用户数据保留 |
| Ollama serve | `~/.ollama/` 模型缓存 | 模型不丢，只是不再 serve |
| bash-language-server | 无状态 | IDE 重启时自动重拉 |
| 豆包 renderer | 依附主 App | 杀后重开 App 恢复 |

### Step 4: 执行清理

```bash
# 1) 优雅杀（SIGTERM）
kill <pid1> <pid2> <pid3> 2>/dev/null
sleep 3
# 2) 强杀残留（SIGKILL）
for pid in <pid1> <pid2> <pid3>; do
  ps -p $pid > /dev/null 2>&1 && kill -9 $pid
done
```

### Step 5: 验证释放

```bash
free_pages=$(vm_stat | awk '/Pages free:/ {print $3}')
python3 -c "print(round($free_pages * 16384 / 1024 / 1024 / 1024, 2))"  # → GB
```

## 30 分钟空闲自动清理

### 一次性方案：`at` 命令（首选，最简单）

```bash
echo "kill_pids=\$(ps aux | grep -i 'pattern' | awk '{print \$2}' | xargs); [ -n \"\$kill_pids\" ] && kill -9 \$kill_pids" | at now + 30 minutes
atq  # 验证任务进入队列
```

**注意**：`at` 任务在系统重启后丢失。需要持久化用 launchd。

### 周期性方案：launchd plist

适用：每天定时清理、基于心跳检测的真实空闲（CDP 客户端连接数 > 0 = 活跃）。

参考：`~/Library/LaunchAgents/ai.hermes.*.plist` 现有模式。

## macOS 内存公式（关键！）

```bash
# 空闲内存 (GB) — Apple Silicon
vm_stat | awk '/Pages free:/ {print $3}' | tr -d '.'
# 计算: pages × 16384 / 1024^3 = GB
# 旧默认值 4096 在 M1/M2/M3/M4 上低估 4 倍！

# Swap
sysctl vm.swapusage
# total / used / free，单位 M

# 负载
sysctl -n vm.loadavg
# { 1min 5min 15min } — 4 核 Mac < 2.5 = 健康

# 内存压力（需要 sudo 才有完整信息）
memory_pressure | head -10
```

### ⚠️ 关键陷阱：`Pages free` 单值会**严重低估**真实可用（2026-06-05 mem_patrol v1.0 误杀真实反例）

macOS 内存压力图顶部"可用 XX GB" = `Pages free + Pages inactive + Pages speculative` **三项求和**。只看 `Pages free` 单值会算成 0.7GB（实际 16.7GB），触发"紧急"→ 误杀无辜进程。

**任何拿 vm_stat 决策的脚本都必须用三项求和 + python 算**（绕开 BSD `paste` 错位坑）。完整复现/修复见 `references/mem-patrol-v1-bug-20260605.md`。

## 配合工具

- `ps -A -o pid,rss,command` — 内存排序（见下方 ⚠️ BSD 坑）
- `osascript -e 'tell application "System Events" to get name of every process whose visible is true'` — 前台检测
- `at` / `launchctl` — 定时清理
- `vm_stat` + `sysctl vm.swapusage` — 内存/交换监控
- `sysctl -n vm.loadavg` — CPU 负载
- `du -sh ~/Library/Application\ Support/<App>/` — 应用数据大小评估

## ⚠️ Bash 实战坑（2026-06-05 跑"内存吃紧"复现 3 次失败 → 修通）

### 坑 1: macOS `ps` BSD 变体**不支持 `--sort`**

❌ 失败：`ps -axo pid,rss,user,command --sort=-rss` → `ps: illegal option -- -`
- BSD `ps`（macOS 默认）只支持短选项，**没有 `--sort`**

✅ 修法：外接 `sort` 管道
```bash
ps -A -o pid,rss,user,command | sort -k2 -nr | head -16
# 关键: -k2 = 按第 2 列 (rss), -nr = 数值降序
```

**更可读**（带表头 + MB 单位）：
```bash
ps -A -o pid,rss,user,command | sort -k2 -nr | head -21 | \
  awk 'NR==1 {printf "%-8s %6s %-10s %s\n","PID","RSS_MB","USER","COMMAND"; next}
       {cmd=""; for(i=4;i<=NF;i++) cmd=cmd" "$i; printf "%-8s %6d %-10s %s\n",$1,$2/1024,$3,cmd}'
```

### 坑 2: awk 输出**多行**进 bash 变量 + `$(( ))` 算术 = 崩

❌ 失败模式（实测触发 3 次）：
```bash
read free active inactive wired compressed < <(vm_stat | awk '...END { print fb, ab, ib, wb, cb; }')
total=$((free + active + inactive + wired + compressed))  # ← "syntax error" 或 "division by 0"
```

**根因**：`END { print ... }` 默认 ORS（输出记录分隔符）是 `\n`，但 `< <( )` 进程替换时 read 拿到的是一整行字符串。多个 var 会被 shell 拆分，**但** END 块里 `print "ok"` 也会被吞进最后一个 var。

✅ 修法 1: `awk` 用 `printf`（不加换行，让进程替换一次返回一行）
```bash
free=$(vm_stat | awk '/Pages free:/{gsub(/\./,"",$3); printf "%d",$3*16384/1048576}')
active=$(vm_stat | awk '/Pages active:/{gsub(/\./,"",$3); printf "%d",$3*16384/1048576}')
# 每个 var 单独赋, 不玩 read 多变量 + 算术的组合拳
```

✅ 修法 2: 必须用 `read` 时，`END { printf "%d %d %d %d %d\n", ... }` + 确认 IFS
```bash
IFS=' ' read -r free active inactive wired compressed < <(vm_stat | awk '
  /Pages free:/        {free=$3+0}
  /Pages active:/      {active=$3+0}
  ...
  END { printf "%d %d %d %d %d\n", free, active, inactive, wired, compressed }')
# END 必须用 printf "%d %d ...\n", 不要 print (print 加 \n 后 read 会拿到空最后一格)
```

**自检**：`echo "free=$free active=$active total=$((free+active))"` 看是否正常。如果变量含 `()` 数字，恭喜踩中。

### 坑 3: "active 内存清不掉" 用户的体感

rm 完缓存后，**Pages active 几乎不动**（实测：前 9167MB → 9244MB 反而微涨，Inactive 8421→8505 微涨）。这是 macOS 正常行为：
- `Pages free` 上升 = 缓存确实清掉
- `Pages active` 下降 = OS 决定把内存挪给 inactive
- **In 8.5GB Inactive** 是 OS 留给你的"复利账户"，内存压力时自动吐出
- 想立刻腾空间 = **重启**（用户已授权"可以重启 Mac"，直接 `R` 选）

## 进程组聚合（从 20 行 ps → 5 行对账表）

用户问"哪些进程吃内存最多"时，**别直接把 top 20 贴过去**——会触发"对账表+不扩大战果"反模式（用户以为你在扩大战果）。**聚合到 5-6 个进程组**给对账表：

```bash
# 1) 拿到 RSS 排序的进程
ps -A -o pid,rss,command | sort -k2 -nr | head -21 > /tmp/top_mem.txt

# 2) 按"应用组"聚合（每个组的 helper/renderer 算一起）
echo "Chrome 进程组:   $(grep -E 'Google Chrome' /tmp/top_mem.txt | awk '{s+=$2} END {printf "%.0fMB", s/1024}')"
echo "QQ 进程组:       $(grep -E '/QQ[^/]*|/QQ Helper' /tmp/top_mem.txt | awk '{s+=$2} END {printf "%.0fMB", s/1024}')"
echo "Hermes 自身:     $(grep -E 'hermes_cli|hermes-agent' /tmp/top_mem.txt | awk '{s+=$2} END {printf "%.0fMB", s/1024}')"
echo "Claude:          $(grep -E 'Claude.app' /tmp/top_mem.txt | awk '{s+=$2} END {printf "%.0fMB", s/1024}')"
```

实测样例（2026-06-05 19:00）：
```
Chrome 进程组 ≈1.3GB (主 431M + Renderer 510M + GPU 171M + Network 139M)
QQ 进程组     ≈1.3GB (主 364M + 4 个 Helper 298+234+171+171)
Hermes 自身   ≈1.0GB (gateway 336 + dashboard 208 + LSP 179 + hermes 243)
Claude        225MB
Terminal/输入法/Finder/WebContent ≈800MB
```

**对账表模板**（给用户的 A/B/C/D 选项，**不超过 4 个**）：
```
已做 (零授权):
  ✅ A. 缓存清理（9MB 磁盘，无内存影响）

如果你授权杀这些（不杀就这些）:
  🟡 B. 杀 QQ      → 释放 ~1.3GB
  🟡 C. 杀 Claude  → 释放 ~225MB
  🟡 D. B + C      → 释放 ~1.5GB

不建议杀:
  ❌ Chrome — 刚验完 6 站登录, 杀 = 重开 + 重验
  ❌ Hermes 自身 — 杀 Hermes = 杀我自己
```

**用户说"等会吧"**：立刻停手 + 留状态备忘（数字 + 已做 + 未做的对账表 + 一个重启选项 `R`），**不重复问"你确定吗"**，不重复给"还能清哪些"清单。详见 `proactive-execution` skill 的"对账表+不扩大战果"。

## Chrome Debug 按需启停（2026-06-04 实测落地）

**背景**：Chrome debug 端口 9333 常驻占 ~108MB RSS，用户要求"调用时启动、不用关闭"。

**关键发现**：
- launchd plist `KeepAlive=false` 只保证 launchd **不主动重启**，但 Chrome 一旦启动就会一直跑
- Chrome 自己的调试服务会保持进程活跃，需要 watchdog 脚本主动 kill
- `--user-data-dir=~/.hermes/chrome-debug` 是独立 profile，cookies 存在这里 → **关进程不丢登录态**

**已实施的脚本**：

| 脚本 | 路径 | 用途 |
|------|------|------|
| chrome-on-demand.sh | `~/.hermes/scripts/chrome-on-demand.sh` | 手动 start/stop/status |
| chrome_cdp_health.sh | `~/.hermes/scripts/chrome_cdp_health.sh` | watchdog（后台常驻） |

已归档到 skill：devops/macos-process-lifecycle/scripts/chrome-on-demand.sh + chrome-watchdog.sh

**chrome-on-demand.sh 核心逻辑**：
```bash
# 检测端口是否有人监听（存在 = Chrome 在跑）
lsof -i :9333 -t 2>/dev/null | head -1

# 启动（独立 profile，cookies 不丢）
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --user-data-dir=/Users/aimac/.hermes/chrome-debug \
  --remote-debugging-port=9333 \
  --load-extension=/Users/aimac/.hermes/mcp-chrome-extension \
  --no-first-run --no-default-browser-check --no-startup-window

# PID 文件（供 watchdog 使用）
echo "$pid" > /tmp/hermes-chrome-cdp.pid
```

**watchdog 判断空闲的标准**：
```bash
# established 连接数 > 1 说明有外部客户端（Chrome 自己占 1 个 listening）
lsof -i :$PORT -s TCP:ESTABLISHED 2>/dev/null | wc -l | tr -d ' '
# n > 1 → 有客户端，保持运行
# n ≤ 1 → 空闲 30 分钟 → kill Chrome
```

**watchdog 脚本（/tmp/hermes-chrome-watchdog.sh，PID 49970）**：
```bash
while true; do
    sleep 60
    pid=$(lsof -i :9333 -t 2>/dev/null | head -1)
    [ -z "$pid" ] && exit 0  # Chrome 未运行，退出
    if has_cdp_clients; then
        log "CDP 客户端活跃 PID=$pid"
    else
        log "无客户端，超时，关闭 Chrome PID=$pid"
        kill -TERM $pid 2>/dev/null; sleep 3; kill -9 $pid 2>/dev/null
        exit 0
    fi
done
```

**验证命令**：
```bash
bash ~/.hermes/scripts/chrome-on-demand.sh status   # running:PID 或 stopped
bash ~/.hermes/scripts/chrome-on-demand.sh start    # 手动启动
bash ~/.hermes/scripts/chrome-on-demand.sh stop     # 手动关闭
ps -p $(bash ~/.hermes/scripts/chrome-on-demand.sh status | cut -d: -f2) -o rss=  # 内存 KB
```

**当前状态（2026-06-04）**：Chrome debug PID 49913，watchdog PID 49970，CDP 客户端有 `verge-mih`（其他应用）和 `agent-bro`（Hermes 自身）。

## 实际案例（2026-06-04）

| 进程 | 占用 | 处理 | 释放 |
|------|------|------|------|
| bash-language-server | 666 MB | kill（IDE 重启自拉） | +0.66 GB |
| 豆包 renderer × 3 | 1.05 GB | kill（App 不活跃，前台无窗口） | +1.05 GB |
| Ollama serve + Ollama.app | 287 MB | `at now + 30 min` 自动 kill | +0.29 GB |
| Chrome debug (设计) | ~108 MB RSS | watchdog 30min idle → 自动关 | ~+0.1 GB |

最终效果：空闲从 2.97 GB → 4.56 GB（+1.59 GB）。

## 卸载一个 macOS 子系统（桌面客户端类）的标准流程

适用：用户说"把 Hermes Desktop 客户端删了" / "卸载 X.app" / "清理 Y"，目标是一个**独立的 macOS GUI 子系统**（区别于后台 CLI 服务）。

**核心区别**：这种 uninstall 不能像 `rm -rf /Applications/X.app` 那么粗暴，必须识别它和宿主系统（Hermes CLI）的边界——杀错进程或删错 plist 会让宿主也挂。

### Step 1：定位资产

```bash
# 1) 找 .app 主体（可能在 /Applications 或 ~/.hermes 子目录里）
mdfind -name "X.app" 2>/dev/null
ls -la /Applications/ ~/Applications/ 2>/dev/null | grep -i X
# Hermes 客户端特殊位置: ~/.hermes/hermes-agent/apps/<name>/

# 2) 找用户数据（聊天记录/缓存/cookies）
ls -la ~/Library/Application\ Support/X/ 2>/dev/null
du -sh ~/Library/Application\ Support/X/ 2>/dev/null

# 3) 找 plist 偏好设置
ls -la ~/Library/Preferences/ 2>/dev/null | grep -i X
# 命名规则: com.<vendor>.<app>.plist

# 4) 找运行中进程
ps aux | grep -E "X\.app|X Helper" | grep -v grep
```

### Step 2：区分"子系统 plist"和"宿主 plist"

**关键判断**：在 `~/Library/LaunchAgents/` 里看到 `ai.hermes.*.plist`，**不要全删**。

| 类别 | 例子 | 能不能删 |
|---|---|---|
| 子系统 plist（要删的） | `com.<vendor>.<app>.plist` 在 ~/Library/Preferences/ | ✅ |
| 宿主核心 plist（保留） | `ai.hermes.gateway.plist` / `ai.hermes.dashboard.plist` / `ai.hermes.self-evolution*.plist` | ❌ |
| 自家后台服务 plist（保留） | `ai.hermes.chrome.plist` / `com.aimac.hermes-chrome-debug.plist` | ❌ |

**判断方法**：
- plist 名包含**子系统产品名**（如 `com.nousresearch.hermes`）→ 子系统的
- plist 是 `ai.hermes.<service>.plist` 格式但服务名是 gateway/dashboard/evolution → 宿主的
- 不确定 → `cat <plist>` 看 `ProgramArguments` 第一项是哪个二进制

### Step 3：执行卸载（按这个顺序）

```bash
# 1) 杀进程（SIGKILL 直接干，因为要卸载了）
pkill -9 -f "X\.app" 2>/dev/null
pkill -9 -f "X Helper" 2>/dev/null
sleep 1

# 2) 删 .app 主体
rm -rf /Applications/X.app
# 或: rm -rf ~/.hermes/hermes-agent/apps/X/

# 3) 删用户数据
rm -rf ~/Library/Application\ Support/X
rm -rf ~/Library/Application\ Support/com.<vendor>.X  # 备份位置

# 4) 删 plist
rm -f ~/Library/Preferences/com.<vendor>.X.plist
# 注意：LaunchAgents 里通常没有这个，LaunchAgents 是宿主服务

# 5) 清缓存
rm -rf ~/Library/Caches/com.<vendor>.X 2>/dev/null
rm -rf ~/Library/Saved\ Application\ State/com.<vendor>.X.savedState 2>/dev/null
```

### Step 4：四路验证（必走，缺一不可）

```bash
# 1) 进程残留
ps aux | grep -E "X\.app|X Helper" | grep -v grep | wc -l
# 期望: 0

# 2) 磁盘残留
mdfind -name "X.app" 2>/dev/null
# 期望: 空

# 3) 用户数据残留
ls -la ~/Library/Application\ Support/ 2>/dev/null | grep -i X
ls -la ~/Library/Preferences/ 2>/dev/null | grep -i X
# 期望: 空

# 4) 宿主服务没受影响（关键：避免误删）
ps aux | grep "hermes_cli.main gateway" | grep -v grep | wc -l
# 期望: ≥ 1（gateway 还在跑）
```

### 反面教材

- **直接 `rm -rf /Applications/X.app` 不杀进程** → 用户再启动会报 "应用已损坏" 或文件锁住
- **不区分 plist 全删 `ai.hermes.*.plist`** → 删完用户发现 self-evolution/gateway 全停了
- **不验证宿主服务** → 用户回头发现 "Hermes 怎么没响应了" → 不知道哪步搞坏的

## 与其他 skill 的边界

- **不**管 Hermes Gateway / 屏幕监控等自家进程（那些归 `hermes-memory-hpc`）
- **不**管 macOS 桌面 UI 控制（那些归 `macos-computer-use`）
- **只**管"用户机器上跑着的资源大户"的生命周期

## 引用

- `references/macos-vmstat-formulas.md` — 内存/CPU 计算公式
- `references/launchd-bash-logging-pitfall.md` — **launchd 跑 bash 脚本时 `tee -a` + stdout 双写到同一 log 文件的坑**（mem_patrol v1.0→v1.2 复现/修复），新写 launchd bash 脚本前必看
- `references/hermes-storage-audit.md` — ~/.hermes 13GB 存储地图（每个目录的性质 + 可清理项 + 代价，2026-06-06 更新 v2，含 venv/Homebrew 分级瘦身策略）
- `references/cua-driver-idle-pattern.md` — 2026-06-04 实战：cua-driver 45% CPU 99% 时间在空转的诊断（99% 在 `_pthread_wqthread`，不能盲杀）+ 30 分钟空闲回收的正确判断姿势（不能按 cputime delta，要按 Hermes 工具调用时间戳）
- `references/idle-killer-implementation-2026-06-04.md` — 30 分钟空闲回收脚本/状态/cron 完整实现 + 监控名单 + 误杀防护 + 副作用清单
- `scripts/idle_kill.sh` — 30 分钟空闲自动 kill 模板
- `scripts/memory_top10.sh` — Top 10 内存大户 + 可清理性评估

## 30 分钟空闲回收规则（用户拍板，2026-06-04 落地）

**用户偏好**：吃资源的服务（cua-driver、ToDesk、ddddocr 驻留、heavy python 子进程）30 分钟无调用就杀，需要时按需拉起。

### 白名单（绝对不杀）
- `hermes gateway` 主进程
- 所有 `*python*` 跑的 cron 任务
- launchd 系统服务（PID 1 的子进程）

### 监控名单（候选杀）

| 服务 | 资源占用 | 杀法 | 拉起法 |
|---|---|---|---|
| `cua-driver` | 45% CPU / 53MB（**99% 时间空转，详见 cua-driver-idle-pattern.md**）| `launchctl bootout gui/$(id -u)/com.trycua.driver` | `launchctl bootstrap gui/$(id -u) /Library/LaunchDaemons/com.trycua.driver.plist` |
| `ToDesk_Service` | 远程工具 | `pkill -9 -f ToDesk_Service` | `open -a ToDesk` |
| `hermes venv python` 子进程 | 视情况 | `pkill -f 'hermes-agent/venv/bin/python'` | gateway 重启时自然拉起 |
| `ddddocr` 模型驻留 | 200MB | 进程退出自动释放 | 引用 `slide_solver` 时自动加载 |

### ⚠️ cua-driver 特殊处理

**⚠️ 修正（2026-06-04 验证）**：cua-driver 99% 时间在 `_pthread_wqthread`（1449/1462 sample = 99%），这是 macOS workqueue 的空轮询，**cputime 在空闲时几乎不增长**（delta < 0.1s/15min）。所以**简化版 ps cputime delta 模式实际上是对的**——不是错的。

**两种判断模式（都可用）**：

| 模式 | 优点 | 缺点 |
|---|---|---|
| **A: ps cputime delta**（当前实现）| 简单，无需侵入 Hermes 工具调用 | cputime 即使空转也可能有微小漂移（tokio worker 池） |
| **B: last-use timestamp**（侵入式） | 精确，无误杀风险 | 需要在每个 `mcp_cua_driver_*` 工具前后写时间戳，侵入大 |

**当前落地（job `2f527c06f06d`）**：模式 A，30 分钟阈值，cputime delta < 0.1s 视为空闲。**已通过 sample 工具验证 cputime 行为符合预期**。

**修正历史**：
- 2026-06-04 v1: 误判模式 A 错（基于猜测）
- 2026-06-04 v2 (现): 实测 `sample cua-driver 2 1` 显示 99% 在 `_pthread_wqthread` → cputime 实际几乎不动 → 模式 A 是对的

### ddddocr 模型驻留（新增案例，2026-06-04）

ddddocr 装在 `~/.hermes/hermes-agent/venv/`，模型 ~85MB + onnxruntime 66MB。**首次 import `slide_solver` 触发模型加载，后续常驻 ~200MB**。但当前没有任何 `slide_solver` 引用点常驻模型——只在脚本显式调用时加载，调用完进程退出就释放。

**结论**：ddddocr 当前**不需要**纳入 idle_killer 监控（按需加载）。等未来 `slide_solver` 被常驻进程引用后再加监控。

## Ollama 按需释放（`OLLAMA_KEEP_ALIVE`）

Ollama 自带"模型加载后保持活跃"的机制，通过 `OLLAMA_KEEP_ALIVE` 环境变量控制释放时间。

### 诊断

```bash
# 查当前设置
launchctl getenv OLLAMA_KEEP_ALIVE   # 默认 5m，未设置=5 分钟
launchctl getenv OLLAMA_KV_CACHE_TYPE  # 如 q8_0

# 查 Ollama 进程状态
ollama ps  # 当前加载的模型
pgrep -a -f ollama  # 进程 PID

# 查 launchd 配置
cat ~/Library/LaunchAgents/com.ollama.env.plist
```

### 设置按需释放

**两步走**（立即生效 + 持久化）：

```bash
# 1) 立即生效
launchctl setenv OLLAMA_KEEP_ALIVE 1m

# 2) 持久化（修复 plist，让重启后也生效）
# 在 ProgramArguments 数组里添加：
#   <string>OLLAMA_KEEP_ALIVE</string>
#   <string>1m</string>
```

**plist 示例**（保留原有的 `OLLAMA_KV_CACHE_TYPE`）：
```xml
<array>
    <string>/bin/launchctl</string>
    <string>setenv</string>
    <string>OLLAMA_KV_CACHE_TYPE</string>
    <string>q8_0</string>
    <string>OLLAMA_KEEP_ALIVE</string>
    <string>1m</string>
</array>
```

验证 plist 格式：`plutil -lint ~/Library/LaunchAgents/com.ollama.env.plist`

### 验证

```bash
launchctl getenv OLLAMA_KEEP_ALIVE   # → 1m
ollama ps  # 确认新模型按策略释放
```

### 参数建议

| 值 | 适用场景 |
|---|---|
| `5m`（默认） | 模型频繁使用，不想每次都等加载 |
| `1m` | 偶尔用的模型（如视觉 `qwen3-vl:2b`） |
| `0` | 用完立刻释放（不推荐，每次都要等） |
| `-1` | 永久驻留（模型常驻，省加载时间） |

### ⚠️ 注意

- `launchctl setenv` 只对当前 gui session 生效，**不重启也保持**
- 设置后，**新加载的模型**立即生效；已加载的模型在本次会话结束前不会重新评估
- Ollama 服务本身（serve 进程）只占几十 MB，不受 `KEEP_ALIVE` 影响
- 如果 Ollama 是手动 `ollama serve` 启动的（非 launchd），`setenv` 不会生效——需要 export 到 shell rc
- **plist 格式坑**：`launchctl bootstrap` 可能报错 5 (I/O error) 如果 plist XML 结构不对（如两个 `<dict>` 同级）。确保所有 key/value 在**同一个** `<dict>` 里。用 `plutil -lint` 验证。**修复流程（2026-06-06 实战）**：
  1. `launchctl setenv OLLAMA_KEEP_ALIVE 1m` → 立即生效（不用重启 Ollama）
  2. 用 `plutil -lint` 验证当前 plist 格式（`OK` 通过说明 XML 合法）
  3. 修改 plist 时，**不要把新 key 加在 dict 外**（否则 bootstrap 报 Input/output error）
  4. 修改后用 `plutil -lint` 再验证一次，确认 `OK` 后再 reload
- **plist 不要直接 bootstrap reload（会报错）**：如果 plist 之前未加载（bootout failed），`bootstrap` 也会报错。**`launchctl setenv` 本身不需要 bootstrap reload**，它是直接设置全局环境变量，Ollama 子进程继承即可。只有在需要重启 launchd 服务时才用 bootstrap。

### 副作用
- 杀 cua-driver 后 `mcp_cua_driver_*` 全失效
- 正在跑的 `computer_use` 任务会卡住 → **等任务跑完再杀**
- 重新调用时**等 5-10 秒**让 cua-driver 冷启动完成
- 拉到模型驻留服务（ddddocr）有 1-2 秒首次加载延迟
