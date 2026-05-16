#!/bin/bash
# Hermes 备份脚本
# 用法: bash backup.sh

set -e

HERMES_DIR="$HOME/.hermes"
BACKUP_DIR="$HOME/hermes-backup"

echo "=== Hermes 备份 ==="

mkdir -p "$BACKUP_DIR"

echo "[1/4] 备份 .env..."
[ -f "$HERMES_DIR/.env" ] && cp "$HERMES_DIR/.env" "$BACKUP_DIR/.env" || echo "    .env 不存在，跳过"

echo "[2/4] 备份 auth.json..."
[ -f "$HERMES_DIR/auth.json" ] && cp "$HERMES_DIR/auth.json" "$BACKUP_DIR/auth.json" || echo "    auth.json 不存在，跳过"

echo "[3/4] 备份 Chrome 登录态（1688 Cookie）..."
if [ -d "$HERMES_DIR/hermes-agent/chrome-debug/Default" ]; then
    rm -rf "$BACKUP_DIR/chrome-default"
    cp -r "$HERMES_DIR/hermes-agent/chrome-debug/Default" "$BACKUP_DIR/chrome-default"
else
    echo "    Chrome 调试目录不存在，跳过"
fi

echo "[4/4] 备份完成"
du -sh "$BACKUP_DIR"

echo ""
echo "提示：把 $BACKUP_DIR 目录同步到 GitHub 私有仓库："
echo "  cd ~/hermes-backup && git add -A && git commit -m 'backup' && git push"
