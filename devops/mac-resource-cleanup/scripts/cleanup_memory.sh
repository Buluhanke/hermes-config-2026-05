#!/bin/bash
# cleanup_memory.sh — 一键内存清理（用户授权后用）
# 默认：清应用缓存 + Hermes 旧文件，预期腾 2-3GB
# 不可恢复的操作已在脚本里写明，需用户授权后跑

set -e
DRY_RUN="${1:-real}"  # 传 "dry" 只打印不执行

log() { echo "[$(date +%H:%M:%S)] $*"; }
del() {
  if [[ "$DRY_RUN" == "dry" ]]; then
    echo "[DRY] 跳过（真要删去掉 dry 参数）: $*"
  else
    rm -rf "$@" 2>/dev/null && log "✅ 删: $*"
  fi
}

log "═══ 内存清理启动（模式: $DRY_RUN）═══"
FREE_BEFORE=$(vm_stat | awk '/Pages free/ {print $3}' | tr -d '.')
FREE_BEFORE_MB=$((FREE_BEFORE * 16384 / 1024 / 1024))
log "当前 free: ${FREE_BEFORE_MB} MB"

# ① 应用缓存（用户授权后）
log ""
log "── 应用缓存 ──"
del ~/Library/Caches/ms-playwright
del ~/Library/Caches/com.anthropic.claudefordesktop.ShipIt
del ~/Library/Caches/electron
del ~/Library/Caches/Google
del ~/Library/Caches/Homebrew

# ② Hermes 自带（always 允许）
log ""
log "── Hermes 日志（保留最近 3 个）──"
LOG=~/.hermes/logs
if [[ -d "$LOG" ]]; then
  ls -t "$LOG"/* 2>/dev/null | tail -n +4 | while read f; do
    del "$f"
  done
fi

log ""
log "── state-snapshots 保留 30 天 ──"
SNAP=~/.hermes/state-snapshots
if [[ -d "$SNAP" ]]; then
  find "$SNAP" -type f -mtime +30 2>/dev/null | while read f; do
    del "$f"
  done
  find "$SNAP" -type d -empty 2>/dev/null | while read f; do
    del "$f"
  done
fi

log ""
log "── audio_cache 全清（TTS 临时产物）──"
del ~/.hermes/audio_cache

log ""
log "── /tmp/hermes_* / /tmp/smoke_* ──"
del /tmp/hermes_* /tmp/smoke_*.py 2>/dev/null || true

log ""
log "═══ 完成 ═══"
FREE_AFTER=$(vm_stat | awk '/Pages free/ {print $3}' | tr -d '.')
FREE_AFTER_MB=$((FREE_AFTER * 16384 / 1024 / 1024))
log "free: ${FREE_BEFORE_MB} MB → ${FREE_AFTER_MB} MB"
log "注意：active 内存要等 OS 几分钟自动回收"
