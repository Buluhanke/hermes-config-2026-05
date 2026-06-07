# 跨平台 Skill 感知三件套 — 设计文档

> **兄弟架构**：`hermes-agent-status-monitor` 负责"agent 在线状态"广播；本文件描述的架构负责"skill 事件 + 审计 + 索引"，与前者同家族但不同侧重。
> 两个架构可以在同一个 Hermes 实例上**同时跑、互不依赖**。

## 背景与目标

用户原话（2026-06-07）："同步一下 QQ 和微信还有 telegram 的所有信息及技能，要让三个 agent 彼此都知道对方装过什么 skill 技能，毕竟 hermes 是一个整体，虽然各自机器人 agent 对话不相通但是要本事相通，可以随意调用。"

**关键洞察**：QQ/微信/Telegram 三个平台在 hermes 内部是**同一个 gateway 进程**下的三个 channel adapter，共用同一份 skills 库（~190 个），所以"本事相通"已经天然成立。**真正缺的是"彼此知道"**——也就是 awareness 维度。

## 三件套设计

### 1. 白板（Whiteboard）— 实时事件流

- 路径：`~/.hermes/registry/SKILL_WHITEBOARD.md`
- 模式：append-only，**不修改历史**
- 格式：`[YYYY-MM-DD HH:MM] <platform> | <action> | <skill> | <note>`
- 平台枚举：`qq` / `weixin` / `telegram`
- action 枚举：`installed` / `upgraded` / `uninstalled` / `used` / `shared-note` / `built`

### 2. 看板（Audit）— 跨平台调用聚合

- 路径：`~/.hermes/registry/SKILL_AUDIT.md`
- 模式：定期**整段重写**（由 cron 触发）
- 数据源：
  - `state.db` 的 `messages.tool_calls` 字段 → 统计实际调用过哪些工具（按 platform 字段聚合）
  - 白板的 `installed`/`upgraded`/`uninstalled` 事件 → 增删追踪
- 输出段：
  - 总览（时间、累计 tool call 数）
  - 各平台 Skill 调用频次 Top 10
  - 最近 N 天 Skill 变更事件表
  - 跨平台共性 Skill（被 ≥2 平台调用过）
  - 平台独占 Skill（只 1 个 agent 在用）

### 3. 索引（Registry）— 可注入 system prompt 的一行话清单

- 路径：`~/.hermes/skills/cross-platform-awareness/SKILLS_REGISTRY.md`
- 模式：定期**整段重写**
- 数据源：扫描 `~/.hermes/skills/**/SKILL.md` + `~/.hermes/profiles/default/skills/**/SKILL.md`
- 抽取字段：name（frontmatter）+ description（取首段 ≤30 字）+ category（从目录路径推）
- 使用：`cross_platform_skill.sh inject` 把整个文件 dump 到 stdout，拼到 system prompt 即可

## 入口脚本模板（已落 `~/.hermes/scripts/`）

```bash
cross_platform_skill.sh append <platform> <action> <skill> "<note>"
cross_platform_skill.sh audit      # 重写 SKILL_AUDIT.md
cross_platform_skill.sh regen      # 重写 SKILLS_REGISTRY.md
cross_platform_skill.sh inject     # 打印可注入到 system prompt 的索引段
```

**关键设计决策**：
- 单一入口（`cross_platform_skill.sh`）封装 4 个子命令 → 满足"用户问有快捷方式吗=要 1 行命令"的 UX 原则
- bash 是外壳（用户易记），Python 做实际工作（重写 MD）
- install 脚本 (`install_cross_platform_skill_sync.sh`) 幂等，可重跑

## Cron 配置

```cron
30 9 * * * /bin/bash $SCRIPTS/cross_platform_skill.sh regen >> $LOG_DIR/cron_skill_regen.log 2>&1 \
            && /bin/bash $SCRIPTS/cross_platform_skill.sh audit >> $LOG_DIR/cron_skill_audit.log 2>&1
```

每天 09:30 重建索引 + 跑审计，log 落到 `~/.hermes/logs/cron_skill_*.log`。

## Python 解析坑（实踩过）

### 坑 1：中文全角引号 `""` 撞 Python 源

写中文 description 时手滑打成全角引号（`""` 而不是 `""`），Python 解析器认不出来直接 SyntaxError。
**修法**：所有写到 .py 的中文文本都先 lint pass；或者在 heredoc/write_file 后立刻 `python3 -c "import py_compile; py_compile.compile(...)"` 验证。

### 坑 2：regex `match` 用了 capturing group 但用 `m.end()` 取尾

```python
m = re.match(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]\s+(\w+)\s*\|", line)
ts = m.group(1)
rest = line[m.end():]   # ← end() 指向第二个 group 之后, 不是 ts 之后
```

如果用 `re.partition` 或 `str.partition('|')` + 显式 split，比 regex 更稳：

```python
head, _, rest = line.partition("]")
ts = head[1:].strip()        # 去 [
parts = [p.strip() for p in rest.split("|")]
platform, action, skill = parts[0], parts[1], parts[2]
note = parts[3] if len(parts) >= 4 else ""
```

### 坑 3：state.db 平台字段不一定存在

`messages` 表未必有 `platform` / `source` 字段——取决于 gateway 怎么写。先 `PRAGMA table_info` 探测，存在就按字段聚合，不存在就 fallback 到字符串匹配（content 里有 "qq" / "weixin" / "telegram" 关键字）。

## 与状态广播 skill 的边界

| 用户问 | 用哪个 |
|--------|--------|
| "现在哪些 agent 在线" | `hermes-agent-status-monitor`（agent_status.py） |
| "技能库多了啥 / 总数" | `hermes-agent-status-monitor`（skill_summary） |
| "微信那边装了啥新 skill" | **本架构**（SKILL_WHITEBOARD） |
| "QQ 这周用过哪些 skill" | **本架构**（SKILL_AUDIT） |
| "把全部 skill 清单装进 prompt" | **本架构**（SKILLS_REGISTRY + inject） |

**不要混用**：状态广播管"在线 + 数量级"，本架构管"事件流 + 审计 + 索引"。两者的输出文件结构、cron 周期、报告形态都不一样，混了会乱。
