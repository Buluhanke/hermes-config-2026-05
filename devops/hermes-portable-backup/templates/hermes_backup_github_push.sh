#!/usr/bin/env bash
# hermes_backup_github_push.sh — 用 git push 把 .gpg 推到 GitHub 私有仓
# 适用: 116MB 单文件超过 GitHub 100MB 单文件限制, 拆成 50MB/卷(2-3 卷)
# 优势: git push 协议稳定(实测 0-7MB + 50MB×3 都成功), 不走 release upload API
# 还原: 拼回 .gpg → 解密 → 解压
#
# 必须前置: 脚本头 export PATH="/opt/homebrew/bin:$PATH"(Apple git 2.15 必撞 HTTP/2 EOF)
#
# 用法: 直接跑, 或 launchd 每周调

set -euo pipefail

# 关键: 用 homebrew 的 git(2.53+), 不用 apple 自带 git(2.15 太老不支持 HTTP/2)
export PATH="/opt/homebrew/bin:$PATH"

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
BACKUP_DIR="$HERMES_HOME/.backups"
STAGING_DIR="$BACKUP_DIR/staging"
LOG_FILE="$BACKUP_DIR/github-push.log"
GITHUB_REPO="hermes-backup"
CHUNK_SIZE="50M"   # GitHub 单文件 ≤100MB, 留余量
KEEP_VERSIONS=4    # 保留几个 tag 历史
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')

