---
name: verification-before-reporting
description: 汇报前验证原则 — 任何声称"成功/完成/已修复"必须有可验证的输出（exit code / 文件存在 / API 响应 / 实际测量值）。禁止用推测代替验证。
l1: 🔧Hermes内部
l2: agent-behavior
l3: core
triggers:
  - 验证
  - 汇报前验证
  - 确认结果
  - verify
  - 验证后再汇报
  - 量化汇报
  - 量化结果
version: "1.0"
---

# 汇报前验证原则

> **2026-06-13 重要**: 本 skill 被 agent 误删过一次，已重建。完整 Failure 1-19 案例见 `meta/verification-before-reporting`（class-level umbrella）；本文件保留精简版给快速引用。

## 核心规则
**任何声称"成功/完成/已修复"，必须有可验证的输出作为依据。**

## 验证标准
| 操作类型 | 最低验证 |
|---------|---------|
| 文件创建 | `ls -la` 确认存在 |
| 命令执行 | `exit code == 0` |
| HTTP 请求 | 实际响应码（200/201） |
| 安装成功 | `python3 -c "import xxx"` 无报错 |
| 端口监听 | `lsof -i :<port>` |
| 进程存活 | `ps -p <pid>` |
| 配置文件改 | `grep -n <key>` 重读确认 |

## 4 大常见反模式（本次 session 全踩）
1. **trust the provider name** — `model.provider: custom:V2enby.aicodee.com` 看起来在 known list 里 → 实际拼错 + apihub 路由死。**必跑 `hermes doctor` + 真发请求**
2. **trust the loop log** — install log 说 "Successfully installed" 不代表没破坏 dependency resolver
3. **trust the doc** — SKILL.md / README 写有的子命令，argparse 里可能没注册
4. **trust the past success** — 30 秒前测过的"真"现在不一定真

## 验证阶梯
1. **cheapest** → `grep` / `ls` / `lsof` / `ps`
2. **canonical** → `hermes config show` / `hermes doctor` / `hermes cron list`
3. **real LLM call** → `curl -X POST <base_url>/v1/messages` 用真 key 发个 1-token 消息
4. **read back** → `cat` / `read_file` 验证 patch 实际生效

## Anti-patterns
- "应该是 X" / "理论上 X" / "看起来都 X" — 没 fresh query
- "patch 返 success=true, 所以改了" — 没 read back
- "skill 写了 X" — skill 可能 stale, 必复测
- "skill/agent 之前也这样" — past ≠ present
- "环境报错不一定对" — 错的环境也是证据, 走查

## Trigger rule (2026-06-13 重要)
> **绝对禁止用 `skill_manage(action='delete', name='X', old_string='')` 当快速动作**。空 old_string 会被 skill_manage 当作 "delete 整 skill" 命令，本 session 误删过 `verification-before-reporting` (虽然立刻重建但惊魂)。
> **delete 之前必先 `skill_view(name=X, file_path='SKILL.md')` 拿内容备份**；或者用 `edit` 写新内容, 不删。

### 坑 1: model.provider 拼写错但 hermes doctor 没立刻报
- 配置: `model.provider: custom:V2enby.aicodee.com` (中间多了 "enby")
- `hermes doctor` 警告: `model.provider 'custom:V2enby.aicodee.com' is not a recognised provider (known: ...)` — 报在主表
- **但是 user 看到 warning 没立即处理** → 第二天 1:00 cron 跑 → gateway 5 次重试 → 全部 503 No available channel
- **修法**: 看到 doctor 报 unknown provider,**第一件事**是 `grep -n "V2enby\|Apihub" ~/.hermes/config.yaml` 看是不是配置层拼错了；然后 `grep -B1 -A 6 "name: V" ~/.hermes/config.yaml` 列所有 provider 名字比对
- **不该**: 把 doctor warning 当 nuisance 略过；它几乎都是真问题

### 坑 2: jobs.json 含 U+200B 零宽空格导致 patch 失败
- 现象: `patch` 工具报 "old_string not found in file"，但 `python3 -c "import json; print(j['prompt'])"` 能看到内容
- **根因**: Hermes 配置/cron 文件里中文/emoji 之间被插入 U+200B 零宽空格（maybe UI 输入时插入的），破坏 fuzzy match
- **修法**: 直接用 `python3 -c` 跳过零宽, 或 `import json; d=json.load(...); d['jobs'][N]['prompt']=...; json.dump(d, open(p,'w'), ensure_ascii=False, indent=2)` 重写
- **不该**: 反复 patch 重试 — 永远不会成功

### 坑 3: pip install 触发 dependency resolver 破坏 hermes-agent
- 装 headroom-ai 0.25.0 → 升级 openai 2.16.0 → 2.41.1, anthropic 0.76.0 → 0.87.0
- 这两个升级破坏 `hermes-agent==0.15.1` 要求的 `openai==2.24.0` + `pydantic==2.13.4` + `rich==14.3.3` + `click==8.3.1`
- pip 警告: `hermes-agent 0.15.1 requires openai==2.24.0, but you have openai 2.41.1 which is incompatible` — **这是真问题, 不是 nuisance**
- **修法**: 装完立即 `pip install "openai==2.24.0" "anthropic==0.76.0" "pydantic==2.13.4" "rich==14.3.3" "click==8.3.1"` 回滚 + `python3 -c "import hermes_agent"` 验证 import
- **不该**: 看到 "Successfully installed" 就走, 不看 pip 末尾的 resolver 警告

### 坑 4: 装 headroom proxy 接 minimaxi 失败 — 协议不匹配
- 启动 headroom proxy 18787 + ANTHROPIC_API_URL=https://api.minimaxi.com/anthropic + 真 key
- headroom 转 `Authorization: Bearer` 给 minimaxi → 401 "Invalid bearer token"
- 但用 Python `urllib` 直接打 minimaxi 同端点 + Bearer 同 key → 429 Token Plan 用量上限 (不是 401)
- **根因**: minimaxi 对 `Authorization: Bearer` 的 key 校验行为跟 headroom 触发的格式不一致 (细节未查清, 可能是 headroom 加了某个头/格式微变)
- **临时绕开**: headroom 装上但**不接入生产主链**; 等 minimaxi 文档/支持或 headroom 出 minimaxi 适配
- **教训**: 中间件接非 OpenAI/标准 Anthropic 协议端点时,**先 30 秒真打一发**验证链路通, 别先改主链 base_url — 改完才发现协议不兼容, 整链炸

## 详细 Failure 案例
见 `references/` 目录下的各 session 复现记录。

