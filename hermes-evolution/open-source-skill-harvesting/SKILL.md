---
name: open-source-skill-harvesting
description: 从 GitHub 等开源平台搜索、评估、筛选并落地可复用的 AI agent skill 文件到 Hermes skills/ 目录。区别于「安装桌面App」——目标是 SKILL.md 纯文本文件，可直接被 Hermes skill 系统加载。
triggers:
  - "全网搜索一下有没有这些技能"
  - "这个项目有哪些 skill"
  - "找类似的角色库/技能库"
  - "把这个项目的 skill 落地"
---

# Open Source Skill Harvesting

从开源项目（如 agency-agents、claude-skills、awesome-agent-skills）中提取可复用的 SKILL.md 文件，落地到 `~/.hermes/skills/`。

## 标准流程

### 1. 搜索
```bash
# 优先用 git clone（避免 GitHub API rate limit）
git clone --depth 1 https://github.com/<owner>/<repo>.git /tmp/<repo-name>
```

### 2. 评估
- 找 SKILL.md 文件：`find /tmp/<repo> -name "SKILL.md" -type f`
- 看格式：frontmatter `name`/`description` + markdown body
- 评估 Hermes 兼容性：纯 prompt 模板可直接用；有 vendor lock-in 需裁剪

### 3. 筛选
按领域优先级选取：
1. `research/` 类（deep-research、pulse、dossier）→ 补充 B_insight
2. `engineering/` 类（self-improving、code-review）→ 补充 D_action
3. `strategy/` 类（executive-mentor、stress-test）→ 通用元认知

### 4. 落地
```bash
cp /tmp/<repo>/<path>/SKILL.md ~/.hermes/skills/<skill-name>/SKILL.md
mkdir -p ~/.hermes/skills/<skill-name>/{references,scripts,templates}
```

### 5. 验证
```bash
python3 -m py_compile ~/.hermes/skills/<skill-name>/SKILL.md
```

## 关键判断
- **skill 库 vs 桌面 App**：agency-agents 是桌面 App（安装到 Claude Code），不是纯文本 skill。alirezarezvani/claude-skills 才是纯 SKILL.md 文件。
- **兼容性格式**：frontmatter 必须有 `name` 和 `description` 字段
- **数量**：按领域筛选 5-10 个核心的，不过度复制

## 参考项目
- alirezarezvani/claude-skills: 2244 .md，775 SKILL.md，36 分类
- VoltAgent/awesome-agent-skills: 1000+ skills，兼容多 agent
- heilcheng/awesome-agent-skills: 社区 text file skill 合集
- **anysearch-ai/anysearch-skill**: 多 runtime CLI skill 范式（Python/Node/Shell/PowerShell），runtime.conf 缓存机制，credential frontmatter 扩展。详见 `references/anysearch-research.md`

## 已知落地（2026-07-12）
deep-research, pulse, dossier, litreview, grants, self-improving-agent, executive-mentor（共7个）

## Skill 架构模式库（references/）
- `anysearch-research.md` — 多 runtime CLI skill 范式（runtime.conf 平台检测缓存、多语言 CLI 并行、credential frontmatter 扩展）
