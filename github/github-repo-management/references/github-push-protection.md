# GitHub Push Protection — Secret/Key Detection

## What Triggers It
GitHub's pre-receive hooks scan **all commits** in the push for embedded secrets:
- API keys (Groq, OpenRouter, etc.)
- Passwords, tokens, private keys
- Authentication headers (`Authorization: Bearer ...`)

Even a single old commit in a large history will block the entire push.

## Symptom
```
$ git push origin main
ERROR: denied: commit contains forbidden content
remote: error: GH001: Large files detected (or)
remote: error: pre-receive hook declined
```

Or the push appears to succeed but GitHub shows nothing new on the remote.

## Core Fix: Clean History

### Step 1 — Stash any uncommitted changes
```bash
git stash push -m "temp" -- <files>
```

### Step 2 — Nuclear reset
```bash
git reset --hard origin/main
```
This discards all local commits, making a clean break from the problematic history.

### Step 3 — Re-commit (optional — skip if no local commits needed)
```bash
git stash pop
git add -A
git commit -m "clean restart $(date '+%Y-%m-%d')"
```

### Step 4 — Push
```bash
git push origin main
```

## Why `git rm --cached` Doesn't Work
`git rm --cached <file>` only removes the file from the **current** commit. The blob still exists in `.git/objects/` from all previous commits. GitHub scans the full history — history rewrite is the only real solution.

## Case Study: 2026-05-24
- 59 local commits carried a hidden Groq API key embedded in a file
- Reset `--hard origin/main` succeeded where `git rm --cached` + re-commit failed
- Local skills were unaffected — only the public GitHub sync was blocked
- Backup strategy: `/tmp/hermes-skills-backup-20260524.zip` (77MB) preserved before reset

## Prevention
- Never commit API keys or tokens to git
- Use `.gitignore` for credentials files
- Consider `git secrets` or Gitleaks for pre-commit scanning
- For secrets needed in CI, use GitHub Actions secrets, not env vars in code