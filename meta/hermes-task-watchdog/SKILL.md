---
name: hermes-task-watchdog
category: meta
description: Periodically scan Hermes tasks directory for stalled tasks, completed tasks, and send alerts via Telegram when appropriate.
---

# Hermes Task Watchdog Skill

## Purpose
Periodically scan the Hermes tasks directory for stalled tasks, completed tasks, and send alerts via Telegram when appropriate.

## When to Use
- Running as a cron job every 15 minutes (or as configured).
- Need to monitor task progress and alert on stagnation.

## Steps
1. **Scan tasks directory**: List all `.md` files under `~/.hermes/tasks/` (excluding subdirectories like `done/` and `archive/`).
2. **Parse each task file**:
   - Extract frontmatter (between `---` lines) to find `状态:` field.
   - If missing, treat as unknown.
3. **Categorize**:
   - `状态: 进行中` → In‑progress.
   - `状态: 完成` → Completed.
   - Any other status or missing → treat as unknown (ignore for alerting).
4. **Detect stalling**:
   - **DO NOT use file mtime as the progress signal** (see v1.5.0 pitfall below). Use the embedded progress marker instead.
   - For each in‑progress task, parse a "last progress" timestamp from the frontmatter/body in this priority order:
     1. `最后检查:` / `last_check:` field (most reliable — only updated when human/agent actually touches the task)
     2. `步骤:` section's most recent `[x]` step timestamp if present
     3. Frontmatter `创建时间:` (worst case — only tells you age, not stagnation)
   - If the last-progress timestamp is older than 30 minutes → stalled.
5. **Alert** (with de‑dup, see v1.5.0 告警去重 pitfall):
   - If gateway is running (check for `hermes-gateway` process or webhook listener PID) and there are stalled tasks:
     1. First, read `~/.hermes/tasks/.stuck_alert.json` for each stalled task's `last_alert_sent`.
     2. If `last_alert_sent` is < 1 hour ago → **suppress** the TG push; still record in stdout that the task is stuck + alert suppressed.
     3. If first detection OR > 1 hour since last alert → send a Telegram message:
        ```
        任务 [<任务名称>] 停滞超过 30 分钟，是否需要干预？
        ```
        Task name can be taken from the `任务:` field in frontmatter or fallback to filename.
     4. Update `.stuck_alert.json` with `last_alert_sent` for each task actually alerted.
   - **Cron context default**: in cron runs (no user present), prefer write-only mode (append alert to task file or update alert JSON) unless it's the first detection of a new stuck task. The cron output channel is what matters — see v1.2.0 刷屏 pitfall for `deliver=local`.
6. **Archive completed tasks**:
   - Move files with `状态：完成` or `状态：DONE` from `~/.hermes/tasks/` to `~/.hermes/tasks/done/`.
   - **Watchdog self-reports**: Files named `watchdog-report-*.md` are NOT user tasks — move them to `~/.hermes/tasks/archive/` instead of `done/` to keep the root directory clean.
   - Preserve filename; if duplicate exists, add timestamp suffix.
7. **Report**:
   - Output summary: `进行中 X 个，已完成 Y 个，停滞 Z 个`.
   - This output is the cron job’s result and will be sent to the user via the configured channel.

## Frontmatter Example
```
---
任务：示例任务描述
状态：进行中
创建时间：2026-06-26 10:00
步骤：
- [ ] 步骤 1
- [x] 步骤 2
结果：
---
```