red()   { echo -e "\033[31m$*\033[0m" >&2; }
green() { echo -e "\033[32m$*\033[0m" >&2; }
yellow(){ echo -e "\033[33m$*\033[0m" >&2; }
bold()  { echo -e "\033[1m$*\033[0m" >&2; }
log()   { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

# ============ 1. 找最新 .gpg ============
find_latest_gpg() {
    # 优先找桌面的(用户最近跑的)
    local desktop_gpg
    desktop_gpg=$(ls -t ~/Desktop/hermes-backup-*.gpg 2>/dev/null | head -1)
    if [ -n "$desktop_gpg" ] && [ -f "$desktop_gpg" ]; then
        echo "$desktop_gpg"
        return
    fi
    ls -t "$STAGING_DIR"/hermes-backup-*.gpg 2>/dev/null | head -1
}

# ============ 2. 拆分 .gpg ============
chunk_gpg() {
    local gpg_file="$1"
    local ts="$2"
    local chunk_dir="$STAGING_DIR/github-chunks/$ts"
    mkdir -p "$chunk_dir"

    yellow "  拆分 .gpg 成 50MB/卷..." >&2
    cd "$chunk_dir"
    split -b "$CHUNK_SIZE" -d -a 3 "$gpg_file" "hermes-${ts}.gpg.part"
    local parts
    parts=$(ls hermes-${ts}.gpg.part* | wc -l | tr -d ' ')
    green "  ✓ 拆成 $parts 卷" >&2

    cat > "$chunk_dir/MANIFEST.txt" <<EOF
Hermes 加密备份 - 拆分清单
===========================
时间戳: $ts
原文件: $(basename "$gpg_file")
原始大小: $(stat -f "%z" "$gpg_file" | awk '{printf "%.1f MB", $1/1024/1024}')
分卷大小: $CHUNK_SIZE
分卷数: $parts

拼回原文件: cat hermes-${ts}.gpg.part* > hermes-merged.gpg
还原步骤:  gpg -d hermes-merged.gpg > /tmp/hermes.tar.gz
            tar --strip-components=1 -xzf /tmp/hermes.tar.gz -C ~/.hermes
EOF

    # 复制 restore.sh(容错 cp identical 报错)
    cp "$HERMES_HOME/scripts/hermes_restore.sh" "$chunk_dir/restore.sh" 2>&1 | grep -v "same file" || true
    # 只 echo 路径给 $() 捕(避免 ANSI 染色)
    echo "$chunk_dir"
}

# ============ 3. 推到 GitHub 私有仓(独立分支) ============
push_to_github() {
    local user="$1"
    local chunk_dir="$2"
    local ts="$3"
    local branch="backup-${ts}"
    local repo_dir="$STAGING_DIR/github-push"
    local default_branch
    default_branch=$(gh api "repos/$user/$GITHUB_REPO" --jq '.default_branch' 2>/dev/null || echo "main")

    yellow "  推到 GitHub 分支: $branch ..." >&2
    mkdir -p "$repo_dir"
    cd "$repo_dir"

    if [ ! -d .git ]; then
        git init -q
        git remote add origin "https://github.com/$user/$GITHUB_REPO.git"
        git fetch origin "$default_branch" --depth 1 2>&1 | tail -2
        git checkout -q "$default_branch" 2>/dev/null || git checkout -q -b "$default_branch"
    fi

    if git ls-remote --heads origin "$branch" 2>/dev/null | grep -q "$branch"; then
        yellow "  分支已存在, 删除重建" >&2
        git branch -D "$branch" 2>/dev/null || true
    fi
    git checkout -q -b "$branch"

    # 清空旧内容
    find . -maxdepth 1 -not -name '.git' -not -name '.' -exec rm -rf {} + 2>/dev/null || true

    # 拷贝分卷(容错 cp identical)
    if [ ! -f "$chunk_dir/$(basename "$chunk_dir" | awk '{print "hermes-"$0".gpg.part000"}')" ]; then
        red "  ✗ 拆分目录异常: $chunk_dir"
        exit 1
    fi
    cp "$chunk_dir"/* . 2>&1 | grep -v "same file" || true

    # 提交
    git add .
    git -c user.name="hermes-backup" -c user.email="backup@hermes.local" \
        commit -q -m "backup: $ts ($(du -sh . 2>/dev/null | awk '{print $1}'))" || {
            red "  ✗ commit 失败"
            exit 1
        }

    # 推(可能 1-2 次重试)
    yellow "  推送 $(ls hermes-*.gpg.part* 2>/dev/null | wc -l | tr -d ' ') 个分卷..." >&2
    local attempt=0
    local max_attempts=3
    local success=false
    while [ $attempt -lt $max_attempts ] && ! $success; do
        attempt=$((attempt + 1))
        if [ $attempt -gt 1 ]; then
            yellow "  重试 $attempt/$max_attempts..." >&2
            sleep 5
        fi
        if git -c http.postBuffer=104857600 push -u origin "$branch" 2>&1 | tail -5; then
            success=true
        fi
    done

    if $success; then
        green "  ✓ https://github.com/$user/$GITHUB_REPO/tree/$branch" >&2
    else
        red "  ✗ 推送 3 次都失败"
        exit 1
    fi

    git checkout -q "$default_branch" 2>/dev/null || true
}

# ============ 4. 清理旧备份分支 ============
cleanup_old_branches() {
    local user="$1"
    local pattern="^backup-2"

    yellow "  清理旧 backup 分支(保留最近 $KEEP_VERSIONS 个)..." >&2

    local branches
    branches=$(gh api "repos/$user/$GITHUB_REPO/branches?per_page=100" --jq '.[].name' 2>/dev/null | grep -E "$pattern" | sort -r)
    local total
    total=$(echo "$branches" | grep -c "^backup-" || echo "0")
    if [ "$total" -le "$KEEP_VERSIONS" ]; then
        green "    远端只有 $total 个 backup 分支, 无需清理" >&2
        return
    fi

    echo "$branches" | tail -n +$((KEEP_VERSIONS + 1)) | while read -r branch; do
        if [ -n "$branch" ]; then
            yellow "    删: $branch" >&2
            gh api -X DELETE "repos/$user/$GITHUB_REPO/git/refs/heads/$branch" 2>&1 | tail -1 >&2
        fi
    done
    green "  ✓ 清理完成" >&2
}

# ============ 主流程 ============
main() {
    mkdir -p "$STAGING_DIR"
    log "==== GitHub Push 备份 $TIMESTAMP 开始 ===="

    local user
    user=$(gh api user --jq '.login' 2>/dev/null) || {
        red "✗ gh 没登录"
        exit 1
    }
    green "✓ 登录: $user" >&2

    local gpg_file
    gpg_file=$(find_latest_gpg)
    if [ -z "$gpg_file" ] || [ ! -f "$gpg_file" ]; then
        red "✗ 找不到 .gpg 文件, 先跑 hermes_backup_simple.sh"
        exit 1
    fi
    green "  ✓ 找到: $(basename $gpg_file) ($(du -h "$gpg_file" | awk '{print $1}'))" >&2

    # 拆分(走临时文件避免 ANSI 污染 $())
    local tmp_chunk
    tmp_chunk=$(mktemp)
    chunk_gpg "$gpg_file" "$TIMESTAMP" > "$tmp_chunk" 2>/dev/null
    local chunk_dir
    chunk_dir=$(cat "$tmp_chunk")
    rm -f "$tmp_chunk"

    if [ -z "$chunk_dir" ] || [ ! -d "$chunk_dir" ]; then
        red "✗ 拆分失败"
        exit 1
    fi
    green "  ✓ 拆完成" >&2

    push_to_github "$user" "$chunk_dir" "$TIMESTAMP"
    cleanup_old_branches "$user"

    log "==== GitHub Push 备份完成 $TIMESTAMP ===="
    green "" >&2
    green "✅ 备份已推到 GitHub 私有仓!" >&2
    echo ""
    echo "新电脑还原:"
    echo "  1. gh repo clone $GITHUB_REPO.git   # 或: gh api repos/<user>/$GITHUB_REPO/contents/hermes_restore_one.sh --jq .content | base64 -d | bash"
    echo "  2. cd $GITHUB_REPO && git checkout backup-$TIMESTAMP"
    echo "  3. cat hermes-*.gpg.part* > hermes-merged.gpg"
    echo "  4. bash restore.sh"
}

main "$@"
