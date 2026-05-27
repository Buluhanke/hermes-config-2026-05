---
name: github-repo-management
description: "Clone/create/fork repos; manage remotes, releases."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Repositories, Git, Releases, Secrets, Configuration]
    related_skills: [github-auth, github-pr-workflow, github-issues]
---

# GitHub Repository Management

Create, clone, fork, configure, and manage GitHub repositories. Each section shows `gh` first, then the `git` + `curl` fallback.

Add step: Verify URL with case-sensitive check. Add pitfall: Private repos require owner contact. Add reference: 404 error handling workflow (see references/404-github-repo.md). Update trigger to include "repository not found" scenarios.

### Setup

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi

# Get your GitHub username (needed for several operations)
if [ "$AUTH" = "gh" ]; then
  GH_USER=$(gh api user --jq '.login')
else
  GH_USER=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | python3 -c "import sys,json; print(json.load(sys.stdin)['login'])")
fi
```

If you're inside a repo already:

```bash
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

---

## 1. Cloning Repositories

Cloning is pure `git` — works identically either way:

```bash
# Clone via HTTPS (works with credential helper or token-embedded URL)
git clone https://github.com/owner/repo-name.git

# Clone into a specific directory
git clone https://github.com/owner/repo-name.git ./my-local-dir

# Shallow clone (faster for large repos)
git clone --depth 1 https://github.com/owner/repo-name.git

# Clone a specific branch
git clone --branch develop https://github.com/owner/repo-name.git

# Clone via SSH (if SSH is configured)
git clone git@github.com:owner/repo-name.git
```

**Pitfall: Embedded Git Repositories**
If `~/.hermes/hermes-agent/` is itself a git clone, `git add -A` will add it as an embedded submodule and produce a cryptic warning:
```
warning: adding embedded git repository: hermes-agent
```
Before staging, either `git rm --cached hermes-agent` or add it to `.gitignore`. Large vendored directories (`node_modules/`, `lib/`, `share/`, `include/`, `sandboxes/`, `cache/`, etc.) should also be in `.gitignore` to avoid bloating the repo.

---

### Clone via SSH (if SSH is configured)

```bash
gh repo clone owner/repo-name
gh repo clone owner/repo-name -- --depth 1
```

## 2. Creating Repositories

**With gh:**

```bash
# Create a public repo and clone it
gh repo create my-new-project --public --clone

# Private, with description and license
gh repo create my-new-project --private --description "A useful tool" --license MIT --clone

# Under an organization
gh repo create my-org/my-new-project --public --clone

# From existing local directory
cd /path/to/existing/project
gh repo create my-project --source . --public --push
```

**With git + curl:**

```bash
# Create the remote repo via API
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos \
  -d '{
    "name": "my-new-project",
    "description": "A useful tool",
    "private": false,
    "auto_init": true,
    "license_template": "mit"
  }'

# Clone it
git clone https://github.com/$GH_USER/my-new-project.git
cd my-new-project

# -- OR -- push an existing local directory to the new repo
cd /path/to/existing/project
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/$GH_USER/my-new-project.git
git push -u origin main
```

To create under an organization:

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/orgs/my-org/repos \
  -d '{"name": "my-new-project", "private": false}'
```

### From a Template

**With gh:**

```bash
gh repo create my-new-app --template owner/template-repo --public --clone
```

**With curl:**

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/template-repo/generate \
  -d '{"owner": "'"$GH_USER"'", "name": "my-new-app", "private": false}'
```

## 3. Forking Repositories

**With gh:**

```bash
gh repo fork owner/repo-name --clone
```

**With git + curl:**

```bash
# Create the fork via API
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/repo-name/forks

# Wait a moment for GitHub to create it, then clone
sleep 3
git clone https://github.com/$GH_USER/repo-name.git
cd repo-name

# Add the original repo as "upstream" remote
git remote add upstream https://github.com/owner/repo-name.git
```

### Push to a Pre-Created GitHub Repo (No gh / No Token)

When the user has already created the repo on GitHub web UI and you have no `gh` CLI and no GitHub token, you cannot push directly. Two options:

**Option A (Recommended): Let the user run `git push` manually**
The terminal will open a browser window for GitHub login — no token needed on your end.
```bash
cd /path/to/local/repo
git remote add origin https://github.com/username/repo-name.git
git push -u origin main
# GitHub will prompt for username + password (use PAT as password)
```

**Option B: Embed PAT in remote URL**
If the user provides a Personal Access Token, push directly:
```bash
git remote add origin https://<TOKEN>@github.com/username/repo-name.git
git push -u origin main
```

