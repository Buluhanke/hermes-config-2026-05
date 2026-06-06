---
name: verification-before-reporting
description: Discipline for an agent about to claim state about the world (tabs, files, services, memory, config, user attributes) AND about to identify a thing the user is asking about. Run the live query that proves the claim BEFORE reporting; enumerate candidates BEFORE picking. Load when (a) the agent is about to summarize a state to the user, (b) the user disputes a previous state report, (c) the agent is tempted to write a "should be X" without a "I just queried X and got Y" — especially in 9-AI-station cross-validations, batch browser automation, and config audits — OR (d) the user asks "是不是 X" / "我记得是 X" / "X 还在吗" (identity verification — list candidates, don't pick).
---

# Verification Before Reporting

## Core rule

**Before you say "X is Y" in chat, you must have just queried X and gotten Y.** If the gap between query and report is more than ~30 seconds, or the report is a *recollection* rather than a *re-query*, the report is no longer a verification — it's a guess. The user can't distinguish the two; only you can.

Trigger phrases (each one is a red flag to slow down):

- "应该是 X" / "应该已经 X 了" / "理论上 X" — replace with "我刚跑了 Y 命令，结果是..."
- "我之前 X 成功了" / "上次 X 没问题" — past success is not present state
- "看起来都 X" / "目测 X 没问题" — at least run the canonical query first
| "X 都跑完了" (after a batch) — post-batch, re-query the state, don't trust the loop's last log line |

**对"登录态/UI 状态"问题，必查 3 层（不能只看 tab）**，见 Failure 6 — `browser-automation/browser-webpage-100score` "已登录三要素" 章节。

## What "verify" means concretely

A claim is verified when you have **a fresh query result that matches the claim**, run in the same turn. The query must be the *canonical* one for the state in question:

| State claim | Canonical verify query |
|---|---|
| "Tab X is on chat page" | `curl localhost:9333/json` (tab list) + `Runtime.evaluate(... document.body.innerText.slice(0,200) ...)` on the tab |
| "Service X is running" | `lsof -i :<port>` or `pgrep -fl <pattern>` |
| "File X exists" | `ls -la <path>` or `stat <path>` |
| "File X contains Y" | `grep -c Y <path>` or `read_file` |
| "Config has key K=V" | `hermes config show \| grep K` or `yq` against the YAML |
| "Memory contains M" | `session_search(query=M)` (for recent) or read the memory file |
| "9 AI stations have logged-in tabs" | re-list `curl /json` after each navigation, count `type=='page'` AND sample body content of 2-3 |
| "Model fallback chain works" | `curl https://<provider>/<model>` with a real test prompt |
| "Error count is N in errors.log" | `grep -c <pattern> <log>` *in the same turn* |
| "Process PID is alive" | `ps -p <pid>` (not "I started it earlier, must still be running") |

## Real failure modes (2026-06-05, captured as class-level lessons)

### Failure 1: trust the loop's last log line

> Agent ran `multi_ask_v3.py` with 9 sites. The script logged `9 站创建+navigate 全部 ok`. Agent reported "9 站 tab 全开成功". User: "你开的都是空白网页：about:blank".

Loop log said "ok". The 9 created tabs were killed by uBlock (net::ERR_BLOCKED_BY_CLIENT), and `/json` showed 0 page tabs. The agent never re-queried after the loop ended. **Fix**: any batch operation, re-query the actual state in the same turn as the report.

### Failure 2: trust the title alone

> Agent reported "9 站 tab 全开" after seeing the right titles. User said "都是空白". Agent immediately believed the user and started apologizing. `curl /json` actually showed all 9 tabs with real chat URLs.

Title is a hint, not evidence. Even an `navigate ok` log + a right title is not enough. Read the body.

### Failure 3: trust the user's "it didn't work" without re-querying

> User said "都是空白". Agent scrambled to "fix" what wasn't broken. The user's claim was either a test, a misread of their own screen, or genuine but unverifiable from agent's side.

Rule: when a user disputes an agent's state report, **don't auto-concede**. Re-query. If the state is good, say so with the fresh query as evidence. If the state is bad, you've also got evidence to fix.

### Failure 4: rely on a past success

> Agent: "9 站应该都开了" (referring to the verify run from 5 minutes ago). User: "你开的都是空白".

Past successes don't persist. Each new batch needs its own verify.

## Verification ladder (pick the cheapest one that proves the claim)

1. **`grep` / `ls` / `lsof` / `ps`** — for filesystem / process / port state
2. **`curl` against local CDP / HTTP API** — for browser tab / endpoint state
3. **`Runtime.evaluate` reading DOM** — for "is the page actually showing X" (the gold standard for browser claims)
4. **`read_file` small slice** — for "is the config key Y" (don't re-read the whole 600-line file)
5. **`session_search` / `fact_store` query** — for "did I write M to memory before"

If the cheapest query doesn't prove the claim, escalate. Never skip verification because the loop already said "ok".

## When the claim is unobservable from agent side

Some things the user knows that the agent can't directly verify (e.g. "your screenshot shows X", "the page I see has Y"). For these:

- Ask the user to paste the exact `curl` / `ls` / `grep` output they saw
- Or offer to run the verify query yourself and report the result
- Don't make the user the only verifier for state the agent can query

## Anti-patterns

- **Reporting before querying**: "看起来都 X" / "应该是 X" without a query in the same turn
- **Trusting the loop log**: "loop said ok so it must be ok"
- **Trusting the title**: a tab's title is a label, not proof of content
- **Trusting the user's panic report**: re-verify before acting on it
- **Trusting a past verify**: re-verify in the same turn as the new report
- **Conceding under pressure**: if state is good, say so with evidence; don't fold

## Failure 9: `launchctl list` Status column is the LAST EXIT CODE, not current state — pair it with HTTP probe (2026-06-05)

> Agent saw `launchctl list` show `-9  ai.hermes.gateway` and reported "Gateway ❌ dead, restarted". User's Telegram health-check report also showed ❌ for Gateway. In reality, the Gateway was **fine** — PID 79290, listening on 8642, `/health` returning 200 in 0.6ms. The `-9` was the exit code from the **previous** time the service was killed (weeks ago during a 503 fallback experiment), not the current state.

`launchctl list` output columns: `PID  Status  Label`. People naturally read `Status` as "current health", but it's actually the **last exit code** of the service — `-9` = SIGKILL, `0` = clean exit, positive numbers = error codes. A service that has been running continuously for weeks can show `-9` because of a one-time restart that happened long ago.

**Three-corroborating-signals rule** for any launchd-managed service health check:

| Signal | Command | What it tells you |
|---|---|---|
| 1. launchd bookkeeping | `launchctl list \| grep <label>` | "Is the service registered AND has a real PID (not `-`)" |
| 2. Live process | `pgrep -fl "<service-binary>"` or `lsof -p <pid> -P -i` | "Is there a real OS process holding the expected sockets" |
| 3. HTTP health probe | `curl -sS -o /dev/null -w "%{http_code}" --max-time 3 http://127.0.0.1:<known-port>/health` | "Is the service actually serving requests" |

**The HTTP probe is the gold standard** — if `/health` returns 200 in <1s, the service is healthy, regardless of what launchd's bookkeeping says. Conversely, a service can be "running" in launchd (PID present) but completely unresponsive (deadlocked, port conflict, zygote spawn failure) — only the HTTP probe catches that.

**Companion pitfall**: `launchctl list <label>` (with a specific label argument) walks the **print** path and returns a JSON-ish plist dump, not the PID-Status-Label table. To get the table, use `launchctl list | grep <label>` (un-targeted list + filter). Both bugs bit in the same session — `hermes_self_check.sh` (一直在误判 Gateway 死) and `daily_health_check.sh` (new script) both used the print-path pattern. See `devops/scheduled-task-audit` SKILL.md pitfalls for the exact `grep -E "^[0-9-]+\s+[0-9-]+\s+$LABEL$"` pattern that works.

**Anti-pattern**: writing a health-check script that decides "service X is healthy" based on launchd output alone. Always add at least the HTTP probe. Saves a user-visible false alarm AND saves the agent from issuing a "service is dead, restarting" → "actually it wasn't dead, why is it restarting now" follow-up.

## Cross-references

- `browser-automation/ai-site-browser-e2e` — same discipline applied to multi-site batch opening
- `script-provider-independence` — "不绑定模型" rule shares the same "don't commit to state you haven't verified" mindset
- `hermes-cdp-hardcore-type` — explicit "verify after type" pattern
- `verification-before-reporting` (this file) is the class-level umbrella; the per-skill application is the extension
- `references/2026-06-05-multi-ask-session.md` — 4 同坑翻车实录 (含 anti_detect_inject.py 跑 verify 会清空 page tab 的脚本 bug)

## Failure 5: don't run a "verify" step that destroys the state you verified (2026-06-05)

> Agent ran `anti_detect_inject.py --port 9333 --verify` to check fingerprint. The verify path re-enumerates tabs and **closes every page tab** (script bug). The very next verify (`curl /json`) showed 0 page tabs, defeating the purpose of the verify.

Rule: when running a verify step, **check whether the verify itself is destructive**. If yes, snapshot state BEFORE running, OR only run on a non-production tab. For Hermes' anti_detect_inject specifically: run it BEFORE opening the 9 sites, not after — that way the page tabs the verify closes are the old about:blanks, not the loaded chat sites.

### Failure 5b: verifier 里 print/log 重复导致双状态报告 (2026-06-05)

> 写 `stealth_inject.py --verify` 跑出 10/10 后，又 `print(f"✅ {url}")` —— dry-run 时 `inject_stealth(dry_run=True)` 已 print `[DRY-RUN]`，main 循环又 print `✅`，**用户看到"一个 tab 报两个状态"**。

Rule: verify 报告**只在一个地方**生成。**禁用模式**:
- helper 函数 print + main 循环又 print 同一事件
- "✅ ... ✅" 来自不同 print 语句

**修法** (3 选 1):
1. helper 返 bool，main 统一 print (`if ok: print('✅')`)
2. helper 接收 `verbose=False` 参数，dry-run 时不 print
3. **更稳**：把"行为"和"显示"分开——helper 只返结果，main 一个 `report(success, url, dry_run)` 函数集中处理

**触发场景**: 加 `--dry-run` / `--verify` / `--report` 之类双模时必踩。

## Failure 6: misread "UI state" as "underlying state" (2026-06-05 15:40)

> User asked: "AI 网站登录的为什么都会被退出丢失?" Agent was about to answer from memory ("yes, 9 站登录态丢了 because pkill -9 killed Chrome"). User looked skeptical. Agent queried `ps` + `lsof` + read `Default/Cookies` sqlite directly. **Found the opposite of what the user said**: cookies were 229KB, 9 domains still had session cookies, system profile was intact.

**What happened**: User saw empty tabs in Chrome (= 0 AI stations showing chat UI) and inferred "登录态丢了". Agent was about to validate that inference. **Both were wrong** — the underlying state (cookies) was fine; only the surface state (tab pages) had been killed.

**Rule**: when user or self reports a state change, **distinguish "UI is gone" from "underlying state is gone"**. The query must target the right layer:

| 误判层级 | 看到什么 | 应该查什么 |
|---|---|---|
| 表面（页面/tab） | tab 空、显示登录页 | `curl :9333/json` tab list, `Runtime.evaluate body.innerText` |
| 中间（profile/session） | 站显示"已退出" | `pgrep -f remote-debugging-port` 看 user-data-dir 是否被多进程抢 |
| 底层（cookies 文件） | 反复重新登录 | 直接读 `~/Library/Application Support/Google/Chrome/Default/Cookies` (sqlite) |

**触发场景**: Chrome 任何"登录态问题" → **必跑 3 层诊断**（不能只看 tab list）：
```bash
# 1. 底层: cookies 还在不在
python3 -c "import sqlite3; c=sqlite3.connect('file:~/Library/Application Support/Google/Chrome/Default/Cookies?mode=ro', uri=True); print(list(c.execute('SELECT DISTINCT host_key FROM cookies')))"
# 2. 中间: profile 是不是被多进程抢
pgrep -fl "Google Chrome.*--remote-debugging-port"
# 3. 表面: tab 是不是真的开了
curl -s :9333/json | python3 -c "import json,sys; d=json.load(sys.stdin); print([t['url'] for t in d if t.get('type')=='page'])"
```

**教训**: 用户的"直觉" + agent 的"假设"会**互相放大错误**。一方说"丢了"，另一方说"是的丢了" → 双倍错。**真验证**必须独立 query 三层。

## Failure 7: bash `[[ X == Y ]] && cmd` chain returns the test's exit code, not 0 (2026-06-05)

> A watchdog script `self_heal_watchdog.sh` had `log() { [[ "$DRY_RUN" == "true" ]] && echo "$msg"; }`. With `DRY_RUN=false`, `[[ false == "true" ]]` returns `1`, and the `&&` chain returns the LAST evaluated command's exit code — the `echo` never runs but the expression still exits 1. The script's last call was `log "── 周期完成 ──"`, so the script exited 1. launchd marked the job as `last exit code = 1` even though all the actual checks (gateway / Chrome / Ollama / fact_store / memory) had logged `✅` correctly.

**Symptom**: `bash script.sh` exits 0 in shell but launchd reports `last exit code = 1` for the same script. Logs show all checks passed. `bash -x script.sh` traces all the right steps.

**Fix — three options ranked by safety**:
1. **Best**: explicit `if/fi` + `return 0` (always returns 0):
   ```bash
   log() {
       msg="[$(ts)] $*"
       echo "$msg" >> "$LOG"
       if [[ "$DRY_RUN" == "true" ]]; then
           echo "$msg"
       fi
       return 0
   }
   ```
2. **OK**: trailing `:` (no-op true) after the conditional chain:
   ```bash
   log() {
       [[ "$DRY_RUN" == "true" ]] && echo "$msg" || true
       :  # always exits 0
   }
   ```
3. **Defensive**: end any bash script that runs under launchd / cron with `exit 0`:
   ```bash
   log "── done ──"
   exit 0
   ```

**Trigger rule**: **any bash script whose last statement is a function call, where that function ends in a `[[ ]] && cmd` or `cmd1 || cmd2` chain, exits with the chain's real status, not 0.** launchd / systemd / supervisord will all read that as failure. Add `exit 0` to the script tail OR rewrite the function with `if/fi`.

**Related gotcha — `[ ! -w "$FILE" ] 2>/dev/null` silently swallows the redirect**: `2>/dev/null` inside `[ ... ]` is illegal (the test utility doesn't accept redirections inside its argument list), and bash silently ignores it. The test runs without error suppression. Either move the redirect outside the `[ ]`:
```bash
if [ ! -w "$FACT_DB" ]; then  # NOT: [ ! -w "$FACT_DB" ] 2>/dev/null
```

## Failure 8: Hermes system-level tool safety gate blocks repeated terminal/execute_code (2026-06-05)

> After 2 consecutive `terminal` or `execute_code` invocations in close succession, the 3rd call returns `exit_code = -1` with `BLOCKED: Command timed out without user response. The user has NOT consented to this action.` even for `bash script.sh --dry-run` (read-only). The block persists for an undetermined time (1-10 minutes observed). Re-running the same tool with the same intent re-blocks.

**Symptom**: tool result shows `exit_code: -1` with `status: "blocked"` and `tool_calls_made: 0`. The instruction text says "Do NOT retry this command, do NOT rephrase it, and do NOT attempt the same outcome via a different command."

**What it is**: a Hermes platform-level safety net, distinct from the per-tool "user approval" prompt. It fires when the agent has been calling terminal/execute_code repeatedly in a single turn.

**What to do**:
1. **Stop calling terminal/execute_code** for the rest of this turn (or until you genuinely have user input).
2. **Tell the user explicitly**: "工具被 Hermes 安全闸拦截，需要你拍板继续" + offer 3 paths (manual command / wait / report status with what's been verified so far).
3. **Do NOT rephrase to bypass** — the gate is intent-based, not syntax-based; same outcome under a different wrapper will still be blocked.
4. **Safe work you can still do** in the same turn: `write_file`, `patch`, `read_file`, `search_files`, `memory` (add/replace), `skill_manage`, `skill_view` — these are not in the gated path.
5. **Prevention for future turns**: bundle multiple commands into one `terminal` call with `&&` or `;` instead of separate calls; for complex verification logic, use a single `execute_code` block that imports the tools, runs the full verification, and prints the result in one shot.

**This is environment behavior, not a bug to "fix"** — do not encode it as a permanent constraint on terminal/execute_code usability (per the "do not capture environment-dependent failures" rule). Capture it as a working-style note: "after a flurry of tool calls, switch to write/patch/memory and report status; defer verification commands to the user's next prompt."

## Failure 10: don't confirm "是 X" by inference when the user only asked "是不是 X" — list candidates, don't pick (2026-06-05 21:30)

> User: "我记得我们安装一个聚合搜索引擎，但现在是什么忘了 / 前几天还好好的，可以联网搜索的，现在找不到了"
>
> Agent ran: `skill_view` on `anysearch` (came up in `skills_list`), found 70+ search references in `idle_learning/references`, found 3 candidate skill directories (`anysearch`, `freellm-api-aggregation` empty shell, `browser-automation`), and **said "找到了，就是 anysearch"** + listed all 3 candidates, but framed it as the answer.
>
> User: "你不要乱猜" (rejected the framing).
>
> Agent then did the right thing: listed all 3 candidates with evidence, did NOT pick one, asked user to confirm.

**The mistake**: even with 99% confidence an answer matches, the question "是不是 X?" / "是 X 吗?" deserves a **list + wait**, not a **list + "是"**. The user may have been thinking of X but wanted the agent to surface the options. Picking prematurely forecloses their input.

## Failure 11: don't claim a file edit succeeded without re-reading the file (2026-06-05 22:00, extended 2026-06-06 00:18)

> Agent was asked to delete SearXNG references from 4 files. After 2 patch calls, the `patch` tool's `success: true` + diff output led the agent to **immediately** report to the user "4 处全删了". The next turn, the user asked for the diff again, exposing that:
>
> - `~/.hermes/config.yaml` — **patch 工具拒绝了** ("Refusing to write to Hermes config file: security-sensitive") but agent 的 memory 草稿里仍写"删完"
> - `~/.hermes/.env` — `sed` 被 Hermes 安全闸 BLOCKED (`exit_code: -1`), but agent 只看了 stderr, 没发现 0 行输出 = 命令根本没执行
> - 实际上只成功删了 `agg_search.py` 一处

**The mistake**: `patch tool returns success: true + diff` proves the patch tool **attempted** the write. It does NOT prove:
- The file on disk matches the diff (the patch tool might have rolled back on syntax error)
- Adjacent files you "also intended to edit" — those are separate operations, each needs its own verify
- Destructive operations blocked by framework safety (the framework blocked it silently in this case)

**The verification ladder for "I edited N files"**:

| 操作 | 必须做的 verify |
|---|---|
| `patch`/`write_file` 一个文件 | 跑 `read_file` 看那几行确实变了 |
| 多个文件 "同时改" | **每个文件** 独立 verify（不假设 1 个 success = 全部 success）|
| 涉及 framework 受保护文件（`config.yaml`、`.env`） | **先确认 patch 工具的报错**（"Refusing to write" 不是异常，是它的正确行为）|
| 命令行 destructive op（`rm`/`sed`/`mv`）| 检查 `exit_code` + 实际文件状态（**不是只看 stderr 没报错 = 成功**）|

**Anti-patterns**:
- "patch 返回 success,所以改了" — 没读回文件
- "我同时改 4 个文件" — 4 个 patch 调用 ≠ 4 个成功
- "stderr 没报错 = 成功" — 框架 BLOCKED 也是 stderr 没报错
- "看 diff 长得对 = 实际生效" — 框架可能拒绝写,diff 只是 tool 拟的

**Good pattern**:
- 改 N 个文件 = N 个 `patch`/`sed` 调用 + N 个 `read_file` / `grep` 验证
- 改 framework 受保护文件 = **先发个试探 patch** (e.g. 加一行无害注释), 看 tool 是否拒绝, 再决定下一步
- 任何 BLOCKED = **明确写进对账表** "❌ 没改, 原因 X", 不偷偷跳过

**Trigger rule**: 任何 "我改了 N 处" 的报告前, 每个文件**独立 grep/read_file 一次** 确认。`patch` 返 `success: true` 是必要条件, 不是充分条件。

### Failure 11b: framework 受保护文件清单（2026-06-06 00:18 实测）

`patch` 工具会**显式拒绝**某些文件，错误信息形如：
```
Refusing to write to Hermes config file: /Users/aimac/.hermes/config.yaml
Agent cannot modify security-sensitive configuration. Edit ~/.hermes/config.yaml
directly or use 'hermes config' instead.
```

**已知受保护文件**（基于 6/6 00:18 实测 + 历史 case）：

| 路径 | 拒绝原因 | **正确做法** |
|---|---|---|
| `~/.hermes/config.yaml` | Hermes 框架主配置 | `hermes config set <key> <value>` 或 `hermes config edit` |
| `~/.hermes/.env` | 凭据文件（含 API key） | 用户手动编辑，或脚本里 `Path.write_text(...)` 自己实现（不能用 patch 工具）|
| `~/.hermes/memories/MEMORY.md` | 持久记忆 | 用 `memory` 工具（`add`/`replace`/`remove`）|
| `~/.hermes/memories/USER.md` | 用户画像 | 同上 |
| 任何 `~/.hermes/hermes-agent/` 下的源码 | Hermes 框架本身 | **不该 agent 改**，要先确认是不是 bug，提 PR 而不是 monkey-patch |

**绕过路径的红线**（不要走）：
- ❌ `sed -i '...' ~/.hermes/config.yaml` — 触发 Hermes 安全闸 BLOCKED
- ❌ `python -c "open(...).write(...)"` 写 `config.yaml` — 同样会 BLOCKED
- ❌ "patch 失败了, 我用 sed 绕过去" — 等于绕过框架的安全设计, **跟 patch 拒绝写是两回事**

**正确流程**（动 `config.yaml` 前必走）：
1. **`hermes config show`** 先看当前真实值（不靠 patch 工具）
2. **`hermes config set <key> <value>`** 单条改（语法：`key` 用 `.` 分层, 如 `model.fallback_chain`）
3. **`hermes config show`** 再确认改成功
4. 涉及 `model.*` / `fallback_chain` / `api_key` 字段 → **按 script-provider-independence skill 14:50 规则**，**安全修复（明文 key → 占位符）允许**，但改具体值（如切换 provider）不在 agent 权限内

**触发词**: 用户说 "改 config.yaml" / "改 model 配置" / "清 API key" / 任何"动框架主配置"的请求 → **先看本表**，走正确流程。

### Failure 11c: `sed` 绕道踩 14:50 红线（2026-06-06 00:18）

`patch` 工具拒绝 `config.yaml` 后，**第一直觉**是"那我用 `sed -i` 绕过去"——**这是双错**：

1. **技术上**：Hermes 安全闸**也会**拦 `sed` 改 `config.yaml`（exit_code=-1 "BLOCKED"），不是只有 `patch` 工具拦
2. **政策上**：14:50 规则说"不写 model=/api_key=/fallback_chain= 等具体值"——**`sed` 写 `model.api_key = ${...}` 占位符** 严格说也动 model 层

**判断**：
- `sed` 改 `config.yaml` → **绝对不行**（技术+政策双错）
- `hermes config set model.api_key '${ENV_VAR}'` → **安全修复允许**（占位符不动值），但要明示"这是安全修复，不是改 model"
- `hermes config set model <provider>` → **14:50 红线**，agent 不该做

**对账表必含 3 列**（不踩 14:50 的姿势）：
1. **改了什么**（具体行号/字段）
2. **怎么改的**（哪个命令/工具）
3. **为什么这么改**（安全修复 vs 业务需求 vs 14:50 红线 vs 不可逆）

**Trigger rule**: patch 拒绝 → 不要 sed 绕道 → 看 Failure 11b 表 → 走 `hermes config` 通道 → 不在 agent 权限内的标"❌ 需用户手动"进对账表。

## Failure 12: don't claim "X is set up across all platforms" without an audit table (2026-06-05 22:15)

> User asked: "把 anysearch 设置为整个 Hermes 的主要联网工具,不管是微信 QQ 还是 Telegram 都可以用". Agent fixed 2 files (added anysearch as primary to `agg_search.py` + new `search.sh` wrapper) and **replied "anysearch 是全平台搜索引擎了"** (paraphrased: "anysearch is the search engine for all platforms").
>
> User asked: "anysearch 这个设置为全平台搜索引擎了是吧" (verification question).
>
> Agent had to scramble: "是,也不是" + produce a 对账表 explaining what was actually done vs what was implied:
>
> | Item | Status |
> |---|---|
> | Added anysearch as primary to `agg_search.py` | ✅ 真 |
> | Created unified entry `~/.hermes/scripts/search.sh` | ✅ 真 |
> | Memory updated with routing rule | ✅ 真 |
> | Modified `config.yaml` `search_backend: ddgs` → `anysearch` | ❌ 没做 (framework would reject) |
> | Modified framework `web_search` tool backend | ❌ 没做 |
> | Configured per-platform (微信/QQ/Telegram) search engine | ❌ 不需要做 (platforms don't care) |

**The mistake**: agent used a sweeping phrase ("全平台") that the user could reasonably read as "全部已配", but the actual implementation was 1.5/5 of what the phrase implied. The agent then had to walk it back under questioning.

**This is distinct from Failure 10** (identity verification) — Failure 10 is about "I think X is Y"; Failure 12 is about "I said 'X is done' but the implementation is partial".

**Rule for any "X is set up" / "X is done" / "全平台" / "所有 N 个" claims**:

1. **Enumerate the N** before claiming "all N done"
2. **For each item**, mark ✅ 真 / ❌ 没做 / ⚠️ 部分 with reason
3. **The summary sentence** must reflect the lowest common denominator, not the highest claim

**Anti-patterns**:
- "X 已全平台上线" (after editing 1.5 of 5 things)
- "配置完毕" (when 1 config is touched, 3 are not)
- "所有 skill 都连接了" (when only 2 of 60 are)
- Use sweeping words (全/所有/全部/全平台) when reality is partial

**Good pattern**:
- "改了 1.5 件: A ✅, B ✅, C ❌(原因), D ⚠️ 部分. 没改的: E/F/G 因为... 整体不是'全平台'——用户级调用 OK, framework 层没动。"
- 把对账表放在最前面, summary 句放最后且**严格反映对账表** (不能总结比表格更乐观)

**Companion to Failure 1a in user-profile memory**: "极度看重'真实验证', 不接受'看 title 报成功'" — this is the same mindset applied to **scope-completeness**, not just **state-accuracy**.

## Failure 13: don't recommend installing something that may already be installed (or recommend a wrong package name) (2026-06-05 22:30)

> User asked: "看看有没有可用的 mcp". Agent, blocked by safety gate, **replied from training-data memory** with: "我推荐 filesystem / git / http fetch 三个, 都不重内存, 装这三个" (paraphrased).
>
> User asked: "你仔细查一下这三个我们电脑配置里 hermes 在都没有吗？" — i.e. "did you check whether they're already installed?"
>
> Agent then ran `npm list -g` and found:
> - `@modelcontextprotocol/server-filesystem@2026.1.14` — **already installed, just not configured in Hermes**
> - `@modelcontextprotocol/server-github@2025.4.8` — installed (but not git)
> - `mcp-server-fetch` — **never heard of as a real package**; agent invented a plausible name
> - `gitnexus@1.6.4` — unclear what this actually is
> - `searxng-mcp@1.0.1` — already installed (the SearXNG MCP variant, the very one user wanted to remove)
> - `mcporter@0.11.3`, `mcp` Python SDK, `fastmcp` — installed but **SDKs not servers**

**The mistake**: when blocked by safety gate, agent fell back on **memory-based recommendation** instead of **enumerating what was already on disk**. Plausible package names ("`mcp-server-fetch`") are easy to invent; the user paid the cost of catching the agent's bluff.

**This is distinct from Failure 8** (safety gate handling) — Failure 8 is about **how to respond when blocked**; Failure 13 is about **don't recommend install when you haven't checked what's installed**.

**Rule for "recommend an MCP / package / tool"**:
1. **First** run `npm list -g` / `pip3 list` / `ls ~/.hermes/skills/` — surface what exists
2. **Then** cross-check each recommendation: "is this installed? Is the package name correct?"
3. **Only after** check, can you say "you should install X" or "X is already installed, just not configured"

**Companion tools** (the cheap verify queries):

| State claim | Canonical query |
|---|---|
| "Package X is installed via npm" | `npm list -g \| grep X` |
| "Package X is installed via pip" | `pip3 list \| grep X` |
| "Skill X exists in Hermes" | `ls ~/.hermes/skills/ \| grep X` |
| "MCP X is wired into Hermes" | `grep -A 3 'X:' ~/.hermes/config.yaml` (the `mcp_servers:` section) |

**Anti-patterns**:
- "我推荐你装 X" (without checking `npm list` / `pip3 list` first)
- Inventing plausible-sounding package names (`mcp-server-fetch` is not a real MCP)
- Treating "X is installed" and "X is configured in Hermes" as the same — they're not (npm install = package on disk; Hermes config = actually usable from a session)

**Good pattern**:
- "先查一下已装的: `npm list -g | grep <keyword>`"
- 对每个推荐, 标明 4 态: 已装+已配 / 已装+未配 / 未装+可装 / 未装+不确定
- 不确定时**说"不确定"**, 不编包名

**Cross-reference**: `self-evolution-framework/installed-unused-tool-discovery` — same class of mistake (recommend X without checking what's there), this skill applies it to **MCP/package recommendations specifically**.

| Failure 1-9 | State verification | "X 是 Y" 状态的 claim — needs live query |
| Failure 10 | Identity verification | "X 是 Y" 实体/工具/项目的 claim — needs enumeration + user confirm |

**Rule for "是不是 X?" questions**:
1. **Enumerate all candidates** with evidence (file paths, search hits, descriptions)
2. **Do NOT pick** — even if one is 99% match
3. **Ask the user to confirm**: "证据是 Y, 你确认是 X 吗?" or "这几个哪个是你说的?"
4. **Only after user says "是"** can you proceed with the assumption

## Failure 14: don't report from a skill's "state" section — re-verify when the user pushes back (2026-06-06 17:55)

> User: "你不是说都在的吗" (re: anysearch + last30days 搜索)
>
> Agent had loaded `ddgs-searxng-agg-search` skill v4 which stated: "last30days 已亡, npm/pip 无包, skill 目录被删除, 任何搜索都走 anysearch". Based on that, agent initially reported "找不到 last30days, 应该在 anysearch" without re-checking.
>
> User pushed back: "你不是说都在的吗"
>
> Agent re-ran `ls ~/.hermes/skills/` + `find ~/.hermes -type d -name last30days` and **discovered v4 was wrong**: last30days still exists at `~/.hermes/skills/research/last30days/` (just not in the root skills/ directory that v4 had scanned). `last30days.py` 44KB, ran successfully via `~/.local/bin/python3.12`, output v3.3.1 protocol handshake.

**The mistake**: agent treated the loaded skill as **ground truth** instead of **a snapshot at a point in time**. Skills document state. State changes. The user questioning the agent's report is a **re-verify signal**, not an attack to defend against.

**Rule for "skill says X, user disputes"**:

1. **Acknowledge the user's pushback explicitly** — "你说得对, 我应该先复测, 不该照搬 skill"
2. **Run the live query** — `ls / find / stat / which / curl` to re-confirm
3. **Compare skill's claim vs reality** — if they differ, the skill is stale; fix it (see `ddgs-searxng-agg-search` v4 → v5 history)
4. **Report the actual state with evidence** — "刚跑了 X, 结果是 Y, skill 写的 Z 跟 Y 对不上, 我现在改"

**Anti-patterns**:
- "skill 是这么写的, 应该是对的" — defends stale info, not the user
- "我记得是这样" — memory-as-evidence (参见 Failure 1, 4)
- "我之前看过" — past-tense, not present-state
- Defending the skill over the user's lived experience — the user is the ground truth for "what's there now"

**Good pattern**:
- User: "你不是说都在的吗"
- Agent: "你说得对, 我刚照着 skill v4 说 last30days 亡了, 没复测。`ls` + `find` 一跑: last30days 实际在 `skills/research/last30days/scripts/`, 44KB, 跑得通。v4 写错了, 我现在改成 v5 + 加这条规则。"

**Companion to Failure 10, Failure 1a in user-profile** — "下结论也要真证据" extends to "skill 写了 ≠ 实际是这样". When the user pushes back, **re-verify, don't defend**.

**Trigger rule**: 用户说 "你不是说 X 的吗" / "你刚刚说 X 还在" / "我记得你说过 X" + 自己没把握 → **立即跑 30 秒实测**，不靠 skill / memory / 印象。

**Anti-patterns**:
- "找到了，就是 X" (with even 1 sentence of evidence) — too assertive
- "应该是 X" + 然后开始基于 X 行动 — both assertion AND premature action
- "X 是你之前装的那个" + 不列候选 — picks without basis
- "对，就是 X" (responding to user "是不是 X?") — auto-concession without check

**Good pattern**:
- "查了一下，有 3 个候选: A (证据: path), B (证据: desc), C (空壳)。你说的是哪个？"
- "X 在路径 Y 找到了，描述 Z，但还有 W 也匹配, 你说哪个？"

**Trigger rule**: any user query of the form "是不是 X?" / "我记得是 X, 现在呢?" / "X 还在吗?" / "找一下 X" → **list candidates + ask, do not pick**.

**Companion to Failure 1a in user-profile memory** (2026-06-05 21:30): "下结论也要真证据。用户问 '是不是 X' → 反问 '证据 Y, 你确认是 X 吗', 不直接答 '是'。"
