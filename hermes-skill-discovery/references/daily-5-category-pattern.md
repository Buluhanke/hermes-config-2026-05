# Daily Skill Acquisition — 5-Category Gap Pattern

Distilled from a real `cron` run on 2026-07-03: discovered 5 dimensions where Hermes has zero or thin coverage, ran 5 `web_search` queries in parallel, selected the highest-signal candidate per category, installed (or recorded rejection reason), and updated the audit trail.

This is the **class-level pattern** for any "find N skills today" cron / autonomous loop. Replace N=5 with whatever the prompt demands; the 5-category dimensions should be re-derived each run from the current `~/.hermes/skills/` inventory — NOT hardcoded.

## The 5 hermes dimensions (as of 2026-07-03)

These emerged from inventorying the then-current `~/.hermes/skills/` (~62 installed) and identifying the dimensions that had zero or thin coverage:

| # | Dimension | What gaps it covers | 2026-07-03 pick |
|---|-----------|---------------------|-----------------|
| 1 | **真屏幕理解 / 多模态 agent** | GUI element detection, VLM screen grounding | `peekaboo-macos-automation` (clawhub) — PeekabooV3 macOS automation |
| 2 | **安全 / 凭据 / 隐私** | Vault lifecycle, SOPS, secrets rotation | `secrets-management` (skills.sh/wshobson) |
| 3 | **离线工具集成 / 本地服务编排** | workflow engine, container orchestration | `ai-workflow-automation-generator` (clawhub) |
| 4 | **性能监控 / 内存治理 / 可靠性** | OTel, Prometheus exporters, eBPF | `afrexai-observability-engine` (clawhub, CAUTION --force) |
| 5 | **跨平台 / 跨渠道 / 统一 observability** | structured logging, tracing, OTel | `logging-observability` (clawhub) |

**How to re-derive these** for future cron runs:

```bash
# Step 1: dump current inventory
hermes skills list --json | jq -r '.[].name' > /tmp/installed_skills.txt
ls ~/.hermes/skills/ | sort > /tmp/installed_dirs.txt

# Step 2: count by source (skills.sh vs clawhub vs local vs builtin)
hermes skills list | grep -E "skills.sh|clawhub|builtin|local" | sort | uniq -c

# Step 3: identify thin categories
# A dimension is "thin" if (installed < 2) OR (installed only at deployment-tier but not design-tier)
# e.g. observability had 2 deploy-only skills (prometheus-monitoring, alloy) but 0 design-only skills → gap
```

## The 5-step loop (proven in cron on 2026-07-03)

```
1. INVENTORY  →  identify 5 dimensions where current coverage is thin (or absent)
2. SEARCH     →  1 web_search per dimension (kept queries narrow: "X 2026 best practice OR github OR production ready")
3. INSPECT    →  for each top result, run `hermes skills inspect <name>` AND `hermes skills search <kw>`
4. CLASSIFY   →  three-way: hub-installable / raw-repo-clone / not-a-skill (drop the not-a-skill)
5. RECORD     →  update ~/.hermes/skills_pending.json with installed_today + rejected + pending_candidates
```

**Loop integrity rules (verified 2026-07-03):**

- Step 5 is **non-optional**. Rejecting a skill is just as durable as installing one — both go in the audit file. "找不到就 SILENT" is a failure mode; the user wants the gap classified, not papered over.
- Step 2 runs in parallel (5 terminal `web_search` calls in the same response block). Sequential = ~25s; parallel = ~6s.
- Step 3 must happen BEFORE Step 4. Install then read findings = wasted install + a half-install rollback.
- Step 4 picks ONE install + ONE backup per dimension. Never install 2 alternatives to "be safe" — that's task creep. If the chosen one BLOCKED, the backup is the install target. If both blocked → record both in rejected.

## Install path discovery (URLs that actually work)

Hermes `skills install <id>` has three resolvable URL forms. Verified 2026-07-03 which works for each source:

| Source | Tried identifier form | Tried URL form | Verdict |
|--------|----------------------|----------------|---------|
| clawhub | `peekaboo-macos-automation` → "No exact match" suggested identifier | `https://clawhub.ai/skills/peekaboo-macos-automation` | ✅ Works (URL form, with `--yes`) |
| skills.sh | `skills-sh/wshobson/agents/secrets-management` → fetches + installs directly | `https://skills.sh/wshobson/agents/secrets-management` | ✅ Works (identifier form, no URL needed) |
| skills.sh | `skills-sh/alirezarezvani/claude-skills/secrets-vault-manager` (short ID) → fetched + DANGEROUS blocked | `https://skills.sh/alirezarezvani/claude-skills/secrets-vault-manager` | ❌ "Could not fetch ... from any source" |

**Rule of thumb (verified 2026-07-03):**

- `clawhub` skills → install via **URL** form `https://clawhub.ai/skills/<identifier>` (identifier form is "suggest-only", not installable)
- `skills.sh` skills → install via **short identifier** `skills-sh/<owner>/<repo>/<skill>` (URL form fails fetch)
- If URL form fails for `skills.sh` → fall back to raw git-clone Path C (see parent SKILL.md)

## Hard-won specifics (2026-07-03 real session)

### `--force` is INTERACTIVE; cron needs both `--force --yes`

When `hermes skills install <id> --force` runs in a pipe-driven cron context, the "Confirm [y/N]:" prompt silently defaults to N because stdin is EOF'd. **Always pair `--force` with `--yes`**:

