# 每日 Skill 采集员 cron 协议

> 来源：2026-07-01 cron 任务首次实战落地，5/5 全部安装成功
> 触发：用户在 prompt 里给"你是 Hermes 技能采集员。每天 03:00 跑一次"的硬性 quota 任务

## 1. 铁律（用户原话，不可妥协）

- **任务量固定 5 个**。找到 5 个就停，找不到 5 个**不许 SILENT**。
- **禁止 SILENT 的标准**：5 个全部搜索+处理完成才算任务完成。
- 用户原话触发词：「必须搜索到 hermes 当下缺的 5 个 skill 并安装落地」→ 0 思考执行，不要"找不到就静默"。
- 找不到就**明确写出"为什么没找到"**，列具体失败原因（搜索引擎全 0 / 仓库不存在 / verdict dangerous 等），不要糊弄。

## 2. 工作流（4 步硬流程）

### Step 1: 列缺位清单（5 类，每类 1-2 个候选）
按 Hermes 当前缺的能力排序，列出 5 类缺位：

| 优先级 | 缺位类别 | 判断依据 |
|---|---|---|
| 1 | 真屏幕理解 / 多模态 agent | MCP 没 vision-grounding 专项 |
| 2 | 离线工具集成 / 本地服务编排 | 多语言多 runtime 编排 |
| 3 | 安全 / 隐私 / 凭据管理 | 凭据 + API key 管理 |
| 4 | 性能监控 / 内存治理 | Mac mini 24GB 自保护 |
| 5 | 跨平台 / 跨渠道统一 | 用户多设备多渠道 |

### Step 2: 5 个并行 web 搜索
- 每类用 `web_search` 搜 1-2 次
- 搜的目标：`site:github.com` 找有 SKILL.md 的仓，或 `agentskill.sh` / `skills.sh` / `skillsmp.com` 目录
- **SearXNG MCP 不可靠**（实测 2026-07-01 5 个并行调用全 0 返回），**用 `web_search`**
- 找不到现成 skill 时，把搜索到的 GitHub 仓库 URL 落盘到 `~/.hermes/skills_pending.json` 作为候选

### Step 3: 安装 / 落地（两个必有一）
- 已有成熟的、有 SKILL.md 的 → 用 `hermes skills install` 安装
- 只有 README / awesome-list 类 → 落 `~/.hermes/skills_pending.json` 当作 discovery 参考
- **每个 skill 必须留下可验证痕迹**：要么装了，要么 URL 落盘了

### Step 4: 强制 markdown 报告（不允许只"汇报一下"）

格式（用户钉的）：
```markdown
# 每日 Skill 采集 <YYYY-MM-DD>
1. <skill name> — 已安装 / 已落盘 URL / 搜索失败原因
2. ...
3. ...
4. ...
5. ...

落地清单：
- ~/.hermes/skills/<installed>/ (N 个)
- ~/.hermes/skills_pending.json (M 个候选)
```

每行必须含：skill 名 + 处理结果（已装/已落盘/搜索失败）+ 失败原因（如有）。

## 3. `hermes skills install` 实战命令（2026-07-01 验证）

```bash
# 路径 C: raw SKILL.md URL（最稳 — 适用于 anthropics/skills 这种多 skill 仓）
hermes skills install --yes \
  "https://raw.githubusercontent.com/anthropics/skills/main/skills/<skill-name>/SKILL.md" \
  --name "<skill-name>"
```

**必须加 `--name` 的理由**（实战的"末段命名陷阱"）：URL 末段 `SKILL.md` 之前的 `main` / `master` 会被当 skill 名，所有此类 skill 都装到 `~/.hermes/skills/main/` 互相覆盖。

**5 个并行安装推荐**：5 个独立的 `terminal` background call 同时跑（每个约 5-15s）。串行做浪费时间。

**装完必查**：
```bash
ls ~/.hermes/skills/main/ 2>/dev/null   # 撞名信号
hermes skills list | grep <name>         # 验证 enabled
```

撞名修法：`mv ~/.hermes/skills/main ~/.hermes/skills/<real-name>`

## 4. Ponytail 适配（不造轮子）

在 Step 2 搜之前先检查「昨日采集记录」：

```bash
cat ~/.hermes/skills_pending.json   # 看 yesterday 的 installed_today + missing_categories_remaining
```

避免重复装同类 skill，优先填 `missing_categories_remaining` 列出的空缺。

## 5. 报告落盘格式（写在 ~/.hermes/skills_pending.json）

```json
{
  "date": "2026-07-01",
  "installed_today": [
    {"name": "mcp-builder", "category": "mcp-integration", "source": "anthropics/skills/...", "verdict": "safe", "uses": "..."}
  ],
  "rejected": [...],
  "missing_categories_remaining": [...],
  "outcome": "5/5 落地完成 (5 个 SAFE 安装)"
}
```

**outcome 字段钉死成 `N/5 落地完成` 格式**，方便后续 cron 跑扫描脚本判断当日是否达标。

## 6. 关联 / 区别

| Skill | 关系 |
|---|---|
| `idle-learning-rounds` | 姐妹 skill：A→B→C→D 多方向扫描 + fact_store。本协议是 quota-driven harvest + 安装落地，**不写 fact_store** |
| `hermes-skill-optimization` (本 skill 主 SKILL.md) | 大换血 SOP（步骤 1-3 列了一堆 clone + reset 命令）；本参考文件专注**每日 5 个 cron 协议** |
| `verification-before-reporting` | 强制报告里每行含"已装/已落盘/搜索失败"可验证状态 |
| `proactive-execution` | Failure 51 fallback：cron 环境 memory tool 不可用 → 本协议不需要写记忆，只需落 JSON |

## 7. 触发词

- "技能采集员 / 采集 skill / 每日 skill 采集" → 直接加载本协议
- "5 个 skill" / "5/5 必须落地" → 触发 quota 铁律
- "不许 SILENT" / "不要沉默" → 强制报告格式
- "raw SKILL.md URL 安装" → 加载本参考文件的命令模板
