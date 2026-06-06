# Chrome 多程序争用户数据目录 — 登录态"平白无故丢失"根因诊断与治本

> **触发场景**：用户报"AI 站登录态一直在丢"、"每天都要重新登录"、"9 站 tab 总是空"
> **本次事件**：2026-06-05 15:40 用户问"AI 网站登录的为什么都会被退出丢失？"
> **根因**：5 个程序都管 Chrome，3 个用 `~/.hermes/chrome-debug` 隔离 profile，1 个用 system Default，1 个每小时 pkill 全杀光
> **用户原话**："平白无故丢失登录记录数据，这不解决永远在维修的路上"

---

## 症状（用户看到的）

- 早上登录了 9 个 AI 站
- 中午再开，tab 全空 / 全跳登录页
- 每次"重新登录后又丢"
- 看起来"毫无征兆"（不是重启 / 不是手动退出）

---

## 根因链（5 个程序同时管 Chrome）

按发现顺序列出（每个都是审计输出）：

| # | 程序 | plist / 脚本 | user-data-dir | 频率 | 行为 |
|---|------|-------------|---------------|------|------|
| 1 | `ai.hermes.chrome.plist` | 5/9 旧 | `~/.hermes/chrome-debug` | RunAtLoad | 启隔离 profile Chrome（不跟 system 共享）|
| 2 | `com.aimac.hermes-chrome-debug.plist` | 6/1 旧 | `~/.hermes/chrome-debug` | RunAtLoad | 启隔离 profile Chrome（跟 #1 抢 profile）|
| 3 | `chrome-on-demand.sh` | 手动 | `~/.hermes/chrome-debug` | 按需 | 启隔离 profile Chrome（再添一份）|
| 4 | `self_evolution.sh` line 78 | hourly | **不启，只杀** | 每小时 | `pkill -f "chrome.*9333"` 杀光所有带 debug port 的 |
| 5 | `chrome_keepalive.sh` (v1.0) | 5 分钟 | `.../Chrome/Default` (system) | StartInterval=300 | 唯一用 system profile 启的 |

**3 个隔离 profile** + **1 个 system profile** + **1 个每小时 pkill** =
- 登录 9 站写到隔离 profile 的 cookies → **杀后 keepalive 起来的是 system profile，cookies 找不到** → "登录态丢"
- 即使 1 个隔离 profile 没被杀，cookies 在 `~/.hermes/chrome-debug/Cookies` 是 6/2 旧（6 月 5 日之前的登录）→ **登录态过期**也是"丢"

---

## 根因诊断命令（一键跑）

```bash
# 1. 找所有跑着 debug port 的 Chrome 进程
echo "=== 全部 debug Chrome ==="
ps -axo pid,etime,args | grep "Google Chrome.app" | grep -v "Helper\|crashpad\|grep" | awk '{
    pid=$1; etime=$2;
    cmd="";
    for(i=3;i<=NF;i++) cmd = cmd " " $i;
    if (cmd ~ /--user-data-dir/) {
        match(cmd, /--user-data-dir=[^ ]+/);
        udd = substr(cmd, RSTART+16, RLENGTH-16);
        print pid "  up=" etime "  user-data-dir=" udd
    }
}'

# 2. 看 9333 端口在哪个 PID
echo "=== 9333 LISTEN ==="
lsof -nP -iTCP:9333 -sTCP:LISTEN | head -3

# 3. 看 launchd 加载了哪些 Chrome 相关
echo "=== launchd Chrome ==="
launchctl list | grep -iE "chrome"

# 4. 看 plist 实际指定的 user-data-dir
echo "=== plist 内容 ==="
for f in ~/Library/LaunchAgents/*chrome*.plist*; do
    echo "--- $f ---"
    grep -E "user-data-dir|--args|remote-debugging" "$f" 2>/dev/null | head -5
done

# 5. 看每个 profile 目录的 cookies mtime
echo "=== 各 profile 的 cookies mtime ==="
for dir in \
    "$HOME/Library/Application Support/Google/Chrome/Default" \
    "$HOME/.hermes/chrome-debug"; do
    if [ -f "$dir/Cookies" ]; then
        stat -f "  %Sm  %z bytes  %N" "$dir/Cookies"
    else
        echo "  (no Cookies)  $dir"
    fi
done
```

**期望输出（健康态）**：
- 只有 **1 个 Chrome 进程**有 `--user-data-dir`
- 那个 user-data-dir 是 `.../Chrome/Default`（system profile）
- 9333 LISTEN 跟那个 PID 一致
- 唯一活跃的 plist 是 `ai.hermes.chrome-keepalive`
- `Default/Cookies` mtime 是**最近**（< 1 小时）| `chrome-debug/Cookies` 应该是**空 / 过期** |

---

## 治本方案（3 步）

### 第 1 步：disable 2 个旧 plist