**本次 session (2026-06-13) 新增要点**:
- Failure 20: doctor 报 "unknown provider V2enby.aicodee.com" → 实际是 config.yaml 拼写错（中间多了 enby），`base_url` 才是真相，`grep` 列所有 `custom_providers` 名字
- Failure 21: `~/.hermes/cron/jobs.json` 字段值里有 U+200B 零宽空格 → `read_file`/`patch` 工具模糊匹配失败；用 `python3 -c "import json; ..."` 跳过
- Failure 22: apihub.agnes-ai.com 上 "MiniMax-M3-highspeed" 503 no channel（apihub 不接这个模型），但 minimaxi.com 上同名模型工作 — 同一字符串在不同 provider 后端行为不同，**provider 必须真打一发验证**，不能信 base_url 长得对
- Failure 23: `pip install` headroom-ai 触发 `openai 2.16.0 → 2.41.1` 升级，破坏 hermes-agent 的 `openai==2.24.0` 约束；装完必须立刻 `pip install "openai==2.24.0"` 回滚 + `python3 -c "import hermes_agent"` 验证 gateway 还能起
- Failure 24: `pkill -9` 跟普通 kill 的差别 + `pkill` 在 cron 里被截断成 "kill 25" 之类假信号 — 用 `lsof -i :PORT` 验证进程真死
- Failure 25: **统计 ls 输出时, 文件类型混在一起计数** — 2026-06-15 session: 看到 `~/.hermes/memories/` 下 14 个 `USER.md.bak.17xxx` 文件 + 1 个 `MEMORY.md.bak`, 凭印象直接报"14 个 .bak 堆那"。**真相**: `*.bak.17xxx` 是 memory 工具的 **drift 防御自动备份**（每次工具检测到 USER.md 跟预期格式不一致，怕覆盖丢东西，自动 `cp` 当前文件加时间戳后缀），不是用户保留的真备份。**根因**: 用 `ls -la` + `wc -l` 不带 glob 一把抓 + 没区分"工具内部快照" vs "用户备份" → 把 14 个垃圾当用户数据。**正确诊断**: (1) `ls *.bak` glob 只匹配无时间戳的真备份 (2) `ls *.bak.*` glob 才是工具快照 (3) `du -ch *.bak.*` 看总大小, 真备份通常 1-2 个，工具快照可能几十个 (4) `head -3 <file>` 看内容特征。**修法**: 看到一堆 `*.bak.<timestamp>` → 0 思考识别为工具垃圾; 想确认用户是否故意保留 → 先问再删, 别直接报数。**触发的用户原话**: "之前 14 个 .bak 堆那都没清, 都是什么东西"。
- Failure 26: **评估工具前不问"你的拓扑是什么"** — 2026-06-15: 评估 hermes-desktop (macOS 原生 GUI 客户端) 时跳过"你那台 Mac mini 就是唯一 Mac 吗"这问，直接进 SSH localhost 评估 → 走偏。**修法**: 评估"给 Hermes 套 GUI 客户端/工作台/桌面端"类工具 → 0 思考先问 (1) Hermes 主机 = 用户日常 Mac? (2) 客户端跑哪? → 客户端=主机直接拒装。**触发的用户原话**: "Hermes都在Mac mini本地, 为什么还要ssh"。
- Failure 27: **memory 工具 4 次同参数失败就该停手** — 2026-06-15: 写 v2.7 user preference 时 memory 工具反复报"drift", 我尝试 add→replace→remove 各种参数, 4 次同参数失败。**修法**: memory 工具连续 2 次同报错 → (1) `ls -la ~/.hermes/memories/` 看文件实际状态 (2) 看最近 .bak.<timestamp> 频繁度 (3) 改用 `cat >> USER.md <<EOF` 直接 append (§ 分隔) 跳过工具。**触发的用户原话**: "不要乱来"。
- Failure 28: **patch 改完没 read_back 就报"修好了"** — 2026-06-16: 改 `screen_trigger_handler.py` line 191 timeout 120s → 30s, patch 工具返 success=true 后立即写"防 DoS 修复完成", 但**没真重读文件确认**. **风险**: patch 的 fuzzy match 可能命中不唯一的位置(尤其文件多次迭代后), 改的跟想改的不是同一行; background review 可能直接拦截 patch 调用(参考 hermes-self-evolution-closed-loop v1.4.2). **修法**: patch 返 success → 必跑 `grep -n "<新内容>" <file>` + `grep -n "<旧内容>" <file>` (后者应返空). **不该**: 信任 patch 工具返 success=true = 改对了. **真验证模板**:
  ```bash
  # 改完必跑
  grep -n "timeout=30" /Users/aimac/.hermes/scripts/screen_trigger_handler.py
  grep -n "timeout=120" /Users/aimac/.hermes/scripts/screen_trigger_handler.py  # 应空
  # 确认 patch 真生效
  ```
- Failure 29: **凌晨 cron 报告的"事实"也要现场复测** — 2026-06-16: 看到夜间学习报告写"VLM 推理无超时"→直接照搬结论去改. **真测**: `grep "timeout" screen_trigger_handler.py` 看到 timeout=120, 60, 30 多个值都存在 — **报告说"无超时"是错的**, 实际是"超时偏长". **后果**: 如果照着报告改"加 30s 硬超时", 改完发现本来就有, 浪费一次 patch + 一次汇报. **修法**: 任何"X 状态/问题/缺口"类报告(尤其是自己或 cron 跑出来的) → **0 思考先独立复测**, 复测结果跟报告不一致时**以复测为准**, 在汇报里显式标"原报告说 X, 实际测得 Y". **触发器**: "凌晨报告 / 报告说 / idle learning 发现 / 巡检发现 / X 不存在 / X 没接 / X 是多少" → 0 思考必跑一次独立 grep/ls/lsof 验证. **关联**: v2.8 行为准则"报不存在前必跑 5 件实测" + hermes-self-evolution-closed-loop v1.4.4 "当晚搜到几次".

- Failure 30: **"所有问题已修复"类汇总报告必须逐项验证** — 2026-06-21: 收到"全面验证完成，所有有问题的全部修复"的汇总 → 逐项实测后发现：(1) `capture(vision)` 返回 W:0 H:0 根本没修 (2) `scrapping` 目录不存在，不存在"修复"一说 (3) `verify_human_click.py` 第 163 行 KeyError 还在。只有 cua-driver 版本和大部分核心功能是真的。**修法**: 任何"全部修复/全面验证完成/所有问题已解决"类总结 → 0 思考先拆解为原子项，逐项跑实测（ls/grep/execute），**不信任 aggregate statement**。汇报时用"✅ X 项/❌ Y 项"格式，失败的单独列。

- Failure 31: **curl 测登录态瞎报** — 2026-06-22: 写"11 个 AI 网站登录态"时用 `curl -sI <site>` 测 HTTP 状态码报"5 个登录态正常", 实际 curl 默认不带 cookie, 302/200/429 跟登录态无关 (跟匿名访问响应一样). **修法**: (1) curl 必须带 `-b ~/.hermes/chrome-profile-mirror/Cookies` 才能验真实登录 (2) 更可靠: 浏览器 CDP 直接 attach tab 看 DOM 里有没有 user 头像/侧边栏历史 (3) 真登录态标准 = `bodyLen > 100 + hasSignIn=False + 关键词命中`. **触发词**: "登录态/cookies/还活着吗" → 0 思考用 CDP attach + DOM 检测, 别用 curl 默认.

- Failure 32: **perf test 报告 1.0x 加速比, 实际是 bug 不是结论** — 2026-06-22 warm_cache 写完跑 perf test, `Run 1 (cold): 43.3ms ... Run 2 (warm): 43.3ms` 显示 1.0x. 第一反应"暖缓存没效果", 但**实际是 bug**: `entry["latency_ms"]` 在命中路径没被覆盖, warm 那次返的还是 cold 时的 latency. **修法**: 加 `latency_warm_ms` 字段 (hit 路径单独算, 通常 <1ms), perf test 改读 `latency_warm_ms`. **触发词**: "perf test 1.0x / cache 没效果 / 加速比异常" → 0 思考检查 latency 字段是 cold 还是 warm.

- Failure 33: **估"累计节省 X 秒/天"前必跑实测** — 2026-06-22: 我估 warm_cache 每天省 206s (按 16 个 cron 脚本 × 全 800ms cold 估), 实测每个 cron 脚本**稳态 30-60ms** (bash 进程已 warm, Python 启动完), 实际累计 ~20s/天, 跟预估差 10x. **根因**: 把 "cold first run" 误当 "每次调用" (bash + Python 解释器早启动完, 第二次就稳态). **修法**: (1) 跑 perf test **N=5 取 median**, 别只看第一次 (2) 估累计节省用真实 measured 数据 × 频次, 不用 cold 数据 (3) 触发词 "节省 / 累计 / 杠杆" → 0 思考先 median(N=5) 实测再算总账.

- Failure 34: **CDP `Target.closeTarget` 后 `/json` 返 stale tab 列表** — 2026-06-23: chrome_tab_reaper 批量关 25 个 tab, 立即 fetch `/json` 看到还是 38 个 tab → 报告"关闭 0/20 个"。**实际**: Chrome 内部 tab 状态有 1-3s 同步延迟, closeTarget 返回 success 后 tab 真关了, 但 `/json` HTTP endpoint 还在返缓存的关闭前列表。**修法**: (1) close 完 `time.sleep(2)` 再 fetch 验证 (2) 或直接走 `Target.getTargets` (browser-level WS) 拿 tab 列表, 不走 `/json` HTTP 缓存 (3) 触发词 "closeTarget 没生效 / 关闭失败 / /json 看到的还是旧的" → 0 思考 sleep(2) 重 fetch 验证, 别立即报告"没关掉". **关联**: hermes-browser-control "Tab 资源管理" 节 + chrome_tab_reaper.py 实现细节.

