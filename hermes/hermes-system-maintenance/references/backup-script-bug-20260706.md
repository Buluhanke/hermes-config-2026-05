# Backup Script Bug Fix — 2026-07-06

## 问题
`hermes_backup_github_push.sh` 清理远程 GitHub 分支（`cleanup_old_branches`）但**从不清理本地** `github-chunks/` 和 `github-push/`。

导致 9.6GB staging 残留，每次运行都追加新分卷。

## 根因
脚本 `main()` 里只调用了 `cleanup_old_branches`，没有调用本地清理函数。

## 修复
在 `hermes_backup_github_push.sh` 的 `main()` 函数末尾，`cleanup_old_branches` 调用之后添加：

```bash
cleanup_local_staging
```

新增 `cleanup_local_staging()` 函数（加在 `cleanup_old_branches` 后面）：

```bash
cleanup_local_staging() {
    yellow "  清理本地 staging 目录(保留最近 $KEEP_VERSIONS 个)..."
    local chunks_dir="$STAGING_DIR/github-chunks"
    local push_dir="$STAGING_DIR/github-push"

    for dir in "$chunks_dir" "$push_dir"; do
        [ ! -d "$dir" ] && continue
        local count=$(ls -1d "$dir"/2?????????????? 2>/dev/null | wc -l | tr -d ' ')
        if [ "$count" -le "$KEEP_VERSIONS" ]; then
            green "    $dir 只有 $count 个,无需清理" >&2
            continue
        fi
        ls -1dt "$dir"/2?????????????? 2>/dev/null | tail -n +$((KEEP_VERSIONS + 1)) | while read -r sub; do
            [ -d "$sub" ] && rm -rf "$sub" && yellow "    删: $sub" >&2
        done
    done
    green "  ✓ 本地 staging 清理完成" >&2
}
```

## 清理前
```
github-chunks: 19 个时间戳目录，7.5GB
github-push: 0 个（无时间戳子目录）
```

## 清理后（KEEP_VERSIONS=4）
```
github-chunks: 4 个最新目录，~6.3GB
github-push: 0 个
```

保留的 4 个：
- `20260704-221158` (116MB)
- `20260630-232344` (5.8GB 完整备份，113 个分卷)
- `20260628-030005` (116MB)
- `20260621-030005` (116MB)

## 教训
备份脚本的"写入逻辑"和"清理逻辑"必须同步设计。staging 目录是中间目录，不是归档。
