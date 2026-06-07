---
name: hermes-agent-status-monitor
description: 周期性运行 Hermes 跨平台 agent 状态广播 — 调用 ~/.hermes/scripts/agent_status.py 抓取在线 agent 与技能摘要、检测新增技能、写回 .agent_status.json、announce 广播。触发词：agent 状态广播、状态板、agent 在线状态、跨平台 agent 状态、agent_status、状态报告、status broadcast、status board、agent 状态巡检。
---

# Hermes 跨平台 Agent 状态监控

周期性（典型 15 分钟）执行 `agent_status.py`，抓 QQ/微信/Telegram 三个 agent 的在线状态 + 共享技能库摘要 + 新增技能检测，写回状态文件并广播。

## 适用场景

- cron 任务："每 N 分钟刷新一次 agent 状态"
- 用户问："现在哪些 agent 在线？技能库多没多东西？"
- 平台协调：跨 agent 状态公告板
- 技能库基线追踪：上次广播后有没有新技能加入

## 5 步标准流程

### 1. 并行抓取原始数据

```bash
python3 ~/.hermes/scripts/agent_status.py list
python3 ~/.hermes/scripts/agent_status.py skill_summary
python3 ~/.hermes/scripts/agent_status.py whoami   # 看自己平台
```

三条命令互不依赖，必须**并行**发（一次 function_calls 块里），不要串行。

### 2. 解析输出

- `list` 输出末尾的 `共 N 个 agent 在线` —— 这是真实数字。**忽略表格里任何带 `?` 平台或 `last_broadcast` / `_meta` 这类元数据行**（见下方坑 1）。
- `skill_summary` 输出开头的 `共 N 个` —— 总技能数；【🔥 核心技能】段落列出的实际条目数 —— 核心技能数（脚本里硬编码 15 个，注册表里只展示存在的）。
- `whoami` —— 当前 agent ID 和平台。

### 3. 检测新增技能（用 baseline diff）

```python
# 关键：把当前 skill 集合与上次 _meta.last_broadcast.skill_list 做差集
new_skills = sorted(current_skills - prev_skill_list)
removed_skills = sorted(prev_skill_list - current_skills)
```

首次运行 `prev_skill_list` 为空，diff 全是新增属正常，不报错。

### 4. 写回状态文件（**核心坑：必须用 _meta 命名空间**）

⚠️ **坑 1（已踩过）**：`agent_status.py` 的 `load_status()` 返回一个**扁平 dict**，`announce()` 直接把 `{agent_id: {...}}` 写进去，**没有任何元数据命名空间**。如果你天真地把 `last_broadcast` 当顶层 key 写进去：

```json
{
  "last_broadcast": {...},       // ← 污染！list 命令会把它当 fake agent
  "telegram-12345": {...},
  "qq-67890": {...}
}
```

`list` 命令会显示 `共 3 个 agent 在线`（多了 last_broadcast 这个假的）。正确做法是把元数据塞进 `_meta` 字段：

```json
{
  "telegram-12345": {...},
  "qq-67890": {...},
  "_meta": {
    "last_broadcast": {
      "time": "14:30",
      "iso": "2026-06-07T14:30:00",
      "agents_online": 2,
      "platforms": ["telegram", "qq"],
      "core_skills": 13,
      "total_skills": 190,
      "skill_list": [...],   // ← baseline diff 用这个
      "new_skills": [...],
      "removed_skills": [...],
      "report": "..."
    }
  }
}
```

读取时也要过滤掉 `_meta` 才是真实 agent 列表。

### 5. 广播

```bash
python3 ~/.hermes/scripts/agent_status.py announce "📡 14:30 状态广播：2 个 agent 在线 | 核心技能 13 | 总技能 190"
```

`announce` 会自动添加 `unknown-<pid>` 之类的 agent 条目到状态文件（如果 `HERMES_PLATFORM` 环境变量未设），不影响 `_meta`。

## 报告输出格式（500 字以内）

```
📡 Hermes 状态广播 @ 14:30
👥 在线 agent: 2 | 平台: 🔵Telegram / 🟡QQ
🔥 核心技能 13 个 | 📦 总计 190 个技能
🆕 新增：hermes-new-skill, another-skill 等 2 个
```

- 时间 `%H:%M` 中文格式（"14:30"）
- 平台 emoji 映射：`telegram→🔵Telegram`、`weixin/wechat→🟢WeChat`、`qq/qqbot→🟡QQ`、`unknown/cron→⚪cron`
- 技能格式固定：`🔥 核心技能 N 个 | 📦 总计 N 个技能`
- 新增技能另起一行标注 `🆕 新增：xxx`，超过 8 个写 `等 N 个`
- 移除技能：`🗑️ 移除：xxx`

