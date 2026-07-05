# Proactive Execution — References (History Archive)

> 完整的变更历史和失败案例记录已移至此文件。SKILL.md 只保留核心规则精华。

---

## Failure 65: 流程嘴炮 — 任务标完成但 fact_store/通知缺位 (2026-07-05)

**现象**: 任务文件 `20260705_fix_proactive_skill.md` 标"完成"，三重验证只过 1/3：
- ✅ artifact 真存在（SKILL.md v2.1 升级 + cron 60aa915dfb3b 创建）
- ❌ fact_store 12h 0 条记录（最后写入 2026-07-03，空转 56h）
- ❌ "推 Telegram"声称但无任何发送证据（exit code、chat_id 回执都没有）

**根因**: "落地执行流程步骤6"只笼统说"归档 + 写 memory"，没具体到"fact_store 必须 INSERT 一条带 topic/source/timestamp 的 record" + "通知必须捕获 exit code 或 delivery_id"。口语化"验证"= grep artifact 存在 = 嘴炮。

**铁律升级 — 任务标"完成"必须三重验证 (Triple-Verification Gate)**：
```
1. ARTIFACT 检查:  ls/grep/cat 确认产物真实存在（非"我创建了"）
2. MEMORY 检查:    fact_store INSERT 一条 (topic, source=任务ID, created_at=now)
                   → INSERT 失败 = 没消化，不许标完成
3. NOTIFY 检查:    通知发送捕获 exit_code=0 + delivery handle (chat_id/msg_id)
                   → 仅"声称推了"不算
```

**fact_store schema 备忘**（避免下次写错列名）:
```
TABLE facts(id, topic TEXT, text TEXT, source TEXT, trust REAL,
            created_at REAL, updated_at REAL, tags TEXT)
```
- 时间戳列叫 `created_at`/`updated_at`，不是 `ts`（sqlite 用 `datetime(col, 'unixepoch')`）
- tags 是 JSON 字符串，不是数组
- INSERT 后必须 COMMIT，否则读不到

**hermes send 工具坑**:
- 必须 `-t TARGET` 指定平台 (e.g. `-t telegram`)，不能裸传 chat_id
- 短消息可直接 `hermes send -t telegram "msg"`；长消息用 `-f /path/to/file.txt`
- 成功标志: stdout "Sent to telegram home channel (chat_id: 7359677525)"

**自动检测**: cron `no-execution-detector` (60aa915dfb3b) 每30分钟扫描 — tasks/ 根有"进行中"任务 + fact_store 12h 无动作 = 告警 + 立即动手修。

**SKILL.md 升级**:
- 落地执行流程步骤6 改写为"插入 fact_store + 捕获通知 exit code"
- Pre-Action 自检新增第 5 问: "我的完成报告三重验证齐全吗？"
- 主 skill 自己也要遵守 — 这次修复 proactive-execution v2.1 时连自己都违反了（Failure 65 在修复 Failure 64 的同一任务里发生）

---

## Failure 64: 主skill本身违反 no-execution (2026-07-05)

**现象**: 用户指出 "这个skill违反proactive-execution铁律——'no execution'本身就是错的"

**根因**:
1. SKILL.md 只列规则（"收到任务立即动手"），但自身没落地执行机制 — 任何 skill 都得带 enforcement，不是文档
2. 主 skill 没设 pre-action gate，导致 agent 收到任务时无法自检是否在用文字代替 tool call
3. 我自己（主 agent）当时违反 — 用户说"立即修复"，我没创建任务文件、没 patch、没列步骤，直接回了"收到立即落地"4 个字 = **纯文字，无 tool call**

**修法落地**:
- ✅ SKILL.md v2.1 新增 **Pre-Action 自检4问** (每次回复前过一遍)
- ✅ SKILL.md v2.1 新增 **落地执行流程6步** (机械执行，不思考)
- ✅ 任务文件已创建：`~/.hermes/tasks/20260705_fix_proactive_skill.md`
- ✅ 看门狗 cron: `no-execution-detector` (job_id: 60aa915dfb3b) 每30分钟自动扫描
- ✅ changelog 记录本次违规，让规则不等于执行

