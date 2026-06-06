#!/usr/bin/env bash
# hermes_backup.sh — Hermes 完整状态加密备份到云端
#
# 设计原则:
#   1. 只备份"换电脑就没了"的数据 (state.db / skills / config / memory / cron / scripts / plugins / .env)
#   2. 不同步 hermes-agent/ (git 仓库, 换电脑 git clone 即可)
#   3. GPG 对称加密 (AES-256), 密码存 macOS Keychain, 不写脚本
#   4. 100M 分卷 (坚果云 WebDAV 单文件 500M 限制, 留 5x 余量)
#   5. rclone 增量上传, 本地只保留 1 份
#   6. 远端保留 7 份历史
#   7. SQLite 备份前做 WAL checkpoint (避免 .db + .db-wal 拆分丢数据)
#   8. macOS BSD tar 限制: 不支持 --transform, 不用通配 exclude
#   9. set -euo pipefail + 日志全 >&2 + 函数返回值只 echo (详见 references/set-e-pipefail-pitfalls.md)
#
# 触发:
#   ~/.hermes/scripts/hermes_backup.sh                  # 默认(增量, 保留 7 份)
#   ~/.hermes/scripts/hermes_backup.sh --full           # 完整(同默认, 标记)
#   ~/.hermes/scripts/hermes_backup.sh --no-upload      # 只生成加密包, 不上传
#   ~/.hermes/scripts/hermes_backup.sh --dry-run        # 列出将被打包的文件
#   ~/.hermes/scripts/hermes_backup.sh --keychain-set   # 首次: 把 GPG 密码写入 Keychain

set -euo pipefail
shopt -s inherit_errexit 2>/dev/null || true
trap 'log "ERROR at line $LINENO: $BASH_COMMAND"' ERR

# ============ 配置 ============
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
BACKUP_DIR="$HERMES_HOME/.backups"
STAGING_DIR="$BACKUP_DIR/staging"
LOG_FILE="$BACKUP_DIR/backup.log"
KEEP_COUNT=7
CHUNK_SIZE="100M"
RCLONE_REMOTE="${RCLONE_REMOTE:-jianguoyun}"
RCLONE_DEST="${RCLONE_DEST:-hermes-backups}"
KEYCHAIN_SERVICE="com.hermes.backup.gpg"
KEYCHAIN_ACCOUNT="hermes-archive"

# 排除项 — 纯目录名 (BSD tar 不支持通配, 见 references/macos-bsd-tar-pitfalls.md)
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
    ".hermes/.git"
    ".hermes/skills/.git"
    ".hermes/skills/.hub"
    ".hermes/skills/.curator_backups"
    ".hermes/profiles/default/.git"
    ".hermes/.state"
    ".hermes/.update_check"
    ".hermes/models_dev_cache.json"
)

# 转成 tar 参数
TAR_EXCLUDES=()
for x in "${EXCLUDES[@]}"; do
    TAR_EXCLUDES+=("--exclude=$x")
done

# ============ 工具函数 ============
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2; }
die() { log "ERROR: $*"; exit 1; }

usage() {
    cat <<EOF
用法: $0 [选项]
  --keychain-set    首次:把 GPG 密码写入 macOS Keychain(交互输入)
  --no-upload       只生成加密包, 不上传(调试用)
  --dry-run         列出将被打包的文件, 不执行
  --key PASSWORD    使用指定密码(覆盖 Keychain)
  -h, --help        帮助

默认行为: 备份 + 加密 + 分卷 + 上传 ${RCLONE_REMOTE}:${RCLONE_DEST}/ + 清理旧备份
EOF
}

# ============ Keychain 管理 ============
gpg_password_get() {
    security find-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" -w 2>/dev/null
}

gpg_password_set() {
    local pw="$1"
    security delete-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" 2>/dev/null || true
    security add-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" -w "$pw" -U
}