## Pitfalls
- **Missing frontmatter**: If a task file lacks proper frontmatter, skip it and log a warning (optional).
- **Clock skew**: Ensure system time is correct; otherwise mtime comparison may be off.
- **Gateway check**: If the gateway is not running, do **not** send Telegram alerts to avoid spamming when the system is down.
- **File moves**: When moving completed tasks, handle errors gracefully (e.g., permission issues) and continue processing other files.
- **Watchdog 自报告过滤 (v1.2.0 增强, 2026-06-28 实战)**: `watchdog-report-*.md` 文件**必须完全排除在任务扫描之外** — 不仅不归档，还不能参与状态统计。**根因**: 这些报告 frontmatter 格式与用户任务不同，grep 匹配"状态：进行中"时会误判 (如 watchdog 自身报告里的摘要行)。**正确扫描逻辑**:
  ```bash
  # 1. 先排除 watchdog 自报告 + 非任务文件
  find ~/.hermes/tasks/ -maxdepth 1 -type f -name "*.md" \
    ! -name "watchdog-report-*.md" \
    ! -name ".last_watchdog_state.json" \
    -exec grep -l "^状态：进行中\|^状态：进行中" {} \;
  # 2. 归档时也要区分：用户任务→done/, watchdog 报告→archive/
  ```
  **检测顺序**: 先按文件名过滤 (排除 `watchdog-report-*`) → 再按 frontmatter 状态分类 → 最后做_mtime_ 停滞判断。**触发词**: "watchdog 报告被误统计 / 误报进行中 / 扫描逻辑" → 检查文件名过滤是否在最前面.
- **Cron self-dedup missing (v1.1.0, 2026-06-26 night-learning cron 实战)**: Hermes cron 调度**不内置去重** — 同一脚本被 cron 多次触发 (e.g. `*/15 * * * *` + `0 23 * * *` 触发两次) 会**双跑**并产生重复 Telegram 汇报。**修法**: 脚本入口加 lockfile:
  ```bash
  LOCK=/tmp/hermes-night-learning.lock
  exec 9>"$LOCK" || exit 1
  flock -n 9 || { echo "已在运行，跳过"; exit 0; }
  # ... 主逻辑 ...
  rm -f "$LOCK"
  ```
  或用 `pgrep -f "$0" | wc -l` > 1 检查自身重入。**触发词**: "cron 双跑 / 重复执行 / 夜间学习跑两次 / cron 没去重" → 0 思考加 lockfile.
- **memory tool 在 cron 不可用 (v1.1.0)**: `memory(action='add')` 在 cron 启动的 session 报 "Memory is not available"。**修法**: 见 `proactive-execution` skill Failure 51 坑 B — fallback 写 `~/.hermes/learning/<date>.md`.
- **Telegram 推送用 `hermes send` (v1.1.0)**: 别用 `hermes_notify.py` (内部 telegram_send 是占位 `print`)，真捷径是 `cat <content> | hermes send -t telegram`，gateway 不在线也能发。详见 `proactive-execution` Failure 51 坑 C.
- **⚠️ 看门狗本身也在刷屏 (v1.2.0, 2026-06-27 用户原话"看门狗报告不用发了吧，很刷屏")**: 9 个常驻 cron (task-watchdog/morning-briefing/night-learning x2/evening-briefing/ai-patrol/morning-health/session-bootstrap/夜间 ABCD 自学) 默认 deliver=origin/telegram/qqbot → 推消息刷屏.**机制**: `no_agent=True` + `deliver=local` + 空 stdout = **完全静默**（落到 `~/.hermes/cron/output/` 不推任何渠道）。**修法**: 批量 `cronjob action=update deliver='local'`，9 个 job 一行 update. 要查静默报告 `ls ~/.hermes/cron/output/`，要拉起 `cronjob action=run job_id=<id>`. **触发词**: "看门狗刷屏 / cron 报告 / cron 静默 / 不想收 cron" → 0 思考 deliver='local', 不切回 origin. **例外**: 真异常（task-watchdog 检测到 stalled task / gateway 挂）→ 脚本 stdout 非空 + deliver=origin 才推。关联：`proactive-execution` v1.11.0 + `cross-channel-sop-sync` v3.2.
- **停滞告警也要去重，不要每 15 分钟轰炸同一条 (v1.5.0, 2026-06-28 13:31 cron 实战)**: 同一个 stalled task 不应该每轮 cron 都推一次 TG — 用户已经收到告警了，正在赶回来，没响应不代表没看到。**根因**: step 5 原文写"send a Telegram message for each stalled task" 无去重。**修法**:
  1. 看门狗维护 `~/.hermes/tasks/.stuck_alert.json`，记录每个 stalled 任务的 `last_alert_sent`
  2. 新一轮检测到 stalled 时：如果该任务 `last_alert_sent` 距今 < 1 小时 → **静默**，stdout 仍写出 "stuck=1, alert_suppressed" 让 cron 投递
  3. 只有超过 1 小时未响应、或任务首次进入 stalled 状态才真推 TG
  4. 配合 v1.2.0 的 `deliver=local` 默认静默 → 即使有真告警也只是写文件不轰炸
  ```bash
  # 简化逻辑
  alert_file=~/.hermes/tasks/.stuck_alert.json
  last_sent=$(jq -r ".tasks.\"$task_name\".last_alert_sent // empty" "$alert_file" 2>/dev/null)
  if [ -n "$last_sent" ] && [ $(( $(date +%s) - $(date -d "$last_sent" +%s) )) -lt 3600 ]; then
    echo "alert_suppressed (last sent $last_sent)"
  else
    # 真推 TG / 写文件
    curl -s -X POST "$TG_API/sendMessage" ... || echo "tg failed, file-only"
    # 更新 alert_file
  fi
  ```
  **触发词**: "watchdog 重复推送 / 告警轰炸 / 同一任务每 15 分钟 TG / 用户没响应也别刷屏" → 0 思考加 alert_file 去重.
