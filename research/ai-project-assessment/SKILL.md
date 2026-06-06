---
name: ai-project-assessment
description: "Assess AI/Agent projects beyond the hype — evaluate real technical depth, actual code vs marketing, ecosystem viability, and integration value for Hermes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [AI, Agent, Project Assessment, Hype-Check, Research]
    related_skills: [github-repo-vetting]
triggers:
  - user shares an AI/Agent project URL or description
  - user asks "研究一下这个" / "看看这个AI项目" / "值不值得用"
  - user mentions AI community platforms, agent networks, AI social tools
  - user asks about zeroentropyai / GBrain / similar niche AI projects
---

# AI Project Assessment

Evaluate AI/Agent projects beyond marketing — determine real technical depth, code vs hype, and practical value for Hermes workflows.

## When to Use

- User shares a GitHub link or project URL that claims AI/Agent capabilities
- User asks to research an AI tool, framework, or community platform
- Any "AI Agent platform/social network/self-evolving knowledge base" type project

## Assessment Framework

### Step 1: Quick Credibility Check

```bash
# 1. Existence + metadata via GitHub API
curl -s https://api.github.com/repos/OWNER/REPO | python3 -c "
import sys, json
r = json.load(sys.stdin)
if 'message' in r: print('404: Not Found'); sys.exit(1)
print(f'Stars: {r[\"stargazers_count\"]}')
print(f'Forks: {r[\"forks_count\"]}')
print(f'Last push: {r[\"pushed_at\"]}')
print(f'License: {r.get(\"license\",{}).get(\"spdx_id\",\"none\")}')
"

# 2. Star/Fork ratio check (quick scam signal)
# ratio = stars/forks > 50 → suspicious (bot stars)
# ratio = stars/forks 5-30 → normal
# ratio < 5 → very new or dead
```

### Step 2: Code Depth Analysis

**CRITICAL**: AI projects heavily overclaim. Always verify with `git ls-tree -r HEAD`:

| Claim Type | What it usually IS | How to verify |
|------------|-------------------|---------------|
| "X AI Agents" | X prompt files / SKILL.md | `git ls-tree -r HEAD | grep -i "agent\|skill" \| wc -l` |
| "Agent OS" | Config pack / prompt pack | `git ls-tree -r HEAD | grep -E "\.py$|\.js$|\.ts$|\.go$" \| wc -l` |
| "Y security tests" | Unit tests (not security-focused) | `git ls-tree -r HEAD \| grep -E "test" \| wc -l` |
| "Self-evolving" | Cron job + memory files | `cat SKILL.md | grep -i "self\|evolv\|learn"` |
| "Multi-agent system" | Single process with loops | `grep -r "class.*Agent" --include="*.py"` |
| "AI Social Network" | Web forum + API | `curl <URL> \| grep "post\|comment\|login"` |

### Step 3: Architecture Reality Check

| Signal | Green | Yellow | Red |
|--------|-------|--------|-----|
| Repo file count | 500+ real source files | 100-500 | <100 + lots of docs |
| Missing blobs in git | None | Few | Many → incomplete repo |
| CI badge | Present + green | Present + yellow | Missing or red |
| Installable | pip/npm install works | Needs manual setup | `npx skills add` (fake) |
| Documentation | README has code examples | README is conceptual | README has no code |
| Author track record | Known / multiple projects | Unknown / single project | Anonymous / new account |

### Step 4: AI-Specific Red Flags

1. **"人类只能旁观/人类不能注册"** — 典型的 AI-only 概念项目。检查：真的有 AI 用户？还是作者自己用 bot 跑的？
2. **"自进化知识库"** — 查有没有实际的向量数据库 / RAG 实现。多数情况只是文件搜索。
3. **"零摩擦接入 / 一行命令集成"** — 通常只是写 skill.md 让 Agent 自己 curl 注册。
4. **"全球首个"** — 大概率是真的（这类领域没什么竞品），但不等于"值得用"。
5. **无头 GitHub 仓库**（0 forks, 0 issues, 2 commits）— 闭源项目的营销页，代码不可审计。

### Step 5: Verdict Format

```
**评估：✅ 值得 / ⚠️ 有趣但早期 / ❌ 不值得**

**真实定位：** [一句话]
**技术栈：** [前端/后端/数据库/部署]
**真实功能：** [能做什么，不能做什么]
**与 Hermes 关系：** [能集成吗？需要额外配置吗？安全吗？]
**结论：** [具体建议]
```

## Pitfalls

1. **web_extract 对 GitHub 可能失败**（SearXNG 只支持搜索）。回退：`curl -sL raw.githubusercontent.com/...` 或 `browser_navigate`。
2. **GitHub API 有 rate limit**（60 req/hr 未认证）。优先用 raw.githubusercontent.com 获取 README，API 只用于元数据。
3. **Apple git 版本太老**：不支持 `--filter=blob:none`、`--sparse`、`diff-filter=ACMRT`。用 `git clone --depth 1 --no-checkout` + `git checkout HEAD -- README.md` 代替。
4. **README 夸大 ≠ 项目没用** — 区分"夸大"和"完全虚假"。ECC 本质是配置集，但配置质量不错；HermesWorld 是真实论坛，只是规模小。
5. **独立开发者项目**：很多 AI-only 社区是单人维护。评估重点不是"公司背书"，而是"概念是否可行 + 代码是否完整"。
6. **API 文档在 skill.md 里** — 很多 AI 项目的接入文档是作为 skill.md 发布的（如 HermesWorld），不是传统 README。搜 `skill.md` / `heartbeat.md` / `api.md` 找到 API 端点。
7. **missing blob 不等于项目假** — 可能只是 CI 漏传了部分文件（如测试 fixture、大型 assets）。但要标注为"代码库不完整"信号。

## Linked Files

- `references/marketing-vs-code-cases.md` — Real-world cases where marketing diverged from codebase reality (ECC, HermesWorld). Includes detection signal matrix.
