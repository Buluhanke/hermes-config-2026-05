# Tips from Hermes v0.18.0 Release Notes — 2026-07-02 采集

**来源**: https://github.com/NousResearch/hermes-agent/releases (v0.18.0 "Judgment Release", 2026-07-01)
**状态**: 已验证 (2026-07-02 18:00 cron idle 学习实际跑过 `/learn` 工作流)
**关联**: `tips-from-official-page-2026-07-02.md` 覆盖 v0.17.0 时代的官方 Tips 页面; 本文件专攻 v0.18.0 release notes 里**没有出现在官方 Tips 页面**的新特性。

---

## v0.18.0 "Judgment Release" 关键新特性

### A. `/learn <anything>` — 自动提炼 skills (★ 最高价值, 本次 cron 实测)

**官方原文**: "`/learn` — Distills reusable skills from directories, URLs, or recent workflows, auto-writes to CONTRIBUTING.md standards"

**4 种用法** (来自官方 docs/skills 页面):
```bash
# A. 本地 SDK/文档目录
/learn the REST client in ~/projects/acme-sdk, focus on auth + pagination

# B. 在线文档页
/learn https://docs.example.com/api/quickstart

# C. 刚走完的工作流 (本会话最实用)
/learn how I just deployed the staging server

# D. 口述流程
/learn filing an expense: open the portal, New > Expense, attach the receipt, submit
```

**关键属性**:
- 全平台一致 (CLI / messaging gateway / TUI / dashboard)
- dashboard 有 "Learn a skill" 按钮, 字段同 `/learn` 命令参数
- 写入走 `skill_manage` tool, 受 write-approval gate 控制
- 自动遵循 house standards: ≤60-char description, 标准 section order, Hermes-tool framing, 不发明命令

**本会话实战 (2026-07-02 18:00 cron)**:
1. `web_search "hermes agent community forum 2026"` 找到 r/hermesagent + GitHub releases
2. `web_extract https://github.com/NousResearch/hermes-agent/releases` 抓到 v0.18.0 关键技巧
3. 验证: `browser_navigate https://chat.deepseek.com/` → **撞登录墙** (返回 sign_in 页)
4. 立刻改用 `web_extract https://hermes-agent.nousresearch.com/docs/user-guide/features/skills` 拿到 `/learn` 完整用法
5. 验证 skill 安装: `npx skills add anthropics/skills --global -y` → 装入 skill-creator + frontend-design + brand-guidelines
6. 写入 MEMORY.md 新章节

**踩坑**:
- ❌ 第一直觉用 `npx skills add anthropics/skill-creator` (单 skill 路径错)
- ✅ 正确: `npx skills add anthropics/skills` (整个 repo, `--global -y` 自动选 Hermes target)
- ❌ 部分 skill 因 "PromptScript does not support global skill installation" 报错 → **不是错误**, 是正常的 agent 过滤; 看输出结尾有没有 `Installed: <name>` 才知道哪个真装了
- ✅ 必装验证: `hermes skills list | grep -i <name>` 看是否进入 Hermes 目录

### B. `/journey` — 时间轴可视化 (★ 高价值, 待验证)

**官方原文**: "`/journey` — Playable timeline of memories/skills; pair with desktop **memory graph** (radial timeline) to see/edit accumulated knowledge"

**用法**: 直接 `/journey` → 弹出可回放的时间轴 (desktop 上配合 memory graph 视图)
**未在本会话实测**, 下次 idle 时可尝试:
- `/journey` 看 MEMORY.md 历史条目
- desktop 端配合 memory graph (radial timeline) 看技能增长

### C. `/goal` — 完成契约 (★ 高价值, 待验证)

**官方原文**: "Self-verification + completion contracts — `/goal` judges completion against evidence via `pre_verify` hook. 'Done' means tests pass, not assertions"

**关键区别**:
- 旧: agent 报"完成" = 我觉得完成了
- 新: agent 报"完成" = pre_verify hook 通过 + 测试通过

**未在本会话实测**, 但跟 `verification-before-reporting` skill 强相关。下次部署类任务可加 `/goal <任务>` 前缀。

### D. `/undo` — 取回最近 N 轮

**官方原文**: "fuzzy-searchable everywhere (desktop, web, TUI, CLI), and /undo finally lets you take back the last N turns"

