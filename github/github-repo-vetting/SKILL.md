---
name: github-repo-vetting
description: "Investigate and assess third-party GitHub repos shared by the user — rapid credibility check, key metrics, README extraction, and structured assessment."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Repo Investigation, Vetting, Assessment, Open Source]
    related_skills: [github-repo-management, codebase-inspection]
triggers:
  - user shares a GitHub URL in chat (any format: github.com/owner/repo, raw.githubusercontent.com, or just "owner/repo")
  - user asks "check this project" / "研究一下这个项目" / "看看这个"
  - user asks whether a tool/library is worth using
prerequisites:
  - "curl for raw.githubusercontent.com README access"
  - "Alternatively: browser_navigate for GitHub page access"
---

# GitHub Repo Vetting

Investigate third-party GitHub repositories shared by the user — rapid assessment of activity level, credibility, and relevance.

## When to Use

- User drops a GitHub link (`github.com/owner/repo`) and wants to know what it does
- User asks "研究一下这个项目" / "看看这个" with a repo URL
- User shares a tool/library and expects a verdict: worth using or not?
- Any session where a third-party repo needs evaluation

## Investigation Workflow

### Phase 1: Existence & First Check (fast)

Start with the GitHub API to confirm the repo exists and get key metadata:

```bash
# Quick existence + key metrics via API
curl -s https://api.github.com/repos/OWNER/REPO | python3 -c "
import sys, json
r = json.load(sys.stdin)
if 'message' in r and r['message'] == 'Not Found':
    print('404: Repo does not exist')
    sys.exit(1)
print(f\"Stars: {r['stargazers_count']}  Forks: {r['forks_count']}\")
print(f\"Last push: {r['pushed_at']}\")
print(f\"License: {r.get('license', {}).get('spdx_id', 'none')}\")
print(f\"Description: {r.get('description', 'none')}\")
"
```

Alternatively, use the `mcp_github_get_file_contents` tool to probe the repo — it returns existence info naturally.

**Key signals at a glance:**
- **Stars**: < 10 ≈ tiny/personal; 10-100 ≈ new but real; 100+ ≈ established; 1k+ ≈ popular
- **Last push**: > 1 year = abandoned (unless explicitly stable/complete)
- **License**: missing = can't use in production without asking
- **Description**: empty or vague = red flag

### Phase 2: README Extraction

Get the README to understand what the project actually does:

**Path A — Raw GitHub (fastest):**
```
https://raw.githubusercontent.com/OWNER/REPO/main/README.md
```
Try `main`, then `master` if 404.

**Path B — GitHub API (when raw.githubusercontent is blocked/slow):**
Use `mcp_github_get_file_contents(owner=OWNER, repo=REPO, path='README.md')`. Returns base64-encoded content — just pass it through to the model for reading.

**Path C — Browser (last resort):**
`browser_navigate(url)` + `browser_scroll` if the README has images, diagrams, or complex formatting.

**Path D — Curl with proxy (when behind firewall):**
```bash
curl -sL "https://raw.githubusercontent.com/OWNER/REPO/main/README.md" | head -300
```

### Phase 3: Key Assessment Dimensions

Evaluate the repo on these axes:

| Dimension | What to check | Green flags | Red flags |
|-----------|--------------|-------------|-----------|
| **Activity** | Last commit date, commit count | Active (days/weeks ago), 50+ commits | >1 year, <5 commits |
| **Community** | Stars, forks, issues, PRs | 100+ stars, open issues being discussed | 0 stars, 0 forks, 0 issues |
| **Credibility** | README quality, author history | Detailed docs, known author | Vague README, fake install commands |
| **Installability** | Package manager, Docker, deps | pip/npm install, Dockerfile | "npx skills add" (fake command) |
| **Relevance** | Solves what the user actually asked about | Direct match | Different domain entirely |
| **Maintenance** | Recent commits, CI passing | Active development, green CI badge | Stale, broken CI |