> **Pitfall:** `git push` fails with "could not read Username: Device not configured" — this means no credential helper is configured and no token is embedded. Do NOT keep retrying; offer the user Option A (manual push) or ask for a PAT.

> **Pitfall: Large file in git history (>100MB).** If GitHub rejects the push with `GH001: Large files detected` and the large file is already committed in local history, `git rm --cached <file>` on the current commit does NOT remove it from history — the blob still exists in `.git/objects/`. GitHub runs pre-receive hooks that scan the entire history. **Fix: rebuild a clean history.**
>
> ```bash
> # Step 1: Save any uncommitted changes you want to keep
> git stash push -m "temp" -- <files>
>
> # Step 2: Nuke the corrupt .git and reinitialize
> cd /path/to/local/repo
> rm -rf .git
> git init
>
> # Step 3: Re-add only the files you actually want to track
> # (make sure .gitignore is in place first, then add selectively)
> git add .gitignore README.md src/ config/ ...
> git commit -m "clean initial commit"
>
> # Step 4: Push with PAT embedded in URL
> git remote add origin https://<PAT>@github.com/owner/repo.git
> git push --force origin main
>
> # Step 5: Restore uncommitted changes from stash
> git stash pop
> ```
>
> In this session: `bin/node` (108MB, a Node binary) was committed and blocked the push. The rebuild approach succeeded where `git rm --cached` + re-commit failed.

---

### Keeping a Fork in Sync

```bash
# Pure git — works everywhere
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

**With gh (shortcut):**

```bash
gh repo sync $GH_USER/repo-name
```

## 4. Repository Information

**With gh:**

```bash
gh repo view owner/repo-name
gh repo list --limit 20
gh search repos "machine learning" --language python --sort stars
```

**With curl:**

```bash
# View repo details
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO \
  | python3 -c "