# ============ 1. SQLite 安全检查点 ============
sqlite_checkpoint() {
    log "SQLite WAL checkpoint..."
    python3 << EOF
import sqlite3
for db in ['$HERMES_HOME/state.db', '$HERMES_HOME/memory_store.db']:
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        print(f'  {db}: {cur.fetchone()}')
    except Exception as e:
        print(f'  {db}: WARN {e}')
EOF
}

# ============ 2. 打包 ============
pack() {
    local ts="$1"
    local out="$STAGING_DIR/hermes-${ts}.tar.gz"

    log "打包核心数据到 $out ..." >&2
    cd "$HERMES_HOME/.."

    # macOS BSD tar 不支持 --transform, 路径保留为 .hermes/...
    # 还原时用 --strip-components=1 跳过 .hermes 这一层
    tar "${TAR_EXCLUDES[@]}" \
        -czf "$out" \
        .hermes 2>&1 | tail -5 | tee -a "$LOG_FILE" >&2

    local size=$(du -h "$out" | awk '{print $1}')
    log "打包完成: $size" >&2
    echo "$out"
}

# ============ 3. GPG 加密 + 分卷 ============
encrypt_chunk() {
    local tarball="$1"
    local ts="$2"
    local pw="$3"
    local out_dir="$STAGING_DIR/encrypted"
    mkdir -p "$out_dir"

    log "GPG 加密(AES-256)..." >&2
    gpg --batch --yes --pinentry-mode loopback --passphrase "$pw" \
        --cipher-algo AES256 --compress-algo none \
        --symmetric --output "$out_dir/hermes-${ts}.tar.gz.gpg" \
        "$tarball" 2>&1 | tail -3 | tee -a "$LOG_FILE" >&2

    local enc="$out_dir/hermes-${ts}.tar.gz.gpg"
    local encsize=$(du -h "$enc" | awk '{print $1}')
    log "加密完成: $encsize" >&2

    log "分卷(${CHUNK_SIZE}/卷)..." >&2
    cd "$out_dir"
    split -b "$CHUNK_SIZE" -d -a 3 "hermes-${ts}.tar.gz.gpg" "hermes-${ts}.tar.gz.gpg.part"
    rm "$enc"
    ls -lah "hermes-${ts}.tar.gz.gpg.part"* | tee -a "$LOG_FILE" >&2
    echo "$out_dir"
}

# ============ 4. 上传 ============
upload() {
    local chunk_dir="$1"
    log "上传到 ${RCLONE_REMOTE}:${RCLONE_DEST}/ ..."
    rclone copy "$chunk_dir" "${RCLONE_REMOTE}:${RCLONE_DEST}/" \
        --transfers 2 --checkers 4 --progress \
        --log-file "$LOG_FILE" --log-level INFO 2>&1 | tail -5
    log "上传完成"
}

# ============ 5. 清理 ============
cleanup_local() {
    log "本地清理(只保留最新 1 份分卷)..."
    cd "$STAGING_DIR/encrypted"
    ls -1t hermes-*.tar.gz.gpg.part* 2>/dev/null | tail -n +$((KEEP_COUNT * 3 + 1)) | xargs -I {} rm -f {} || true
    rm -f "$STAGING_DIR"/hermes-*.tar.gz "$STAGING_DIR"/hermes-*.manifest
    log "本地清理完成"
}

cleanup_remote() {
    log "远端清理(只保留 ${KEEP_COUNT} 个最新时间戳)..."
    rclone lsf "${RCLONE_REMOTE}:${RCLONE_DEST}/" --files-only 2>/dev/null | \
        grep -oE 'hermes-[0-9]{8}-[0-9]{6}' | sort -u > /tmp/hermes-remote-ts.txt
    local total=$(wc -l < /tmp/hermes-remote-ts.txt | tr -d ' ')
    if [ "$total" -le "$KEEP_COUNT" ]; then
        log "  远端有 $total 份, 无需清理"
        return
    fi
    local to_delete=$(($total - KEEP_COUNT))
    log "  远端有 $total 份, 删 $to_delete 份旧备份"
    head -n "$to_delete" /tmp/hermes-remote-ts.txt | while read ts; do
        rclone delete "${RCLONE_REMOTE}:${RCLONE_DEST}/" \
            --include "${ts}.*" --log-level ERROR 2>&1 | tail -2
    done
    log "  远端清理完成"
}

