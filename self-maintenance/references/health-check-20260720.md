# Hermes + Mac 大体检 SOP（2026-07-20 实测版）

用户说"来个大体检"/"健康检查"/"全面体检"时，按下面流程一次性跑完。
所有命令已经验证在 macOS 26.5.2 / Apple Silicon 上可用。

## 报告输出结构（三段式）

1. **硬件基线**（CPU/内存/磁盘/电池，表格化，全部健康打 ✅）
2. **🚨 需立刻关注的问题**（按 🔴/🟡/🟢 标优先级，每条带修复命令）
3. **模块明细**（Hermes Agent / 网络 / 安全 / 更新 / 进程 / 磁盘可优化项）

末尾给"🎯 建议下一步操作"按优先级排序。

---

## 第一步：硬件基线（一组命令并行）

```bash
# 系统 + 硬件
sw_vers
system_profiler SPHardwareDataType | head -25
uptime

# CPU / 内存 / 磁盘
top -l 1 -n 0 -s 0 | grep "CPU usage"
vm_stat | head -10
sysctl vm.swapusage
df -h / /System/Volumes/Data
diskutil apfs list | head -30

# 电池
pmset -g batt
system_profiler SPPowerDataType | grep -E "Cycle Count|Condition|Maximum Capacity"

# 网络
ifconfig | grep -E "^[a-z]|inet " | head -20
netstat -rn | grep default
```

**判定**：负载 > 5 / 内存 Pages free < 20000 / 磁盘剩余 < 5G / 电池循环 > 1000 触发告警。

---

## 第二步：Hermes Agent 健康（核心）

```bash
# Gateway 进程（关键！确认是固定端口不是 --port 0）
ps aux | grep 'hermes_cli.main serve' | grep -v grep
lsof -nP -p <gateway_pid> 2>/dev/null | grep TCP | head -5
# 端口验证（必须用 netstat，lsof 可能漏看）
netstat -an | grep -E "18281|LISTEN" | head -10
# 关键端口扫描
for p in 18280 18281 18282 20128 7066 9090 9222; do
  (echo > /dev/tcp/127.0.0.1/$p) 2>/dev/null && echo "$p: OPEN" || echo "$p: closed"
done

# Skills 深度（合规检查）
echo "skills: $(find ~/.hermes/skills -mindepth 2 -maxdepth 2 -name 'SKILL.md' | wc -l)"
echo "depth>2 违例: $(find ~/.hermes/skills -mindepth 3 -name 'SKILL.md' | grep -v '/.archive/' | grep -v '/.hub/' | grep -v '/.curator_backups/' | wc -l)"

# Cron（应用层 + 系统层两套都要查）
hermes cron list
crontab -l 2>/dev/null

# Hermes self-check
hermes status

# launchd 保活配置
cat ~/Library/LaunchAgents/ai.hermes.gateway.plist 2>/dev/null
```

**关键判定**：
- Gateway 必须跑 `--port 18281`（固定），不是 `--port 0`
- `Next run: None` = 该 cron 调度失效，必须 `hermes cron show <id>` 排查
- depth>2 违例 > 0 = 有伞包嵌套未扁平化

---

## 第三步：磁盘 + 大文件

```bash
# 顶级目录占用
du -sh ~/Library/* 2>/dev/null | sort -hr | head -15
du -sh ~/Library/Caches/* 2>/dev/null | sort -hr | head -10
du -sh ~/Library/Application\ Support/* 2>/dev/null | sort -hr | head -10

# Hermes 自家占用
du -sh ~/.hermes 2>/dev/null
du -sh ~/.hermes/* 2>/dev/null | sort -hr | head -15

# state.db 健康
ls -la ~/.hermes/state.db
sqlite3 ~/.hermes/state.db ".tables"
# 可选瘦身: sqlite3 ~/.hermes/state.db "VACUUM;"
```

**判定**：ms-playwright / Chrome cache / pip cache 都可清，单项 > 1G 提示用户。

---

## 第四步：网络 / 代理

```bash
# DNS / 代理
scutil --dns | head -10
scutil --proxy
networksetup -getwebproxy Wi-Fi
networksetup -getsecurewebproxy Wi-Fi

# 出口连通性（用 curl + timeout）
for url in https://www.google.com https://github.com https://openrouter.ai; do
  curl -s --max-time 5 -o /dev/null -w "$url: %{http_code} %{time_total}s\n" "$url"
done

# 代理进程
ps aux | grep -iE "clash|surge|quantumult" | grep -v grep | head -5

# LaunchAgents 实际生效的
launchctl list | grep -E "hermes|nousresearch|clash|chrome"
```

**判定**：系统级 HTTPEnable=No 但有残留 Server=192.168.0.x:7890 → Clash Mi 走 TUN，本机未监听 7890 是正常的；openrouter 超时 + google 通 = 出口代理配置问题。

---

## 第五步：安全审计

```bash
# 最近登录（只看本机用户登录）
last -n 10 | head -15

# 失败 SSH / sudo
log show --predicate 'eventMessage contains "ssh"' --last 24h 2>/dev/null | grep -iE "failed|invalid" | head -5
log show --predicate 'eventMessage contains "sudo"' --last 24h 2>/dev/null | head -5

# 内核错误
log show --predicate 'eventType == logEvent' --last 24h 2>/dev/null | grep -iE "error|fail|crash" | head -10
```

**判定**：非本机 IP 的 SSH 登录 = 立即告警；sudo 频繁出现 = 检查流程。

---

## 第六步：更新状态

```bash
softwareupdate -l 2>&1 | head -10
brew outdated 2>/dev/null | wc -l    # 总数
brew outdated --cask 2>/dev/null | wc -l
```

**判定**：macOS/brew 都有 0 更新 = 系统干净。

---

## 第七步：Time Machine

```bash
tmutil status 2>&1
tmutil latestbackup 2>&1
tmutil listlocalsnapshots /
```

**判定**：`Failed to mount destination` = 备份盘离线；超过 2 天没备份 = 告警。

---

## 第八步：进程 / 资源

```bash
ps -ax -o pid,user,%cpu,%mem,command | wc -l    # 总进程数
ps axo pid,user,%cpu,%mem,rss,comm | sort -nrk5 | head -11 | tail -10  # 内存 top 10
```

**判定**：Chrome 进程 > 20 提示用户关 tab；单进程 %CPU > 50 持续 5min 是异常。

---

## 第九步：写入体检报告

格式三段：
1. **硬件基线表**（所有指标一行一表，全 ✅）
2. **🔴🟡🟢 告警列表**（按优先级，每条带修法）
3. **模块明细**（Hermes/网络/安全/更新/进程/磁盘可优化项）

末尾给"🎯 建议下一步操作"按优先级 1-2-3-4 列出，让用户挑要修哪条。

---

## 已知踩坑（提前避坑）

- `du ~/*` 在大目录会超时 180s → 用 `du -sh ~/Library/Caches/*` 精确查
- `ps --sort=-%cpu` 是 GNU 语法，macOS BSD `ps` 不支持 → 用 `ps axo ... | sort -nrk3`
- `brew` 命令偶发没 PATH → `which brew && ls -la $(which brew)` 先确认
- `last` 命令在 macOS 默认没启用 utmp 持久化，看到的只是当前 session
- 报告里**不写 "X 工具不可用"**，只写 "X 当前状态：超时 / 关闭 / 未监听"
- drift guard 误报处理：MEMORY.md 末尾缺 `§` 或内容含 box-drawing 字符会被 memory tool 拒绝 round-trip（详见 SKILL.md pitfall）