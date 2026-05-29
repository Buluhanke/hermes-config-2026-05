# GitHub Push Protection — Secret/Key Detection + OAuth vs PAT

## What Triggers It
GitHub's pre-receive hooks scan **all commits** in the push for embedded secrets:

| Prefix | Service | Example |
|--------|---------|---------|
| `sk-` | OpenAI (legacy) | `sk-abc123...` |
| `sk-proj-` | OpenAI (project) | `***...` |
| `sk-cp-` | OpenAI (chat completion) | `sk-cp-abc123...` |
| `gsk_` | Groq | `gsk_abc123...` |
| `nvapi-` | NVIDIA | `nvapi-abc123...` |
| `AIzaSy` | Google AI | `AIzaSyabc123...` |
| `gho_` | GitHub OAuth | `gho_MtQw4...` |
| `ghp_` | GitHub PAT | `ghp_abc123...` |
| `xoxb-` | Slack | `xoxb-abc123...` |
| `AKIA` | AWS | `AKIAABC123...` |

Even a single old commit in a large history will block the entire push.

## Symptom
```
$ git push origin main
remote: error: GH013: Push cannot contain secrets
remote:   — Push cannot contain secrets
remote:     — Groq API Key — path: scripts/test_keys.py:26
```
Or:
```
ERROR: denied: commit contains forbidden content
remote: error: GH001: Large files detected (or)
remote: error: pre-receive hook declined
```

## Core Fix: Clean History

### Approach A — Reset to clean remote (fastest when remote is good)
```bash
git stash push -m "temp" -- <files>
git reset --hard origin/main
git stash pop  # if you have uncommitted changes worth keeping
```

### Approach B — Rebuild from scratch (when remote is also bad)
```bash
# Step 1: Triage — identify large/excluded dirs
du -sh */

# Step 2: Check for embedded git repos (they become submodules if staged!)
ls -la some-dir/.git  # if exists, mv it aside:
mv embedded-repo/.git embedded-repo/.git.bak

# Step 3: Build comprehensive .gitignore
cat > .gitignore << 'EOF'
# Large cache dirs
node_modules/
.venv/
__pycache__/
*.pyc
*.db
*.db-wal
*.db-shm
.DS_Store
*.swp
*.git.bak/

# Runtime dirs
logs/
cache/
cron/output/

# Standalone projects (own .git)
hermes-agent/
hermes-agent.git.bak/
EOF

# Step 4: Nuclear rebuild
rm -rf .git
git init
git add .gitignore
git add dir1/ dir2/ config.yaml  # NOT -A, add selectively
git commit -m "clean init $(date '+%Y-%m-%d')"

# Step 5: Push to new repo
gh repo create new-repo-name --public --description "..."
git remote add origin https://github.com/owner/new-repo-name.git
git push origin master
```

## Why `git rm --cached` Doesn't Work
`git rm --cached <file>` only removes the file from the **current** commit. The blob still exists in `.git/objects/`. GitHub scans the full history — history rewrite is the only real solution. After `rm --cached`, always verify: `du -sh .git/objects/` to confirm size decreased.

## The 3-Pass filter-branch Pattern (git ≤ 2.22 fallback)

When `git-filter-repo` is unavailable (git < 2.22), use `git filter-branch`. **Do NOT try to catch all patterns in one pass** — testing reveals what was missed. Use 3 passes:

```bash
# PASS 1 — obvious patterns (sk-, gho_)
git filter-branch --force --index-filter \
  'git rm -rf --cached --ignore-unmatch \
    $(find . -type f -name "*.md" -o -name "*.py" -o -name "*.yaml" -o -name "*.json" -o -name "*.sh" 2>/dev/null)' \
  --prune-empty --tag-name-filter cat -- --all

# PASS 2 — expand to all known secret prefixes
# Run this AFTER verifying pass 1 removed obvious keys
# This sed catches gsk_, nvapi-, AIzaSy, etc.
git filter-branch --force --index-filter \
  'git rm -rf --cached --ignore-unmatch $(git ls-files)' \
  --prune-empty --tag-name-filter cat -- --all

# Alternative to pass 2 — sed all files directly:
git filter-branch --tree-filter \
  'if [ -f SKILL.md ]; then
     sed -i "" "s/sk-[a-zA-Z0-9]*/SK_REDACTED/g
                  s/gsk_[a-zA-Z0-9]*/GRSK_REDACTED/g
                  s/nvapi-[a-zA-Z0-9]*/NVIDAPI_REDACTED/g
                  s/AIzaSy[a-zA-Z0-9]*/GOOGLE_AI_KEY_REDACTED/g
                  s/gho_[a-zA-Z0-9]*/GHO_REDACTED/g
                  s/ghp_[a-zA-Z0-9]*/GHP_REDACTED/g
                  s/xoxb-[a-zA-Z0-9]*/SLACK_REDACTED/g
                  s/AKIA[A-Z0-9]*/AWS_KEY_REDACTED/g"
   fi' \
  --prune-empty --tag-name-filter cat -- --all

# PASS 3 — verify, then push
git show HEAD:SKILL.md | grep -c "gsk_\|nvapi-\|AIzaSy"
# Should return 0

git push --force origin main
```

