# GitHub OAuth Token vs PAT — `delete_repo` Scope Gap

## The Problem

A GitHub OAuth token (prefix `gho_`, obtained via `gh auth login` device code flow) may have `admin: true` permissions on a repository (confirmed via `gh api repos/owner/repo` returning `"admin": true`), yet still be **unable to delete the repository** via API — returning HTTP 403 with `x-oauth-scopes: gist, read:org, repo, workflow` and `x-accepted-oauth-scopes: delete_repo` absent from the response headers.

## Root Cause

GitHub OAuth apps do **not** automatically get `delete_repo` scope even with full `repo` scope. `delete_repo` is a separately granted scope that must be explicitly requested when authorizing the OAuth app.

## How to Detect

### Step 1: Identify token type by prefix
```
gho_...  → OAuth token (device code flow)
ghp_...  → Personal Access Token (PAT)
```

### Step 2: Get the token from osxkeychain (macOS)
```bash
git credential fill <<'EOF'
protocol=https
host=github.com
EOF
```
Returns: `username=Buluhanke`, `password=gho_Mt...Qp1H`

### Step 3: Check scopes via API
```bash
curl --proxy http://127.0.0.1:7897 -I \
  -H "Authorization: token $TOKEN" \
  https://api.github.com/repos/owner/repo
```

Look for these headers in the response:
- `x-oauth-scopes:` — what the token actually has (e.g., `gist, read:org, repo, workflow`)
- `x-accepted-oauth-scopes:` — what the endpoint accepts; if `delete_repo` is NOT listed here, the call will 403

### Step 4: Verify delete capability
```bash
curl --proxy http://127.0.0.1:7897 -s -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/owner/repo
```

If scopes are missing → HTTP 403.

## Solutions

### Option A: Manual deletion (fastest)
User deletes via GitHub web UI: Settings → Danger Zone → Delete this repository. No token changes needed.

### Option B: Get a PAT with `delete_repo`
Request a new PAT at https://github.com/settings/tokens with:
- Scopes: `repo` (full) + `delete_repo`
- Use it in place of the OAuth token

### Option C: Refresh OAuth token with `delete_repo` scope
```bash
gh auth refresh -h github.com -s delete_repo
```
This requires the user to complete a browser flow at github.com/login/device within the command timeout.

## Quick Reference

| Check | Command |
|-------|---------|
| Token type | Prefix `gho_` = OAuth, `ghp_` = PAT |
| Get token | `git credential fill` (macOS osxkeychain) |
| Check scopes | `curl -I -H "Authorization: token $TOKEN" https://api.github.com/repos/owner/repo` |
| Delete repo (API) | `curl -X DELETE -H "Authorization: Bearer $TOKEN" https://api.github.com/repos/owner/repo` |
| gh repo rename | `gh repo rename <new-name> --repo <owner/repo>` (positional, not `--new-name`) |