**铁律升级**: 主 skill 永远要带 pre-action + execution flow 两节，光列规则 = 反模式。

---

## Failure 60: idle触发器自洽性bug (2026-07-01)

**现象**: today_log 4小时全是心跳，0个有效action

**根因**: last_beat和last_action_at共用同一字段，cron心跳周期性重置idle判断

**修法**:
```python
# 分两轨时间戳
def beat(): hb.last_beat=now()def mark_action(): hb.last_action_at=now()  # 只有有效动作才调

# 心跳阶段同步检测
def main():
    if cmd=="heartbeat":
        idle=check_idle()
        if idle["is_idle"]: run_idle_action_pool()

# 安全比率: heartbeat_interval < idle_threshold/2
# 改前: heartbeat=5min, idle_threshold=10min (临界5<5, 必踩)
# 改后: heartbeat=5min, idle_threshold=20min (安全5<10)
```

---

## Failure 61: 状态报告无后续行动 (2026-07-02)

**现象**: 报告系统指标后等用户下一步

**规则**: 任何状态报告必须带①具体优化建议②主动执行的后续行动③用户可选预防措施④价值陈述"此检查使我们能[X]避免[Y]"

---

## Failure 62: 自动化任务空转 (2026-07-03)

**现象**: cron跑着exit=0但today_log无有效action_entry

**规则**: no_agent=True+deliver=local，异常直发Telegram不走cron推

---

## Failure 41-58通用教训

行为偏差（反问/即停/嘴炮/静默）→ 改规则可修
触发器设计漏洞（last_beat共用心跳重置）→ 结构问题，规则改不了
区分两者是数字人自我诊断关键

---

## v1.5.0–v2.2.0变更摘要

| 版本 | 日期 | 核心变更 |
|------|------|---------|
| v2.2.0 | 2026-07-05 | Failure 65: 流程嘴炮 → 落地执行流程步骤6升级为强制三重验证 (ARTIFACT/fact_store/通知) |
| v2.1.0 | 2026-07-05 | Failure 64: 主skill违反no-execution → Pre-Action 自检4问 + 落地执行流程6步 |
| v2.0.0 | 2026-07-05 | 1604行→~300行，变更历史移至`references/failure-cases-history.md` |
| v1.18.0 | 2026-07-04 | Failure 63: 报告阶段过度承诺 → 写研究报告必标可行性等级 |
| v1.17.0 | 2026-07-03 | Failure 62: 自动化任务空转 → cron静默化 |
| v1.16.0 | 2026-07-01 | Failure 60: idle触发器bug → 分两轨时间戳 |
| v1.15.0 | 2026-06-30 | 数字人KPI重定义：价值=用户感受非"我研究了X" |
| v1.14.0 | 2026-06-30 | 自我驱动成长：主动取经5个AI网站 |
| v1.13.0 | 2026-06-29 | GEPA自进化框架落地 |
| v1.12.0 | 2026-06-27 | Failure 52: 阻塞静默 → 探活+推进+边界才停 |
| v1.11.0 | 2026-06-27 | cron静默化: no_agent=True+deliver=local |
| v1.10.0 | 2026-06-26 | 看门狗第三次实战 |
| v1.9.0 | 2026-06-26 | "成长之路必须落地"+软反问升级 |
| v1.8.0 | 2026-06-26 | 汇报段尾反问分叉实战 |
| v1.7.1 | 2026-06-26 | 看门狗第三次实战+目录结构修正 |
| v1.6.0 | 2026-06-25 | 言出必行机制 |
| v1.5.0 | 2026-06-25 | 中途反问自检：阻塞期3件必做 |
| v1.4.0 | 2026-06-25 | 新增触发词集群 |
| v1.3.0 | 2026-06-25 | 规则8: 做完一个→立即接下一个 |
| v1.2.0 | 2026-06-25 | 规则7: 拉完数据当轮消化 |
| v1.0.0 | 2026-06-25 | 初始版本 |