#!/usr/bin/env bash
# hermes_backup_simple.sh — 极简版备份:生成单个加密 .gpg 文件,自己拖到云盘
#
# 用途: 当主方案(rclone + WebDAV + 100M 分卷)对用户来说太重时,用这个
# 优势: 零依赖(GPG 系统自带),每周手动 2 分钟,适合任何云盘
# 劣势: 不能自动,得自己点上传
#
# 触发场景: 用户说"能直接打个压缩包上传吗" / "不想折腾 rclone" / "给我最简单的方案"
#
# 用法:
#   ./hermes_backup_simple.sh                      # 用 Keychain 密码
#   ./hermes_backup_simple.sh --set-password       # 首次:设密码到 Keychain
#   ./hermes_backup_simple.sh --no-encrypt        # 不加密(只信任的网盘才用)
#   ./hermes_backup_simple.sh --output ~/Desktop/  # 输出到指定目录
#   ./hermes_backup_simple.sh --dry-run           # 看会备份什么

set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
OUTPUT_DIR="${HERMES_HOME_OUTPUT:-$HOME/Desktop}"  # 默认输出到桌面
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
FINAL_NAME="hermes-backup-${TIMESTAMP}.gpg"
KEYCHAIN_SERVICE="com.hermes.backup.simple"
KEYCHAIN_ACCOUNT="hermes-simple"

red() { echo -e "\033[31m$*\033[0m"; }
green() { echo -e "\033[32m$*\033[0m"; }
yellow() { echo -e "\033[33m$*\033[0m"; }
bold() { echo -e "\033[1m$*\033[0m"; }

usage() {
    cat <<EOF
极简版 Hermes 备份
==================

用法:
  $0                          # 备份 + 加密,输出到桌面
  $0 --set-password           # 首次:设/改 GPG 密码
  $0 --no-encrypt             # 不加密(不推荐,除非你信得过网盘)
  $0 --output /path/to/dir/   # 输出到指定目录
  $0 --dry-run                # 看会备份什么

特点:
  - 零依赖(GPG 系统自带)
  - 每周手动跑一次,2 分钟搞定
  - 输出单个 .gpg 文件,直接拖到阿里云盘/百度网盘/任何网盘

首次使用:
  1. $0 --set-password    设密码(把密码记在 1Password 或纸上)
  2. $0                   跑一次测试
  3. 把输出文件拖到网盘
EOF
}

