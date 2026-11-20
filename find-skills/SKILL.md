---
name: find-skills
slug: find-skills
displayName: 技能发现·Find Skills
description: 不知道装什么技能？想让 AI 自己找到最合适的技能？技能发现·Find Skills 是场景驱动+关键词双模式的技能发现工具（skill discovery / skill finder / install skills）：用自然语言描述场景/需求（如"我想做一个海报"“帮我分析股票"“找个薅羊毛技能"），或明确说"安装技能/find skills/找个skill/有没有做XX的技能"时，自动从官方内置、本地已安装、本地缓存、**GitHub**、SkillHub、虾评、ClawHub 七层联合搜索并推荐最合适的技能，支持一键安装。已完全替代官方原 find-skills 插件。触发词：找技能、安装技能、技能推荐、技能发现、find skills、skill discovery、install skill。
version: "1.8.0"
---
# find-skills（场景技能匹配器）

## Overview

本技能用于**场景驱动的技能发现引擎**——用户用自然语言描述需求，系统自动理解意图，联合搜索并推荐最合适的技能。

**与官方原 `find-skills` 插件的关系**：
- 官方原 `find-skills` 插件的 description 已被标记为 DEPRECATED，不会主动触发
- 本技能已完全覆盖其所有能力，并新增了官方内置扫描 + 本地已安装扫描 + 场景语义理解 + 推荐理由输出

---

## 核心流程

### Step 1：理解用户场景

从用户的自然语言描述中提取：
1. **任务意图**：用户想做什么？
2. **领域标签**：属于哪个领域？
3. **搜索关键词**：中英文都要（用于远程搜索）

**示例**：
- "我想做一个海报" → 意图：设计/制图；领域：内容创作；关键词：poster, design, 海报, 设计
- "帮我分析今天的大盘" → 意图：股票分析；领域：金融；关键词：stock, A股, 大盘, 分析

---

### Step 2：联合搜索（七层）

#### 2.1 第一层：本机内置技能（Agent 自带，无需安装）

扫描官方内置技能目录，读取每个技能的 `name` 和 `description`：

```bash
ls ~/.hermes/skills/
ls ~/.openclaw/workspace/skills/
```

用 `Read` 工具读取每个技能的 `SKILL.md` YAML frontmatter，与用户场景做**语义匹配**。

**匹配规则**（按优先级）：
1. 用户场景关键词直接出现在技能 description 中 → 高分
2. 技能 name 与用户意图高度相关 → 高分
3. 技能 description 与用户领域相关 → 中分

---

#### 2.2 第二层：本地已安装技能

扫描以下两个位置的已安装技能：

```bash
# 用户级技能（Hermes / OpenClaw）
ls ~/.hermes/skills/ 2>/dev/null
ls ~/.openclaw/workspace/skills/ 2>/dev/null

# 项目级技能（当前工作区）
ls .workbuddy/skills/ 2>/dev/null || echo "无项目级技能"
```

用 `Read` 工具读取每个技能的 `SKILL.md` YAML frontmatter，提取 `name` 和 `description`，与用户场景做**语义匹配**。

> **注意**：如果本地已安装技能在 Step 2.1 官方内置中也出现，去重，只保留最高优先级的记录。

---


#### 2.3 第三层：本地 marketplace 缓存

先检查本地 marketplace 缓存（原 `find-skills` Step 5 逻辑）：

```bash
ls ~/.openclaw/workspace/skills-marketplace/skills 2>/dev/null || echo '无市场缓存'
```

如果缓存目录中存在与用户需求匹配的技能，直接复制安装，无需远程下载：

```bash
cp -r ~/.openclaw/workspace/skills-marketplace/skills/<skill-folder-name> ~/.hermes/skills/<skill-folder-name>
```

---

#### 2.4 第四层：GitHub 技能仓库（开源技能来源 · 用户显式请求时提升至第一远程层）

🔴 **当用户要求"先去 GitHub 找"、"别从零造轮子"、"找现成的 skill 项目"时，执行 GitHub-First 模式**：

**第一步：用 `gh` CLI 搜索（已认证，5000次/小时）**

`gh` CLI 已在系统中配置（keyring 登录，scopes: gist, read:org, repo, workflow）：

```bash
# 1. 搜索包含 SKILL.md 的仓库
gh search repo --json name,description,stargazersCount --sort stars --limit 20 "skill finder OR skill discovery OR agent skills" 2>/dev/null

# 2. 搜索技能相关仓库（按星标数）
gh search repo "skill hub" --json name,description,stargazersCount --sort stars --limit 20 2>/dev/null

# 3. 搜索特定技能关键词
gh search repo "find skills" --json name,description,stargazersCount --sort stars --limit 10 2>/dev/null
```

> **说明**：`gh` CLI 比 API 更稳定，已通过认证，无需 GITHUB_TOKEN 环境变量。若 `gh` 不可用，降级使用 API 带 `GITHUB_TOKEN` 或匿名仓库搜索。

**第二步：检索仓库 SKILL.md 内容（人工判断有效性）**

对候选仓库：
```bash
# 获取仓库 README / SKILL.md
gh api repos/<owner>/<repo>/readme 2>/dev/null | base64 -d | head -50
gh api repos/<owner>/<repo>/contents/SKILL.md 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d, indent=2)[:2000])"
```

**第三步：优先安装高评分仓库技能**

参考本技能「推荐的高价值 GitHub 技能仓库」列表（见 §3），直接克隆或复制到本地：
```bash
# 示例：安装 agentic-awesome-skills 中的某个技能
git clone https://github.com/sickn33/agentic-awesome-skills.git ~/.hermes/skills/agentic-awesome-skills
```

**关键参考**：各市场 API 端点与质量过滤规则见 `references/remote-markets.md`；高价值 GitHub 仓库详见 `references/github-skills.md`。

---

#### 2.5 第五层：SkillHub 官方市场

```bash
curl -s "https://lightmake.site/api/v1/search?q=<URL-encoded 中文关键词>&limit=10"
curl -s "https://lightmake.site/api/v1/search?q=<URL-encoded English keywords>&limit=10"
```

过滤 `score < 0.05` 的低相关结果。

---

#### 2.6 第六层：虾评技能市场（中文技能重点来源）

虾评 API Base URL：`https://xiaping.coze.com`（注意：不是 `coze.site`）

搜索技能：
```bash
curl -s "https://xiaping.coze.com/api/skills/search?q=<URL-encoded 关键词>&limit=10"
# 获取技能详情 / 下载链接
curl -s "https://xiaping.coze.com/api/skills/<skill-id>"
curl -s "https://xiaping.coze.com/api/skills/<skill-id>/download"
```

需要先加载 `虾评指南` 技能（路径：`~/.openclaw/workspace/skills/虾评指南/SKILL.md`，若未安装可跳过），按其中 §1.1 + §1.2 的规范执行搜索和下载。

> **重要**：虾评是中文技能的核心来源，对于中文场景的技能搜索，虾评的结果往往比 SkillHub 更相关。

---

#### 2.7 第七层：ClawHub 技能市场（补充兜底）

- 检查 ClawHub 市场（参考 `skills_hub_clawhub.py` 的搜索接口）
- 按需调用附带的 ClawHub 相关工具
### 输出规范

- 推荐给用户时，必须包含：**名称 + 一句话用途 + 入口链接**，不只扔 `ID`；让用户可直接复制/点开。
- 规格、参数、路径一律精确到位（带单位和层级），不接收近似。
- 回复通道与收到的消息一致：**语音消息用语音回复，文字消息用文字回复**。

---
