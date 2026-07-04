#!/usr/bin/env bash
# install_from_clone.sh — Path C: raw git clone → spec-compliant Hermes install
#
# Automates what was a 5+ step manual sequence:
#   1. git clone --depth=1 <repo-url> /tmp/<repo>
#   2. Find SKILL.md inside the clone (handles monorepos where SKILL.md is nested)
#   3. Read the `name:` field from YAML frontmatter
#   4. Copy to ~/.hermes/skills/_community/<name>/ (or other scope)
#   5. Rename destination directory to match frontmatter name (spec compliance)
#   6. Verify with `hermes skills list`
#
# Usage:
#   install_from_clone.sh <repo-url> [destination-suffix]
#
# Examples:
#   install_from_clone.sh https://github.com/thorwhalen/skill
#   install_from_clone.sh https://github.com/owner/repo --scope=official
#
# Verified 2026-07-02 against thorwhalen/skill (1.1MB, MIT, skills/skill-manage/SKILL.md)

set -euo pipefail

REPO_URL="${1:-}"
DEST_SUFFIX="${2:-}"

if [ -z "$REPO_URL" ]; then
    echo "Usage: $0 <repo-url> [destination-suffix]"
    echo "Example: $0 https://github.com/thorwhalen/skill"
    exit 1
fi

SCOPE="_community"
if [[ "$DEST_SUFFIX" == *"--scope="* ]]; then
    SCOPE="${DEST_SUFFIX#*=}"
    DEST_SUFFIX=""
fi

# Derive repo name from URL
REPO_NAME=$(basename "$REPO_URL" .git)
CLONE_DIR="/tmp/hermes-skill-clone-$$"

echo "==> Cloning $REPO_URL (depth=1) to $CLONE_DIR"
git clone --depth=1 "$REPO_URL" "$CLONE_DIR" 2>&1 | tail -3

# Find SKILL.md (may be at root or nested in skills/<name>/)
SKILL_MD=$(find "$CLONE_DIR" -name "SKILL.md" -not -path "*/node_modules/*" -not -path "*/.git/*" | head -1)

if [ -z "$SKILL_MD" ]; then
    echo "ERROR: No SKILL.md found in $REPO_URL" >&2
    rm -rf "$CLONE_DIR"
    exit 1
fi

echo "==> Found SKILL.md at: ${SKILL_MD#$CLONE_DIR/}"

# Extract name: from YAML frontmatter (first line starting with `name:` after the ---)
SKILL_NAME=$(awk '/^---$/{f++; next} f==1 && /^name:/{print $2; exit}' "$SKILL_MD")

if [ -z "$SKILL_NAME" ]; then
    echo "ERROR: SKILL.md has no 'name:' field in frontmatter" >&2
    rm -rf "$CLONE_DIR"
    exit 1
fi

echo "==> Frontmatter name: $SKILL_NAME"

# Compose destination
DEST_DIR="$HOME/.hermes/skills/$SCOPE/$SKILL_NAME"

# Safety check
if [ -d "$DEST_DIR" ]; then
    echo "WARNING: $DEST_DIR already exists. Use --force to overwrite (not yet implemented)." >&2
    rm -rf "$CLONE_DIR"
    exit 1
fi

mkdir -p "$DEST_DIR"

# Copy the SKILL.md (and any sibling files in the same directory — handles scripts/ etc.)
SKILL_DIR_REL=$(dirname "${SKILL_MD#$CLONE_DIR/}")
if [ "$SKILL_DIR_REL" = "." ]; then
    # SKILL.md at repo root
    cp "$SKILL_MD" "$DEST_DIR/SKILL.md"
    # Copy common sibling dirs if present
    for sub in scripts references templates assets; do
        if [ -d "$CLONE_DIR/$sub" ]; then
            cp -r "$CLONE_DIR/$sub" "$DEST_DIR/"
        fi
    done
else
    # SKILL.md nested — copy the parent directory's contents
    cp -r "$CLONE_DIR/$SKILL_DIR_REL/." "$DEST_DIR/"
fi

echo "==> Installed to: $DEST_DIR"

# Cleanup
rm -rf "$CLONE_DIR"

# Verify spec compliance
DIR_NAME=$(basename "$DEST_DIR")
if [ "$DIR_NAME" != "$SKILL_NAME" ]; then
    echo "WARNING: Directory name ($DIR_NAME) != frontmatter name ($SKILL_NAME)" >&2
    echo "Renaming for spec compliance..."
    mv "$DEST_DIR" "$(dirname "$DEST_DIR")/$SKILL_NAME"
    DEST_DIR="$(dirname "$DEST_DIR")/$SKILL_NAME"
fi

# Verify with hermes
echo "==> Verifying via hermes skills list..."
if hermes skills list 2>&1 | grep -q "$SKILL_NAME"; then
    echo "OK: $SKILL_NAME is visible to Hermes"
else
    echo "WARNING: $SKILL_NAME not visible to Hermes. Check SKILL.md frontmatter and run:" >&2
    echo "    hermes skills list" >&2
fi

echo ""
echo "Done. Skill installed at: $DEST_DIR"