# Safe Cron Script Edit Protocol（2026-06-05 实战沉淀）

## 背景

self_evolution.sh 是 launchd 拉起的多模式 cron 脚本（hourly 30min / daily 09:00 /
weekly 周一）。当给 hourly 模式加 Do 段（自动重启 gateway / Chrome 9333 / 拉起 proxy）
时，**直接 `bash self_evolution.sh hourly` 验证会立刻 kill 掉所有 launchd 拉起的
活进程**（dashboard / screen_watcher / gateway 本体），造成 10-30s 闪断。

**事故风险**（按严重度排序）：

| 等级 | 现象 | 后果 |
|---|---|---|
| CRITICAL | 重启 gateway 同时 kill 掉 dashboard 进程 | 闪断 + dashboard 重启导致用户活跃 session 失联 |
| HIGH | `pkill -f "chrome.*9333"` 误杀同命令行的 Chrome 父进程 | 用户所有 Chrome 标签页全关 |
| MEDIUM | 自动拉起 clash 时未先检查已运行 | 双进程争抢 7897 端口 |
| LOW | 重复 fact 写入 | 记忆库膨胀（无功能影响） |

## 安全协议（5 步强制）

### 1. 静态分析（`grep -F` 验证关键 marker）

不要 live-test，**先把 Do 段在脚本文件里写完，然后 grep 验证安全保护全在位**：

```bash
F=~/.hermes/scripts/self_evolution.sh

# 验证 5 个安全保护 marker 全部存在
for marker in \
  "尝试 3 次健康检查" \
  "尝试重启 gateway" \
  "SIGTERM 无效, 已 SIGKILL" \
  "尝试拉起 clash/proxy" \
  "kill -TERM \"\$GW_PID\"" \
  "TODAY_KEY=\"tg_proxy_alert_" \
  "CHROME_KEY=\"chrome_9333_restart_"; do
  if grep -qF "$marker" "$F"; then
    echo "✅ $marker"
  else
    echo "❌ 缺失: $marker"
  fi
done
```

**grep 误报陷阱**：含 `$` 的 marker 在 shell 里被解释成变量。`grep -F 'kill -TERM "\$GW_PID"'`
会匹配文件里的 `kill -TERM "$GW_PID"`（反斜杠在 shell 单引号下字面保留）。若用 `grep -qF 'kill -TERM "$GW_PID"'`
不写反斜杠，反而匹配不到。这是 shell quoting 的常见坑。

### 2. 语法检查（`bash -n`）

```bash
bash -n ~/.hermes/scripts/self_evolution.sh && echo "✅ 语法 OK"
```

`bash -n` 只检查语法不执行。**必做**。少做这一步的常见后果是 hour 段写完部署后 30min
natural-trigger 跑 → syntax error → cron 静默失败（no_agent 模式 stdout 空=不报错）。

### 3. 进程白名单（手动核查 live PIDs）

```bash
# 列出所有 launchd 拉起的 Hermes 进程（do 段会涉及的）
pgrep -fl "hermes_cli.main" | head -5
# 列出 chrome / proxy 进程
pgrep -fl "chrome.*9333|ClashX|clash " | head -5
```

**核对清单**：
- 哪些 PID 是 launchd 拉起的（会被 Do 段一起 kill 闪断）
- 哪些 PID 是用户手动启的（kill 后用户知道）
- 哪些 PID 在白名单（绝不能杀，如 screen_watcher）

### 4. 自然触发（让 cron 自己跑，不手动 live-test）

```bash
# 看 plist 调度间隔
grep StartInterval ~/Library/LaunchAgents/ai.hermes.self-evolution.plist
# → <integer>1800</integer>  = 30min
```

**最迟 30min 内** 自然触发，**不手动跑**。若立即想看效果：
```bash
# 用 --dry-run 模式（如果脚本支持），或新加 DRY_RUN 开关
DRY_RUN=true bash ~/.hermes/scripts/self_evolution.sh hourly
```

### 5. 触发后立刻看 evolution.log

```bash
tail -50 ~/.hermes/logs/evolution.log
```

**找 3 类信号**：
- `✅ ...` （修复成功）
- `❌ ...` （Do 段失败）
- 进程是否仍在（`pgrep -f hermes_cli.main` 应有 PID）

## 反面教材：手动 live-test 触发闪断（2026-06-05 已规避）

**潜在场景**（若直接 `bash self_evolution.sh hourly`）：
1. 检测到 CDP 9333 异常段（**不会**触发，9333 实际在监听）
2. 检测到 Telegram 错误段 → 走 2b → `kill -TERM PID` → dashboard 闪断
3. 用户 5 分钟后发现 dashboard 死了 → 报错 → 排查 → 浪费时间

**规避**：本次 session 全部走静态分析，**不手动跑**。等 30min 后自然触发。

## 验收清单

每次给 cron 脚本加 Do 段后强制走：

- [ ] `bash -n` 语法 OK
- [ ] 5 个 marker grep 全在
- [ ] live PID 列表已记录（哪些会被 kill 闪断）
- [ ] plist 调度间隔已知（最长等多久）
- [ ] `evolution.log` tail 50 已读（找修复/失败标记）
- [ ] 关键白名单进程（screen_watcher）未被 kill

## 配套工具（推荐加入 self_evolution.sh 头部）

```bash
# safety_check 函数（建议加在文件最顶部）
safety_check() {
    local LIVE_DASHBOARD=$(pgrep -fl "hermes_cli.main dashboard" | wc -l | tr -d ' ')
    local LIVE_GATEWAY=$(pgrep -fl "hermes_cli.main gateway" | wc -l | tr -d ' ')
    log "safety: dashboard=$LIVE_DASHBOARD gateway=$LIVE_GATEWAY  (会随 gateway 重启闪断 dashboard)"
    # 真正的保护：kill 前先确认是否在白名单
    if echo "$PID" | grep -qE "$(cat ~/.hermes/.hermes_protected_pids 2>/dev/null)"; then
        log "🛡️  PID $PID 在白名单, 跳过 kill"
        return 1
    fi
    return 0
}
```

白名单文件 `~/.hermes/.hermes_protected_pids` 内容示例：
```
33447  # dashboard
33454  # dashboard worker
```

每次 launchd 拉起新进程时由对应 plist 的 post-script 写入。

## 经验总结

> **修 cron 脚本 = 改生产环境 + 立刻自然触发**。Live-test = 主动制造线上事故。
> 静态分析能查 95% 的 bug，剩下的 5% 由 cron 自然触发 + evolution.log 兜底。
> **永远不要 `bash cron_script.sh mode` 跑**——除非你 100% 确认 Do 段已临时注释或 DRY_RUN。

## 相关参考

- `self-evolution-framework` 的"⚠️ 关键坑位：框架搭了 ≠ 集成进了"小节
- `proactive-execution` 的规则3"破坏性操作需要授权" + Gateway 重启技术笔记
- `scheduled-task-audit` 的 launchd 改时间必须 reload