```bash
cd ~/Library/LaunchAgents/

# 停用（unload + rename .disabled，**不删**，用户可改回）
launchctl unload ai.hermes.chrome.plist
mv ai.hermes.chrome.plist ai.hermes.chrome.plist.disabled

launchctl unload com.aimac.hermes-chrome-debug.plist
mv com.aimac.hermes-chrome-debug.plist com.aimac.hermes-chrome-debug.plist.disabled

# 验证
launchctl list | grep -iE "chrome"  # 应该只剩 keepalive + chrome-devtools-mcp
```

### 第 2 步：改 on-demand 脚本走 system profile

```bash
# chrome-on-demand.sh line 19-26
# 旧: --user-data-dir=/Users/aimac/.hermes/chrome-debug
# 新: --user-data-dir="$HOME/Library/Application Support/Google/Chrome/Default"
# 注释加一句 "治本: 用 system Default profile, 跟用户日常 Chrome 共享, 登录态不会丢"
```

### 第 3 步：改 self_evolution 不直接 pkill，委托给 keepalive

```bash
# self_evolution.sh line 74-87
# 旧: pkill -f "chrome.*9333" + open ... --user-data-dir=chrome-debug
# 新: bash ~/.hermes/scripts/chrome_keepalive.sh
# 验证 keepalive 起来没, 失败用 osascript 通知用户, 不强杀
```

### 验证（治本完成态）

```bash
# 1. 只有 1 个 Chrome debug 进程
pgrep -fl "Google Chrome.*--remote-debugging-port" | grep -v "Helper\|crashpad" | wc -l
# 期望: 1

# 2. 全部用同一 user-data-dir (system Default)
pgrep -fl "Google Chrome.*--user-data-dir" | grep -oE "user-data-dir=[^ ]+" | sort -u | wc -l
# 期望: 1

# 3. 9333 在 system profile 启的 Chrome 上
lsof -nP -iTCP:9333 -sTCP:LISTEN
# 对比 ps 看哪个 Chrome 的 user-data-dir 是 system Default

# 4. cookies 在 Default 里有 1688 / grok / alipan 等
python3 -c "
import sqlite3, os
db = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Cookies')
conn = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
hosts = set(r[0] for r in conn.execute('SELECT host_key FROM cookies'))
print(f'共 {len(hosts)} 个 host 的 cookies')
for h in sorted(hosts):
    if any(k in h for k in ['1688','x.ai','grok','alipan','google','youtube','bilibili']):
        print(f'  ✅ {h}')
"
```

---

## 治本前的临时缓解（不要直接采用 — 用户拍板"治本"）

如果用户还没拍板"治本"，临时可以：
- 启 `chrome_keepalive.sh` 5 分钟保活（不杀，只确保有 1 个 system-profile Chrome 跑 9333）
- 不再 `pkill -f "Google Chrome"`（只 `pkill -f "remote-debugging-port=9333"` 精准杀 debug Chrome）

但用户说"治本" = 直接做第 1-3 步，不要再加第 6 个脚本。

---

## 复现 → 治本 → 验证 全流程时间线（2026-06-05）

| 时间 | 动作 | 验证 |
|------|------|------|
| 15:40 | 用户问"AI 站登录态为什么都丢" | — |
| 15:40-15:42 | 跑根因诊断命令，发现 5 程序管 Chrome | pgrep 5 个 debug 进程 + 2 个用错 profile |
| 15:43 | 写 `chrome_keepalive.sh` v1.0（缓解）| bash -n OK + dry-run no-op |
| 15:46 | 用户追问"平白无故丢不解决永远在维修" | 拍板"治本" |
| 15:47-15:50 | disable 2 旧 plist + 改 on-demand + 改 self_evolution | launchctl list 剩 1 个 keepalive + 2 个 disabled |
| 15:50 | 实地验证：Default/Cookies 229KB + 1688/x.ai/alipan cookies 全在 | python sqlite 读出 host 列表 |
| 15:51 | 汇报"治本完成, 5 程序 → 1 程序, 登录态以后不再丢" | 用户满意 |

---

## Pitfall 速记（下次少走 2 步弯路）

- ❌ **不要只启 keepalive 了事** — keepalive 是缓解，根因是 3 程序用错 profile，不 disable 它们 keepalive 也救不了登录态
- ❌ **不要 pkill -f "Google Chrome"** — 会把 system Chrome（带登录态的）也杀了，cookies 持久化但 tab 全空
- ❌ **不要用隔离 profile（`~/.hermes/chrome-debug`）做长期方案** — 跟用户日常 Chrome 不共享 cookies，每次启都是新会话
- ✅ **永远统一到 system Default profile** — `~/Library/Application Support/Google/Chrome/Default`，跟用户日常 Chrome 同源，登录态无缝
- ✅ **disable 而不是 delete 旧 plist** — 用户可改回，rename `.plist.disabled` 是 launchd 通用 idiom
- ✅ **每次 pkill 后实地验证登录态** — `python sqlite 读 Cookies 表`，不靠"看 tab 空就报丢"
- ✅ **治本前先列全 5 个程序** — `ps -p + plist + on-demand + self_evolution + keepalive` 5 类，要全列完
