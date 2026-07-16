# Skill 安装绕过记录（2026-07-12 更新）

## GitHub API 超时 → git clone

当 GitHub API rate limit 或网络超时时，`git clone --depth 1` 是最稳的绕过方案：

```bash
git clone --depth 1 https://github.com/<owner>/<repo>.git /tmp/<repo>
```

**今日验证成功**：`alirezarezvani/claude-skills`（2244个.md文件）
- API 超时 rate limit
- `git clone --depth 1` 5秒完成

---

## 精选 skill 库（2026-07-12 新增）

### alirezarezvani/claude-skills
- **地址**：https://github.com/alirezarezvani/claude-skills
- **规模**：2244个文件，775个 SKILL.md，36个子目录
- **结构**：按职业/部门分类（research/engineering-team/business-growth/c-level-advisor等）
- **安装**：直接 git clone 选 skill 目录
- **已复制到 ~/.hermes/skills/**：
  - `deep-research` — 多源深度调研
  - `pulse` — 实时趋势感知（Reddit/HN/Twitter）
  - `dossier` — 决策级实体调研
  - `litreview` — 学术文献综述
  - `grants` — NIH 基金研究
  - `self-improving-agent` — 工程自改进
  - `executive-mentor` — 高管思维伙伴

### agency-agents（msitarzewski/agency-agents）
- **地址**：https://github.com/msitarzewski/agency-agents
- **规模**：127k stars，232个AI角色，11部门
- **注意**：是桌面应用（安装到 Claude Code/Cursor），不是独立 skill 库
- **思路可借鉴**：关键词匹配角色 + 知识库导入 + 智能推荐组合
- **不直接安装**：桌面 App，无 SKILL.md

---

## 安装验证命令

```bash
ls ~/.hermes/skills/<name>/SKILL.md  # 文件存在
wc -l ~/.hermes/skills/<name>/SKILL.md  # >10行
python3 -m py_compile ~/.hermes/skills/<name>/SKILL.md  # 语法检查
```
