#!/bin/bash
# Hermes 一键恢复脚本
# 用法: bash restore.sh
# 从 GitHub 私有仓库 hermes-backup 恢复核心配置

set -e

HERMES_DIR="$HOME/.hermes"
BACKUP_REPO="https://github.com/Buluhanke/hermes-backup.git"

echo "=== Hermes 一键恢复 ==="

# 1. 克隆备份仓库
if [ ! -d "$HERMES_DIR/.git" ]; then
    echo "[1/4] 克隆备份仓库..."
    git clone "$BACKUP_REPO" "$HERMES_DIR"
else
    echo "[1/4] 配置已存在，跳过"
fi

# 2. 恢复敏感文件
echo "[2/4] 恢复敏感文件..."
[ -f "$HERMES_DIR/.env" ] && echo "    .env 已存在"
[ -f "$HERMES_DIR/auth.json" ] && echo "    auth.json 已存在"

# 3. 恢复 Chrome 登录态（1688 Cookie）
echo "[3/4] 恢复 Chrome 登录态..."
if [ -d "$HERMES_DIR/chrome-default" ]; then
    mkdir -p "$HERMES_DIR/hermes-agent/chrome-debug"
    cp -r "$HERMES_DIR/chrome-default/" "$HERMES_DIR/hermes-agent/chrome-debug/Default/"
    echo "    1688 Cookie 恢复完成"
else
    echo "    未找到 Chrome 备份，需重新登录1688"
fi

# 4. 克隆技能库
if [ ! -d "$HERMES_DIR/skills/.git" ]; then
    echo "[4/4] 克隆技能库..."
    git clone https://github.com/Buluhanke/hermes-skills.git "$HERMES_DIR/skills"
else
    echo "[4/4] 技能库已存在，跳过"
fi

echo ""
echo "=== 恢复完成 ==="
echo ""
echo "下一步："
echo "1. 检查配置：hermes config show"
echo "2. 启动服务：hermes gateway"
echo "3. 1688 Cookie 恢复后重启 Chrome 调试实例"
