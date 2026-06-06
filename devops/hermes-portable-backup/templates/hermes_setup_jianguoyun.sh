#!/usr/bin/env bash
# hermes_setup_jianguoyun.sh — 一键配置 rclone + 坚果云 WebDAV
#
# 前提: 用户已经在坚果云网页端为 hermes 创建了 app 授权密码
# 路径: https://www.jianguoyun.com/d/account#security
#       → 安全选项 → 第三方应用管理 → 添加应用密码
#       → 名字填 hermes-backup, 得到 32 位密码(只显示一次!)

set -euo pipefail

red() { echo -e "\033[31m$*\033[0m"; }
green() { echo -e "\033[32m$*\033[0m"; }
yellow() { echo -e "\033[33m$*\033[0m"; }

echo ""
yellow "=== 坚果云 WebDAV 配置向导 ==="
echo ""
echo "1. 打开 https://www.jianguoyun.com/d/account#security"
echo "2. 找到「第三方应用管理」→「添加应用密码」"
echo "3. 名字填 hermes-backup, 确定后会得到一个 32 位密码(只显示一次!)"
echo ""

# 拿坚果云账号
read -rp "请输入你的坚果云登录账号(邮箱): " JGY_USER
echo ""
read -rp "请输入刚才生成的 32 位应用密码(不是登录密码): " JGY_PASS
echo ""

RCLONE_CONF="$HOME/.config/rclone/rclone.conf"
mkdir -p "$(dirname "$RCLONE_CONF")"

# 先看是不是已经配置过
if grep -q "^\[jianguoyun\]" "$RCLONE_CONF" 2>/dev/null; then
    yellow "检测到 [jianguoyun] 已存在, 先备份到 rclone.conf.bak"
    cp "$RCLONE_CONF" "$RCLONE_CONF.bak.$(date +%s)"
    # 删掉旧的 [jianguoyun] 段
    python3 -c "
import re
with open('$RCLONE_CONF') as f:
    content = f.read()
content = re.sub(r'\\[jianguoyun\\][^\\[]*', '', content, flags=re.DOTALL)
with open('$RCLONE_CONF', 'w') as f:
    f.write(content)
"
fi

cat >> "$RCLONE_CONF" << EOF
[jianguoyun]
type = webdav
url = https://dav.jianguoyun.com/dav/
vendor = other
user = $JGY_USER
pass = $(rclone obscure "$JGY_PASS")
EOF

chmod 600 "$RCLONE_CONF"
green "✓ rclone.conf 已更新"

# 测试连接
echo ""
yellow "测试 WebDAV 连接..."
if rclone lsd jianguoyun: 2>&1 | head -5; then
    green "✓ 连接成功!"
else
    red "✗ 连接失败, 检查账号/密码"
    exit 1
fi

# 创建备份目录
echo ""
yellow "创建备份目录 hermes-backups/..."
rclone mkdir jianguoyun:hermes-backups/ 2>&1 | tail -3
green "✓ 已创建"

# 试传一个测试文件
echo ""
yellow "测试上传..."
echo "Hermes backup test $(date)" > /tmp/hermes-rclone-test.txt
if rclone copy /tmp/hermes-rclone-test.txt jianguoyun:hermes-backups/ 2>&1 | tail -3; then
    green "✓ 上传成功"
    rclone delete jianguoyun:hermes-backups/hermes-rclone-test.txt 2>&1 | tail -1
    rm -f /tmp/hermes-rclone-test.txt
else
    red "✗ 上传失败"
    exit 1
fi

echo ""
green "✅ 坚果云配置完成!"
echo ""
echo "接下来跑第一次完整备份:"
echo "  ~/.hermes/scripts/hermes_backup.sh"
echo ""
echo "或者先 dry-run 看看会备份什么:"
echo "  ~/.hermes/scripts/hermes_backup.sh --dry-run"