# ============ 6. 摘要 ============
manifest() {
    local ts="$1"
    local tarball="$2"
    local manifest_file="$STAGING_DIR/hermes-${ts}.manifest"
    {
        echo "Hermes Backup Manifest"
        echo "======================="
        echo "时间戳: $ts"
        echo "Mac:    $(hostname)"
        echo "用户:   $(whoami)"
        echo ""
        echo "文件清单(前 50 大):"
        echo "--------------------"
        local tmp_manifest=$(mktemp)
        tar -tzf "$tarball" | sed 's|^\.hermes/||' | while read p; do
            local full="$HERMES_HOME/$p"
            [ -e "$full" ] && stat -f '%z %N' "$full" 2>/dev/null
        done > "$tmp_manifest" 2>/dev/null || true
        sort -rn "$tmp_manifest" 2>/dev/null | head -50 || echo "(无)"
        rm -f "$tmp_manifest"
        echo ""
        echo "还原命令:"
        echo "--------------------"
        echo "  gpg --batch --passphrase <密码> -d hermes-${ts}.tar.gz.gpg > hermes.tar.gz"
        echo "  tar --strip-components=1 -xzf hermes.tar.gz -C ~/.hermes"
    } > "$manifest_file" 2>/dev/null || true
    log "摘要: $manifest_file" >&2
}

# ============ 主流程 ============
main() {
    local do_upload=true
    local password=""
    local dry_run=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --keychain-set)
                local pw1 pw2
                read -rs -p '设置 GPG 密码: ' pw1
                echo
                read -rs -p '再输一次确认: ' pw2
                echo
                [ "$pw1" = "$pw2" ] || die "两次输入不一致"
                gpg_password_set "$pw1"
                log "已写入 Keychain"; exit 0
                ;;
            --no-upload) do_upload=false; shift;;
            --dry-run) dry_run=true; shift;;
            --key) password="$2"; shift 2;;
            -h|--help) usage; exit 0;;
            *) die "未知参数: $1";;
        esac
    done

    mkdir -p "$BACKUP_DIR" "$STAGING_DIR"

    local ts=$(date '+%Y%m%d-%H%M%S')
    log "==== 开始备份 $ts ===="

    if $dry_run; then
        cd "$HERMES_HOME/.."
        echo "将被打包的文件(前 30 + 统计):"
        local tmp_list=$(mktemp)
        tar "${TAR_EXCLUDES[@]}" -cf - .hermes 2>/dev/null | tar -tf - > "$tmp_list" 2>/dev/null
        head -30 "$tmp_list" | sed 's/^/  /'
        local total_files=$(wc -l < "$tmp_list" | tr -d ' ')
        echo ""
        echo "  备份包预估: $total_files 个文件"
        echo "  排除: hermes-agent, lsp, bin, cache, screenshots, 旧日志, mcp-chrome, .backups, venv"
        echo ""
        echo "包内根目录: .hermes/(解压时用 --strip-components=1)"
        rm -f "$tmp_list"
        return
    fi

    if [ -z "$password" ]; then
        password=$(gpg_password_get) || die "Keychain 无密码, 先跑 --keychain-set"
    fi

    sqlite_checkpoint
    local tarball=$(pack "$ts")
    manifest "$ts" "$tarball"
    local chunk_dir=$(encrypt_chunk "$tarball" "$ts" "$password")

    if $do_upload; then
        upload "$chunk_dir" "$ts"
        cleanup_remote
    else
        log "跳过上传(--no-upload)"
    fi

    cleanup_local
    log "==== 备份完成 $ts ===="
}

main "$@"