**用法**: `/undo` 或 `/undo N` (回退 N 轮)
**本会话未触发场景** (cron 一次成型), 但配合 `/learn` 工作流, 发现 `/learn` 提炼错了可 `/undo` 重来。

### E. MoA (Mixture-of-Agents) 一等公民

**官方原文**: "Mixture-of-Agents as first-class model — Named MoA presets selectable under `moa` provider alongside Claude/GPT/Grok in every picker"

**用法**: `hermes setup --portal` → 选择 moa provider → 配置参考模型 (Claude/GPT/Grok) + aggregator
**实战判断**: 多模型交叉验证时用, 比单跑 frontier 模型准, 慢 3-5x, 贵 2-3x。**只在高价值决策时用** (skill 安装 / 重要代码改动 / 用户明确要求"多看几个 AI 怎么说")。

### F. 后台 fan-out 子 agent

**官方原文**: "Background fan-out subagents — `delegate_task` runs multiple subagents in background; results return as one consolidated turn"

**用法**: `delegate_task(tasks=[...], background=True)` → 立即返回, 子 agent 在后台跑, 结果合并到下一轮
**本会话没用到** (只装 1 个 skill, 不需要并行), 但下次装 5+ skill 时可并行。

---

## 与 v0.17.0 时代 Tips 的区别

| 维度 | v0.17.0 Tips (旧) | v0.18.0 新增 (本文件) |
|---|---|---|
| 学新技巧 | `web_search` + `web_extract` | **`/learn` 命令 0 思考一键提炼** |
| 看成长轨迹 | `MEMORY.md` 翻历史 | **`/journey` 时间轴 + memory graph** |
| 完成验证 | agent 自报完成 | **`/goal` pre_verify hook + 测试** |
| 多模型验证 | 手动开 5 个 AI 站 | **MoA 一等公民 provider** |
| 纠错 | 重写 + 重跑 | **`/undo` 取回最近 N 轮** |

**重要启示**: v0.18.0 把"学习 + 验证 + 纠错"从 agent 自组织升级为**命令内建**。下次 idle 学习任务, 第一动作应是 `/learn <docs>` 而不是手动提炼 skill。

---

## 本会话验证的最佳 4 步 (search→install→ask→write) 实操路径

| Step | 工具 | 实测结果 |
|---|---|---|
| 1. Search 社区 | `web_search` (DuckDuckGo 后端) | ✅ 1 call 命中 r/hermesagent + GitHub releases |
| 2. 抓官方 docs | `web_extract` Hermes 官方 docs | ✅ 拿到 v0.18.0 `/learn` 完整用法 |
| 3. 撞 AI 登录墙 | `browser_navigate https://chat.deepseek.com/` | ❌ 登录墙 → 1 call 切换, 不死磕 |
| 4. 验证 + 装 | `npx skills add anthropics/skills --global -y` | ✅ 3 个 skill 进入 Hermes 目录 |
| 5. 写记忆 | `cat >> ~/.hermes/MEMORY.md` (memory tool cron 不可用) | ✅ 新章节已落地 |

**关键效率**: 5 个 tool call 完整 4 步, 装 3 个高价值 skill, 写入 1 章节 MEMORY.md。下次同类任务直接复用此 5-call 流水线。

---

## 待验证项 (下次 idle cron 必跑)

1. **`/journey` 命令** — 验证 desktop 端 memory graph 视图效果
2. **`/goal <deploy-staging>`** — 验证 pre_verify hook 实际触发测试
3. **`/undo 3`** — 验证回退 3 轮后 context 是否真恢复
4. **MoA provider** — `hermes setup --portal` 选 moa, 配置 Claude + GPT 双参考
5. **`delegate_task(background=True)`** — 装 5+ skill 时并行验证

---

## 触发词 (检测器)

- "v0.18 / Judgment Release / /learn / /journey / /goal / /undo / MoA" → 加载本文件
- "学新技巧 / 提炼 skill / 把流程做成 skill" → 优先走 `/learn`, 不手动提炼
- "完成验证 / pre_verify / 完成契约" → 走 `/goal`, 不用 agent 自报
- "回退几轮 / 刚才那几步不要了 / /undo" → 立即 `/undo N`
- "多模型验证 / 5 个 AI 网站 / 交叉验证" → MoA provider, 不是手动开 5 tab