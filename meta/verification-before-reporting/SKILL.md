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
见 `references/failure-cases-archive.md`（v1.0→v2.0 精简时归档，共 292 行）。

最近 3 个高价值案例（摘要）：

**Failure 30**: "全面验证完成"类汇总报告必须逐项打脸——grep 报0≠真的0，可能是grep范围不够/路径错/格式问题。

**Failure 55**: cron job体检5步模板——28个active jobs vs 26个引用错位 + 4条cron-script字段陷阱。

**Failure 63**: 研究报告"无缝替代"过度承诺——必须标可行性等级+切换可行性4问+"立即/今天"紧迫度vs破坏性授权区分。

**Failure 64**: 删干净≠真删干净——5链体检（主链/手动池/MOA/辅助任务/ENV凭据），任一残留都会偷调。

**Failure 65 (2026-07-05)**: 任务完成报告三重验证必须齐全——
- ❌ 反模式: artifact 存在 + "声称推了 Telegram" + fact_store 没写 = 流程嘴炮 (Failure 65)
- ✅ 正解: 三项都验 (1) ls/grep artifact 存在 (2) fact_store INSERT 一条带 source=任务ID 的记录 + read back 确认 (3) 通知发送捕获 exit_code=0 + chat_id/msg_id delivery handle
- 触发场景: 任何"我标完成了"/"全部完成"类报告生成前
- 自动化: cron `no-execution-detector` (60aa915dfb3b) 每30分钟扫描 tasks/ 进行中任务 vs fact_store 12h 空转，触发立即动手修

详见：`references/failure-cases-archive.md`