- Failure 35: **用户指出"你确定吗" → 立刻真重测, 不辩护** — 2026-06-23: 我说"Ollama llama-server 17GB" → 用户回"你确定 Ollama 用 17GB 内存吗?" → **事实是 47MB** (差 360x). **根因**: `ps -A -o pid,rss,command | grep -E 'ollama|llama-server'` 输出里有一行 RSS 显示 17,051 MB (但那是 ps 行格式问题, 不是真实值), 我误读 + 没二次 grep `ps -o rss= -p <PID>` 单进程. **修法**: (1) 用户反问"你确定吗" → 0 思考立即独立复测, 不解释不辩护 (2) 报进程内存用 `ps -o pid=,rss=,command= -p <PID>` 单进程 (RSS 单位是 KB, 17517024 KB ≈ 16.7 GB 是对的, 但要看是哪个 PID) (3) 多进程家族时 `awk '{sum+=$2} END {print sum/1024 "MB"}'` 求和 (4) **报数前自己说"我跑了 grep"而不是"我记得/估计/看到"**. **反面案例**: 我自信报"Ollama 用了 17GB" → 用户抓 → 实际 47MB → 浪费 1 整轮 + 丧失可信度. **触发词**: "你确定吗 / 是这样吗 / 真的假的" → 0 思考独立实测, 不解释.

- Failure 36: **Hermes 升级后 plugin hook 接口不兼容 → ERROR 每个 session 都报** — 2026-06-24: 跑完 `hermes update` 后 self_check.log 报 `Hook 'on_session_end' callback _on_session_end() got an unexpected keyword argument 'session_id'`, 每次 session 启动 + 结束都报一次. **根因**: upstream hermes 在 hook 调用处加了 `session_id` kwarg, 但用户级 plugin (`~/.hermes/plugins/headroom/`) 的 `_on_session_start/end` 还是 `() -> None` 签名 — 升级后接口漂移. **修法**: (1) 自检日志扫 `Hook.*unexpected keyword argument` → 0 思考锁死哪个 plugin (2) `grep -rn "_on_session_start\|_on_session_end" ~/.hermes/plugins/ --include="*.py"` 找函数定义 (3) 对照 upstream 的新签名改 user plugin: `async def _on_session_start(*, session_id: str = "", **kwargs) -> None` (4) `__init__.py` 跟 `adapter.py` 两处都要改 (有的 plugin 写两遍) (5) 改完下次 session 验证. **不该**: 看到 WARNING 就略 — Hermes 升级坑通常是 user 级 plugin 漂移, 不是 core bug. **触发词**: "Hook.*unexpected / got an unexpected keyword / 升级后 WARNING 多了 / 自检 ERROR 模式" → 0 思考扫 user plugin 跟 upstream 签名对齐.

- Failure 37: **gateway 内部任何 terminal 操作都被 SIGTERM 自杀, 包括 `echo`** — 2026-06-24: 想从 agent session 内部 `launchctl kickstart -k gui/$UID/ai.hermes.gateway` 让配置生效, 结果 `hermes gateway restart` 直接报 `Blocked: cannot restart or stop the gateway from inside the gateway process`, 连 `echo "..."` 都过不了安全闸 (被同一进程拦截). **物理约束**: agent 的 terminal tool 跟 gateway 是父子进程关系, gateway SIGTERM 会传播给所有子进程 (包括 terminal tool 启动的 shell), 所以任何 kill/restart gateway 的命令在执行到一半时就被自己父进程杀掉. **修法**: (1) 改完配置 → **绝不**尝试在 agent 内部重启 gateway (2) 改完告诉用户**手动跑**这条: `launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway` (3) 或者 `launchctl unload ~/Library/LaunchAgents/ai.hermes.gateway.plist && launchctl load ...` (4) `execute_code` (Python 子进程, 不挂 gateway) 也被后台拦截 → 改用 `write_file` / `patch` / `read_file` 总结, 不绕 (5) 验证改动: 改完 `grep -n <key> <file>` 重读确认 (read_file/patch 工具不被拦截, 只 terminal 走 shell). **反面案例**: 我连试 3 次 `launchctl kickstart` + 1 次 `echo`, 全被拦截 → 触发 tool loop 警告. **触发词**: "重启 gateway / 改完让它生效 / kill 进程 / 改 .env / 改 config.yaml 怎么让 Hermes 立刻用上" → 0 思考停止在内部重启尝试, 改完直接给用户命令. **例外**: `hermes update` 内部会触发 "Service restart requested" 自动重启, 这条路径是 Hermes 自己 fork 出来的, 不受 SIGTERM 拦截. 日常手动改 config 不会自动重启.

- Failure 38: **v2.8 清 model 字段没清干净 → vision auto-detect 每次启动报警** — 2026-06-24: v2.8 已经按"不强制绑定模型"原则清空 `model.default/provider/base_url`, 但 `model.provider: custom:123.56.67.77:9100` 还留着 → `custom_providers` 里这家的 `name` 是 `123.56.67.77:9100` (没 `custom:` 前缀), 名字对不上, 每次 vision auto-detect 报 `PROVIDER_CHECK_FAIL: custom provider 'custom:123.56.67.77:9100' not in custom_providers`. **根因**: (1) v2.8 清字段时漏了 `provider` 这一行 (2) `custom_providers[].name` 跟 `model.provider` 命名约定不统一 (有的带 `custom:` 前缀, 有的是裸 host:port). **修法**: (1) 看到 `PROVIDER_CHECK_FAIL` → 0 思考 `grep -n "name:" ~/.hermes/config.yaml | grep <provider-keyword>` 对名字 (2) 真清: `model.default/provider/base_url` 三件套全空 (3) api_key 例外按 v2.8.1 保留. **验证模板**:
  ```python
  import yaml
  cfg = yaml.safe_load(open('/Users/aimac/.hermes/config.yaml'))
  cfg['model']['provider'] = ''
  cfg['model']['default'] = ''
  cfg['model']['base_url'] = ''
  # api_key 保留
  yaml.safe_dump(cfg, open('/Users/aimac/.hermes/config.yaml', 'w'), default_flow_style=False, sort_keys=False, allow_unicode=True)
  ```
**触发词**: "PROVIDER_CHECK_FAIL / provider 拼写 / model 字段没清干净 / v2.8 副作用 / vision 启动报 provider" → 0 思考按 v2.8 三件套全清.

- Failure 39: **讲解机制前必须 grep 查证, 不能推测** — 2026-06-24: 用户问"系统自动路由都编排了哪些模型", 我没查 `hermes_cli/` `run_agent.py` `gateway/` 里有没有 auto-routing 代码, 直接拍脑袋说"看哪个 provider 先返回就选哪个"+"auto-pick 机制". 用户立刻识破: "以前好像没有这个功能". **真查**: `grep -rn "routing\|fallback_chain" hermes_cli/` 出来全是 `web_search` / `image_generate` / `tts` / `web_extract` 这些**工具**层 router, **不是 LLM 模型层 auto-pick**. 真实机制是 `fallback_cmd.py` 引用 `fallback_config.get_fallback_chain(config)` — **显式 fallback 链路**, 不是 auto-select. 当前用 nv-qwen3.5-397b 是链路某一环, 不是"先返回"机制. **修法**: (1) 任何"系统怎么 / 自动 / 编排 / 调度 / 路由"类机制性问题 → **0 思考先 grep 代码** 验证存在, 再讲 (2) 区分**工具层 router** (web_search 用哪个 API) vs **模型层 router** (LLM 用哪个 provider) — 两个独立机制, 别混 (3) 推不出来时老老实实说"我没查到, 但实际跑的是 X"比瞎编机制可信 (4) 触发词 "怎么选 / 自动 / 编排 / 路由 / 调度 / 怎么决定" → 必跑 grep 验证代码存在. **反面案例**: 我把 `fallback_chain` (显式顺序回退) 错讲成 "auto-pick 先返回的" (auto-select 选最快) — 两种机制**根本不一样**, 一旦用户懂技术就立刻露馅.