import sys, json
r = json.load(sys.stdin)
print(f\"Name: {r['full_name']}\")
print(f\"Description: {r['description']}\")
print(f\"Stars: {r['stargazers_count']}  Forks: {r['forks_count']}\")
print(f\"Default branch: {r['default_branch']}\")
print(f\"Language: {r['language']}\")"

# List your repos
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/user/repos?per_page=20&sort=updated" \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin):
    vis = 'private' if r['private'] else 'public'
    print(f\"  {r['full_name']:40}  {vis:8}  {r.get('language', ''):10}  ★{r['stargazers_count']}\")"

# Search repos
curl -s \
  "https://api.github.com/search/repositories?q=machine+learning+language:python&sort=stars&per_page=10" \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin)['items']:
    print(f\"  {r['full_name']:40}  ★{r['stargazers_count']:6}  {r['description'][:60] if r['description'] else ''}\")"
```

## 5. Repository Settings

**With gh:**

```bash
gh repo edit --description "Updated description" --visibility public
gh repo edit --enable-wiki=false --enable-issues=true
gh repo edit --default-branch main
gh repo edit --add-topic "machine-learning,python"
gh repo edit --enable-auto-merge
```

**With curl:**

```bash
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO \
  -d '{
    "description": "Updated description",
    "has_wiki": false,
    "has_issues": true,
    "allow_auto_merge": true
  }'

# Update topics
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.mercy-preview+json" \
  https://api.github.com/repos/$OWNER/$REPO/topics \
  -d '{"names": ["machine-learning", "python", "automation"]}'
```

## 6. Branch Protection

```bash
# View current protection
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/branches/main/protection

# Set up branch protection
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/branches/main/protection \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": ["ci/test", "ci/lint"]
    },
    "enforce_admins": false,
    "required_pull_request_reviews": {
      "required_approving_review_count": 1
    },
    "restrictions": null
  }'
```

## 7. Secrets Management (GitHub Actions)

**With gh:**

```bash
gh secret set API_KEY --body "your-secret-value"
gh secret set SSH_KEY < ~/.ssh/id_rsa
gh secret list
gh secret delete API_KEY
```

**With curl:**

Secrets require encryption with the repo's public key — more involved via API:

```bash
# Get the repo's public key for encrypting secrets
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/secrets/public-key

# Encrypt and set (requires Python with PyNaCl)
python3 -c "
from base64 import b64encode
from nacl import encoding, public
import json, sys

# Get the public key
key_id = '<key_id_from_above>'
public_key = '<base64_key_from_above>'

# Encrypt
sealed = public.SealedBox(
    public.PublicKey(public_key.encode('utf-8'), encoding.Base64Encoder)
).encrypt('your-secret-value'.encode('utf-8'))
print(json.dumps({
    'encrypted_value': b64encode(sealed).decode('utf-8'),
    'key_id': key_id
}))"

# Then PUT the encrypted secret
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/secrets/API_KEY \
  -d '<output from python script above>'

# List secrets (names only, values hidden)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/secrets \
  | python3 -c "
import sys, json
for s in json.load(sys.stdin)['secrets']:
    print(f\"  {s['name']:30}  updated: {s['updated_at']}\")"
```

Note: For secrets, `gh secret set` is dramatically simpler. If setting secrets is needed and `gh` isn't available, recommend installing it for just that operation.

## 8. Releases

**With gh:**

```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release create v2.0.0-rc1 --draft --prerelease --generate-notes
gh release create v1.0.0 ./dist/binary --title "v1.0.0" --notes "Release notes"
gh release list
gh release download v1.0.0 --dir ./downloads
```

**With curl:**

```bash
# Create a release
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/releases \
  -d '{
    "tag_name": "v1.0.0",
    "name": "v1.0.0",
    "body": "## Changelog\n- Feature A\n- Bug fix B",
    "draft": false,
    "prerelease": false,
    "generate_release_notes": true
  }'

# List releases
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/releases \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin):
    tag = r.get('tag_name', 'no tag')
    print(f\"  {tag:15}  {r['name']:30}  {'draft' if r['draft'] else 'published'}\")"

# Upload a release asset (binary file)
RELEASE_ID=<id_from_create_response>
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/octet-stream" \
  "https://uploads.github.com/repos/$OWNER/$REPO/releases/$RELEASE_ID/assets?name=binary-amd64" \
  --data-binary @./dist/binary-amd64
```

## 9. GitHub Actions Workflows

**With gh:**

```bash
gh workflow list
gh run list --limit 10
gh run view <RUN_ID>
gh run view <RUN_ID> --log-failed
gh run rerun <RUN_ID>
gh run rerun <RUN_ID> --failed
gh workflow run ci.yml --ref main
gh workflow run deploy.yml -f environment=staging
```

**With curl:**

```bash
# List workflows
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/workflows \
  | python3 -c "
import sys, json
for w in json.load(sys.stdin)['workflows']:
    print(f\"  {w['id']:10}  {w['name']:30}  {w['state']}\")"

# List recent runs
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?per_page=10" \
  | python3 -c "
import sys, json
for r in json.load(sys.stdin)['workflow_runs']:
    print(f\"  Run {r['id']}  {r['name']:30}  {r['conclusion'] or r['status']}\")"

# Download failed run logs
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs

# Re-run a failed workflow
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/rerun

# Re-run only failed jobs
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/rerun-failed-jobs

# Trigger a workflow manually (workflow_dispatch)
WORKFLOW_ID=<workflow_id_or_filename>
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/workflows/$WORKFLOW_ID/dispatches \
  -d '{"ref": "main", "inputs": {"environment": "staging"}}'
```

## 10. Gists

**With gh:**

```bash
gh gist create script.py --public --desc "Useful script"
gh gist list
```

**With curl:**

```bash
# Create a gist
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/gists \
  -d '{
    "description": "Useful script",
    "public": true,
    "files": {
      "script.py": {"content": "print(\"hello\")"}
    }
  }'

# List your gists
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/gists \
  | python3 -c "
import sys, json
for g in json.load(sys.stdin):
    files = ', '.join(g['files'].keys())
    print(f\"  {g['id']}  {g['description'] or '(no desc)':40}  {files}\")"
```

## 11. Automated Git Backup via Cron

Set up recurring `git add` + `commit` + `push` using Hermes's cron system so the repository is backed up automatically.

### Hermes 备份脚本（已创建）

两个脚本已保存在 `scripts/hermes-backup.sh` 和 `scripts/hermes-restore.sh`：

- `scripts/hermes-backup.sh` — 备份 .env、auth.json、Chrome Cookie 到本地目录
- `scripts/hermes-restore.sh` — 从 GitHub 私有仓库 `hermes-backup` 恢复所有配置

### Create the Script

Write a bash script to `~/.hermes/scripts/`:

```bash
cat > ~/.hermes/scripts/hermes-git-backup.sh << 'EOF'
#!/bin/bash
cd ~/.hermes || exit 0

# Check if there are any changes
git diff --quiet && git diff --cached --quiet
if [ $? -eq 0 ]; then
    exit 0  # No changes, silent exit
fi

# Add all changes, commit with timestamp, push
git add -A
git commit -m "auto backup $(date '+%Y-%m-%d %H:%M')"
git push origin main 2>&1 | tail -1
EOF
chmod +x ~/.hermes/scripts/hermes-git-backup.sh
```

### Create the Cron Job

Use Hermes's cron tool (NOT system crontab — Hermes cron jobs survive config reinstall):

```bash
# Hermes CLI
/cron create name=hermes-config-backup schedule=every 1h script=hermes-git-backup.sh no_agent=true
```

Parameters:
- `no_agent=true` — runs the shell script directly, doesn't consume model tokens
- `script=<filename>` — references a script in `~/.hermes/scripts/`
- `schedule` — supports `every 1h`, `every 6h`, `daily at 03:00`, etc.

### ⚠️ Pitfalls

- **First push with no upstream branch**: `git push` may fail with `fatal: The current branch main has no upstream branch.` Fix by running `git push --set-upstream origin main` once manually.
- **Cron job created but script fails silently**: Check the cron job's last run status: `/cron list` shows `last_status` field. The no_agent script's stdout/stderr may not be visible — test it manually first.
- **GitHub token expiry**: If the remote URL embeds a PAT, the token may expire. Configure the remote to use a credential helper or embed a long-lived PAT.
- **Repository must have an upstream set**: If the clone was shallow or has no tracking branch, set it up before scheduling.
- **gh repo delete requires delete_repo scope**: OAuth tokens (prefix `YOUR_TOKEN`, granted via `gh auth login` device flow) do NOT include `delete_repo` scope — even if `gh api` shows `admin: true` on a repo, the underlying token lacks this scope. Device code refresh (`gh auth refresh -h github.com -s delete_repo`) works but requires completing the browser flow at github.com/login/device within the command timeout. PATs (prefix `ghp_`) include `delete_repo` by default. Workaround when OAuth token lacks the scope: have the user delete manually on GitHub web UI, or request a PAT with `delete_repo` permission. Token type can be identified by running `gh auth status` — it shows scopes like `gist, read:org, repo, workflow` — `delete_repo` will be absent if using OAuth flow.
- **GitHub 仓库减肥（清除历史垃圾文件）**：当仓库因历史积累变大（如 chrome-debug、缓存文件、备份文件等已删除但仍在历史中），`git filter-branch` + force push 可真正减小仓库体积。步骤：
  1. `git clone --mirror https://github.com/owner/repo.git /tmp/repo-mirror`（镜像克隆效率更高）
  2. `git filter-branch --force --index-filter 'git rm -rf --cached --ignore-unmatch <大文件或目录>' --prune-empty --tag-name-filter cat -- --all`
  3. `git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin`（清除备份 refs）
  4. `git reflog expire --expire=now --all && git prune && git gc --aggressive --prune=now`
  5. `git push --force --mirror`（推送所有分支和标签）
  - 注意：`gh api repos/<owner>/<repo>` 返回的 `size` 字段有延迟，可能数小时后才更新；用 `git clone` 新建本地目录验证实际大小更准确
  - 此操作不可逆，提前告知用户
- **Merging two unrelated repos**: Use `git fetch <remote>` first, then `git merge <remote>/<branch> --allow-unrelated-histories`. Conflicts in `.gitignore` are common — combine both versions (OR the contents together), then `git add .gitignore` and commit. After merge, push with `--force` if needed.
- **Extracting a remote branch's files without switching**: Use `git archive <remote>/<branch> --prefix=<dir>/ | tar -xf - -C .` — this pulls files directly from the remote without creating a local branch or worktree. Useful when a branch (e.g., `obsidian-backup`) exists on remote but not locally. After extraction, `git add` the new directory and commit.
- **Fetching a remote branch that has no local tracking**: `git ls-tree <remote>/<branch>` shows what's in that branch without fetching. Use `git archive <remote>/<branch> --prefix=<dir>/ | tar -xf - -C .` to extract files from a remote branch into a local directory without switching branches.

## Quick Reference Table

| Action | gh | git + curl |
|--------|-----|-----------|
| Clone | `gh repo clone o/r` | `git clone https://github.com/o/r.git` |
| Create repo | `gh repo create name --public` | `curl POST /user/repos` |
| Fork | `gh repo fork o/r --clone` | `curl POST /repos/o/r/forks` + `git clone` |
| Repo info | `gh repo view o/r` | `curl GET /repos/o/r` |
| Edit settings | `gh repo edit --...` | `curl PATCH /repos/o/r` |
| Create release | `gh release create v1.0` | `curl POST /repos/o/r/releases` |
| List workflows | `gh workflow list` | `curl GET /repos/o/r/actions/workflows` |
| Rerun CI | `gh run rerun ID` | `curl POST /repos/o/r/actions/runs/ID/rerun` |
| Set secret | `gh secret set KEY` | `curl PUT /repos/o/r/actions/secrets/KEY` (+ encryption) |
