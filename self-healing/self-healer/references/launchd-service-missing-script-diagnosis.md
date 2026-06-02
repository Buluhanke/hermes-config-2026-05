# launchd Service 故障诊断 — ProgramArguments 指向不存在的脚本

## 故障特征

launchd service 状态为 `not running`，但 `launchctl list` 显示该 service 已注册（`-` 在第一列，或显示 PID=0）。

## 诊断命令

```bash
# 1. 查看所有 hermes 相关服务的状态
launchctl list | grep -E "hermes|ai.hermes"

# 2. 查看具体服务的详细状态（含 stderr 来源）
launchctl print gui/$(id -u)/ai.hermes.self-evolution-daily 2>&1 | head -30

# 3. 查看该 service 的 stderr 日志（最关键！）
cat ~/.hermes/logs/evolution_err.log 2>/dev/null | tail -20

# 4. 检查 plist 中 ProgramArguments 指向的脚本是否真实存在
cat ~/Library/LaunchAgents/ai.hermes.self-evolution-daily.plist | grep -A3 ProgramArguments
```

## 典型错误信息

```
/bin/bash: /Users/aimac/.hermes/scripts/run_daily.sh: No such file or directory
```

→ service 已注册但脚本不存在，launchd 每次触发时执行 `/bin/bash /不存在的路径` → 立即退出 exit 127

## 修复步骤

### Step 1: unload 服务
```bash
launchctl unload ~/Library/LaunchAgents/ai.hermes.self-evolution-daily.plist
```

### Step 2: 检查 plist 内容
```bash
cat ~/Library/LaunchAgents/ai.hermes.self-evolution-daily.plist
```

重点看 `<key>ProgramArguments</key>` 下的 `<array>` 中的 `<string>` 路径。

### Step 3: 确认目标脚本是否存在
```bash
# 检查 plist 指向的脚本
ls -la /Users/aimac/.hermes/scripts/run_daily.sh 2>/dev/null || echo "NOT FOUND"

# 查找实际存在的同类脚本（可能名字变了）
ls ~/.hermes/scripts/self_evolution.sh
```

### Step 4: 修正 plist 中的 ProgramArguments

**错误示例**（daily plist 指向不存在的脚本）：
```xml
<key>ProgramArguments</key>
<array>
    <string>/bin/bash</string>
    <string>/Users/aimac/.hermes/scripts/run_daily.sh</string>
</array>
```

**正确示例**（调用 self_evolution.sh 并传参）：
```xml
<key>ProgramArguments</key>
<array>
    <string>/bin/bash</string>
    <string>/Users/aimac/.hermes/scripts/self_evolution.sh</string>
    <string>daily</string>
</array>
```

使用 `patch` 工具修正：
```python
patch(
  mode='replace',
  old_string='''    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/aimac/.hermes/scripts/run_daily.sh</string>
    </array>''',
  new_string='''    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/aimac/.hermes/scripts/self_evolution.sh</string>
        <string>daily</string>
    </array>''',
  path='~/Library/LaunchAgents/ai.hermes.self-evolution-daily.plist'
)
```

### Step 5: reload 服务
```bash
launchctl load ~/Library/LaunchAgents/ai.hermes.self-evolution-daily.plist
```

### Step 6: 验证
```bash
launchctl list | grep self-evolution-daily
# 应显示 PID > 0 或状态正常（非 "-"）
```

## 预防措施

建立 plist 引用脚本存在性检查脚本（可加入自检流程）：
```bash
#!/bin/bash
# 检查所有 hermes plist 的 ProgramArguments 脚本是否存在
for plist in ~/Library/LaunchAgents/ai.hermes.*.plist; do
    script=$(grep -A2 ProgramArguments "$plist" | grep '<string>' | tail -1 | sed 's/.*<string>//;s/<\/string>//')
    if [ -n "$script" ] && [ "$script" != "${script%.sh}" ]; then  # 跳过无 .sh 的路径
        if [ ! -f "$script" ]; then
            echo "BROKEN: $plist -> $script (NOT FOUND)"
        else
            echo "OK: $plist -> $script"
        fi
    fi
done
```

## 相关文件

- `/Users/aimac/Library/LaunchAgents/ai.hermes.self-evolution-daily.plist`
- `/Users/aimac/Library/LaunchAgents/ai.hermes.self-evolution-weekly.plist`
- `/Users/aimac/.hermes/scripts/self_evolution.sh` — 实际存在的脚本，支持 `hourly`/`daily`/`weekly` 三种模式

## 根因分析（2026-06-02 实测）

`self_evolution.sh` 支持三种模式通过命令行参数切换：
- `bash self_evolution.sh hourly` — 每30分钟轻量巡检
- `bash self_evolution.sh daily` — 每天深度学习
- `bash self_evolution.sh weekly` — 每周进化

最初创建的 plist 可能分别指向 `run_daily.sh`/`run_weekly.sh`，但这两个脚本从未被创建。service 注册成功但执行失败，导致 `not running` 状态。