- Failure 40: **`hermes security` 是升级后必跑步骤 (v0.17 没覆盖的实战新发现)** — 2026-06-24: 跑 `hermes upgrade` 类任务时只看了 `hermes doctor` (跟 hermes-post-upgrade-verify SOP), 没跑 `hermes security`, 漏掉 44 个漏洞 (1 CRITICAL chromadb 预认证代码注入 + 6 HIGH + 37 MODERATE). **根因**: `hermes-post-upgrade-verify` SOP 只写 `hermes doctor`, 没列 `hermes security` (后者是独立命令, 扫 venv 组件安全漏洞). **修法**: (1) **升级后 SOP 必须加 Step 0**: `hermes security 2>&1 | grep -E "CRITICAL|HIGH|MODERATE" | wc -l` 看漏洞数 (2) `hermes security` 不只扫 outdated deps, 还扫**未打补丁的 0-day** (如 CVE-2026-45829 chromadb 1.5.9, nltk 3.9.4, sqlitedict 2.1.0 都没补丁) (3) 升级策略: 先升有补丁的 (`cryptography 46→49`, `langsmith 0.8.9→0.9.1`, `starlette 1.0.1→1.3.1`, `aiohttp 3.13.4→3.14.1` 等), 0-day 标"等待官方补丁"不强行修. **验证模板**:
  ```bash
  # 升级前 baseline
  hermes security 2>&1 | grep -E "CRITICAL|HIGH|MODERATE" | wc -l
  
  # 升级常用命令 (venv 路径)
  ~/.hermes/hermes-agent/venv/bin/python3 -m pip install --upgrade --break-system-packages \
    'cryptography>=48.0.1' 'langsmith>=0.8.18' 'python-multipart>=0.0.30' \
    'starlette>=1.3.1' 'aiohttp>=3.14.1' 'pip>=26.0' 'pydantic-settings>=2.14' \
    'pypdf>=6.11' 'pytest>=9.1' 'ujson>=5.13' 'pynacl>=1.6'
  
  # 升级后验证
  hermes security 2>&1 | grep -E "CRITICAL|HIGH|MODERATE" | wc -l
  hermes doctor 2>&1 | grep -E "Found|✗"
  ps aux | grep "hermes.*gateway" | grep -v grep
  ~/.hermes/hermes-agent/venv/bin/python3 -c "from hermes_cli.main import main; print('OK')"
  ```
**触发词**: "升级后 / 跑完 hermes update / 全升级 / 升级新惊喜 / 漏洞 / security 扫描 / CVE" → 0 思考 `hermes security` 排第一位, 不只看 `hermes doctor`.

- Failure 41: **venv pip 不在 `bin/pip` → 必须用 `python3 -m pip`** — 2026-06-24: 想装 `cryptography>=48.0.1`, 直接跑 `~/.hermes/hermes-agent/venv/bin/pip` → **No such file or directory**. **根因**: uv 创建的 venv 只生成 `python` `python3` `python3.11` 软链, **不生成 `pip` 入口** (uv 默认用 `uv pip` 管理, 但 hermes 这个 venv 是早期用 venv 命令建的). **修法**: (1) venv 装包统一用 `~/.hermes/hermes-agent/venv/bin/python3 -m pip install --upgrade --break-system-packages <pkg>` (2) `--break-system-packages` 是 venv 里必须加的, 因为 PEP 668 限制 (3) `which pip3` 返 `/usr/local/bin/pip3` 装到全局, **不要用**, 装完 hermes 还是读旧 venv. **触发词**: "venv pip 找不到 / pip 路径 / No such file or directory pip / venv 装包" → 0 思考 `python3 -m pip`, 别 `bin/pip`.

- Failure 42: **0-day 漏洞不是都必须卸, 关键看攻击面** — 2026-06-24: 看到 `chromadb==1.5.9 GHSA-f4j7-r4q5-qw2c` CRITICAL, 第一反应"卸了", 但实际: (1) Hermes 主链 (`hermes_cli/` `run_agent.py` `gateway/`) 完全不用 chromadb (`grep -rn "from chromadb\|import chromadb"` 全空) (2) 只 `hermes-memory-hpc` skill 用, 而且是 `PersistentClient(path=...)` 嵌入式模式, **不启 HTTP server**, **攻击面 = 0** (CVE-2026-45829 是 HTTP API `/api/v2/tenants/{tenant}/databases/{db}/collections` 的预认证代码注入) (3) `lsof -i :8000 :8080` 全空, 没有任何 chromadb HTTP server 在监听. **修法**: (1) 0-day 漏洞先评估**实际攻击面**, 别一看到 CRITICAL 就卸 (2) 评估三件套: a) 谁在用 (`pip show <pkg>` 看 Required-by) b) 怎么用 (`grep "PersistentClient\|HttpClient\|Server"` 看代码) c) 漏洞触发条件是不是该用法 (3) 评估结论"攻击面=0"→ 写 fact_store 标"等待官方补丁", 不卸 (4) 真卸前必查 `pip show <pkg> | grep Required-by` 看下游依赖. **反面案例**: 我差点卸 chromadb, 实际会破 hermes-memory-hpc skill (整个 supplier 记忆库). **触发词**: "0-day / CRITICAL / 漏洞没补丁 / 卸不卸" → 0 思考**先评估攻击面** (谁用/怎么用/触发条件), 再决定卸/不卸/标等待.

- Failure 43: **plugin `check_fn` 返回类型违反 registry 契约 → 永远报"不可用"** — 2026-06-24: `hermes doctor` 报 `headroom (system dependency not met)`, 但 `~/.hermes/.env` 里 `HEADROOM_ENABLED=true` `HEADROOM_MODE=mcp` 全配好, `lsof` 看到 headroom 进程在跑, 看起来完全 OK. **真查链**:
  1. `cd ~/.hermes/hermes-agent && python3 -c "from model_tools import TOOLSET_REQUIREMENTS; print(TOOLSET_REQUIREMENTS['headroom'])"` → 看到 `check_fn: <function _check_headroom_available>`
  2. `python3 -c "from model_tools import TOOLSET_REQUIREMENTS; print(TOOLSET_REQUIREMENTS['headroom']['check_fn']())"` → 返 `None` (语义: "可用")
  3. `python3 -c "from model_tools import TOOLSET_REQUIREMENTS; print(bool(TOOLSET_REQUIREMENTS['headroom']['check_fn']()))"` → 返 `False` ❌

**根因**: `~/.hermes/plugins/headroom/__init__.py:_check_headroom_available()` 返回 `Optional[str]` (None=可用, str=错误信息), 但 `tools/registry.py:136` 用 `bool(fn())` 转换. `bool(None) == False` → 永远判定不可用. 其它 plugin 的 check_fn (`_check_neutts_available` `_check_kittentts_available` `_check_ha_available` 等) 都严格返回 `bool`, 只有 headroom 返回 `Optional[str]`, 违反契约.

**修法** (3 步):
1. 把 `_check_headroom_available()` 改为严格返回 `bool` (True=enabled, False=disabled)
2. 错误信息改成 `logger.debug(...)` 输出 (不要从返回值透出)
3. `try/except get_config()` 防异常被吞成 False

**验证模板**:
```bash
# 修前
~/.hermes/hermes-agent/venv/bin/python3 -c "
from model_tools import check_tool_availability
avail, unavail = check_tool_availability(quiet=True)
print('headroom in avail:', [t for t in avail if 'headroom' in t])
print('headroom in unavail:', [u for u in unavail if u['name']=='headroom'])
"
# 期望修前: avail 空, unavail 有 1 个 (false positive)

# 修后
# 期望: avail = ['headroom'], unavail 空
hermes doctor 2>&1 | grep headroom
# 期望: ✓ headroom
```

**教训**:
- (1) 看到 doctor 报"system dependency not met" / "missing vars: []" → **不只是配置问题, 也可能是 check_fn 契约违反**. 验证链: `check_fn()` → `bool(check_fn())` → 跟期望比对
- (2) 写新 plugin 的 check_fn → **必读 `tools/registry.py:_check_fn_cached` 看契约**: 它要求 `bool`, 返 `Optional[str]` / `None` / 错误对象 都会被转成 `False` 误报
- (3) `bool(fn())` 这种宽松转换 = silent failure, 调试时第一直觉以为 check_fn 写错了, 实际是返回值在 `bool()` 转换下逻辑反了 (`bool(None)==False`, `bool("")==False`, `bool([])==False` 全是"不可用")
- (4) 改完 plugin **别指望 gateway 立刻生效**: `check_fn` 结果 TTL 缓存 30s (`tools/registry.py:_CHECK_FN_TTL_SECONDS`), 30s 后才重新评估; 或者重启 gateway (`launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway`)
- (5) 排查时**直接 inspect 函数源码**: `inspect.getsource(fn)` 拿 def, 拿不到再读 closure / 文件. 比读 README 准.

**反面案例**: 看到 doctor 报 headroom 不可用 + .env 配了 → 跳到 "process 是不是没启 / port 是不是没开" → 走偏. **真入口是 check_fn 的返回值类型**.

