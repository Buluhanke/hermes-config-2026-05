#!/usr/bin/env bash
# hermes_restore.sh — 从加密分卷还原 Hermes 状态
#
# 场景: 你已经
#   1. 在新电脑装了 macOS + brew + python3.11
#   2. 用 rclone / 网页从云盘(坚果云等)下载了 hermes-backups/ 目录
#   3. 知道 GPG 密码(从老 Mac 的 Keychain 导出, 或原始来源)
#
# 这个脚本会:
#   - 拼回所有 .part 文件
#   - GPG 解密(问密码)
#   - 解压到 ~/.hermes
#   - 修权限
#   - 跑完整性检查
#
# 用法:
#   hermes_restore.sh /path/to/hermes-YYYYMMDD-HHMMSS.tar.gz.gpg.part000
#   hermes_restore.sh --latest /path/to/dir/  # 自动找最新的备份

set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
STAGING="/tmp/hermes-restore-$$"

red() { echo -e "\033[31m$*\033[0m"; }
green() { echo -e "\033[32m$*\033[0m"; }
yellow() { echo -e "\033[33m$*\033[0m"; }
bold() { echo -e "\033[1m$*\033[0m"; }

usage() {
    cat <<EOF
用法: $0 <hermes-YYYYMMDD-HHMMSS.tar.gz.gpg.part000>

例:
  $0 /tmp/hermes-backup/hermes-20260606-133000.tar.gz.gpg.part000

或者直接给一个目录, 自动找最新的备份:
  $0 --latest /tmp/hermes-backup/
EOF
}

find_latest() {
    local dir="$1"
    ls -1 "$dir"/hermes-*.tar.gz.gpg.part000 2>/dev/null | sort -r | head -1
}

