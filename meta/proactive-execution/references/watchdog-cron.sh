#!/bin/bash
TASKS_DIR="$HOME/.hermes/tasks"
NOW=$(date +%s)
STALE_MIN=30
STALE_SEC=$((STALE_MIN * 60))
STALE_TS=$((NOW - STALE_SEC))

for file in "$TASKS_DIR"/*.md; do
    [ -e "$file" ] || continue
    # Skip done/ and archive/
    if [[ "$file" == */done/* ]] || [[ "$file" == */archive/* ]]; then
        continue
    fi
    # Skip if not a regular file
    [ -f "$file" ] || continue
    # Get modification time
    MTIME=$(stat -f%m "$file" 2>/dev/null || stat -c%Y "$file")
    if [ "$MTIME" -lt "$STALE_TS" ]; then
        # Check if gateway is running
        if pgrep -f "hermes_cli.main gateway" >/dev/null; then
            # Send Telegram alert via webhook
            curl -s -X POST http://127.0.0.1:9888/webhook/telegram \
                -d "chat_id=$(cat $HOME/.hermes/telegram_chat_id 2>/dev/null || echo 'unknown')" \
                -d "text=任务 $(basename "$file") 停滞超过 30 分钟，是否需要干预？"
        fi
    fi
done

# Archive completed tasks
for file in "$TASKS_DIR"/*.md; do
    [ -e "$file" ] || continue
    if grep -q "^状态：完成" "$file"; then
        mkdir -p "$TASKS_DIR/done"
        mv "$file" "$TASKS_DIR/done/"
    fi
done