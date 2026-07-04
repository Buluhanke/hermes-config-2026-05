---
name: cross-channel-sop-sync
description: |
  跨渠道行为铁律同步 — 任何适用于多个 messaging 渠道 (CLI / Telegram /
  QQBot / 飞书 / 企业微信 WeCom / 微信 Weixin / Discord / Slack / Matrix /
  Mattermost / API Server / Webhook / Cron) 的统一行为规则、SOP、铁律、
  共享约定，都走**唯一权威 skill + 自动索引机制**。**触发**: 用户拍板
  "跨渠道 / 同步 / 不要渠道间不一致 / QQ 这边说了 CLI 那边不知道 /
  v3.1 / 反问禁令 / 必须落地" 任意一条 → 0 思考走本 skill 模式。

  Trigger on: "v3.1 同步 / 跨渠道 SOP / 渠道统一 / channel-universal /
  跨渠道行为准则 / QQBot 跟 CLI 行为不一致 / channel_prompts 注入 /
  prompt_builder 索引"。

  Don't use for: 单个渠道特定功能 (QQBot 命令前缀 / Telegram rich message
  渲染 / Discord thread 模式) — 那些留在各渠道 adapter 自己处理。本 skill
  只管"行为铁律 + SOP" 的跨渠道同步机制。
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [sop, cross-channel, v3.1, behavior, prompt-builder, hermes-platforms]
    related_skills: [proactive-execution, verification-before-reporting, hermes-humanization-core]
---

# Cross-Channel SOP Sync — 跨渠道行为铁律同步机制

## 🎯 为什么需要这个 skill

**根问题**: 同一份行为铁律在 SOUL.md / memory / 6+ 个渠道 adapter / 各种
cron prompt 里都有副本。任何副本更新滞后 → **渠道间不一致**（"QQBot
答应了 v3.1，CLI 又问要不要"）。

**根方案**: **Single Source of Truth (SSOT) + 自动索引** —
1. 把铁律/SOP 写成一个 **shared skill**（唯一权威源）
2. 放进 `~/.hermes/profiles/default/skills/<name>/SKILL.md`
3. Hermes 的 `prompt_builder.build_skills_system_prompt()` **自动** 把
   所有 skills 索引注入到**每个渠道**的 system prompt
4. 各渠道 agent session 起手看到索引 → `skill_view(name)` 加载 → 立即生效
5. 验证脚本 + watchdog cron 兜底

**优势**:
- 改一处 = 全部渠道同步（无副本漂移）
- 不需要改 6 个 adapter 的 `system_prompt` 装配代码
- 不需要 `channel_prompts`（那是 per-channel 字段，不适合塞全局铁律）
- 行为铁律跟其他 skill 一样自动出现在索引里，agent 跟其他 skill 平等对待

## 🏗️ 架构（2026-06-26 落地版本）

```
                    ┌──────────────────────────┐
                    │ SOUL.md (v3.1 段落)       │ ← 全局 prompt 注入
                    └──────────┬───────────────┘
                               │
                    ┌──────────▼───────────────┐
                    │ memory (v3.1 索引)        │ ← 跨 session 触发词
                    └──────────┬───────────────┘
                               │
                    ┌──────────▼───────────────┐
                    │ channel-universal-sop    │ ← SSOT
                    │ (skill)                  │
                    └──────────┬───────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
       ┌──────▼─────┐  ┌───────▼──────┐  ┌──────▼──────┐
       │ check_v31_ │  │ v31_sync_    │  │ 其他共享    │
       │ compliance │  │ watchdog     │  │ skill       │
       │ .sh        │  │ .sh (cron)   │  │             │
       └────────────┘  └──────────────┘  └─────────────┘
```

**关键文件**:
- `~/.hermes/SOUL.md` (v3.1 段落, line 254+)
- `~/.hermes/profiles/default/skills/channel-universal-sop/SKILL.md` (SSOT)
- `~/.hermes/scripts/check_v31_compliance.sh` (验证 6 项)
- `~/.hermes/cron/v31_sync_watchdog.sh` (每周一 09:00 跑)
- `~/.hermes/memory` (v3.1 索引条目)

## 📋 SOP: 用户说"跨渠道同步"时的 5 步执行