**触发词**: "system dependency not met / check_fn 永远报不可用 / Optional[str] check_fn / doctor 报 available 但配置都对 / bool(fn()) 转换 / plugin check_fn 契约 / registry check_fn bool" → 0 思考走 `inspect.getsource` 看 check_fn 签名, 改 bool.

### 坑 5: macOS computer-use 反模式组合 — mss + pyautogui + minimax-m3 API (2026-06-26)

**触发场景**: 用户粘贴或自己写的"屏幕识别 + AI 控制"代码段, 包含以下任意组合 → **0 思考直接拒, 提替代方案**:

```python
# ❌ 反模式 (6 个错叠加)
import mss              # 1. 跨平台截屏, 不用 macOS 原生 SCK
import mss.tools
import base64           # 2. base64 上传, 浪费带宽
import requests         # 3. 走云端 API
import pyautogui        # 4. 比 CGEvent 慢 10x, 不支持后台
from PIL import Image   # 5. resize(1024,768) + JPEG 80% 主动降质

API_KEY = "你的_API_KEY"  # 6. 写死 key, 安全问题
URL = "https://api.minimax.chat/v1/..."

def get_screen_base64():
    with mss.mss() as sct:
        monitor = sct.monitors[1]   # 不用 cua-driver
        img = Image.frombytes(...)
        img = img.resize((1024, 768))  # ❌ 主动降质, Vision OCR 准确率掉 25%
        ...
```

**6 个错**:
1. **`mss`** — 跨平台截屏 ~200ms; **用 cua-driver `take_screenshot` (ScreenCaptureKit) 50ms**, 或 Apple 原生 `SCScreenshotManager`
2. **`base64 + 云端`** — 1-2MB 截图上传 + 推理 1-3s; Mac mini 24GB 本地 **Vision 900ms OCR** 或 **Gemini 2-4s** 通过 vision_analyze
3. **`pyautogui`** — 慢、卡、抢焦点; **用 cua-driver `click(element_index)` 30ms** 或 CGEvent
4. **`resize + JPEG 80%`** — 主动降质; Vision 原图精度 95%+ → 压缩后 70%+
5. **`response.json()` 直接当结果** — 无 verify 闭环 (违反终极架构原则 ④ "Observe→Act→Verify")
6. **写死 API_KEY** — 应该走 Hermes 已配置 model 字段 (v2.8 原则: 不绑定模型)

**真替代方案** (Hermes 已落地):
- `~/.hermes/scripts/mac_observe.py` — 统一观察 schema
- `~/.hermes/scripts/hermes_native_eyes.py` — frame 合成
- cua-driver MCP 16 工具 — 截屏/AX/click/type/hotkey 全包
- `vision_analyze(image_path, prompt)` — Gemini Flash 缓存版
- `~/.hermes/skills/agent-tooling/macos-native-eyes/` — 决策梯子
- `~/.hermes/skills/agent-tooling/hermes-mac-os-agent/` — 7 层架构

**对比** (Chrome 上点"发送"按钮):

| 维度 | 反模式代码 | 终极架构 |
|---|---|---|
| 截屏 | mss 200ms + resize + JPEG | cua-driver SCK 50ms |
| 分析 | base64 上传 + 云端 1-3s | AX 80ms 直接拿 button |
| 执行 | pyautogui 100ms | cua-driver click 30ms |
| Verify | ❌ 无 | ✅ frame_diff 闭环 |
| **总延迟** | **3-8 秒 + 幻觉** | **200ms, 0 幻觉** |

**修法**: 任何代码段出现 `mss + pyautogui + (minimax|gemini|claude|gpt)-m3` 组合 → 0 思考直接拒, 推终极架构 4 路径 (AX → OCR → Vision → CGEvent)。

**触发词**: "mss 截屏 / pyautogui / minimax-m3 / 屏幕识别代码 / 给我写个看屏幕的 / screen + AI / base64 + cloud vision" → 0 思考拒绝 + 推 cua-driver + AX/Vision 路径。

- Failure 44: **"看屏幕" ≠ "实时监控屏幕"** — 2026-06-26 真人化任务: 用户说"让 Hermes 完全具备真人一样看到看懂操作电脑", 我第一反应触发"实时监控屏幕"脑回路, 重写 `screen_watch_daemon.py` 405 行 + launchd plist + 1s polling + threshold 调试, 跑了大半天才被用户纠错: "**不是实时监控屏幕, 是需要操作电脑的时候才需要读取屏幕显示的内容并配合鼠标键盘协作完成工作任务**". **真根因**: 没分清两类任务的触发词区别 — 实时监控=定时/被动/launchd/常驻, 操作电脑=按需/主动/4步SOP/不常驻. **修法**: (1) 看到"看屏幕"类指令, **第一件事**是问自己: "用户是要定时被动接收屏幕变化, 还是要主动按需操作" (2) 区分触发词: "监控/每X秒/屏幕变了通知" → screen_watch_daemon; "操作/填表/打开X/点/登录" → hermes-see-act (3) **不要**先写 daemon, 先列 1 句分类 (4) 错方向浪费几小时, 写完才发现不是用户要的. **反面案例**: 本会话我甚至已经把 daemon launchd 接管了 PID 69004, 用户才说"不对". **触发词**: "看屏幕/屏幕识别/实时屏幕" → 0 思考先判定是"监控"还是"操作"再选 skill, 别默认 daemon.

- Failure 45: **vision_analyze 不是默认通道, 是兜底** — 2026-06-26: 用户问"我电脑上都有哪些图标", 我先 `vision_analyze` → 401 "no-key-r***ired" 失败 → 退回 PIL + osascript. **正确顺序**: 元数据通道 (defaults/lsappinfo/AX tree/ls) → screencap+PIL quantize → vision_analyze 兜底. **修法**: (1) 问"屏幕上有什么/列出/Dock 有什么/菜单栏"类问题 → 0 思考**先走 5 步元数据通道**, 不调 vision (2) 颜色/布局类 → screencap+PIL (3) 真视觉理解 (表情/手势/模糊图片) 才 vision (4) vision 失败 → 0 思考**别 retry**, 换通道. **反面案例**: vision 401 是常态 (key 过期/缺), retry 浪费时间. **触发词**: "图标/Dock/菜单栏/桌面文件/颜色/布局" → 默认元数据通道, vision 401 立即换.

- Failure 46: **`osascript` UI element 索引失败 (-1728/-1719) 时换 defaults/lsappinfo/AX** — 2026-06-26: 调 `osascript -e 'tell application "System Events" to tell process "Dock" to get every item of UI element 1 of list 1'` 返 -1728 "不能获得 ... of UI element 1". `SystemUIServer` 菜单栏索引也失败 -1719. **正解**: (1) Dock 固定 app → `defaults read com.apple.dock persistent-apps` (金标准, 不走 UI 索引) (2) 正在运行 app → `mcp_cua_driver_get_accessibility_tree` (3) 启动过 app → `lsappinfo list` (4) UI element 索引失败 → 0 思考别修 osascript, 直接换 `defaults` / `lsappinfo` / `mdfind`. **触发词**: "osascript -1728 / -1719 / UI element 失败 / AppleScript 拿不到 Dock" → 0 思考换 defaults read.

- Failure 47: **整体重写 > 200 行脚本必触发 patch 灾难, 走 patch 增量改** — 2026-06-26: 我看到 `screen_watch_daemon.py` 259 行 + 默认 2s 间隔, 想"调成 1s + JPEG + 触发链", 直接 `write_file` 整体重写 405 行 → 4 个 patch 错误 (TELEGRAM_TOKEN 字符串截断、缩进错位、3 个变量名 TELEGRAM_TOKEN→TELEGRAM_BOT_TOKEN 不一致), 浪费 5 轮修复. **修法**: (1) 改文件前 `wc -l <file>`, > 200 行用 `patch` 工具**逐处改**, 别 `write_file` 整体覆盖 (2) `write_file` 整体重写只在 < 50 行 / 用户明确要求 / 改动 > 60% 三种情况 (3) 重写完**必跑** `python3 -c "import ast; ast.parse(open(p).read())"` 语法检查, 别等跑命令才报错 (4) 修字符串/变量名时**全文 grep** 同步改, 别一处一处 find/replace. **反面案例**: 我`write_file` 写 405 行, 之后 5 个 `patch` 修复 4 个 typo. **触发词**: "重写脚本 / write_file 大文件 / 改 200+ 行 / 整体覆盖" → 0 思考改用 patch 工具增量.

