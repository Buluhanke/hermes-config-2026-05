#!/usr/bin/env bash
# Keep the Chrome CDP profile mirror in sync with the user's live Chrome profile.
#
# Why: a fresh `cp -R` of the profile is 322M+ and re-copies unchanged files.
# `rsync --delete` is incremental and prunes cache dirs the user has trimmed
# from the source. Cache dirs already present in the mirror from a previous
# full copy are NOT touched by `--exclude` alone — they must be rm-rf'd here.
#
# Usage:
#   bash scripts/sync_profile_mirror.sh           # dry-run preview + confirm
#   bash scripts/sync_profile_mirror.sh --yes     # skip the confirmation prompt
#   bash scripts/sync_profile_mirror.sh --dry-run # show what would change, do nothing
#
# Pitfalls:
# - DRY-RUN FIRST. --delete is irreversible; an inverted src/dst wipes the
#   mirror's login state. The script always shows a preview first.
# - Do not run while the CDP Chrome is in active use against Cookies/History;
#   in practice it's safe because CDP runs in a separate process.

set -euo pipefail

SRC="$HOME/Library/Application Support/Google/Chrome"
DST="$HOME/.hermes/chrome-profile-mirror"
EXCLUDES=(
  --exclude="Cache"
  --exclude="Code Cache"
  --exclude="GPUCache"
  --exclude="ShaderCache"
  --exclude="GrShaderCache"
  --exclude="Network"
  --exclude="Storage/ext"
  --exclude="File System"
  --exclude="Crashpad"
  --exclude="Safe Browsing"
  --exclude="WebRTCLogs"
)

DRY_RUN=""
ASSUME_YES=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN="--dry-run" ;;
    --yes|-y)  ASSUME_YES=1 ;;
    *) echo "unknown flag: $arg" >&2; exit 2 ;;
  esac
done

if [ ! -d "$SRC/Default" ]; then
  echo "source profile not found: $SRC/Default" >&2
  exit 1
fi
if [ ! -d "$DST/Default" ]; then
  echo "mirror missing: $DST/Default — run the initial cp -R first" >&2
  exit 1
fi

echo "[1/3] rsync Default/ (delta, with excludes)"
if [ -n "$DRY_RUN" ]; then
  rsync -aun --delete "${EXCLUDES[@]}" "$SRC/Default/" "$DST/Default/"
  echo "(dry-run complete — no files written)"
  exit 0
fi

# Show a dry-run first; only proceed if user confirms (or --yes).
rsync -aun --delete "${EXCLUDES[@]}" "$SRC/Default/" "$DST/Default/" > /tmp/.rsync_preview.log 2>&1 || true
preview=$(cat /tmp/.rsync_preview.log)
if [ -z "$preview" ]; then
  echo "  mirror already in sync — no rsync changes"
else
  echo "$preview" | head -30
  if [ -z "$ASSUME_YES" ]; then
    read -rp "proceed with real sync? [y/N] " ans
    [[ "$ans" =~ ^[Yy]$ ]] || { echo "aborted"; exit 1; }
  fi
  rsync -a --delete "${EXCLUDES[@]}" "$SRC/Default/" "$DST/Default/"
  echo "  rsync OK"
fi

echo "[2/3] refresh Local State"
cp -f "$SRC/Local State" "$DST/Local State"

echo "[3/3] prune stale cache dirs left over from prior full copies"
for d in Cache "Code Cache" GPUCache ShaderCache GrShaderCache Network "File System" Crashpad "Safe Browsing" WebRTCLogs; do
  if [ -d "$DST/Default/$d" ]; then
    size=$(du -sh "$DST/Default/$d" 2>/dev/null | cut -f1)
    rm -rf "$DST/Default/$d"
    echo "  removed $d ($size)"
  fi
done

chmod -R u+rwX "$DST" 2>/dev/null || true

echo
echo "mirror size now: $(du -sh "$DST" | cut -f1)"