- **状态字段健壮解析 (v1.3.0, 2026-06-28 实战)**: 任务文件 `状态:` 可能带括号说明 (e.g. `状态：停滞 (超过 30 分钟无进展)` 或 `状态：进行中 (等待依赖)`)，grep 只匹配 `^状态：进行中$` 会漏判。**正确解析**:
  ```bash
  # 提取 frontmatter 内状态行，去除括号内容后匹配
  status=$(grep "^状态:" "$file" | sed 's/（.*//g' | sed 's/(.*//g' | awk -F: '{print $2}' | xargs)
  case "$status" in
    进行中|in_progress) → 视为进行中 ;;
    完成|done|DONE) → 视为已完成 ;;
    停滞|stuck|cancelled) → 视为非活跃，跳过停滞检测 ;;
  esac
  ```
  **触发词**: "状态字段带括号 / grep 漏判 / frontmatter 解析不准" → 0 思考加 sed 清洗。
- **⚠️ mtime 不是进度信号 — 用 frontmatter 内的最后检查时间 (v1.5.0, 2026-06-28 13:31 cron 实战)**: 文件 mtime 在 watchdog 场景下**完全不可信**作为"任务进展"指标。
  **根因**: 看门狗每 15 分钟都会读+touch 任务文件 (写 `.last_watchdog_state.json` 时连带 update、或者 cron 跑 ls/stat 触发 metadata 更新)；更糟的是 `done/` 里 watchdog 自己生成的 `watchdog-report-*.md` 也跟任务文件混在同一目录级别。上一次 11:32 的 watchdog 跑出来 `stuck: 0` 完全错了 — install_crawlers 任务真实停滞 2h+，但 mtime 是 12:07 (watchdog 自己刚 touch 过)。
  **正确做法** (取代 step 4 旧逻辑):
  1. 解析 frontmatter 里 `最后检查:` / `last_check:` 字段 (human/agent 真动手时才更新这个)
  2. 没有这个字段 → 退到 `步骤:` 区里最近一个 `[x]` 的时间戳
  3. 再没有 → 退到 frontmatter `创建时间:` (只能告诉你 age，不是 stagnation)
  **判定**: last_progress 距今 > 30 分钟 → stalled
  ```bash
  # 提取最后检查时间 (优先) — 不要 stat 文件 mtime
  last_check=$(grep -E "^最后检查:|^last_check:" "$task" | head -1 | sed 's/.*: *//')
  if [ -z "$last_check" ]; then
    # fallback: frontmatter 创建时间
    last_check=$(grep -E "^创建时间:" "$task" | head -1 | sed 's/.*: *//')
  fi
  now_epoch=$(date +%s)
  lc_epoch=$(date -j -f "%Y-%m-%d %H:%M" "$last_check" "+%s" 2>/dev/null || echo 0)
  if [ $((now_epoch - lc_epoch)) -gt 1800 ]; then echo "STUCK"; fi
  ```
  **触发词**: "watchdog 误报 stuck=0 / mtime 不可信 / 任务明明停滞但没告警 / 看门狗自己刷了 mtime" → 0 思考切到 frontmatter 解析。