**Key lesson**: First filter-branch only catches `sk-` and `gho_`. GH013 still fires because `gsk_` (Groq), `nvapi-` (NVIDIA), `AIzaSy` (Google) are missed. Run at least 2 passes.

## .hermes 减肥做减法 — What to Delete, What to Keep

When `.hermes` exceeds 5GB (GitHub limit):

### Always DELETE (bloat):
```
# Large generated artifacts
chrome-debug/          # 5GB+, browser automation state
state-snapshots/      # session snapshots
sessions/             # old session data
mirofish/             # fish shell configs
turix-cua/            # CUA state
UI-TARS-desktop/      # desktop agent
node/                 # node binaries

# Build artifacts in hermes-agent/
hermes-agent/venv/ hermes-agent/.venv/
hermes-agent/node_modules/
hermes-agent/__pycache__/
hermes-agent/.gitnexus/
hermes-agent/docs/ hermes-agent/website/
hermes-agent/tests/ hermes-agent/docker/
hermes-agent/nix/ hermes-agent/packaging/
hermes-agent/assets/ hermes-agent/egg-info/
hermes-agent/infographic/

# Runtime/cache in hermes-agent/
hermes-agent/ui-tui/ hermes-agent/web/

# Large runtime dirs
lsp/ include/ lib/ rtk/
venv-ocr/ bin/
cron/output/ logs/
mcp-chrome-extension/
state.db*  shared/  paste/
screenshots/ cache/ checkpoint*
workspace/ .DS_Store

# Standalone projects (own .git)
mcp/  desktop-agent-template/
notebooklm/  creative/
```

### Always KEEP:
```
# Core Hermes dirs (small)
scripts/           # operational scripts
skills/            # 154MB — skills repo
hermes-agent/      # 80MB — Hermes Agent source (stripped)
venv/              # 8MB — Hermes runtime dep
config files        # YAML, JSON, .env.example
```

### Result:
`.hermes`: 20GB → 1.1GB (skills 154MB + hermes-agent 80MB + rest <20MB)

## OAuth Token vs PAT for delete_repo

When attempting to delete a GitHub repo via API:
```bash
curl -X DELETE https://api.github.com/repos/owner/repo \
  -H "Authorization: token $TOKEN"
# Returns: 403 "Must have admin rights to Repository"
```

`gh auth status` shows scopes: `gist, read:org, repo, workflow` — no `delete_repo`.

**Root cause**: OAuth device code flow (used by `gh auth login`) does NOT grant `delete_repo` scope. PATs (token prefix `ghp_`) include `delete_repo` by default.

**Solution options**:
1. Use a PAT with `delete_repo` scope in the remote URL
2. `gh auth refresh -h github.com -s delete_repo` (requires browser flow, times out on slow network)
3. User deletes old repo manually on GitHub web UI
4. Create new repo → push → user deletes old repo → rename new to original

## Prevention
- Never commit API keys or tokens to git
- Use `.gitignore` for credentials files; for env vars use `.env.example` (values = `***`)
- For secrets needed in CI, use GitHub Actions secrets, not env vars in code
- Run `git add --dry-run -A` before `git add -A` to preview what would be staged
- Before first push: `git verify-commit HEAD` to check for accidentally committed secrets
- When GH013 fires after filter-branch: the pattern list was incomplete — check for missed key types (gsk_, nvapi-, AIzaSy) and run another filter-branch pass