# ============ 工具函数 ============
set_password() {
    yellow "设置 GPG 密码(把你刚加密备份的密码存到 Keychain)"
    yellow "⚠️ 这个密码必须记住!丢了就永远解不开备份!"
    echo ""
    local pw1 pw2
    read -rs -p "新密码(8 位以上): " pw1
    echo ""
    read -rs -p "再输一次确认: " pw2
    echo ""
    if [ "$pw1" != "$pw2" ]; then
        red "两次密码不一致"
        exit 1
    fi
    if [ ${#pw1} -lt 8 ]; then
        red "密码太短,至少 8 位"
        exit 1
    fi
    security delete-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" 2>/dev/null || true
    security add-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" -w "$pw1" -U
    green "✓ 密码已存到 Keychain"
    echo ""
    yellow "⚠️ 重要:把这个密码记到 1Password 或纸上!"
    yellow "    Keychain 损坏/重装系统会导致密码丢失!"
}

# ============ 排除项(跟主方案一致) ============
EXCLUDES=(
    ".hermes/hermes-agent"
    ".hermes/lsp"
    ".hermes/bin"
    ".hermes/cache"
    ".hermes/.cache"
    ".hermes/screenshots"
    ".hermes/mcp-chrome-extension"
    ".hermes/.backups"
    ".hermes/logs"
    ".hermes/models_dev_cache.json"
    ".hermes/.git"
    ".hermes/skills/.git"
    ".hermes/skills/.hub"
    ".hermes/skills/.curator_backups"
    ".hermes/profiles/default/.git"
    ".hermes/.state"
    ".hermes/.update_check"
)

TAR_EXCLUDES=()
for x in "${EXCLUDES[@]}"; do
    TAR_EXCLUDES+=("--exclude=$x")
done

# ============ 1. 打包 ============
pack() {
    local out="$OUTPUT_DIR/hermes-tmp-${TIMESTAMP}.tar.gz"
    yellow "打包核心数据..." >&2
    cd "$HERMES_HOME/.."
    tar "${TAR_EXCLUDES[@]}" -czf "$out" .hermes 2>&1 | tail -3 >&2
    local size=$(du -h "$out" | awk '{print $1}')
    green "✓ 打包完成: $size" >&2
    echo "$out"
}

# ============ 2. 加密 ============
encrypt() {
    local tarball="$1"
    local pw="$2"
    local out="$OUTPUT_DIR/$FINAL_NAME"
    yellow "GPG 加密(AES-256)..." >&2
    gpg --batch --yes --pinentry-mode loopback --passphrase "$pw" \
        --cipher-algo AES256 --compress-algo none \
        --symmetric --output "$out" \
        "$tarball" 2>&1 | tail -3 >&2
    local size=$(du -h "$out" | awk '{print $1}')
    green "✓ 加密完成: $size" >&2
    echo "$out"
}

# ============ 主流程 ============
main() {
    local do_encrypt=true
    local do_pack=true

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --set-password) set_password; exit 0;;
            --no-encrypt) do_encrypt=false; shift;;
            --output) OUTPUT_DIR="$2"; shift 2;;
            --dry-run) do_pack=false; do_encrypt=false; shift;;
            -h|--help) usage; exit 0;;
            *) red "未知参数: $1"; usage; exit 1;;
        esac
    done

    mkdir -p "$OUTPUT_DIR"

    # 拿密码(优先新 keychain, 兼容老的)
    local pw=""
    if $do_encrypt; then
        pw=$(security find-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" -w 2>/dev/null) || \
        pw=$(security find-generic-password -s "com.hermes.backup.gpg" -a "hermes-archive" -w 2>/dev/null) || {
            red "Keychain 没找到密码,先跑一次 --set-password"
            echo ""
            echo "(或把之前 --keychain-set 设的密码复制过来)"
            usage
            exit 1
        }
    fi

    if ! $do_pack; then
        # dry-run
        cd "$HERMES_HOME/.."
        echo "排除项:"
        for e in "${EXCLUDES[@]}"; do echo "  $e"; done
        echo ""
        local total_files=$(tar "${TAR_EXCLUDES[@]}" -cf - .hermes 2>/dev/null | tar -tf - | wc -l | tr -d ' ')
        echo "预估打包: $total_files 个文件"
        echo "输出: $OUTPUT_DIR/$FINAL_NAME"
        return
    fi

    bold "=== Hermes 极简备份 ==="
    echo ""

    # SQLite WAL checkpoint (失败也别死,state.db 本身没坏)
    yellow "SQLite WAL checkpoint..."
    python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$HERMES_HOME/state.db')
    conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
except Exception as e:
    print(f'  state.db checkpoint 警告: {e}')
try:
    conn = sqlite3.connect('$HERMES_HOME/memory_store.db')
    conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
except Exception as e:
    print(f'  memory_store.db checkpoint 警告: {e}')
" 2>&1 | tail -3 || true

    # 打包
    local tarball=$(pack)

    # 加密
    if $do_encrypt; then
        local final=$(encrypt "$tarball" "$pw")
    else
        mv "$tarball" "$OUTPUT_DIR/hermes-backup-${TIMESTAMP}.tar.gz"
        local final="$OUTPUT_DIR/hermes-backup-${TIMESTAMP}.tar.gz"
        yellow "⚠ 警告:未加密! 仅在可信网盘使用!"
    fi

    # 清理临时文件
    rm -f "$tarball"

    echo ""
    bold "✅ 备份完成!"
    echo ""
    echo "文件: $final"
    echo "大小: $(du -h "$final" | awk '{print $1}')"
    echo ""
    echo "下一步:"
    echo "  1. 打开云盘(阿里云盘/百度网盘/iCloud/OneDrive/任何)"
    echo "  2. 拖这个 .gpg 文件到备份目录"
    echo "  3. 等上传完(约 30 秒,看网速)"
    echo ""
    if $do_encrypt; then
        echo "换电脑还原时:"
        echo "  1. 从云盘下载 .gpg 文件"
        echo "  2. 跑: gpg -d hermes-backup-XXX.gpg > hermes.tar.gz"
        echo "  3. 跑: tar --strip-components=1 -xzf hermes.tar.gz -C ~/.hermes"
    fi
}

main "$@"