- **Telegram 推送失败处理 (v1.4.0 + v1.6.0 修正, 2026-06-28 实战)**: 直接 `curl` 调 Telegram API 在 cron 场景下**默认会失败**，因为 `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` 不在 cron 启动的 shell 环境中。v1.4.0 原文建议用 `hermes send` 或 `~/.hermes/telegram_bot_token` — 这两个在 cron 也都不一定可用。**真正的修法**:
  1. **第一步永远是 source env**: `set -a; source ~/.hermes/.env; set +a` — 全部 token/chat_id 在这里
  2. **chat_id 变量名不固定**: 实际有 `TELEGRAM_HOME_CHANNEL` (主 chat) 和 `TELEGRAM_CHAT_ID` (备)，都要 try；`TELEGRAM_HOME_CHANNEL_THREAD_ID` 是 thread，不是 chat
  3. **credential 校验后 fail-safe**: 拿不到 → 写告警到任务文件 + stdout 标注 `tg_creds_missing`，**不阻塞**主扫描
  4. **source .env 会打 stderr 警告**（env 文件含 Chrome.app 路径等不是 export 的行），不影响 Python，**不要 panic**
  ```bash
  set -a; source ~/.hermes/.env 2>/dev/null; set +a
  BOT="${TELEGRAM_BOT_TOKEN:-}"
  CHAT="${TELEGRAM_HOME_CHANNEL:-${TELEGRAM_CHAT_ID:-}}"
  if [ -z "$BOT" ] || [ -z "$CHAT" ]; then
    echo "tg_creds_missing, write-only alert" >&2
    echo "ALERT: task stuck" >> "$task_file"
  else
    curl -s -X POST "https://api.telegram.org/bot${BOT}/sendMessage" \
      -d "chat_id=${CHAT}" -d "text=${msg}" -d "parse_mode=Markdown"
  fi
  ```
  **触发词**: "Telegram 推送失败 / cron 没 token / 404 Not Found / token 文件不存在 / 推送不到 Telegram" → 0 思考先 `source ~/.hermes/.env` 再判断. **关联**: `proactive-execution` v1.11.0 + `cross-channel-sop-sync` v3.2.
- **Telegram 响应要回传 (v1.6.0, 2026-06-28 14:16 cron 实战)**: 推送成功后**必须把 Telegram message_id 写回 `.stuck_alert.json`**，后续用户/agent 在 Telegram 点 "Reply" 能定位是哪个 watchdog 触发的；同时 `.last_watchdog_state.json` 也加 `telegram_msg_id` 字段用于跨次 run diff。**正确做法**:
  ```bash
  resp=$(curl -s -X POST "$TG_API/sendMessage" -d "chat_id=$CHAT" -d "text=$msg")
  msg_id=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('result',{}).get('message_id',''))" 2>/dev/null)
  if [ -n "$msg_id" ]; then
    jq --arg mid "$msg_id" '.stuck_tasks[0].telegram_msg_id = $mid' \
      ~/.hermes/tasks/.last_watchdog_state.json > /tmp/state.json && mv /tmp/state.json ~/.hermes/tasks/.last_watchdog_state.json
  fi
  ```
  **触发词**: "用户问这是哪条告警 / 告警溯源 / message_id 怎么查" → 0 思考把 msg_id 写回 state 文件.