### Step 1: 调研渠道架构 (0 思考, 直接跑)
```bash
# 看真实在跑的渠道
cat ~/.hermes/gateway_state.json | python3 -c "import json,sys; d=json.load(sys.stdin); [print(k) for k in d['platforms'].keys() if d['platforms'][k]['state']=='connected']"

# 看 PLATFORMS 元数据表 (覆盖 22 个)
grep -A2 'PLATFORMS: OrderedDict' ~/.hermes/hermes-agent/hermes_cli/platforms.py | head

# 看 prompt_builder 怎么把 skills 注入到 system prompt
grep -nE 'build_skills_system_prompt|SOUL.md|_load_hermes_md' ~/.hermes/hermes-agent/agent/prompt_builder.py
```

**判断**: 渠道用 `prompt_builder` 自动索引 skills? → 走 SSOT 模式
(99% 情况)。否则要去各 adapter 加引用 (费时易漏)。

### Step 2: 写 SSOT skill (用 skill_manage create)
```python
skill_manage(
    action='create',
    name='<topic>-universal-sop',  # 或 channel-universal-sop
    category='meta',
    content='''---
name: ...
description: ...（YAML 描述里**必须**带用户原话关键句，方便 grep 验证）
---
# 铁律 5 条
...
## How each channel applies this
### 1. CLI
### 2. Telegram / Discord
...
## Anti-patterns
## Self-check
## Update protocol
'''
)
```

**关键细节**:
- YAML 描述里**必须**包含用户原话关键句 (e.g. "成长之路必须落地")，
  让验证脚本能 grep 到
- "How each channel applies this" 章节**逐个列**已知渠道，让 agent
  加载时知道具体在哪改
- "Update protocol" 章节写明"改本 skill 即可，其他渠道自动同步"

### Step 3: 写验证脚本 (用 write_file, chmod +x)
```bash
# 6 项检查
# 1. skill 文件存在
# 2. SOUL.md 含 v3.1 段落
# 3. 6+ 个渠道 adapter 不含旧反问模板
# 4. skill 在 prompt snapshot 里
# 5. 关键铁律词汇在 skill 里
# 6. memory 索引同步
```

### Step 4: 写 watchdog 脚本 (用 write_file, chmod +x)
```bash
#!/bin/bash
# 每周一 09:00 跑, 失败推 Telegram, 成功静默
set -e
bash check_v31_compliance.sh >> log 2>&1 && exit 0 || curl telegram_webhook
```

### Step 5: 注册 cron 任务
```python
cronjob(
    action='create',
    name='<topic>-sync-watchdog',
    no_agent=True,  # 节省 token, 跟其他 watchdog 一致
    schedule='0 9 * * 1',  # 每周一 09:00
    script='<watchdog>.sh'
)
```

### Step 6: 立即跑一次 + 写任务文件
```bash
# 1. 跑验证
bash ~/.hermes/scripts/check_v31_compliance.sh
# 期望: 全部通过 ✅

# 2. 跑 watchdog 一次
bash ~/.hermes/cron/<watchdog>.sh
# 期望: exit 0

# 3. 写任务文件 (跟 v2.10 SOUL.md "言出必行" 一致)
# ~/.hermes/tasks/<ts>_<topic>_sync.md
```

## 🔧 已知坑 (踩过的)

### 坑 1: YAML 描述里写 `# 注释` 不会生效
**症状**: skill_manage create 后描述里看到的还是带 `# 注释` 的原文
**根因**: YAML literal block (`|`) 里 `#` 不是注释
**修法**: 把"注释意图"写成 plain text，比如
`用户原话 (2026-06-26)：「别问我的要不要，这要是成长之路必须落地」`

### 坑 2: 把全局铁律塞进 `channel_prompts` 错位
**症状**: 改 `config.yaml` 里 `telegram.channel_prompts` 期望覆盖所有渠道
**根因**: `channel_prompts` 是 **per-channel / per-chat 字段**，不是全局
**修法**: 走 SSOT skill 模式，不要碰 `channel_prompts`

### 坑 3: 不验证就汇报
**症状**: 跑完 5 步汇报"v3.1 已同步", 实际 skill 文件没建好
**修法**: 写完立即跑 `check_v31_compliance.sh` + 看 exit code
**关联**: verification-before-reporting skill