main() {
    local part_file=""
    if [ "${1:-}" = "--latest" ]; then
        [ -z "${2:-}" ] && { red "需要目录"; usage; exit 1; }
        part_file=$(find_latest "$2")
        [ -z "$part_file" ] && { red "$2 没找到任何分卷"; exit 1; }
    else
        part_file="${1:-}"
        [ -z "$part_file" ] && { usage; exit 1; }
        [ ! -f "$part_file" ] && { red "找不到: $part_file"; exit 1; }
    fi

    bold "=== Hermes 还原器 ==="
    echo "备份源: $part_file"
    echo "目标:   $HERMES_HOME"
    echo ""

    local ts=$(basename "$part_file" | sed -E 's/hermes-([0-9]+-[0-9]+)\..*/\1/')
    local base_dir=$(dirname "$part_file")
    local merged="$STAGING/hermes-${ts}.tar.gz.gpg"
    local parts=$(ls "$base_dir"/hermes-${ts}.tar.gz.gpg.part* 2>/dev/null | sort)

    if [ -z "$parts" ]; then
        red "没找到配套分卷: ${base_dir}/hermes-${ts}.tar.gz.gpg.part*"
        exit 1
    fi

    yellow "分卷清单(共 $(echo "$parts" | wc -l | tr -d ' ') 个):"
    echo "$parts" | sed 's/^/  /'
    echo ""

    read -rp "确认拼接并解密? (yes/no): " confirm
    [ "$confirm" = "yes" ] || { yellow "已取消"; exit 0; }

    mkdir -p "$STAGING"
    echo "拼接分卷..."
    cat $parts > "$merged"
    local enc_size=$(du -h "$merged" | awk '{print $1}')
    green "✓ 拼好 ($enc_size)"

    # 2. GPG 解密
    echo ""
    yellow "现在需要 GPG 密码(就是你当初跑 --keychain-set 时设的密码)"
    local decrypted="$STAGING/hermes-${ts}.tar.gz"

    # 提示拿密码
    local pw
    read -rs -p 'GPG 密码: ' pw
    echo ""
    # 解密 - 错误走 stderr, 只把 stdout(解密数据)写文件
    if ! gpg --batch --pinentry-mode loopback --passphrase "$pw" \
        --decrypt "$merged" > "$decrypted" 2> "$STAGING/gpg-error.log"; then
        red "GPG 解密失败, 看下错误:"
        cat "$STAGING/gpg-error.log" | head -5
        exit 1
    fi

    [ -s "$decrypted" ] || { red "解密失败: 文件为空, 密码错了?"; exit 1; }
    green "✓ 解密完成 ($(du -h "$decrypted" | awk '{print $1}'))"

    # 3. 完整性检查
    echo ""
    yellow "检查包内容..."
    tar -tzf "$decrypted" 2>&1 | head -10 | sed 's/^/  /'
    local total_files=$(tar -tzf "$decrypted" 2>/dev/null | wc -l | tr -d ' ')
    green "✓ 包内共 $total_files 个文件/目录"

    # 关键文件检查(包内路径是 .hermes/...)
    for f in ".hermes/config.yaml" ".hermes/state.db" ".hermes/.env" ".hermes/skills"; do
        tar -tzf "$decrypted" "$f" >/dev/null 2>&1 \
            && green "  ✓ $f" \
            || yellow "  ⚠ $f 缺失"
    done

    # 4. 二次确认再覆盖
    if [ -d "$HERMES_HOME" ] && [ -z "${FORCE_RESTORE:-}" ]; then
        yellow ""
        yellow "⚠ 目标 $HERMES_HOME 已存在!"
        yellow "  本脚本会把包内 .hermes/* 合并进去(覆盖同名文件)"
        yellow "  强烈建议先: mv $HERMES_HOME ${HERMES_HOME}.old.\$(date +%s)"
        echo ""
        read -rp "继续? (yes/no): " confirm
        [ "$confirm" = "yes" ] || { yellow "已取消"; exit 0; }
    fi

    # 5. 实际解压
    echo ""
    yellow "解压到 $HERMES_HOME ..."
    mkdir -p "$HERMES_HOME"
    # 包内路径是 .hermes/..., --strip-components=1 把 .hermes 这一层去掉
    tar --strip-components=1 -xzf "$decrypted" -C "$HERMES_HOME" 2>&1 | tail -3
    green "✓ 解压完成"

    # 6. 修复权限
    echo ""
    yellow "修复权限..."
    chmod 700 "$HERMES_HOME"
    chmod 600 "$HERMES_HOME/.env" 2>/dev/null || true
    chmod 600 "$HERMES_HOME/cron/jobs.json" 2>/dev/null || true
    find "$HERMES_HOME" -type d -name "private" -exec chmod 700 {} \; 2>/dev/null || true
    green "✓ 权限修复完成"

    # 7. 健康检查
    echo ""
    bold "=== 还原后健康检查 ==="
    echo "  config.yaml: $([ -f "$HERMES_HOME/config.yaml" ] && echo '✓ 存在' || echo '✗ 缺失')"
    echo "  state.db:    $([ -f "$HERMES_HOME/state.db" ] && du -h "$HERMES_HOME/state.db" | awk '{print "✓ 存在 ("$1")"}' || echo '✗ 缺失')"
    echo "  .env:        $([ -f "$HERMES_HOME/.env" ] && echo '✓ 存在' || echo '✗ 缺失')"
    echo "  skills/:     $([ -d "$HERMES_HOME/skills" ] && ls "$HERMES_HOME/skills" | wc -l | awk '{print "✓ "$1" 个技能"}' || echo '✗ 缺失')"
    echo "  memory:      $([ -f "$HERMES_HOME/memory_store.db" ] && echo '✓ 存在' || echo '✗ 缺失')"

    # SQLite 完整性
    if [ -f "$HERMES_HOME/state.db" ]; then
        local integrity=$(python3 -c "
import sqlite3
c = sqlite3.connect('$HERMES_HOME/state.db')
cur = c.execute('PRAGMA integrity_check')
print(cur.fetchone()[0])
" 2>&1)
        echo "  state.db integrity: $integrity"
    fi

    # 8. 收尾
    rm -rf "$STAGING"
    echo ""
    green "✅ 还原完成!"
    echo ""
    echo "下一步:"
    echo "  1. cd ~/.hermes/hermes-agent && python3.11 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    echo "  2. cd ~/.hermes/hermes-agent/ui-tui && npm install"
    echo "  3. hermes config validate"
    echo "  4. hermes --version"
    echo ""
    yellow "⚠ 强烈建议: 重新跑 ./hermes_backup.sh --keychain-set 把 GPG 密码存到这台新电脑的 Keychain"
}

main "$@"
