# Investigation Patterns: Real-World Examples

This file captures specific investigation patterns encountered in real sessions. Updated when new repo archetypes are encountered.

## Archetype 1: The Real Project (Horizon — Thysrael/Horizon)

**Situation:** User shares a link to a legit open-source project. 5.4k stars, active development.

**Fast track:**
```
1. mcp_github_get_file_contents(owner="Thysrael", repo="Horizon", path="README.md")
   → Returns base64 README content immediately. No rate limit concern.
   → 14KB file, rich content with emoji badges, architecture diagram, tables.
2. Navigate GitHub page for visual context (star count, forks, last commit visible).
3. Deliver full structured assessment.
```

**Duration:** ~15-30 seconds.

**Format used:**
```
**基本信息：**
| 维度 | 数据 |
|------|------|
| Stars | 5.4k ⭐ |
...

**核心能力：**
[one-line summary + key lines]

**与Hermes的关联价值：**
[bullet points]
```

## Archetype 2: The Abandoned Project (scrapy_l — quietsunkii/scrapy_l)

**Situation:** User shares a personal learning project that's 9 years old. 1 star, 0 forks.

**Detection signals:**
- Last commit 9 years ago (visible in GitHub file listing)
- Only 15 commits total
- Single contributor, 0 forks
- README says "学习scrapy的练习" (learning exercise)

**Verdict:** ❌ 不用. Quick assessment in one sentence.

## Archetype 3: The Questionable Tool (LG-token-saver — jnbno1163/LG-token-saver)

**Situation:** New repo (< 24h old), claims 92% token savings, but install command is fake.

**Detection signals:**
- GitHub API: 404 at first (repo may be very new, newly-public, or deleted)
- Install command: `npx skills add` — **not a real npm/npx command**
- Promotional marketing language: "92% savings", "三档可调" — typical of ad content
- Author: "廖工/CC杰" — known for cc-switch (proxy tool), not token optimization

**Verification triage:**
1. Does the GitHub repo exist? (API check)
2. Edge case: repo might be so new the API cache is stale — retry with browser_navigate
3. If it does exist: check SKILL.md content to understand their intended use case
4. Cross-reference install command: `npx skills add` is NOT a real command → **fake**
5. Cross-reference claim: "19.8万→1.55万" — may be real for Claude Code (different use case than Hermes)

**Verdict:** ⚠️ 存疑. The repo is real but the install command is fabricated. The approach may be valid for Claude Code but irrelevant to Hermes.

## Archetype 4: The Misattributed Link

**Situation:** User's message references one repo but the context makes it clear they mean another, or the user corrects mid-conversation.

**Approach:** Always confirm context. If user says "介绍的是X项目" with a different URL, re-read the corrected URL and investigate the right one. Don't assume the URL in the message is the only one.

## Archetype 5: The Migrated Repo (GSD Core — open-gsd/gsd-core)

**Situation:** User shares a GitHub project that has moved. Original repo `gsd-build/get-shit-done` is archived; active development moved to `open-gsd/gsd-core`. Key signals:
- 31k+ combined stars (original + new)
- "Trusted by engineers at Amazon, Google, Shopify, Webflow" — credible endorsement
- Context Rot problem: quality degradation as AI fills its context window
- Architecture: main context stays at 30-40%, subagents get fresh 200k-token context per task
- Atomic commits per task, parallel execution waves

**Fast track:**
```bash
# Check if raw README accessible (fastest)
curl -sL "https://raw.githubusercontent.com/open-gsd/gsd-core/main/README.md" | head -120

# GitHub API for metadata
curl -s https://api.github.com/repos/open-gsd/gsd-core | python3 -c "
import sys,json; r=json.load(sys.stdin)
print(f'Stars: {r[\"stargazers_count\"]}  Forks: {r[\"forks_count\"]}')
print(f'Pushed: {r[\"pushed_at\"]}  License: {r.get(\"license\",{}).get(\"spdx_id\",\"none\")}')"
```

**Detection signals for migrated repos:**
- Original repo README says "migrated to X" or shows archive notice
- GitHub API on old repo shows `archived: true` + description pointing to new location
- Stars split across old + new (combined count matters for popularity assessment)
- User may reference the old URL but mean the new one — always probe for current status

**Verdict:** ✅ 值得参考. Context Rot 解决方案有工程价值，原子化任务执行模式可借鉴到 Hermes。

## Tool Preference Order

| Tool | Best for | Limitations |
|------|----------|-------------|
| `mcp_github_get_file_contents` | Fastest: metadata + README in one call | Auth required (rate: 5000/hr authenticated) |
| `curl raw.githubusercontent.com` | README content without API auth | 15s timeout; default branch may not be `main` |
| `browser_navigate` | Rich README with images/diagrams | Slower, more tokens |
| `web_extract` | README as markdown | Credit-based; may fail with "Payment Required" |

## Quick Signal Reference

| Signal | Probable meaning |
|--------|-----------------|
| 0 stars, 0 forks | Personal project, untested |
| <10 stars, last commit >1yr | Abandoned learning project |
| >100 stars, active commits | Established project worth evaluating |
| >1k stars, multiple contributors | Community-vetted, likely reliable |
| Install command involves `npx skills` | **Fake.** npx has no `skills add` subcommand |
| Claims "92%" / "revolutionary" / "shocking" | Marketing language — verify independently |
| MIT license + CI + docs | Professional-grade open source |
| README says "migrated to" | Repo is archived — find the active one |