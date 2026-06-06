#!/usr/bin/env bash
# hermes_restore_one.sh — 真·一键还原:从 GitHub 拉备份 → 解密 → 解压 → 配好 hermes
# 适用: 新电脑/重装系统后,跑这一行就能恢复完整的 Hermes
#
# 用法(3 选 1,按可用性从高到低):
#   gh auth login
#   gh api repos/<user>/<repo>/contents/hermes_restore_one.sh --jq .content | base64 -d | bash
#   # 或者本地:
#   bash ~/.hermes/scripts/hermes_restore_one.sh
#   # 或者等 raw 缓存刷新后(几小时,私有仓不靠谱):
#   curl -sL https://raw.githubusercontent.com/<user>/<repo>/main/hermes_restore_one.sh | bash
#
# 它会:
#   1. 自动检测环境(有没有 brew / python / gpg / git)
#   2. 没有就装
#   3. 从 GitHub 拉最新的 backup 分支
#   4. 拼回 .gpg → 解密(交互式输密码)→ 解压到 ~/.hermes
#   5. 装 hermes-agent 源码 + venv
#   6. 健康检查
#
# 你只要提供: GPG 密码(脑子里)

set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
GITHUB_REPO="${HERMES_BACKUP_REPO:-Buluhanke/hermes-backup}"
BACKUP_BRANCH_PATTERN="^backup-2"  # backup-YYYYMMDD-HHMMSS

red() { echo -e "\033[31m$*\033[0m" >&2; }
green() { echo -e "\033[32m$*\033[0m" >&2; }
yellow() { echo -e "\033[33m$*\033[0m" >&2; }
bold() { echo -e "\033[1m$*\033[0m" >&2; }
say()  { echo "$*" >&2; }

# ============ 第 0 步:打屏欢迎 ============
bold ""
bold "==============================================="
bold "  Hermes 一键还原器 v1.0"
bold "  适用场景: 新电脑 / 重装系统 / 灾难恢复"
bold "==============================================="
echo ""

# ============ 第 1 步:环境检测 ============
bold "[1/7] 环境检测..."

need_install=()

if ! command -v brew &>/dev/null; then
    need_install+=("brew")
    yellow "  ⚠ brew 未装"
else
    green "  ✓ brew 已装"
fi

if ! command -v python3.11 &>/dev/null; then
    need_install+=("python@3.11")
    yellow "  ⚠ python3.11 未装"
else
    green "  ✓ python3.11 已装"
fi

if ! command -v gpg &>/dev/null; then
    need_install+=("gpg")
    yellow "  ⚠ gpg 未装"
else
    green "  ✓ gpg 已装"
fi

if ! command -v node &>/dev/null; then
    need_install+=("node")
    yellow "  ⚠ node 未装"
else
    green "  ✓ node 已装"
fi

if ! command -v git &>/dev/null; then
    red "  ✗ git 未装(应该 macOS 自带)"
    exit 1
else
    green "  ✓ git 已装"
fi

if ! command -v gh &>/dev/null; then
    need_install+=("gh")
    yellow "  ⚠ gh CLI 未装"
else
    green "  ✓ gh CLI 已装"
fi

# ============ 第 2 步:装缺的工具 ============
bold "[2/7] 装缺的工具(可能 1-3 分钟)..."

