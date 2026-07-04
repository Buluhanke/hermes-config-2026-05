#!/usr/bin/env bash
# scaffold_skill.sh — Companion-file scaffolder for hermes skills install
# Usage: scaffold_skill.sh <owner> <repo> <branch> <skill-dir-name>
# Effect: Lists the repo's blob tree, prompts to fetch each non-SKILL.md file
#         into the right subdirectory of the installed skill.
#
# This is the workaround for hermes skills install only copying SKILL.md.
# Verified 2026-07-01 against Romanescu11/hermes-skill-factory.

set -euo pipefail

OWNER="${1:?owner required (e.g. Romanescu11)}"
REPO="${2:?repo required (e.g. hermes-skill-factory)}"
BRANCH="${3:-main}"
SKILL_DIR="${4:?skill dir name required (e.g. skill-factory)}"

DEST="$HOME/.hermes/skills/$SKILL_DIR"
if [[ ! -d "$DEST" ]]; then
  echo "ERROR: $DEST not found. Run 'hermes skills install' first." >&2
  exit 1
fi

API="https://api.github.com/repos/$OWNER/$REPO/git/trees/$BRANCH?recursive=1"
echo "→ Listing $OWNER/$REPO ($BRANCH)..."
FILES=$(curl -fsSL "$API" | python3 -c "
import json, sys
tree = json.load(sys.stdin).get('tree', [])
for t in tree:
    if t['type'] == 'blob' and not t['path'].endswith('SKILL.md'):
        print(t['path'])
")

BASE="https://raw.githubusercontent.com/$OWNER/$REPO/$BRANCH"
for f in $FILES; do
  target="$DEST/$f"
  mkdir -p "$(dirname "$target")"
  if curl -fsSL "$BASE/$f" -o "$target" 2>/dev/null; then
    echo "  ✓ $f"
    # Auto-chmod scripts
    if [[ "$f" == scripts/*.py || "$f" == scripts/*.sh ]]; then
      chmod +x "$target"
    fi
  else
    echo "  ✗ $f (failed, skipping)"
    rm -f "$target"
  fi
done

echo ""
echo "→ Validating Python scripts..."
for py in "$DEST"/scripts/*.py; do
  [[ -f "$py" ]] || continue
  if python3 -m py_compile "$py" 2>/dev/null; then
    echo "  ✓ $(basename "$py")"
  else
    echo "  ✗ $(basename "$py") (syntax error)"
  fi
done

echo ""
echo "Done. Files in $DEST:"
find "$DEST" -type f | sort