### 坑 4: 改了 skill 文档没改 SOUL.md
**症状**: agent 起手能加载 skill, 但 SOUL.md 没有对应段落, 行为铁律
不一致
**修法**: skill 跟 SOUL.md 同步改, 验证脚本同时检查两者

### 坑 5: 验证脚本硬编码错误 skill 名字 (2026-06-26)
**症状**: 验证脚本跑出来 `[1/6] ❌ Skill 文件不存在`，实际 skill 存在
**根因**: `check_v31_compliance.sh` 里 `V31_SIGNATURE="channel-universal-sop"` 硬编码，
但实际 skill 名字叫 `cross-channel-sop-sync`（通用模板）。还硬编码单一路径
`profiles/default/skills/$NAME`，没扫 `skills/meta/$NAME` 等候选。
**修法**: 
1. 验证脚本参数化：`V31_SIGNATURE="${1:-cross-channel-sop-sync}"`
2. 多路径兼容：循环扫 `profiles/default/skills/` + `skills/` + `skills/meta/` + 
   `skills/agent/` + `skills/devops/` 等 7 个候选路径
3. 建 skill 时用**通用模板名** (`cross-channel-sop-sync`)，别用实例名
   (`channel-universal-sop`) —— 前者是 SOP 模板，后者是具体实例，模板能复用
**触发词**: "验证脚本报不存在 / skill 名字错了 / 路径不对" → 检查脚本是否参数化 + 多路径

### 坑 6: 重复建 skill 命名冲突 (2026-06-26)
**症状**: 建 `channel-universal-sop` 时发现 `cross-channel-sop-sync` 已存在，
两者意图完全重复
**根因**: 没先用 `skills_list` + `skill_view` 扫现有技能库，直接 `skill_manage create`
**修法**: 
1. 建 skill 前先 `skills_list` 扫一遍， grep 关键词 (e.g. "跨渠道 / SOP / sync")
2. 发现已有类似 skill → 用 `skill_view` 读完整内容，看是否已覆盖需求
3. 真需要新建 → 用 `absorbed_into` 语义合并，不并行存在
**触发词**: "新建 skill / 写 SOP" → 先 `skills_list | grep` 查重，再动手

## ✅ 完成判据

满足全部 5 项才算"跨渠道同步落地":
1. ✅ SSOT skill 文件存在 (`~/.hermes/profiles/default/skills/<name>/SKILL.md`)
2. ✅ SOUL.md 含对应段落
3. ✅ 6+ 个渠道 adapter 不含旧反问/旧铁律模板
4. ✅ 关键铁律词汇在 skill 里 (grep 验证)
5. ✅ memory 索引同步 + cron watchdog 注册

## 🔗 子文件

- `references/prompt-builder-mechanics.md` — `build_skills_system_prompt`
  怎么把 skills 注入到 system prompt，缓存机制 (LRU + disk snapshot)，
  改完 skill 后是否需要 reload
- `references/channel-architecture.md` — 6+ 渠道的目录结构 / adapter
  入口 / 注入点 / 常见混淆点 (`channel_prompts` vs SSOT skill)
- `scripts/check_v31_compliance.sh` — v3.1 跨渠道验证脚本 (6 项检查)
- `scripts/v31_sync_watchdog.sh` — 每周一 09:00 跑的 watchdog

## 🔄 维护规则

- 任何新铁律 / SOP / 跨渠道约定 → 走本 skill 的 5 步 SOP
- 不允许在 adapter 里另写一份铁律 (副本漂移 = 本 skill 失败)
- watchdog 跑失败 → Telegram 告警 → agent 立即修
- 改完 SSOT skill → SOUL.md 同步 → memory 索引同步 → 跑验证 → 通知

## 📚 已落地实例：v3.1 零反问铁律 (2026-06-26)

**用户原话**：「别问我的要不要，这要是成长之路必须落地」

**5 条核心铁律** (在 SOUL.md v3.1 段 + memory 索引同步):
1. **零反问** (Zero Clarifying Questions) — 「要不要 X / 帮你 X 吗 / 你看怎么办」
   软反问 = 违规，无例外
