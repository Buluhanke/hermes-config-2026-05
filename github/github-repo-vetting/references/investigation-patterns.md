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