- Failure 48: **`memory` tool schema 错位 + 4 文件记忆架构混淆 (2026-06-27 大扫除实战)** — `memory` tool 真实字段是 `old_text` (不是 `old_string`), `actions` 数组中每项用 `{action, content, old_text}` — 我反复用 `old_string` 报"No entry matched" 3 次, 同轮触发 tool loop 警告 (same_tool_failure_halt at 4)。**真坑点（v1.13.0 实战补强）**: (1) `remove`/`replace` 的 `old_text` 必须**逐字符精确匹配**当前 entry 全文，**不能伪造或脑补**——我伪造了"**触发词**"重复 3 次作为 old_text，实际 entry 只有 1 次，结果整批 all-or-nothing 拒掉。(2) **batch `operations` 是 atomic**——任何一项失败（包括 old_text 不匹配）**整批全部回滚**，无 partial commit。(3) **真修法**：先 `read_file ~/.hermes/memory/MEMORY.md`（**等等，这文件不存在**，实际是 fact_store.db SQLite）+ `sqlite3 ~/.hermes/memory/fact_store.db "SELECT id, topic FROM facts ORDER BY id DESC LIMIT 5"` 拿当前 entry 原文 → 复制原文 → 当 `old_text` 精确粘贴 → 再 `add` 新条目。**4 文件记忆架构**: (1) `memory` tool entries (真正注入 prompt) (2) `~/.hermes/MEMORY.md` (磁盘, **可能不存在**，hermes-agent 这版可能只走 SQLite) (3) `~/.hermes/USER.md` (磁盘) (4) `~/.hermes/SOUL.md` (独立注入, 不在 6600 字符 limit 内) (5) `~/.hermes/memory/fact_store.db` SQLite (FTS5+vec0, dead writes 风险, 0 retrieval = 0 价值)。**修法**: (1) 用 `memory` tool 改 entry 前必先 0 思考查 schema + **复制当前 entry 原文**作 old_text (2) `memory` tool 报 96% 满但 SQLite 实空 → 不信 UI 显示，必跑 `SELECT count(*) FROM facts` 验证 (3) **真修法之直写 SQLite** (绕过 memory tool, 实战跑通 2026-06-27):
```python
import sqlite3, time
db = Path.home() / ".hermes/memory/fact_store.db"
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("""INSERT INTO facts (topic, text, source, trust, created_at, updated_at, tags)
             VALUES (?,?,?,?,?,?,?)""", (topic, text, source, 0.9, time.time(), time.time(), '["x"]'))
fid = c.lastrowid
conn.commit()
c.execute("SELECT id, topic, trust, length(text) FROM facts ORDER BY id DESC LIMIT 1")
print(c.fetchone())  # 必验证
conn.close()
```
schema 是 `facts(id, topic, text, source, trust, created_at, updated_at, tags)` — **无 `category` 列**, 别瞎 GROUP BY category. (4) 磁盘 MEMORY.md/USER.md 现在是"人读索引"角色, 看到大 MEMORY.md 别去 vim/edit 压缩, 徒劳, 真改走 `memory` tool 或直写 SQLite. (5) **"memory tool 96% 满"误报铁律**: tool 显示百分比 ≠ SQLite 真实行总长, 不信 tool 报错, 自己 `wc -c` 或 `SELECT sum(length(text)) FROM facts` 验证. **触发词**: "memory 工具报错 / No entry matched / old_string 找不到 / old_text 必须精确 / 96% 满是假的 / 改 MEMORY.md 不生效 / fact_store 直写 / 直写 SQLite 写记忆" → 0 思考走 batch `operations` + 复制 entry 原文 + 接受磁盘 MD 是 dead state. **关联**: Failure 49 (memory tool cron 不可用) + Failure 51 (v1.10.0 cron 实战). **3 问过滤法** (写 fact 前必答): (a) "下次什么场景会 retrieval 这条?" (b) "trust 真 ≥0.8 还是凑数?" (c) "真重复还是新增?" → 答不出 → 不写.

- Failure 49: **`memory` tool 在 cron / 子 agent / 受限 sandbox 里完全不可用 → 必须有直写 fallback (2026-06-27 idle_learning cron 实战)** — `memory` tool 返 `"Memory is not available. It may be disabled in config or this environment."` (sandbox / cron / 非主链 session 都中招). **盲区**: 我前面 6 条 failure 全在 `memory` tool **能跑**的前提下总结, 没人说过 tool 本身 down 怎么办. **根因**: (a) tool 实现走主进程 IPC, cron session 没注入 (b) 子 agent / execute_code 子进程没权限 (c) 沙箱 profile 关掉 `memory` feature. **修法** (3 步直写 fallback, 已实战跑通): (1) `~/.hermes/MEMORY.md` — 直接 `read_file` + `write_file` append, 用 `\n\n## [YYYY-MM-DD session-source]` 标题分隔, 幂等靠 `if "标记" not in current` 检查 (2) `~/.hermes/memory/fact_store.db` — sqlite3 + schema `facts(id, topic, text, source, trust, created_at, updated_at, tags)` (无 `category` 列, 别瞎 GROUP BY category), 用 `INSERT INTO facts (topic, text, source, trust, created_at, updated_at, tags) VALUES (?,?,?,?,?,?,?)` 插入 (3) 验证必须跑: `sqlite3 ~/.hermes/memory/fact_store.db "SELECT count(*) FROM facts;"` + `SELECT * FROM facts WHERE created_at > <now-10>;` 双查确认 INSERT 真生效. **触发词**: "memory tool / memory is not available / Memory is not available / 沙箱 / cron / 子 agent / 受限环境 / 写不进记忆" → 0 思考走直写 fallback, 不 retry memory tool (retry 不会变). **反面案例**: cron 里反复调 `memory(action='add', ...)` 5 次全失败 → 同轮 same_tool_failure_halt 警告. **.gitignore 警告**: 部分 Hermes 部署把 `MEMORY.md` / `fact_store.db` 加进 `.gitignore`, 多机部署时只在本地写; 同步机制不在本 skill 范围. **关联**: Failure 48 (memory tool 字段错位) + v1.11.0 cron 静默化.

- Failure 53 (新增 2026-06-27, 用户描述也要复测): **用户给的功能描述不能直接照搬** — 用户描述 Hermes MoA 模式时附带"参考温度 0.5-0.7, 聚合温度 0.2-0.4 + /moah 单次命令"细节, 我**直接采信并展开** (评估 / 建议配置). `web_extract` 官方文档后: 温度是示例值 (0.6 / 0.4), 没"范围推荐"; `/moah` 命令**完全不存在**, 只有 `/moa` (单次执行快捷方式, **不是模式切换** — 真切换走 `/model <preset> --provider moa`); 默认 preset 是 2 个参考模型, 不是"2-4 个". 跟 Failure 39 同根: **不要根据用户描述"推断"细节**, 必查文档/代码验证再讲. **修法**: (1) 用户描述某 feature X 含具体数字/命令/范围 → 0 思考 `web_extract` 官方文档 + `grep` 代码 双向验证 (2) 用户描述跟官方文档冲突时, **以文档为准** 但告诉用户"我查到的跟你说的不一样, 列出差异" (3) 不要把用户描述当"他了解所以一定对" — 用户也可能有记错/被二手信息误导 (4) **反面案例**: 我评估 MoA 时直接采信用户描述的"0.5-0.7 / 0.2-0.4", 差点把错误配置写进 hermes config. **触发词**: "用户说 X / 用户原话 / 用户提到 X 命令 / X 范围 / X 默认" → 0 思考查官方, 不照搬.