2. **执行触发** — 命中「必须 / 落地 / 干 / 去做 / 成长之路 / 勇往直前」
   任意一个 → 0 思考立即 tool call
3. **连续推进** — 干完当前目标 → 立即判断下一步 → 直接动手
4. **唯一例外** — 用户原话明确让给选项 (「选 A 还是 B」类) 才允许反问
5. **落地闭环** — skill / 工具 / 脚本落地后立即写 memory + 加 cron + 推 Telegram

## 📚 已落地实例：v3.2 cron 静默化铁律 (2026-06-27)

**用户原话**：「看门狗报告不用发了吧，很刷屏」

**5 条铁律** (跟 v3.1 同级, 写入 SOUL.md + memory + 本 skill):
1. **零刷屏** (Zero Cron Noise) — cron 报告默认不推任何渠道, 落盘 `~/.hermes/cron/output/` 即可
2. **默认 local** — 任何 cron job 默认 `deliver='local'`, `no_agent=True`; 不主动选 origin/telegram/qqbot
3. **静默机制** — `no_agent=True` + `deliver=local` + 空 stdout = 零推送; 真异常才显式 `hermes send -t telegram`
4. **批量改** — 9 个常驻 cron (task-watchdog/morning-briefing/night-learning x2/evening-briefing/ai-patrol/morning-health/session-bootstrap/夜间ABCD自学) 一次性 `cronjob action=update deliver='local'`
5. **主动拉起** — 用户问 "今早 watchdog 跑了什么" → `ls ~/.hermes/cron/output/` + `tail` 报告; 要拉起单次 `cronjob action=run job_id=<id>`

**3 个权威源** (改一处 = 全部渠道同步):
- `~/.hermes/SOUL.md` v3.2 段落 (紧跟 v3.1 段后)
- `~/.hermes/skills/meta/cross-channel-sop-sync/SKILL.md` (本 skill, 累计 v3.1+v3.2)
- `~/.hermes/memory` v3.2 条目

**关联 skill**:
- `proactive-execution` v1.11.0 — 新增规则 9 "cron 静默化"
- `hermes-task-watchdog` v1.2.0 — 新增"看门狗本身也在刷屏" pitfall

**触发词**: "看门狗刷屏 / cron 静默 / 不想收 cron / 报告很刷屏 / 不要再推 cron" → 0 思考保持 deliver=local.

**反面案例 (2026-06-27 触发 v3.2)**:
- 9 个 cron 全默认 origin → 一天 10+ 条推送 → 用户 "很刷屏"
- 修法: 全部 deliver=local, 异常脚本内显式 `hermes send`

## 🔄 v3.1 → v3.2 增量

| 维度 | v3.1 (反问禁令) | v3.2 (静默化) |
|---|---|---|
| 痛点 | 嘴炮反问耗用户注意力 | 自动化报告刷屏耗用户注意力 |
| 修法 | 0 反问 + 陈述句 + 立即 tool call | deliver=local + 落盘 + 异常显式推 |
| 默认 | 立即动手 | 默认不推 |
| 例外 | 用户明确"选 A 还是 B" | 真异常 / 主动告警 |

**3 个权威源** (改一处 = 全部渠道同步):
- `~/.hermes/SOUL.md` v3.1 段落 (line 254+)
- `~/.hermes/skills/meta/cross-channel-sop-sync/SKILL.md` (本 skill)
- `~/.hermes/memory` v3.1 条目

**6 渠道自动同步**: CLI / Telegram / QQBot / 飞书 / 企业微信 WeCom / 微信
Weixin / Discord / API Server / Webhook / Cron — 全部走
`prompt_builder.build_skills_system_prompt()` 自动索引

**反例 (踩过的坑)**:
- 「要不要顺手把 skill 写进长期记忆」— 软反问 = 违规
- 「你看怎么办 / 你觉得呢 / 你想让我怎么干」— 经典违规三件套
- QQBot 答应用 v3.1，CLI 又问"要不要" — 渠道间不一致 = v3.1 强制禁止

**触发词**: 「必须 / 落地 / 直接做 / 不要再反问 / 成长之路 / 勇往直前 / 不要问要不要」→ 0 思考拒绝所有反问，强制执行