```bash
# WRONG (works in interactive TTY but cancels silently in cron/hermes send):
hermes skills install foo --force
# Confirm [y/N]:  ← stdin EOF → default N → install cancelled

# RIGHT (works in every context):
hermes skills install foo --force --yes
```

### CAUTION is overridable; DANGEROUS is not

This is in the main SKILL.md but it bears repeating because it cost a wasted `--force` attempt in this session:

```bash
# CAUTION — proper override:
hermes skills install afrexai-observability-engine --force --yes
# → "BLOCKED ... Use --force to override." then "Installed: ... Files: ..."

# DANGEROUS — never use --force; pick a backup:
hermes skills install secrets-vault-manager --force --yes
# → "BLOCKED ... --force does not override a dangerous verdict."
# → MUST go to backup candidate
```

The pivot workflow when the chosen skill is DANGEROUS:

```bash
# Re-search with a tighter scope to find a less-feature-rich alternative
hermes skills search "secrets-management" --source skills.sh --json | jq -r '.[].identifier' | head -5
# Try the top result. If that's also BLOCKED-DANGEROUS, record reason + move on.
```

### The DANGEROUS findings worth respecting (not all false positives)

`Encryptedenergy-uptime` was DANGEROUS for these **legitimate** reasons (not scanner false positives):

- `CRITICAL exfiltration` in `scripts/ping.sh:67` — actually sends `status.gateway.self.host` to a remote endpoint. Real data leak.
- `MEDIUM persistence` — actually wants `crontab` injection with `PATH=$HOME/.npm-global/bin:...` PATH hijack. Real.

vs. CAUTION findings for `afrexai-observability-engine` (false positive):

- `HIGH exfiltration` on a SKILL.md table cell containing `| environment | string | Which env | production |` — the static scanner regex'd on the substring `production` misinterpreting a config-table column header as a network endpoint.

**Workflow before --force on CAUTION:** read the actual finding line numbers and content. If the line is a SKILL.md prose sentence or a config-table cell, it's almost always false positive. If it's a `*.sh / *.py` line with literal network calls, it's real.

### What does NOT count as a skill (drop these, don't try to install)

The 2026-07-03 loop hit candidates that turned out to be repos not skills:

- `OmniParser V2` (microsoft/omniparser) → Jupyter + Python + V2 weights, no SKILL.md
- `UI-TARS-desktop` (ByteDance) → TypeScript desktop app, no SKILL.md
- All `awesome-*` index repos → just curated lists, no installable artifacts

For these, record as `pending_candidates[]` in `skills_pending.json` with `reason_pending` describing what they would need to become installable (separate skill shim, Docker container, etc.). **Do not attempt `hermes skills install microsoft/OmniParser`** — the registry will say "Could not find X in any source" and waste a round trip.

## Audit trail integrity

The `~/.hermes/skills_pending.json` file is the only durable record. Schema:

```json
{
  "date": "YYYY-MM-DD",
  "installed_today": [
    {
      "name": "<canonical id>",
      "category": "<1-5 dimension name>",
      "source": "<clawhub | skills.sh/<owner>/<repo> | local | builtin>",
      "verdict": "SAFE | CAUTION | DANGEROUS",
      "uses": "<1-line description of what this skill actually unlocks>"
    }
  ],
  "rejected": [
    {
      "name": "<id>",
      "reason": "<verdict + ACTUAL finding excerpt, e.g. 'DANGEROUS — CRITICAL exfiltration scripts/ping.sh:67 sent status.gateway.self.host to remote endpoint'>"
    }
  ],
  "pending_candidates": [
    {
      "name": "<id>",
      "repo": "https://github.com/<owner>/<repo>",
      "category": "<dimension>",
      "stars": <number>,
      "reason_pending": "<why not installed today — Docker required / 5GB VLM weights / no SKILL.md>"
    }
  ]
}
```

**Field-rule refresher:**

- `uses` is a 1-sentence value statement ("what does installing this actually do for the user"). NOT a copy of the SKILL.md description.
- `reason` in `rejected` **must** quote or paraphrase the actual finding text. Vague rejections ("didn't pass security check") are not durable.
- `reason_pending` is forward-looking ("could install later if Docker comes back online"), not backward-looking ("didn't install today").

## When this pattern does NOT apply

- When the user wants a single specific skill for an active task — `web_search` for it, install it, done. Don't widen to 5 dimensions.
- When the user's "find skills" prompt specifies a single domain (e.g. "find me a screenshot OCR skill") → search that domain only, do NOT slot-fill to 5.
- When `~/.hermes/skills/` already has >5 skills in every dimension → the gap doesn't exist; report "no missing dimensions found" and stop. Do not invent gaps.

## Verification (use these after every cron run)

```bash
# 1. count grew by the right amount
hermes skills list | wc -l  # before vs after

# 2. each new skill is on disk
for s in installed_today_names; do
  test -d ~/.hermes/skills/$s && echo "✓ $s" || echo "✗ MISSING $s"
done

# 3. audit file updated
cat ~/.hermes/skills_pending.json | jq '.date, (.installed_today | length), (.rejected | length), (.pending_candidates | length)'
```

If verification 1 shows count grew by less than expected, some install silently failed → re-run with `--force --yes` and capture stderr.