- **`hermes send` 在 cron 里能用就走它，别自己 curl (v1.7.0, 2026-06-28 14:31 cron 实战)**: v1.4.0/v1.6.0 默认推荐 `source .env + curl` 是因为早期 cron gateway 不在线时的稳妥路径 — **但用户当前 setup (Mac mini 24GB, gateway 默认常驻) 下 `hermes send` 反而更稳**:
  ```bash
  hermes send --to telegram "🚨 任务 [...] 停滞超过 143 分钟..."
  # 成功返回: "Sent to telegram home channel (chat_id: 7359677525)"
  # 退出码 0 = 成功；非 0 = delivery/backend 错误
  ```
  **为什么 v1.4.0 的"不要用 hermes send"过时了**: `hermes send` 内部会查 profile config → gateway 路由 → TG API，cred 解析走 hermes 自己的 credential store，不依赖 cron shell 环境。**只要 gateway 进程在 (`pgrep -f hermes | head` 至少 1 个 pid) + user profile 是 `default` (或对应 chat_id 配过)，就一定能发**。  
  **修法 — 决策表**:
  1. `pgrep -f hermes` 有结果 + `hermes send --to telegram "test" --quiet` 退出 0 → 用 `hermes send`，省去 `source .env` 的 stub 警告 + 写 jq/python 抓 msg_id 的麻烦
  2. `hermes send` 失败 (exit 1/2) → fallback 到 v1.6.0 的 `source .env + curl` 路径，**不重试三次**，直接切
  3. 都不行 → write-only (写 `ALERT:` 到任务文件 + stdout 标注 `tg_failed`)
  **msg_id 怎么拿** (v1.7.0 新增): `hermes send` 默认不在 stdout 输出 message_id。两条路:
  - 跑 `hermes send --json` (如果该子命令支持) — 当前未实现，需用 curl fallback
  - **更简单**: 写完消息后查 `telegram home channel` 的最近 1 条 bot 消息 (需要 TG API `getUpdates` 权限) — 多数场景**不需要 msg_id**做溯源，v1.6.0 的"必回传"是 nice-to-have，不是 blocking
  **触发词**: "hermes send 能用吗 / cron 推 TG 最简方式 / 不想 source .env / hermes send vs curl" → 0 思考先 `hermes send` 试一发. **关联**: 推翻 v1.4.0 "不要用 hermes send" 的过激结论.

- **JSON 文件原子写入与容错 (v?.?.?)**: 为防止 `.stuck_alert.json`、`.last_watchdog_state.json` 因非原子写入或磁盘中断导致损坏，写入时应先写临时文件（如 `.stuck_alert.json.tmp`），完成后原子重命名（`mv temp target`）；读取时需捕获 JSON 解析异常，若失败则备份 corrupt 文件并重新初始化为空结构（如 `{}` 或预定义模板），以避免 watchdog 整条链条中断。

## References
- See `references/task-frontmatter.md` for detailed frontmatter specification.
- See `references/telegram-cron-push.md` for the env-sourcing recipe, chat_id variable names, and Python push snippet used in cron context (v1.6.0).
- See `scripts/check_gateway.sh` for a helper to verify gateway status.

## Changelog
- 2026-06-26: Initial creation based on watchdog cron task.
- 2026-06-28 13:31 (v1.5.0): Fixed step 4 (mtime → frontmatter `最后检查:`) + added stuck-alert de-dup (step 5 + new pitfall). Caught by 13:31 cron run: prior 11:32 run wrongly reported `stuck: 0` because file mtime was being touched by the watchdog itself. Real stall was 2h44m on `install_crawlers`.
- 2026-06-28 14:16 (v1.6.0): Corrected v1.4.0 Telegram pitfall — cron env has no `TELEGRAM_BOT_TOKEN` by default; real fix is `set -a; source ~/.hermes/.env; set +a` and try `TELEGRAM_HOME_CHANNEL` then `TELEGRAM_CHAT_ID`. Added `telegram_msg_id` capture & write-back to `.last_watchdog_state.json` for alert traceability. New reference file: `references/telegram-cron-push.md`.
- 2026-06-28 14:31 (v1.7.0): Revised v1.4.0–v1.6.0 "always use curl" stance — in this user's current setup (gateway up, default profile), `hermes send --to telegram "..."` is the simpler & more reliable path (exit 0 + stdout confirms chat_id). Added decision table: try `hermes send` first; on exit 1/2, fall back to `source .env + curl`; on both fail, write-only alert to task file. Also softens v1.6.0's "must capture msg_id" from blocking to nice-to-have. Reference file `references/telegram-cron-push.md` "Why not `hermes send`?" section is now stale — needs sync.