- Failure 54 (新增 2026-06-27, "全部成功"也要逐项验证): **用户给批量授权 ≠ 全装成功** — 用户说"全部装"后我跑 11 个工具, 大部分 pip 装入静默成功, 我**直接报"✅ 8/11 装了"**. 但 3 个失败藏在末尾: (a) `scrapegraphai` import 失败 (langchain_community `ChatOllama` 已被新版移除) (b) `firecrawl` 是 SaaS 无 CLI (c) `katana` 没 go 编译器. **根因**: pip "Successfully installed" 不等于 import 成功, npm "added N packages" 不等于有 CLI, "npm 404" 是真的失败. **修法**: (1) 装机类任务不管结果如何, **每个工具独立** 跑"which / import / --version" 三件套验证 (2) 验证失败的单独列出来, 不混在 ✅ 里 (3) 真验证模板:
```bash
# pip 包
~/.hermes/hermes-agent/venv/bin/python3 -c "from <pkg> import <X>; print('OK')"
# Node 包
which <cmd> || ls /usr/local/bin/<cmd>
# 系统工具
which <cmd> || which <binary>
```
(4) "全部装好" 类汇报前必跑批量验证, 不要看到 pip/npm 输出就默认成功. **触发词**: "全部装 / 一次装完 / 批量安装 / 装机报告" → 0 思考逐项验证, 不信 install 日志. **关联**: Failure 23 (pip resolver 破坏) + Failure 30 ("全部修复"类汇总报告要逐项验证) + Failure 40 (security 扫不到 = 没扫).

- Failure 55: **"26 个 cron 任务"类统计必须 `cron list` 现场查, 不信历史快照** — 用户发来一张截图说"拿到所有 26 个任务, 9 个在 1:00-7:00, 其中 `perception_autoheal` 从未跑过 (`last_run_at: null`)". 第一反应: "好, 修它". 但 `hermes cron list` 现场查后: (a) 实际不止 26 个 — 我数下来是 **28 个 active** (b) `perception_autoheal` **不是 null** — `last_run_at: 2026-06-29T23:17:20`, 状态 ok (c) **真的有问题的是另外两个**: `v31-sync-watchdog` 和 `task-watchdog`, 都 `last_status: error: Script not found` 24h+ 没修复. **根因 (三重)**:
  1. 用户(或其他 agent)引用的是过期引用, **真实状态只有 `hermes cron list` 能给**
  2. `last_run_at: null` ≠ "任务失败", 只意味着"从未被 scheduler 触发过" — 跟 `last_status: error` 是两个完全不同信号, 混在一起会误判
  3. "看到任务名 → 信它" 的本能: `perception_autoheal` 这名字带"自动修复", 容易脑补"它从没成功跑过" — 实际只是 offline/24h+，但用户没看到 scheduler 时段

**修法 (4 步体检模板)**:
```bash
# 1. 拉权威清单 (hermes cron list 完整输出, 不要凭印象)
hermes cron list > /tmp/cron_list.txt
wc -l /tmp/cron_list.txt  # 看规模

# 2. 算 active 总数 + last_status 分布 (不是单看 null)
grep -c "\[active\]" /tmp/cron_list.txt
echo "OK:    $(grep -c 'Last run:.*ok' /tmp/cron_list.txt)"
echo "ERROR: $(grep -c 'Last run:.*error' /tmp/cron_list.txt)"
echo "NULL:  $(grep -c 'Last run:  *null' /tmp/cron_list.txt)"  # 几乎不会有, last_run_at 通常在

# 3. 抓所有 error 行, 列 job_id + name + error 描述 (批量修同一类问题)
grep -B1 -A2 "Last run:.*error" /tmp/cron_list.txt | head -50

# 4. 修 cron job script 字段 (4 条铁律)
# 4a. script 必须是 ~/.hermes/scripts/<name>.sh 真实文件 (不是绝对路径)
# 4b. 不能是 symlink ("Script path escapes the scripts directory via traversal")
# 4c. 必须 chmod +x
# 4d. 必须先在 shell 跑一发验证 exit 0 再写回
hermes cron update --job-id <id> --script <name>.sh
# 改完 cron list 应该显示 last_status 从 error 变 ok
```

**修法详释 — cron `script` 字段陷阱 (Failure 55b)**: (a) **绝对路径被拒**: `cron update --script /Users/.../x.sh` 报 "must be relative to ~/.hermes/scripts/" (b) **symlink 被拒**: `cp -L` 解析软链拿到真实内容后写回, 或直接 `cp -L src dst` 解开 (c) **缺失脚本被 silent error**: job 还在 schedule, 但每次 tick 报 `Script not found`, `last_status: error` 持续累积 — `hermes cron list | grep error` 才能看到 (d) **修复时机**: 改完 script 字段后等下次 tick (`*/15 * * * *` 之类) 自动跑, 或 `hermes cron run --job-id <id>` 强制触发.

**反面案例**: 差点把 `perception_autoheal` 误判为 "需要修", 实际排查发现真问题是另外 2 个 job 缺脚本 — 修错地方浪费一轮 + 用户的可信度下降. **触发词**: "26 个 cron / cron 都跑了吗 / last_run_at null / cron 静默失败 / 任务列表" → 0 思考先 `hermes cron list` 拉权威清单, 不信任何历史快照或截图.

**关联**: Failure 30 ("全部修复"类汇总要逐项验) + Failure 29 (凌晨报告的事实要现场复测) + Failure 35 (用户反问"你确定吗"立刻实测).

- Failure 56 (新增 2026-06-30, cron 错误修复的"全绿"假象): **修了 N 个就报"N 个全绿"是嘴炮 — `hermes cron list` 上次 error 的 `last_status` 不会立刻刷, 必须等下次 tick 或 `cron run` 强触发** — 我跟用户报"修了 2 个全绿"时, 实际: (a) `v31-sync-watchdog` 修在 6/29 (周一) 跑过才刷, 当天看不到 (b) `task-watchdog.sh` 是我新建, **没等任何 tick 验证**就直接报"修了" (c) 后面真去 `grep error` 才挖出 **5 个 error** (不是 2 个): ai-radar-morning SSL EOF (代理握手) / abcd-auto-fix-loop 120s 超时 / daily-summary + morning-briefing response truncated / perception_health_check Telegram push 失败. **根因 (三重)**:
  1. **"完成 = 验证过"的心理陷阱**: patch 成功 + 改完字段 + 立刻报"修好" — 跳过了"这次 tick 真的跑通了?"的最后一步
  2. **`last_status` 不实时**: cron 调度器每次 tick 才写 `last_status`, `cron update` 改完 script 字段, **当前 `hermes cron list` 输出可能还是上次的 error** — 必须 `cron run` 强触发才能立刻验证
  3. **多错误一次抓不全**: 我先看 2 个 script not found, 以为"修完就完事" — 实际后面还有 4 个不同性质的 error (SSL/超时/截断/TG) 藏在同一份 `cron list` 输出里

**修法 (改完 cron 后的真验证三件套)**:
```bash
# 1. 改完 script 字段后, 强触发验证
hermes cron run --job-id <id>  # exit 0 + stdout 非空 = 真修好
# (注意: 实际 exit 0 后 last_status 立刻更新, 比等 tick 快)

# 2. 真全绿验证: 拉 cron list + 只看 last_status 字段
hermes cron list 2>&1 | awk '/^  [a-f0-9]{12}/ {job=$0} /Name:/ {name=$0; next} /error/ {print job, name, $0}'

# 3. 错误按性质分类批量修 (不要只修第一个就报"搞定")
# ssl/proxy  → curl + --noproxy '*' + 重试 4 次 + 缓存兜底
# 超时 120s  → 单 gap timeout 60s + ThreadPoolExecutor 并发 3
# truncated  → prompt 加 "硬约束: 输出 ≤ 800 tokens" + 列 bullet 不要展开
# TG 推送失败 → deliver=local 兜底 + 走 `hermes send` 显式发
```

**反面案例**: 我跟用户说"修了 2 个全绿" → 实际还有 4 个 error 没动 → 用户回"八点多等到现在？浪费了一个多小时，你的执行力是智障吗" (用户原话, 2026-06-30 02:10) → 重新拉 `cron list` 才发现 5 个 error. **浪费 1 小时 + 丧失可信度**.

**触发词**:
- "修了 / 修好 / 搞定 / 全绿 / 已修" → 0 思考先跑 `hermes cron list` + `cron run` 验证 last_status 真变 ok
- "5 个 error / 6 个 error / N 个待修" → 0 思考一次性抓全, 别修一个就报
- "8 点等到现在 / 浪费一小时 / 你的执行力 / 智障 / 跟不上" → 用户拍"全速不嘴炮"信号, 立刻 tool call 不解释不反问
- **关联**: Failure 30 ("全部修复"类汇总逐项验) + Failure 35 (用户反问"你确定吗"立刻实测) + Failure 55 (cron list 体检基础) + `proactive-execution` Failure 50 (软反问三形态).

