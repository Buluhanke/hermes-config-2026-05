# Hermes Community Skill Tips — verified install recipes

Distilled from real cron runs (2026-07-02 daily acquisition + earlier sessions).

## Security verdict decision tree (verified 2026-07-02)

The Hermes installer runs a static regex scan and emits one of three verdicts. Each behaves differently with `--force`:

| Verdict | Behavior | `--force` | When to override |
|---------|----------|-----------|-----------------|
| `SAFE` | Installs silently | n/a | Never needed |
| `CAUTION` | Prompts `Confirm [y/N]:` | `--force` skips prompt; install proceeds | Almost always — most findings are static-scanner false positives (e.g. `os.getenv()` flagged as `CRITICAL exfiltration`). Read findings first. |
| `DANGEROUS` | Hard-blocked | `--force does not override a dangerous verdict` (verbatim CLI output) | Never. If you genuinely need this skill, source the SKILL.md manually + manually audit. |

**Practical recipe**: `hermes skills install <name> --force --yes` works for SAFE/CAUTION. For DANGEROUS, drop the skill entirely or contact the user — do NOT try to override.

## Pending-candidates JSON schema (verified 2026-07-02)

Single audit file: `~/.hermes/skills_pending.json`. Replaced wholesale each cron run; preserves last-run schema. Lets future agents see what was tried/rejected/deferred without re-discovering.

```json
{
  "date": "YYYY-MM-DD",
  "installed_today": [
    {"name": "...", "category": "...", "source": "skills.sh/<owner>/<repo>", "verdict": "safe|caution|danger", "uses": "..."}
  ],
  "rejected": [
    {"name": "...", "reason": "DANGEROUS verdict — ..."}
  ],
  "pending_candidates": [
    {"name": "...", "repo": "https://github.com/...", "category": "...", "stars": N, "reason_pending": "..."}
  ],
  "missing_categories_remaining": ["..."]
}
```

## Mac mini 24GB resource classifier

Before install, classify the candidate into one of three footprint tiers:

- **Tier 1: SKILL.md only** (~10-50KB, no runtime) — always safe to install. Examples: `prometheus-monitoring`, `computer-use`, `alloy` (just SKILL.md + a few kb of references).
- **Tier 2: Skill + script helpers** (~100KB-1MB, requires Python/Node) — safe if main process is dead-simple. Examples: `scaffold_skill.sh`.
- **Tier 3: Live service** (Docker stack, daemon, VLM weights) — needs explicit user opt-in. Examples: n8n, LibreChat, OmniParser V2 (needs ~5GB weights).

**Default behavior**: Tier 1 default-on. Tier 2 default-on, mention in pending. Tier 3 default-OFF unless user says install.

## Skills Hub coverage gaps (2026-07-02 snapshot)

Raw repos that don't appear in `hermes skills search` and need manual `git clone`:
- `microsoft/OmniParser` — 25k stars, YOLO+Florence VLM, 5GB weights, GPU recommended
- `bytedance/UI-TARS-desktop` — 37k stars, OSWorld SOTA agent, Node 22+
- `n8n-io/n8n` — 195k stars, requires Docker for full deployment; skills.sh has thin wrapper at `skills-sh/vladm3105/aidoc-flow-framework/n8n` but that wrapper hits DANGEROUS verdict
- `yysd5/macos-monitoring` — 3 stars but specifically macOS + Prometheus + Grafana; Docker required

## Cron-friendly install recipe (no-tty)

```bash
# Interactive shell — answers prompts interactively:
hermes skills install alloy --force
# Confirm [y/N]: y

# Cron / piped stdin — explicitly answer yes:
echo y | hermes skills install alloy --force
# OR explicitly:
hermes skills install alloy --force --yes
```

Without explicit yes, in piped mode the install CANCELS at "Confirm [y/N]:" because stdin EOFs before the prompt.

## Hygiene

- `~/.hermes/skills_pending.json` should grow by at most ~5 entries per day. If it's ballooning, the categories being searched are too broad — narrow `web_search` queries.
- After installing N skills, run `hermes skills list | wc -l` to confirm count grew by N. If not, one or more installs silently failed.
