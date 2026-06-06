# Marketing vs Code: Case Studies

When a repo's README claims more than the codebase delivers, here are real examples to watch for.

## Case: ECC (Everything Claude Code) — June 2026

**Repo**: `github.com/affaan-m/ECC`
**Claimed**: 63 professional sub-agents, 1282 security test cases, Agent Harness OS
**Actual**:
- Stars: 182K+ (high, but "single maintainer ships weekly" + large star count is a red flag for hype-driven projects)
- Files: 2,914 total in tree
- "63 sub-agents": 0 executables, 33 SKILL.md files (prompt templates, not agents)
- "1282 security tests": 157 test files + 181 scripts, but **20 files have missing blobs** (tree references exist, blob data doesn't)
- Actual function: AI coding assistant config pack + skill templates for 14 different harnesses
- Architecture: 14 harness dirs (`.agents`, `.codex`, `.cursor`, `.zed`, `.opencode`, `.qwen`, `.gemini`, `.kiro`, `.trae`, `.codebuddy`, `.vscode`, etc.) each with `.md` / `.yaml` config files

**Quick check commands that revealed the truth**:
```bash
# Count actual files (not marketing)
git ls-tree -r HEAD | wc -l              # 2914 total files
git ls-tree -r HEAD --name-only | grep "SKILL.md" | wc -l  # 792 SKILL.md files across all harnesses
git ls-tree -r HEAD --name-only | grep "agents/openai.yaml" | wc -l  # 33 agent configs (not 63)

# Check for actual executables (not prompt templates)
git ls-tree -r HEAD | awk '{print $4}' | grep -v '\.md$\|\.yaml$\|\.json$\|\.txt$\|\.sh$' | head -20

# Find missing blobs
git rev-list --objects --all | git cat-file --batch-check | grep missing

# Check tests directory
git ls-tree -r HEAD tests/ | wc -l        # real test count
```

**Pattern**: Large star count + "Agent OS" branding + config-pack reality. The product is real (quality config templates) but marketed as an "operating system" rather than a "configuration collection pack."

## General Red-Flag Matrix

| Marketing Claim | What to Verify | Quick Command |
|----------------|----------------|---------------|
| "X Agents" | Are they executables or config files? | `git ls-tree -r HEAD | grep -c "\.py$\|\.js$\|\.go$\|\.rs$"` |
| "Y Tests" | Are blobs present? Any missing? | `git cat-file --batch-check \| grep missing` |
| "Cross-platform" | Real OS detection or just a list? | `find . -name "*.sh" \| xargs grep -l "platform\|sys.platform\|OS" | head -5` |
| "Production-ready" | CI passing? Recent commits? | GitHub Actions tab + `git log --oneline -5` |
| "Multi-agent system" | Separate processes or just prompt files? | `git ls-tree -r HEAD --name-only \| grep -E "\.(py|js|go|rs)$" \| head -20` |