### Phase 4: Structured Report Format

Deliver the assessment in a table + verdict format:

```
**评估结果：✅ 可用 / ⚠️ 存疑 / ❌ 不用**

**基本信息：**
| 维度 | 数据 |
|------|------|
| Stars | N ⭐ |
| Forks | N |
| Commits | N |
| 最后提交 | X天/月/年前 |
| License | MIT/GPL/无 |

**核心信息：**
- 用途：[one-line summary]
- 技术栈：[languages, frameworks]
- 活跃度：[active/stale/abandoned]
- 作者：[known/new/personal project]

**评估：**
[2-3 sentence verdict with reasoning]
```

## Pitfalls

1. **Raw.githubusercontent.com may timeout** (15s curl default). Retry with `--connect-timeout 5` or fall back to GitHub API.
2. **Default branch may not be `main`** — try `main` first, then `master`, then check GitHub page for default branch name.
3. **README may be in a subdir** (e.g., `docs/README.md` in monorepos). Check the file listing if root README is missing.
4. **Non-standard README filenames**: some projects use `README.md`, `README.rst`, `readme.md`, or `README.zh-cn.md`. Try both.
5. **Large repos may truncate**. Use `head -300` on raw content to get the overview section quickly.
6. **GitHub API rate limit** is 60 req/hr unauthenticated. Prefer raw.githubusercontent.com for README content and save API calls for metadata.
7. **npx does not have a `skills add` subcommand**. This is not a legitimate install command. Real tools use pip, npm (direct), cargo, go install, brew, or Docker. Anything involving `npx skills` is fake.
8. **User may share the wrong repo first** (a similar-named abandoned project) and then correct to the right one. Don't commit to a verdict until you've confirmed which repo they mean.
9. **web_extract credits can be exhausted** — "Payment Required" error means Firecrawl credits are out. Fall back to curl raw.githubusercontent.com or mcp_github_get_file_contents.
10. **`mcp_github_search_repositories` returns empty** — this MCP tool can return `{"items": []}` even for valid repos. Use web search as the primary discovery tool instead.
11. **Browser automation repos need extra install steps** — `uv sync` installs Python deps, but Playwright-based projects (Fara, browser-use, etc.) need `playwright install` separately to download browser binaries. Check the README for post-install commands.
12. **Apple git (macOS default) 版本太老**：不支持 `--filter=blob:none`、`--sparse`、`diff-filter=ACMRT` 等参数。macOS 上 clone 大仓库用 `git clone --depth 1 --no-checkout` + `git checkout HEAD -- README.md` 代替 `--filter=blob:none`。Apple git 不支持 `--sparse` 时改用 `git ls-tree -r HEAD` 代替 `git ls-files`。
13. **宣传 vs 实际代码的评估维度**：大项目 README 常常夸大（"63个Agent"实际是33个SKILL.md、"1282安全测试"实际157个测试文件含20个缺失blob、"Agent操作系统"实际是配置集）。必须通过 `git ls-tree -r HEAD` 做代码级验证，不能只看 README。关键验证点：star/fork 比例是否虚高、claimed agents 是否可执行程序还是提示词文件、claimed test count 是否真的是测试文件（注意 missing blob）。
14. **Shallow clone 时 README 多语言版本**：`--depth 1` 可能只包含 `README.md` 不含 `README.zh-CN.md`。需要单独 `git checkout HEAD -- README.zh-CN.md` 获取。

## Linked Files

- `references/investigation-patterns.md` — Real-world archetypes (active repos, abandoned projects, fake install commands, misattributed links) with tool preference order and quick signal reference.
- `references/marketing-vs-code-cases.md` — Real-world cases where marketing claims diverged from codebase reality. Includes detection signal matrix for: "X agents" (usually prompt files not binaries), "Y tests" (check file count + missing blobs), "OS/platform" (usually config pack).
