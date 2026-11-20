# GitHub 技能仓库参考

高价值 GitHub 技能仓库，按 `gh` CLI 搜索命令 + 安装方式组织。用户要求"先去 GitHub 找现成技能"时使用本文件。

---

## 搜索命令速查

```bash
# 1. 搜索含 SKILL.md 的仓库（按星标，注意是 repos 复数）
gh search repos --json name,description,stargazersCount --sort stars --limit 20 "agent skills"

# 2. 搜索技能相关仓库（按星标）
gh search repos "skill hub" --json name,description,stargazersCount --sort stars --limit 20

# 3. 搜索特定关键词
gh search repos "find skills" --json name,description,stargazersCount --sort stars --limit 10

# 4. 搜索已认证用户的仓库
gh search repos --limit 20 --sort stars "skill finder" --owner <username>
```

> **说明**：`gh` CLI 已通过 keyring 认证（scopes: gist, read:org, repo, workflow），无需 GITHUB_TOKEN。若 `gh` 不可用，降级使用 API `curl -s https://api.github.com/search/repositories?q=...`（匿名 60次/小时）。

---

## 高价值仓库（按星标排序）

| 仓库 | stars | 语言 | 适用场景 | 安装方式 |
|------|-------|------|----------|----------|
| `K-Dense-AI/scientific-agent-skills` | 56,785 | Python | 科学研究、AI Scientist、论文阅读、实验设计 | git clone + 复制到 skills/ |
| `sickn33/agentic-awesome-skills` | 49,515 | Python | 2,955+ 种 agent skills，覆盖 Claude Code / Codex / Cursor / Gemini CLI | 克隆后按需复制单个技能 |
| `qufei1993/skills-hub` | 1,871 | Rust | 跨平台桌面工具管理 agent skills 的一站式应用 | 按发布包安装 |
| `zhuyansen/agent-skills-hub` | 497 | HTML | 安全分级的开源 agent skills 目录 | 浏览网站后手动安装 |
| `binance/binance-skills-hub` | 1,161 | Python | 金融/交易相关 agent skills | 按 README 安装 |
| `guipi888/find-skills` | 0 | - | 本技能原作者仓库（SkillHub v1.7.0 来源） | git clone 到本地 |

---

## 安装模式

```bash
# 模式 1：克隆完整仓库
git clone https://github.com/<owner>/<repo>.git ~/.hermes/skills/<skill-name>

# 模式 2：只复制单个技能文件
cp <repo>/skills/<skill-name>/SKILL.md ~/.hermes/skills/<skill-name>/

# 模式 3：下载 Skills Hub 桌面安装包（Rust 项目的 release asset，不是 CI artifact）
# 注意：用 gh release download，不是 gh run download（后者是下载 CI artifacts）。
# 资产名形如 Skills-Hub-v1.1.1-macOS-aarch64.dmg，用 --pattern 匹配。
gh release download --repo qufei1993/skills-hub --pattern 'Skills-Hub-*-macOS-aarch64.dmg'
```

---

## 质量过滤

- **最小星标**：≥ 100 星（避免冷门仓库）
- **SKILL.md 存在性**：目录下必须包含 `SKILL.md`
- **版本兼容性**：检查仓库是否声明兼容当前 Hermes 版本
- **许可证**：优先 MIT / Apache-2.0 / BSD

---

## 推荐阅读

- `agentic-awesome-skills` 的 README：了解 2,955+ 技能的分类体系
- `agent-skills-hub` 的 catalog：了解安全分级方案
- `skills-hub` 的 README：了解跨平台 skills 管理方案
