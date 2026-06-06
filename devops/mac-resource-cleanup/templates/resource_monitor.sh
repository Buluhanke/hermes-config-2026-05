#!/bin/bash
# =============================================================
# Hermes 资源监控 — cron/launchd 触发的精简模板
# 用法：复制本文件 → 改 LOG/CLEANUP_SH 路径 → chmod +x
#      → 加到 crontab 或 launchd
# =============================================================

# ---------- 配置（用环境变量覆盖也行）----------
LOG="${LOG:-$HOME/.hermes/logs/resource-monitor.log}"
THRESHOLD_MEM="${THRESHOLD_MEM:-80}"   # 内存占用 > 此 % 触发
THRESHOLD_CPU="${THRESHOLD_CPU:-70}"   # CPU 占用 > 此 % 触发
CLEANUP_SH="${CLEANUP_SH:-$HOME/.hermes/scripts/cleanup_hermes_logs.sh}"
AUDIO_CACHE_DIR="${AUDIO_CACHE_DIR:-$HOME/.hermes/audio_cache}"
AUDIO_CACHE_AGE_MIN="${AUDIO_CACHE_AGE_MIN:-60}"  # 清掉 N 分钟前的 TTS 临时文件

set -o pipefail

# ---------- 日志（写文件 + stdout，cron 自身另存一份排查）----------
log() {
    local msg="$(date '+%Y-%m-%d %H:%M:%S') [$1] $2"
    echo "$msg" >> "$LOG"
    echo "$msg"
}

mkdir -p "$(dirname "$LOG")"

# ---------- 内存占用 %（兼容新旧 macOS 字段，详见 references/macos-vmstat-fields.md）----------
mem_pct() {
    local vmstat
    vmstat=$(vm_stat 2>/dev/null) || { echo "0"; return; }
    local p_free p_active p_inactive p_wired p_compressed total used
    p_free=$(echo "$vmstat" | awk '/Pages free:/ {gsub(/\./,"",$3); print $3+0}')
    p_active=$(echo "$vmstat" | awk '/Pages active:/ {gsub(/\./,"",$3); print $3+0}')
    p_inactive=$(echo "$vmstat" | awk '/Pages inactive:/ {gsub(/\./,"",$3); print $3+0}')
    p_wired=$(echo "$vmstat" | awk '/Pages wired down:/ {gsub(/\./,"",$4); print $4+0}')
    p_compressed=$(echo "$vmstat" | awk '/Pages stored in compressor|Pages occupied by compressor/ {gsub(/\./,"",$NF); print $NF+0; exit}')
    p_compressed=${p_compressed:-0}
    local page_size=16384
    total=$(( (p_free + p_active + p_inactive + p_wired + p_compressed) * page_size ))
    used=$(( (p_active + p_wired) * page_size ))
    if [ "$total" -le 0 ]; then echo "0"; return; fi
    echo $(( used * 100 / total ))
}

# ---------- CPU 占用 %（load average 归一化）----------
cpu_pct() {
    local cores load1
    cores=$(sysctl -n hw.logicalcpu 2>/dev/null || echo 8)
    load1=$(sysctl -n vm.loadavg 2>/dev/null | awk '{print $2}')
    [ -z "$load1" ] && { echo "0"; return; }
    awk -v l="$load1" -v c="$cores" 'BEGIN { if (c>0) printf "%d", (l/c)*100; else print 0 }'
}

# ---------- 主动释放缓存（🟢 零授权范围：用户自己管的缓存/日志/临时文件）----------
free_caches() {
    log "INFO" "阈值超限，开始自动释放缓存"
    local freed=0

    # ① 日志轮转（保留最近 3 个）
    if [ -f "$CLEANUP_SH" ]; then
        bash "$CLEANUP_SH" 2>&1 | while IFS= read -r line; do
            log "CLEAN" "$line"
        done
        freed=$((freed + 1))
    else
        log "WARN" "未找到 $CLEANUP_SH，跳过日志轮转"
    fi

    # ② Hermes TTS 临时音频
    if [ -d "$AUDIO_CACHE_DIR" ]; then
        local before after
        before=$(du -sm "$AUDIO_CACHE_DIR" 2>/dev/null | awk '{print $1}')
        find "$AUDIO_CACHE_DIR" -type f -mmin +"$AUDIO_CACHE_AGE_MIN" -delete 2>/dev/null
        after=$(du -sm "$AUDIO_CACHE_DIR" 2>/dev/null | awk '{print $1}')
        log "CLEAN" "audio_cache: ${before}M → ${after}M（清掉 ${AUDIO_CACHE_AGE_MIN} 分钟前文件）"
        freed=$((freed + 1))
    fi

    # ③ /tmp 下 hermes 临时文件
    if compgen -G "/tmp/hermes_*" > /dev/null 2>&1 || compgen -G "/tmp/smoke_*.py" > /dev/null 2>&1; then
        local tmp_count
        tmp_count=$(find /tmp -maxdepth 1 \( -name "hermes_*" -o -name "smoke_*.py" \) 2>/dev/null | wc -l | tr -d ' ')
        rm -rf /tmp/hermes_* /tmp/smoke_*.py 2>/dev/null
        log "CLEAN" "/tmp: 清掉 $tmp_count 个 hermes_/smoke_ 临时文件"
        freed=$((freed + 1))
    fi

    # ④ 刷脏页回盘（让 OS 更容易回收 inactive）
    sync 2>/dev/null
    log "CLEAN" "sync 已执行"

    log "INFO" "释放结束，共执行 $freed 项清理"
}

# ---------- 主流程 ----------
main() {
    local mem cpu mem_int cpu_int
    mem=$(mem_pct)
    cpu=$(cpu_pct)
    mem_int=${mem%.*}
    cpu_int=${cpu%.*}

    log "CHECK" "内存=${mem}% CPU=${cpu}% (阈值: 内存>${THRESHOLD_MEM}% 或 CPU>${THRESHOLD_CPU}%)"

    if [ "$mem_int" -gt "$THRESHOLD_MEM" ] || [ "$cpu_int" -gt "$THRESHOLD_CPU" ]; then
        log "ALERT" "超阈值 — 内存=${mem}% CPU=${cpu}%"
        free_caches

        sleep 2
        local mem2 cpu2
        mem2=$(mem_pct)
        cpu2=$(cpu_pct)
        log "RESULT" "清理后: 内存=${mem2}% CPU=${cpu2}% (释放前: 内存=${mem}% CPU=${cpu}%)"
    else
        log "OK" "在阈值内，无需清理"
    fi
}

main "$@"
exit 0