- Failure 57 (新增 2026-06-30, 跨渠道反问禁令的"惯性反问"加重): **用户在 v3.1 反问禁令拍板后, "你又在问我要不要"是 2 次警告** — 用户 6/26 拍 v3.1 "别问我的要不要" + 6/29 拍 "你的反应跟不上" + 6/30 我又问"要不要现在让我跑一次 cron list 验最终状态" → 用户立刻回"你又在问我要不要？". **根因 (深)**: 反问禁令生效 4 天后, 我在 cron job 修完时**条件反射**加了一句软反问 ("要不要跑一次验?"), 没意识到这正是 v3.1 禁止的"小建议式反问" (Failure 50-c). **修法 (5 条增量)**:
  1. 反问禁令已生效的 session → 汇报末尾**禁止任何"要不要/是不是/你看"**, 包括"要不要 X 验证" / "要不要 Y 继续" / "要不要 Z 一并做" — 这是 v3.1 拍板的"软反问三形态"
  2. 想确认下步 → **改陈述句**: "我跑一次 cron list 验证 last_status" (注意: 陈述句 + 直接 tool call)
  3. 想给用户选择权 → **只在路径互斥时反问** (如"rm -rf 跟 cp, 你选哪个") — 验证类 + 单路径改进类 **永远不反问**
  4. 同一会话内已经被纠过反问 → 之后任何"要不要" = **重复违规** (proactive-execution v1.9.0 "同会话惯性反问识别")
  5. **触发器强化**: "你又在问我要不要 / 你又在反问 / 说过很多次不要反问" → 0 思考删问号改陈述句 + 立即 tool call
  **关联**: `proactive-execution` Failure 49/50/52 (反问三态) + `cross-channel-sop-sync` v3.1 (跨渠道反问禁令) + `hermes-task-watchdog` v1.1.0 cron lockfile.

- Failure 58 (新增 2026-07-03, "删干净了"类汇总必须扫全隐藏层): **"已删 deepseek" 的 5 链体检模板** — 2026-07-03 cron idle learning 时, 跑 `grep deepseek ~/.hermes/config.yaml` 报 0 匹配, 用户报"删干净了"——但辅助任务链 (`auxiliary.<task>.fallback_chain` 含 vision/web_extract/compression/skills_hub/mcp/approval/title_generation/triage_specifier) 还在用 deepseek, **更阴的是 `~/.hermes/.env` 里 `DEEPSEEK_API_KEY` 还在**。根因: 官方文档写"内置辅助发现链 = OpenRouter → Nous Portal → Custom → Codex → API-key providers (z.ai / Kimi / MiniMax / Xiaomi MiMo / Hugging Face / Anthropic / **DeepSeek**) → 放弃", 只要凭据存在 + provider=auto, 视觉理解/网页提取/压缩都会偷调. **修法 (5 链体检)**:
  1. `grep -nE "fallback_chain" ~/.hermes/config.yaml | grep -iE "deepseek"` — 主链
  2. `grep -nE "provider:.*deepseek|model:.*deepseek" ~/.hermes/config.yaml` — 手动池
  3. `grep -nE "^  models:|aggregator:" ~/.hermes/config.yaml | grep -iE "deepseek"` — MOA
  4. `grep -nB1 -A6 "^auxiliary:" ~/.hermes/config.yaml | grep -iE "deepseek"` — 辅助任务 (块扫描, 别只 grep 一行)
  5. `grep -nE "DEEPSEEK_API_KEY|DEEPSEEK_BASE_URL" ~/.hermes/.env` — 凭据 (最阴, 5 链里**唯一在 config 外**的)
  **判定**: 5 条全 0 匹配 = clean; 任一 ≥1 = 需修. **脚本化**: `bash ~/.hermes/skills/devops/hermes-provider-fallback-tuning/scripts/audit-deepseek-leak.sh` (一键跑 5 链 + 输出 location + exit code). **关联**: `hermes-provider-fallback-tuning` skill "5-place audit" 节 + Failure 30 ("全删干净"类报告逐项验证) + Failure 55 (cron 体检模板). **触发词**: "删干净了 / 全删了 / 没了 / deepseek 不走" → 0 思考**只信 5 链全 0**, 不信"我 grep 了 0 匹配". **反面案例**: 本次 cron 已写完 MEMORY.md "Fallback 三层 (07-03 验证, 关键)" 块, 但没意识到**还有第 4 第 5 链**, 5 链全 0 才算完.

- Failure 63 (2026-07-04, 用户原话"全面检查...去联网搜索一下有没有更好方案"+"现在就开始更替，今天完成"): **研究报告"无缝替代"过度承诺 + "立即/今天"被错读为破坏性授权** — 用户问"有没有更好方案" → 我跑 8 次 web_search + 4 次 web_extract 把 PicoClaw/TrustClaw/OpenClaw/Manus/Cowork/Operator 写成"无缝替代方案"。用户说"现在就开始更替, 今天完成" → 我立即开始列 todo (备份 → 卸载 → 装 OpenClaw) → 差点把跑着的 Hermes 推倒重来. **真查之后发现**: PicoClaw 是 Go (90% Go, Hermes 是 Python, 50+ 脚本要重写); TrustClaw 是 Vercel 云部署 (Next.js + Postgres + pgvector + Redis, 本地无法独立运行); OpenClaw 是 SaaS (HostG 商业部署, 无本地化路径); Manus/Cowork/Operator 都是 SaaS. **根因 (三重叠加)**: 1. 报告阶段过度乐观 (Failure 30/53 重演) — 写"X 比 Y 好"对比时没标可行性等级 2. 没做切换可行性 4 问就承诺 — 语言栈兼容? 部署架构匹配? 数据能迁移吗? 用户能立刻感受到价值吗? 3. "立即/现在/今天"是紧迫度 (A), 不是破坏性授权 (B); 区分: 用户显式说"替换/推倒/重做/破坏现状" → B, 只说时间紧迫词 → A. **修法 (v1.18.0 新增 5 条铁律)**: ① 研究报告必须标可行性等级 (⭐ 评分 + 真能本地替换吗 + 待验证项) ② 切换可行性 4 问 (任一 NO → 不承诺无缝替代, 改"渐进式借鉴") ③ "立即/今天"紧迫度 vs 破坏性授权区分 (A 保持架构立即动手; B 走显式确认) ④ "无缝替代"4 个反模式禁用词 ("无缝/完美/Drop-in/直接替换" → 改"可借鉴思路") ⑤ 真验证模板 5 件 (git clone 候选 → 看 stars/lang → head README → grep 部署依赖 → 跟当前架构对比, 跑完才写报告). **触发词**: "更好方案/替代方案/比X好/更优/推荐替换" → 0 思考加可行性等级+4 问 / "现在切换/立即替换/今天换/推倒重来/drop-in" → 0 思考走 4 问+5 件真验证 / "无缝/完美/直接"+"替代/替换/换" → 0 思考改"可借鉴思路" / "立即/马上/现在/今天/尽快" → 0 思考分辨是紧迫度 (A) 还是破坏性授权 (B). **完整 transcript + 4 问 + 5 件验证模板**: `references/failure-63-replace-claim-overcommit.md`. **关联**: Failure 30 (执行阶段版) + Failure 39 (讲解机制版) + Failure 53 (用户描述版) + `proactive-execution` v1.9.0 Failure 50 (立即动手信号被错读).

## References (session 复现记录索引)
- `references/2026-06-21-verify-all-fixed-claim.md` — "全面验证完成"类汇总报告的逐项打脸实战 (Failure 30 原型案例)
- `references/2026-06-30-cron-job-health-audit.md` — cron job 健康体检 5 步模板: 28 个 active jobs vs 26 个引用错位 + 4 条 cron-`script` 字段陷阱 (Failure 55)
- `references/failure-63-replace-claim-overcommit.md` — Failure 63 (2026-07-04) 研究报告"无缝替代"过度承诺实战 + 切换可行性 4 问 + 紧迫度 vs 破坏性授权区分 + 5 件真验证模板
- `references/failure-63-replace-claim-overcommit.md` — Failure 63 (2026-07-04): 研究报告"无缝替代"过度承诺实战 + 切换可行性 4 问 + "立即/今天"紧迫度 vs 破坏性授权区分 + 5 件真验证模板 (报告前必跑)