if [ ${#need_install[@]} -gt 0 ]; then
    yellow "  需要装: ${need_install[*]}"
    if [[ " ${need_install[*]} " =~ " brew " ]]; then
        say "  先装 brew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" </dev/null
        if [ -f /opt/homebrew/bin/brew ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    fi
    brew install "${need_install[@]}" 2>&1 | tail -5
    green "  ✓ 装好了"
else
    green "  ✓ 全部都有,跳过"
fi

# 关键: 用 homebrew 的 git(2.53+)
export PATH="/opt/homebrew/bin:$PATH"

# ============ 第 3 步:GitHub 认证 ============
bold "[3/7] GitHub 认证..."

if ! gh auth status &>/dev/null; then
    yellow "  ⚠ 你还没登录 GitHub"
    yellow "  跑下面这行按提示登录(浏览器会跳出来):"
    echo ""
    bold "    gh auth login"
    echo ""
    gh auth login
fi
green "  ✓ GitHub 已登录: $(gh api user --jq .login 2>/dev/null)"

# ============ 第 4 步:找最新 backup 分支 ============
bold "[4/7] 找最新的备份分支..."

LATEST_BRANCH=$(gh api "repos/$GITHUB_REPO/branches?per_page=100" --jq '.[].name' 2>/dev/null | \
    grep -E "$BACKUP_BRANCH_PATTERN" | sort -r | head -1)

if [ -z "$LATEST_BRANCH" ]; then
    red "  ✗ 没找到 backup 分支,确认下你的 GitHub 仓有内容"
    exit 1
fi
green "  ✓ 找到: $LATEST_BRANCH"

PARTS=$(gh api "repos/$GITHUB_REPO/contents/?ref=$LATEST_BRANCH" --jq '.[].name' 2>/dev/null | grep "\.part" | sort)
PART_COUNT=$(echo "$PARTS" | wc -l | tr -d ' ')
green "  ✓ 有 $PART_COUNT 个分卷"

# ============ 第 5 步:clone + 拼分卷 ============
bold "[5/7] 拉备份到本地..."

TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"
gh repo clone "$GITHUB_REPO" backup 2>&1 | tail -3
cd backup
git checkout "$LATEST_BRANCH" 2>&1 | tail -3
green "  ✓ 拉完了"

echo ""
bold "  拼回 .gpg..."
cat hermes-*.gpg.part* > merged.gpg
green "  ✓ 拼好: $(ls -lah merged.gpg | awk '{print $5}')"

# ============ 第 6 步:GPG 解密 + 解压 ============
bold "[6/7] GPG 解密 + 解压到 ~/.hermes..."

yellow ""
yellow "  ⚠️ 重要:下面会要你输 GPG 密码(就是当初设的那个)"
yellow "  你设的密码是什么?现在输:"
echo ""
read -rs -p "  GPG 密码: " GPG_PW
echo ""

gpg --batch --pinentry-mode loopback --passphrase "$GPG_PW" \
    --decrypt merged.gpg > hermes.tar.gz 2> /tmp/gpg-err.log
if [ ! -s hermes.tar.gz ]; then
    red "  ✗ 解密失败,看下错误:"
    cat /tmp/gpg-err.log | head -5 >&2
    exit 1
fi
green "  ✓ 解密完成: $(du -h hermes.tar.gz | awk '{print $1}')"

mkdir -p "$HERMES_HOME"
tar --strip-components=1 -xzf hermes.tar.gz -C "$HERMES_HOME" 2>&1 | tail -3
green "  ✓ 解压到 $HERMES_HOME"

chmod 700 "$HERMES_HOME"
chmod 600 "$HERMES_HOME/.env" 2>/dev/null || true
chmod 600 "$HERMES_HOME/cron/jobs.json" 2>/dev/null || true
green "  ✓ 权限修复"

# 存 GPG 密码到 Keychain
security delete-generic-password -s "com.hermes.backup.gpg" -a "hermes-archive" 2>/dev/null || true
security add-generic-password -s "com.hermes.backup.gpg" -a "hermes-archive" -w "$GPG_PW" -U
green "  ✓ GPG 密码存到 Keychain"

# ============ 第 7 步:装 hermes-agent 源码 ============
bold "[7/7] 装 hermes-agent 源码..."

if [ ! -d "$HERMES_HOME/hermes-agent" ]; then
    mkdir -p "$HERMES_HOME"
    cd "$HERMES_HOME"
    git clone https://github.com/NousResearch/hermes-agent.git 2>&1 | tail -3
else
    yellow "  ⚠ hermes-agent 已存在,跳过 clone"
fi

if [ ! -d "$HERMES_HOME/hermes-agent/venv" ]; then
    cd "$HERMES_HOME/hermes-agent"
    python3.11 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    green "  ✓ venv 重建完成"
else
    yellow "  ⚠ venv 已存在,跳过"
fi

if [ -d "$HERMES_HOME/hermes-agent/ui-tui" ]; then
    cd "$HERMES_HOME/hermes-agent/ui-tui"
    if [ ! -d node_modules ]; then
        npm install --silent
        green "  ✓ ui-tui 依赖装好"
    else
        yellow "  ⚠ ui-tui node_modules 已存在,跳过"
    fi
fi

# ============ 健康检查 ============
bold ""
bold "==============================================="
bold "  健康检查"
bold "==============================================="
echo ""
echo "  config.yaml: $([ -f "$HERMES_HOME/config.yaml" ] && echo '✓ 存在' || echo '✗ 缺失')"
echo "  state.db:    $([ -f "$HERMES_HOME/state.db" ] && du -h "$HERMES_HOME/state.db" | awk '{print "✓ 存在 ("$1")"}' || echo '✗ 缺失')"
echo "  .env:        $([ -f "$HERMES_HOME/.env" ] && echo '✓ 存在' || echo '✗ 缺失')"
echo "  skills/:     $([ -d "$HERMES_HOME/skills" ] && ls "$HERMES_HOME/skills" | wc -l | awk '{print "✓ "$1" 个一级目录"}' || echo '✗ 缺失')"
echo "  memory:      $([ -f "$HERMES_HOME/memory_store.db" ] && echo '✓ 存在' || echo '✗ 缺失')"

if [ -f "$HERMES_HOME/state.db" ]; then
    local integrity=$(python3 -c "
import sqlite3
c = sqlite3.connect('$HERMES_HOME/state.db')
cur = c.execute('PRAGMA integrity_check')
print(cur.fetchone()[0])
" 2>&1)
    echo "  state.db 完整性: $integrity"
fi

# 清理临时
rm -rf "$TEMP_DIR"

bold ""
bold "✅ Hermes 还原完成!"
echo ""
echo "下一步:"
echo "  cd $HERMES_HOME/hermes-agent"
echo "  source venv/bin/activate"
echo "  hermes --version"
echo "  hermes config validate"
echo "  hermes chat 'ping'"