## 已知坑（执行前必读）

1. **扁平 dict 污染**（见上 step 4）—— 必须用 `_meta` 命名空间
2. **平台识别 fallback** —— `agent_status.py` 的 `get_platform()` 依次检查 `HERMES_PLATFORM` 环境变量 → hostname 含 telegram/weixin/qq → `~/.hermes/config.yaml` 的 `platforms` 键。cron 任务三项都不匹配时归为 `unknown`，广播显示 `⚪cron` 是正常现象，**不要试图给它绑 telegram/wechat/qq 标签**
3. **首次运行无基线** —— `new_skills` 永远是当前全集（190 个），这是预期行为。下一次起才有真实 diff
4. **`list` 表格里的 5 分钟过期清理** —— 脚本会自动清理 `>30 分钟` 无更新的 agent 条目。如果你的 agent 15 分钟广播一次，永远不会过期
5. **核心技能清单是脚本硬编码的 15 个** —— `agent_status.py` 的 `skill_summary()` 内部维护了 `core_skills = [...]` 列表，注册表里有几个就显示几个。本次实测：13 个存在于注册表，`browser-automation` 和 `auto-self-healing` 不在
6. **不要修改 `agent_status.py`** —— 跨 agent 共用脚本，修改会影响所有平台。除非所有 agent 都升级，否则改动要走 PR 流程

## 一键脚本

参见 `scripts/status_broadcast.py` —— 把 5 步流程串成一个可重入的 Python 脚本，cron 直接 `python3 -c "import subprocess; subprocess.run([...])"` 调它即可。

## 相关文件

- `references/broadcast-format.md` — 报告输出格式（HH:MM、平台 emoji、🔥/📦 计数行、🆕 标注）+ registry vs filesystem 数据源真相
- `references/file-format-gotcha.md` —— `.agent_status.json` 的结构详解、为什么 `_meta` 命名空间必要
- `scripts/status_broadcast.py` —— 5 步流程的可重入实现

## 不要用于

- 修改 `agent_status.py` 源码（用 `hermes-agent-skill-authoring` 或 `hermes-internal-architecture-patterns`）
- 审计/检查所有 cron 任务是否冲突（用 `scheduled-task-audit`）
- 推送通知给用户（用 `hermes-rhythm-gate` 或 `notification-rhythm-pipeline`，本 skill 只产 report 不负责投递）
- 通用 cron 编写（用 `proactive-execution`）

## 兄弟架构：跨平台 Skill 感知三件套（白板+看板+索引）

本 skill 是"agent 在线状态广播"流派。还有一个**同家族但不同侧重**的"跨平台 Skill 感知"流派（2026-06-07 首次实现）。两者共享目标（"让 QQ/微信/Telegram 三个 agent 彼此知道对方"），但走的路不同：

| 维度 | 本 skill (状态广播) | 兄弟架构 (skill 感知三件套) |
|------|-------------------|----------------------------|
| 侧重 | agent **在线状态** + 技能**总数/新增** | skill **事件流** + **跨平台调用审计** + **可注入 system prompt 的索引** |
| 流向 | 单向广播（一个 agent → 公告板） | 双向（任一 agent 写白板，所有 agent 读） |
| 数据 | 在线 agent 列表 + 技能 baseline diff | append-only 事件 + DB 聚合 + 索引段 |
| 落点 | `.agent_status.json` + announce | `SKILL_WHITEBOARD.md` + `SKILL_AUDIT.md` + `SKILLS_REGISTRY.md` |
| 触发场景 | "哪些 agent 在线 / 技能库多了啥" | "微信装了啥 / QQ 用了啥 / 启动时把全部 skill 装进 prompt" |

**两者并存不冲突**。同一个 Hermes 实例可以同时跑：
- `agent_status.py` 每 15 分钟广播（背景）
- `cross_platform_skill.sh` 每日 09:30 重建索引+审计（背景）
- 任意 agent 启动时 `inject` 索引段到 system prompt

**怎么选**：用户问"哪些 agent 在线" → 本 skill；用户问"彼此装过啥 skill" → 兄弟架构。详细设计、shell entry 模板、Python 解析坑见 `references/cross-platform-skill-awareness.md`。

**入口脚本**：兄弟架构的入口是 `~/.hermes/scripts/cross_platform_skill.sh {append|audit|regen|inject}`，与本 skill 的 `agent_status.py` 互不依赖。
