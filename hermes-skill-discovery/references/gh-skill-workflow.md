# `gh skill` Workflow — GitHub CLI Skill Manager

GitHub shipped `gh skill` on 2026-04-16 as the official package manager for AI agent skills (see https://github.blog/changelog/2026-04-16-manage-agent-skills-with-github-cli/). This reference captures what works, what doesn't, and when to prefer it over `hermes skills install` or raw `git clone`.

## When to use `gh skill` vs `hermes skills install` vs `git clone`

| Source type | Best path | Why |
|---|---|---|
| Skill in `skills.sh` registry (Hub) | `hermes skills install <name> --force --yes` | Native install path, security verdict surfaced |
| Skill published as GitHub Gist | `gh skill add <gist-url>` | `gh skill` is gist-native |
| Skill in raw GitHub repo, NOT in Hub | `git clone --depth=1` + manual copy | `gh skill add owner/repo` fails (gist URL required); `hermes skills search` returns empty |
| Skill in large monorepo (>5MB) | `git clone --depth=1` + manually copy only `SKILL.md` + optional `scripts/` | Avoid cloning entire repo |

**Decision rule**: if `hermes skills search <kw>` returns nothing AND `gh skill search <kw>` returns something, use `gh skill`. If neither returns it, fall back to `git clone`.

## Installation

### Built-in (gh v2.90.0+)
```bash
gh update   # upgrade local gh to 2.90.0+
gh skill --version
gh skill search "memory management"
gh skill add <gist-url> --yes
gh skill list
```

### Extension (gh v2.89.0 and earlier — verified 2026-07-02)
```bash
# Repo name MUST be `gh-` prefixed — "extension name must start with `gh-`" otherwise
gh extension install nicholasspencer/gh-skill
gh skill --version
gh skill search "memory"
gh skill add <gist-url> --yes
```

**Why nicholasspencer/gh-skill works but others don't**: at time of writing (2026-07), the official `github/gh-skill` and `github-actions/gh-skills` extensions are not yet public on the `github` org. `nicholasspencer/gh-skill` is the working community extension with full subcommand coverage.

## Subcommands (verified working)

```
gh skill add         Install a skill from a GitHub Gist
gh skill completion  Generate the autocompletion script for the specified shell
gh skill fork        Fork a skill as your own gist
gh skill info        Show details about an installed skill
gh skill init        Install the gh-skill meta skill into detected tool directories
gh skill install     Download skill files to the current directory
gh skill link        Link a skill to a specific tool's skill directory
gh skill list        List installed skills
gh skill publish     Publish a local skill folder as a GitHub Gist
gh skill remove      Remove an installed skill
gh skill search      Search for skills on GitHub Gists and GitLab Snippets
gh skill trust       Manage trusted authors
gh skill update      Update a skill to the latest gist revision
```

## Pitfalls (verified)

1. **`gh skill add <owner>/<repo>` expects a gist URL, not a repo path.** `gh skill add thorwhalen/skill` fails with "failed to fetch gist: exit status 1". When `gh skill search` returns results in `owner/repo` format, those are gist IDs, NOT GitHub repos. The command needs the actual gist URL or full gist ID.

2. **`gh extension install` enforces `gh-` prefix on repo name.** Community repos named `skilz-cli`, `claude-skill-registry`, etc. cannot be installed as extensions even if they look like they should be. Verified failures: `SpillwaveSolutions/skilz-cli` ("extension name must start with `gh-`"), `github/gh-skill` ("Could not find extension on host github.com"), `github-actions/gh-skills` (same).

3. **`gh skill search` returns results from gist search, which is biased toward popular gists.** Less useful than `hermes skills search` for discovering domain-specific skills, but better for one-off gists that someone published.

4. **Large `gh repo clone` calls RPC-fail on slow links.** When `gh repo clone <large-monorepo>` hangs, fall back to plain `git clone --depth=1 <url>`. The `gh` wrapper adds no value for one-off clones.

5. **`gh skill` and `hermes skills install` are parallel universes.** A skill installed via `gh skill` lives in the `gh-skill` store, NOT in `~/.hermes/skills/`. To make it discoverable to Hermes, copy the gist content into `~/.hermes/skills/<name>/` manually (treat `gh skill` as discovery + download, not install).

## Recommended workflow (Path B from SKILL.md)

```bash
# 1. Find candidates
gh skill search "<keyword>" | head -20

# 2. Try to add the gist
gh skill add <gist-url-or-id> --yes

# 3. Inspect what got downloaded
gh skill list
gh skill info <name>

# 4. Bridge to Hermes — copy into ~/.hermes/skills/_community/
SKILL_DIR=$(gh skill info <name> --json path | jq -r .path)
mkdir -p ~/.hermes/skills/_community/<name>
cp -r "$SKILL_DIR"/* ~/.hermes/skills/_community/<name>/

# 5. Verify spec compliance — name: in frontmatter MUST match directory name
NAME=$(grep '^name:' ~/.hermes/skills/_community/<name>/SKILL.md | awk '{print $2}')
[ "$NAME" = "<name>" ] || echo "WARNING: frontmatter name=$NAME but dir=<name>"

# 6. Confirm Hermes sees it
hermes skills list | grep <name>
```

## When `gh skill` is NOT the right tool

- Skill lives in a real GitHub repo with full README, CI, releases → use `git clone` + `hermes skills install` (Path A) or Path C
- Skill is in the Hermes Hub registry → use `hermes skills install` directly (Path A)
- You only need the SKILL.md content for reference → `web_extract` from `raw.githubusercontent.com/<owner>/<repo>/<branch>/SKILL.md`
- Network is slow / unreliable → `gh skill` adds round-trips for gist fetch that `git clone --depth=1` avoids

## Companion script

See `scripts/install_from_clone.sh` for an automated Path C workflow (raw `git clone` → spec-compliant Hermes install).