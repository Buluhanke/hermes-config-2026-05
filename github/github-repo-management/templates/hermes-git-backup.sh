#!/bin/bash
# Auto-backup script for Hermes config cron job
# Place in ~/.hermes/scripts/ and reference via Hermes cron
# Usage: /cron create name=my-backup schedule=every 1h script=hermes-git-backup.sh no_agent=true

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
